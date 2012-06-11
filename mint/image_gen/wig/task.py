#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import hashlib
import itertools
import json
import os
import re
import StringIO
import time
from collections import namedtuple
from conary import callbacks
from conary import conarycfg
from conary import conaryclient
from conary import files as cny_files
from conary import trove as cny_trove
from conary import trovetup
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from lxml import builder
from lxml import etree
from restlib import client as rl_client
from rmake3.worker import plug_worker
from xobj import xobj

from jobslave import job_data
from mint import buildtypes
from mint.image_gen import constants as iconst
from mint.image_gen.util import FileWithProgress
from mint.image_gen.wig import backend
from mint.image_gen.wig import bootable

log = logging.getLogger('wig')


FileData = namedtuple('FileInfo',
        'pathId fileId fileVer '
        'path kind trvCs fileInfo otherInfo '
        'critical')

CRITICAL_PACKAGES = set(('rTIS:msi',))

NON_BOOTABLE_TYPES = [buildtypes.WINDOWS_ISO, buildtypes.WINDOWS_WIM]

# This list is used in order to automatically map status codes to a "step
# number". For example, when sendStatus(WIG_JOB_SENDING) is invoked, the
# progress element {2/5} would be sent. Some tasks may have variations on this
# step list, they will modify it to include only the steps that will be invoked
# so the numbers line up.
STEP_LIST = [
        iconst.WIG_JOB_QUEUED,
        iconst.WIG_JOB_FETCHING,
        iconst.WIG_JOB_SENDING,
        iconst.WIG_JOB_RUNNING,
        iconst.WIG_JOB_CONVERTING,
        iconst.WIG_JOB_UPLOADING,
        iconst.WIG_JOB_DONE,
        ]


