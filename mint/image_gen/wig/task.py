#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import logging
import hashlib
import json
import os
import restlib.client
import StringIO
from conary import conarycfg
from conary import conaryclient
from conary import files as cny_files
from conary import trove as cny_trove
from conary import trovetup
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from lxml import builder
from lxml import etree
from rmake3.worker import plug_worker

from mint.image_gen import constants as iconst
from mint.image_gen.wig import backend

log = logging.getLogger('wig')


class WigTask(plug_worker.TaskHandler):

    taskType = iconst.WIG_TASK

    def run(self):
        self.sendStatus(iconst.WIG_JOB_FETCHING,
                "Retrieving image contents {1/4}")
        self.setConfiguration()
        self.makeJob()

        self.sendStatus(iconst.WIG_JOB_RUNNING, "Processing image {2/4;0%}")
        ok, message = self.runJob()
        if ok:
            self.sendStatus(iconst.WIG_JOB_UPLOADING,
                    "Transferring image result {3/4}")
            self.postResults()

            self.sendStatus(iconst.WIG_JOB_DONE, "Image built {4/4}")
        else:
            self.wigClient.cleanup()
            self.sendStatus(iconst.WIG_JOB_FAILED, "Build failed: %s" %
                    (message,))

    def setConfiguration(self):
        data = json.loads(self.getData())

        # Image trove tuple
        name = data['troveName'].encode('ascii')
        version = cny_versions.ThawVersion(data['troveVersion'])
        flavor = cny_deps.ThawFlavor(data['troveFlavor'].encode('ascii'))
        self.troveTup = trovetup.TroveTuple(name, version, flavor)

        # Conary configuration
        self.conaryCfg = ccfg = conarycfg.ConaryConfiguration(False)
        for line in data['project']['conaryCfg'].encode('utf-8').splitlines():
            if not line:
                continue
            ccfg.configLine(line)
        # FIXME: hardcoded localhost
        ccfg.configLine('conaryProxy http http://localhost/conary/')
        ccfg.configLine('conaryProxy https http://localhost/conary/')
        self.conaryClient = conaryclient.ConaryClient(self.conaryCfg)

        # WIG service
        # FIXME: hardcoded hostname
        self.wigServiceUrl = 'http://dhcp209.eng.rpath.com/api'
        self.wigClient = backend.WigBackendClient(self.wigServiceUrl)

        # Mint service
        # FIXME: hardcoded localhost
        self.imageBase = ('http://localhost/api/products/%s/images/%d/' % (
                data['project']['hostname'], data['buildId'])
                ).encode('utf8')
        self.uploadBase = 'http://localhost/uploadBuild/%d/' % (
                data['buildId'],)
        self.imageToken = data['outputToken'].encode('ascii')

    def makeJob(self):
        # FIXME: This whole function needs to be rewritten to build an update
        # job so that the packages are ordered correctly.
        jobList = self.getTroveJobList()

        # Fetch all trove contents in one go (for now)
        # FIXME: fetch files separately. It might be streamable that way.
        log.info("Retrieving contents for %d troves", len(jobList))
        repos = self.conaryClient.getRepos()
        cs = repos.createChangeSet(jobList, recurse=False, withFiles=True,
                withFileContents=True)

        interestingFiles = self.filterFiles(cs)

        E = builder.ElementMaker()
        self.wigClient.createJob()
        packageList = []
        for key, value in sorted(interestingFiles):
            # General trove info
            pathId, fileId = key
            path, kind, trvCs, fileInfo, otherInfo = value
            trvName, trvVersion, trvFlavor = trvCs.getNewNameVersionFlavor()
            manifest = '%s=%s[%s]' % (trvName, trvVersion.freeze(), trvFlavor)
            size = fileInfo.contents.size()
            name = os.path.basename(path)

            if kind == 'msi':
                # Use the digest as the name so there aren't conflicts, e.g.
                # two different packages providing Setup.msi
                name = fileInfo.contents.sha1().encode('hex') + '.msi'

                # MSI install job, to be put in servicing.xml
                msiInfo = otherInfo
                pkgXml = E.package(
                        E.type('msi'),
                        E.sequence(str(len(packageList))),
                        E.logFile('install.log'),
                        E.operation('install'),
                        E.productCode(msiInfo.productCode()),
                        E.productName(msiInfo.name()),
                        E.productVerson(msiInfo.version()),
                        E.file(name),
                        E.manifestEntry(manifest),
                        E.previousManifestEntry(''),
                        )
                packageList.append(pkgXml)

            # Upload file contents to the build service.
            log.info("Sending file: pathid=%s fileid=%s path=%s",
                    pathId.encode('hex'), fileId.encode('hex'), path)
            contType, contents = cs.getFileContents(pathId, fileId)
            fobj = contents.get()
            self.wigClient.addFileStream(fobj, kind, name, size)

        # Finish assembling servicing.xml and send it to the build service.
        root = E.update(E.updateJobs(E.updateJob(
            E.sequence('0'),
            E.logFile('setup.log'),
            E.packages(*packageList),
            )))
        doc = etree.tostring(root)
        sio = StringIO.StringIO(doc)
        self.wigClient.addFileStream(sio, 'xml', 'servicing.xml', len(doc))

        # Send registry keys for the rTIS service.
        doc = RTIS_REG_2003_X86.encode('utf-16')
        sio = StringIO.StringIO(doc)
        self.wigClient.addFileStream(sio, 'reg', 'rTIS.reg', len(doc))

    def filterFiles(self, cs):
        # Select files that can be given to the windows build service.
        interestingFiles = []
        for trvCs in cs.iterNewTroveList():
            if trvCs.getName() == 'rTIS:msi':
                # HACK: Telling rTIS to update itself will kill rTIS.
                continue
            for pathId, path, fileId, fileVer in trvCs.getNewFileList():
                fileStream = cs.getFileChange(None, fileId)
                if not cny_files.frozenFileHasContents(fileStream):
                    # No contents
                    continue
                if '.' not in path:
                    # Only files with extensions are interesting
                    continue
                ext = path.split('.')[-1].lower()

                fileInfo = cny_files.ThawFile(fileStream, pathId)
                flags = fileInfo.flags
                if (flags.isEncapsulatedContent()
                        and not flags.isCapsuleOverride()):
                    # No contents
                    continue

                key = pathId, fileId
                if pathId == cny_trove.CAPSULE_PATHID:
                    # Capsule file -- MSI and WIM are interesting
                    if ext == 'msi':
                        otherInfo = trvCs.getTroveInfo().capsule.msi
                    elif ext == 'wim':
                        otherInfo = None
                    else:
                        log.warning("Ignoring capsule file %r -- don't know "
                                "what it is", path)
                        continue
                else:
                    # Regular file -- rTIS.exe is interesting
                    if path.lower() == '/rtis.exe':
                        otherInfo = None
                    else:
                        log.warning("Ignoring regular file %r -- don't know "
                                "what it is", path)
                        continue
                value = path, ext, trvCs, fileInfo, otherInfo
                interestingFiles.append((key, value))

        return interestingFiles

    def getTroveJobList(self):
        """Get list of byDefault troves"""
        log.info("Retrieving trove list for %s", self.troveTup)
        repos = self.conaryClient.getRepos()
        trv = repos.getTrove(*self.troveTup, withFiles=False)
        subtroves = sorted(set( [tup for (tup, isDefault, isStrong)
            in trv.iterTroveListInfo() if isDefault] ))
        return [(n, (None, None), (v, f), True) for (n, v, f) in subtroves]

    def runJob(self):
        self.wigClient.startJob()
        log.info("Job started: %s", self.wigClient.getJobUrl())
        for status, message, progress in self.wigClient.watchJob():
            log.info("Job status: %03d %s: %s", progress, status,
                    message)
            self.sendStatus(iconst.WIG_JOB_RUNNING,
                    "Processing image {2/4;%d%%}" % (progress,))
        ok = status == 'Completed'
        return ok, message

    def _post(self, method, path, contentType='application/xml', body=None):
        # FIXME: copypasta from jobslave, obsoleted by using robj in
        # postResults()
        headers = {
                'Content-Type': contentType,
                'X-rBuilder-OutputToken': self.imageToken,
                }
        url = self.imageBase + path

        client = restlib.client.Client(url, headers)
        client.connect()
        return client.request(method, body)

    def _postFileObject(self, method, targetName, fobj, digest):
        # FIXME: copypasta from jobslave
        headers = {
                'Content-Type': 'application/octet-stream',
                'X-rBuilder-OutputToken': self.imageToken,
                }
        url = self.uploadBase + targetName

        client = FilePutter(url, headers)
        client.connect()
        return client.putFileObject(method, fobj, digest)

    def postResults(self):
        name, size, fobj = self.wigClient.getResults()
        name = name.decode('utf8', 'ignore')

        ctx = hashlib.sha1()
        self._postFileObject('PUT', name, fobj, ctx)

        E = builder.ElementMaker()
        root = E.files(E.file(
            E.title("Windows Image (WIM)"),
            E.size(str(size)),
            E.sha1(ctx.hexdigest()),
            E.fileName(name),
            ))
        self._post('PUT', 'files', body=etree.tostring(root))

        self.wigClient.cleanup()


# FIXME: copypasta from jobslave
class FilePutter(restlib.client.Client):
    CHUNK_SIZE = 16 * 1024

    def putFile(self, method, filePath, digest):
        fObj = open(filePath, 'rb')
        fileSize = os.fstat(fObj.fileno()).st_size
        return self.putFileObject(method, fObj, digest, fileSize)

    def putFileObject(self, method, fObj, digest, fileSize=None):
        headers = self.headers.copy()
        if fileSize is not None:
            headers['Content-Length'] = str(fileSize)
        headers['Content-Type'] = 'application/octet-stream'
        headers['Transfer-Encoding'] = 'chunked'

        conn = self._connection
        conn.request(method, self.path, headers=headers)

        toSend = fileSize
        while toSend is None or toSend > 0:
            if toSend is not None:
                chunkSize = min(toSend, self.CHUNK_SIZE)
            else:
                chunkSize = self.CHUNK_SIZE
            chunk = fObj.read(chunkSize)
            if not chunk:
                break
            chunkSize = len(chunk)

            conn.send('%x\r\n%s\r\n' % (chunkSize, chunk))
            digest.update(chunk)

            if toSend is not None:
                toSend -= chunkSize

        conn.send('0\r\nContent-SHA1: %s\r\n\r\n'
                % (digest.digest().encode('base64'),))

        resp = conn.getresponse()
        if resp.status != 200:
            raise restlib.client.ResponseError(resp.status, resp.reason,
                    resp.msg, resp)
        return resp