class WigTask(plug_worker.TaskHandler):

    taskType = iconst.WIG_TASK
    tempDir = '/srv/rbuilder/tmp'

    def run(self):
        self.setConfiguration()
        self.makeJob()

        if not self.runJob():
            return

        if self.imageType in NON_BOOTABLE_TYPES:
            # WIMs and ISOs can be uploaded directly
            if self.imageType == buildtypes.WINDOWS_ISO:
                kind = 'iso'
                title = "Installable CD/DVD (ISO)"
            else:
                kind = 'wim'
                title = "Windows Image (WIM)"
            size, fobj = self.wigClient.getResults(kind)
            outputName = '%s.%s' % (self.jobData['baseFileName'], kind)
            self.postResults([(fobj, size, outputName, title)])
        else:
            self.convert()
        self.sendStatus(iconst.WIG_JOB_DONE, "Image built")

    def sendStatus(self, code, text, extraProgress=''):
        if code in self.stepList:
            # Automatically append progress information if the status code is
            # in the step list.
            currentStep = self.stepList.index(code)
            totalSteps = len(self.stepList) - 1  # minus the DONE "step"
            progress = '%d/%d' % (currentStep, totalSteps)
            if extraProgress:
                progress += ';' + extraProgress
            text += ' {%s}' % (progress,)
        plug_worker.TaskHandler.sendStatus(self, code, text)

    def setConfiguration(self):
        data = self.jobData = job_data.JobData(json.loads(self.getData()))

        # Image trove tuple
        name = data['troveName'].encode('ascii')
        version = cny_versions.ThawVersion(data['troveVersion'])
        flavor = cny_deps.ThawFlavor(data['troveFlavor'].encode('ascii'))
        self.troveTup = trovetup.TroveTuple(name, version, flavor)
        data['troveTup'] = self.troveTup

        # Image parameters
        self.imageType = data['buildType']
        baseFileName = data.get('baseFileName') or ''
        if baseFileName:
            baseFileName = re.sub('[^a-zA-Z0-9.-]', '_', baseFileName)
        else:
            try:
                arch = self.troveTup.flavor.members[cny_deps.DEP_CLASS_IS
                        ].members.keys()[0]
            except KeyError:
                arch = ''
            baseFileName = '-'.join((
                data['project']['hostname'],
                self.troveTup.version.trailingRevision().version,
                arch))
        self.jobData['baseFileName'] = baseFileName.encode('utf8')

        # Conary configuration
        self.conaryCfg = ccfg = conarycfg.ConaryConfiguration(False)
        for line in data['project']['conaryCfg'].encode('utf-8').splitlines():
            if not line:
                continue
            ccfg.configLine(line)
        ccfg.configLine('conaryProxy http %sconary' % (data['outputUrl']))
        ccfg.configLine('conaryProxy https %sconary' % (data['outputUrl']))
        ccfg.dbPath = ':memory:'
        self.conaryClient = conaryclient.ConaryClient(self.conaryCfg)

        # WIG service
        self.wigServiceUrl = data['windowsBuildService']
        self.wigClient = backend.WigBackendClient(self.wigServiceUrl)

        # Mint service
        self.imageBase = ('%sapi/products/%s/images/%d/' % (data['outputUrl'],
            data['project']['hostname'], data['buildId']) ).encode('utf8')
        self.uploadBase = '%suploadBuild/%d/' % ( data['outputUrl'],
                data['buildId'],)
        self.imageToken = data['outputToken'].encode('ascii')

        # Finalize the list of steps we will perform based on the image type
        # chosen.
        self.stepList = STEP_LIST[:]
        if self.imageType in NON_BOOTABLE_TYPES:
            self.stepList.remove(iconst.WIG_JOB_CONVERTING)

    def makeJob(self):
        E = builder.ElementMaker()

        self.sendStatus(iconst.WIG_JOB_FETCHING, "Retrieving image contents")

        jobList = self.getTroveJobList()

        # Fetch file list but no contents, this way we can stream the files
        # individually.
        log.info("Retrieving metadata for %d troves", len(jobList))
        repos = self.conaryClient.getRepos()
        cs = repos.createChangeSet(jobList, recurse=False, withFiles=True,
                withFileContents=False)
        interestingFiles, fileMap = self.filterFiles(cs)

        self.wigClient.createJob()

        # Choose between WIM and ISO output.
        self.wigClient.setImageType(self.imageType)

        # Select a rTIS registry bootstrap file.
        regFile = self.selectRegFile(fileMap)
        interestingFiles.append(regFile)

        criticalPackageList = []
        packageList = []
        totalFiles = len(interestingFiles)
        for n, data in enumerate(sorted(interestingFiles)):
            name = os.path.basename(data.path)

            if data.kind == 'msi':
                if data.critical:
                    pkgXml, name = self.processMSI(data,
                                                   seq=len(criticalPackageList),
                                                   critical=data.critical)
                    criticalPackageList.append(pkgXml)
                else:
                    pkgXml, name = self.processMSI(data, seq=len(packageList),
                                                   critical=data.critical)
                    packageList.append(pkgXml)
            elif data.kind == 'reg':
                name = 'rTIS.reg'

            self.sendContents(name, data, n, totalFiles)

        # Finish assembling servicing.xml and send it to the build service.
        sysModel = 'install %s=%s\n' % (
            self.troveTup.name, str(self.troveTup.version))
        pollingManifest = '%s=%s[%s]\n' % (
            self.troveTup.name, self.troveTup.version.freeze(),
            str(self.troveTup.flavor))

        jobs = []
        if criticalPackageList:
            jobs.append(E.updateJob(
                    E.sequence('0'),
                    E.logFile('install.log'),
                    E.packages(*criticalPackageList),
                    ))
        if packageList:
            jobs.append(E.updateJob(
                    E.sequence('1'),
                    E.logFile('install.log'),
                    E.packages(*packageList),
                    ))
        root = E.update(
            E.logFile('install.log'),
            E.systemModel(sysModel),
            E.pollingManifest(pollingManifest),
            E.updateJobs(*jobs)
            )
        doc = etree.tostring(root)
        sio = StringIO.StringIO(doc)
        self.wigClient.addFileStream(sio, 'xml', 'servicing.xml', len(doc))

    def sendContents(self, name, data, seq, total):
        """Transfer file from repository to build service."""
        repos = self.conaryClient.getRepos()
        size = data.fileInfo.contents.size()
        statusString = "Transferring file " + name
        progressString = "%d/%d;%%d%%%%" % (seq, total)

        # Retrieve contents
        # Note that getFileContents doesn't pipeline, so rather than creating
        # yet another substep just use the first 50% for fetching and the
        # second 50% for sending.
        last = [time.time()]
        class FetchCallback(callbacks.ChangesetCallback):
            def downloadingFileContents(xself, transferred, _):
                if time.time() - last[0] < 2:
                    return
                last[0] = time.time()
                if size:
                    percent = int(50.0 * transferred / size)
                else:
                    percent = 0
                self.sendStatus(iconst.WIG_JOB_SENDING, statusString,
                        progressString % percent)

        self.sendStatus(iconst.WIG_JOB_SENDING, statusString,
                progressString % 0)
        fobj = repos.getFileContents( [(data.fileId, data.fileVer)],
                callback=FetchCallback() )[0].get()

        # Report progress for file upload.
        def sendCallback(transferred):
            if size:
                percent = 50 + int(50.0 * transferred / size)
            else:
                percent = 50
            self.sendStatus(iconst.WIG_JOB_SENDING, statusString,
                    progressString % percent)

        # Upload file contents to the build service.
        log.info("Sending file: pathid=%s fileid=%s path=%s",
                data.pathId.encode('hex'), data.fileId.encode('hex'),
                data.path)
        wrapper = FileWithProgress(fobj, sendCallback)
        self.wigClient.addFileStream(wrapper, data.kind, name, size)

    def filterFiles(self, cs):
        # Select files that can be given to the windows build service.
        interestingFiles = []
        fileMap = {}
        for trvCs in cs.iterNewTroveList():
            critical = (trvCs.getName() in CRITICAL_PACKAGES)

            for pathId, path, fileId, fileVer in trvCs.getNewFileList():
                fileStream = cs.getFileChange(None, fileId)
                if not cny_files.frozenFileHasContents(fileStream):
                    # No contents
                    continue
                if '.' not in path:
                    # Only files with extensions are interesting
                    continue
                name = os.path.basename(path)
                ext = name.split('.')[-1].lower()

                fileInfo = cny_files.ThawFile(fileStream, pathId)
                flags = fileInfo.flags
                if (flags.isEncapsulatedContent()
                        and not flags.isCapsuleOverride()):
                    # No contents
                    continue

                keep, otherInfo = self.filterFile(pathId, path, ext, trvCs)
                if not keep:
                    continue

                data = FileData(pathId, fileId, fileVer, path, ext, trvCs,
                        fileInfo, otherInfo, critical)
                if ext != 'reg':
                    # Reg files are added later
                    interestingFiles.append(data)
                fileMap.setdefault(ext, []).append(data)

        return interestingFiles, fileMap

    def filterFile(self, pathId, path, ext, trvCs):
        """Is the file interesting, and what other metadata is there?"""
        if pathId == cny_trove.CAPSULE_PATHID:
            # Capsule file
            if ext == 'msi':
                # MSI package to be installed
                return True, trvCs.getTroveInfo().capsule.msi
            elif ext == 'wim':
                # Base platform WIM
                return True, trvCs.getTroveInfo().capsule.wim
            else:
                log.warning("Ignoring capsule file %r -- don't know "
                        "what it is", path)
        else:
            # Regular file
            if path.lower() == '/rtis.exe':
                # rTIS bootstrap executable
                return True, None
            elif ext == 'reg':
                # rTIS bootstrap registry entry
                return True, None
            elif path.lower() == '/platform-isokit.zip':
                # WinPE and associated ISO generation tools
                if self.imageType == buildtypes.WINDOWS_ISO:
                    return True, None
            else:
                log.warning("Ignoring regular file %r -- don't know "
                        "what it is", path)
        return False, None

    def processMSI(self, data, seq, critical=False):
        """Return install job XML for a MSI package."""
        E = builder.ElementMaker()

        # Use the digest as the name so there aren't conflicts, e.g.
        # two different packages providing Setup.msi
        name = data.fileInfo.contents.sha1().encode('hex') + '.msi'

        # MSI install job, to be put in servicing.xml
        trvName, trvVersion, trvFlavor = data.trvCs.getNewNameVersionFlavor()
        manifest = '%s=%s[%s]' % (trvName, trvVersion.freeze(),
                trvFlavor)
        msiInfo = data.otherInfo
        pkgXml = E.package(
                E.type('msi'),
                E.sequence(str(seq)),
                E.logFile('install.log'),
                E.operation('install'),
                E.productCode(msiInfo.productCode()),
                E.productName(msiInfo.name()),
                E.productVerson(msiInfo.version()),
                E.file(name),
                E.manifestEntry(manifest),
                E.previousManifestEntry(''),
                E.critical(str(critical).lower()),
                )

        return pkgXml, name

    def selectRegFile(self, fileMap):
        wimFiles = fileMap.get('wim', [])
        if len(wimFiles) != 1:
            raise RuntimeError("Appliance groups must contain exactly one "
                    "WIM capsule.")
        wimData = wimFiles[0].otherInfo
        imgIdx = str(wimData.volumeIndex())
        wimXml = xobj.parse(wimData.infoXml())

        images = wimXml.WIM.IMAGE
        if not isinstance(images, list):
            images = [images]
        for image in images:
            if image.INDEX == imgIdx:
                break
        else:
            raise RuntimeError("Image index %s was not found." % (imgIdx,))

        arch = image.WINDOWS.ARCH
        if arch == '0':
            archPart = 'x86'
            vmwareSuffix = ''
        elif arch == '9':
            archPart = 'x64'
            vmwareSuffix = '-64'
        else:
            raise RuntimeError("WIM has unsupported architecture %r" % (arch,))

        version = [int(x) for x in wimData.version().split('.')][:2]
        if version >= [6, 0]:
            # Windows Server 2008 (and later, including R2)
            verPart = '2008'
            vmwareName = 'windows7srv'
        else:
            # Windows Server 2003
            verPart = '2003'
            vmwareName = 'winNetStandard'
        self.jobData['vmwareOS'] = vmwareName + vmwareSuffix

        regPath = '/%s%s.reg' % (verPart, archPart)
        for fileData in fileMap.get('reg', []):
            if fileData.path == regPath:
                return fileData
        raise RuntimeError("The rTIS package does not contain the "
                "required registry file %r" % (regPath,))

    def getTroveJobList(self):
        """Return a set of trove install jobs in dependency order."""
        log.info("Retrieving trove list for %s", self.troveTup)
        job = self.conaryClient.newUpdateJob()
        self.conaryClient.prepareUpdateJob(job,
                [(self.troveTup.name, (None, None), (self.troveTup.version,
                    self.troveTup.flavor), True)],
                checkPathConflicts=False)
        return list(itertools.chain(*job.jobs))

    def runJob(self):
        self.sendStatus(iconst.WIG_JOB_RUNNING, "Processing image", "0%")
        self.wigClient.startJob()
        log.info("Job started: %s", self.wigClient.getJobUrl())
        # KLUDGE: This can go away once rMake's build logs are actually piped
        # somewhere.
        self.sendLog("Job started, URL is: %s\n" % self.wigClient.getJobUrl())

        for status, message, progress in self.wigClient.watchJob():
            log.info("Job status: %03d %s: %s", progress, status,
                    message)
            message = message.strip()
            if message and status != 'Completed':
                # Don't update the message at completion because saying "The
                # job has completed" might confuse users into thinking the
                # entire image build is done when it is really just one part...
                self.sendStatus(iconst.WIG_JOB_RUNNING,
                        "Processing image: " + message,
                        extraProgress=("%d%%" % (progress,)) )

        # TODO: send logs upstream to rMake as well
        logs = self.wigClient.getLog()
        self.sendLog(logs)

        if status != 'Completed':
            self.sendStatus(iconst.WIG_JOB_FAILED, "Image failed: %s" %
                    (message,))
            return False
        return True

    def _post(self, method, path, contentType='application/xml', body=None):
        # FIXME: copypasta from jobslave, obsoleted by using robj in
        # postResults()
        headers = {
                'Content-Type': contentType,
                'X-rBuilder-OutputToken': self.imageToken,
                }
        url = self.imageBase + path

        client = rl_client.Client(url, headers)
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

    def sendLog(self, data):
        try:
            self._post('POST', 'buildLog', contentType='text/plain', body=data)
        except rl_client.ResponseError, err:
            if err.status != 204:  # No Content
                raise

    def convert(self):
        """Fetch the VHD result, convert as needed, then upload."""
        size, fobj = self.wigClient.getResults('vhd')
        converter = bootable.getConverter(jobData=self.jobData, vhdObj=fobj,
                vhdSize=size, tempDir=self.tempDir, callback=self.sendStatus)
        self.sendStatus(iconst.WIG_JOB_CONVERTING, "Creating %s image" %
                converter.getImageTitle())
        try:
            outputPaths = converter.convert()
            outputFiles = [(open(path, 'rb'), os.stat(path).st_size,
                os.path.basename(path), title)
                for (path, title) in outputPaths]
            self.postResults(outputFiles)
        finally:
            converter.destroy()

    def _postOneResult(self, fobj, size, name, title, seq, total):
        """Upload a single file and return the XML fragment for the rBuilder
        API.
        """
        statusString = "Transferring image result " + name
        progressString = "%d/%d;%%d%%%%" % (seq, total)
        self.sendStatus(iconst.WIG_JOB_UPLOADING, statusString,
                progressString % 0)

        # Report progress for file upload.
        def callback(transferred):
            if size:
                percent = int(100.0 * transferred / size)
            else:
                percent = 0
            self.sendStatus(iconst.WIG_JOB_UPLOADING,
                    "Transferring image result", "%d%%" % (percent,))
        wrapper = FileWithProgress(fobj, callback)

        # Also calculate SHA-1 digest as it uploads.
        ctx = hashlib.sha1()
        self._postFileObject('PUT', name, wrapper, ctx)

        E = builder.ElementMaker()
        fileXml = E.file(
            E.title(title),
            E.size(str(size)),
            E.sha1(ctx.hexdigest()),
            E.fileName(name),
            )
        return fileXml

    def postResults(self, outputFiles):
        """Upload several files and post the file list to rBuilder.

        C{outputFiles} should be a list of 4-tuples like
        C{(fobj, size, name, title)}.
        """
        xmlFiles = []
        for n, (fobj, size, name, title) in enumerate(outputFiles):
            fileXml = self._postOneResult(fobj, size, name, title, n,
                    len(outputFiles))
            xmlFiles.append(fileXml)

        E = builder.ElementMaker()
        root = E.files(*xmlFiles)
        self._post('PUT', 'files', body=etree.tostring(root))

        self.wigClient.cleanup()


# FIXME: copypasta from jobslave
class FilePutter(rl_client.Client):
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
            raise rl_client.ResponseError(resp.status, resp.reason,
                    resp.msg, resp)
        return resp