# FIXME: this should come from the platform, probably, but definitely doesn't
# belong here.
RTIS_REG_2003_X86 = r"""Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\MountedSYSTEM\ControlSet001\services\rPath Install Manager]
"Type"=dword:00000010
"Start"=dword:00000002
"ErrorControl"=dword:00000001
"ImagePath"=hex(2):25,00,53,00,79,00,73,00,74,00,65,00,6d,00,52,00,6f,00,6f,00,\
  74,00,25,00,5c,00,72,00,70,00,6d,00,61,00,6e,00,2e,00,65,00,78,00,65,00,00,\
  00
"DisplayName"="rPath Install Manager"
"DependOnService"=hex(7):52,00,50,00,43,00,53,00,53,00,00,00,00,00
"ObjectName"="LocalSystem"
"Description"="Manages Unattended Installations"

[HKEY_LOCAL_MACHINE\MountedSYSTEM\ControlSet001\services\eventlog\Application\RPMAN]
"EventMessageFile"="%SystemRoot%\\rpman.exe"
"TypesSupported"=dword:00000007

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\AppID\{8D7E466B-F0FF-44d5-A66C-D725878C7648}]
@="RPMAN"
"LocalService"="RPMAN"
"ServiceParameters"="-Service"

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\AppID\RPMAN.EXE]
"AppID"="{8D7E466B-F0FF-44d5-A66C-D725878C7648}"


[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}]

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}\1.0]
@="RPMAN 1.0 Type Library"

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}\1.0\0]

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}\1.0\0\win32]
@="%SystemRoot%\\rpman.exe"

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}\1.0\FLAGS]
@="0"

[HKEY_LOCAL_MACHINE\MountedSOFTWARE\Classes\TypeLib\{1E26D002-D078-4879-B3FF-80883F12A3A1}\1.0\HELPDIR]
@="%SystemRoot%"


"""
