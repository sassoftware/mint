#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import hashlib
import json
import os
import re
import StringIO
import tempfile
import time
import zipfile
from collections import namedtuple
from conary import callbacks
from conary import conarycfg
from conary import conaryclient
from conary import trovetup
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from conary.lib import util
from lxml import builder
from lxml import etree
from restlib import client as rl_client
from rmake3.worker import plug_worker

from jobslave import job_data
from mint import buildtypes
from mint.image_gen import constants as iconst
from mint.image_gen.util import FileWithProgress
from mint.image_gen.wig import backend
from mint.image_gen.wig import bootable
from mint.image_gen.wig import install_job
from mint.lib.subprocutil import logCall

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

    def run(self):
        data = job_data.JobData(json.loads(self.getData()))
        imageType = data['buildType']
        if imageType == buildtypes.WINDOWS_ISO:
            genClass = IsoGenerator
        elif imageType == buildtypes.WINDOWS_WIM:
            genClass = WimGenerator
        elif imageType in (buildtypes.VMWARE_IMAGE,
                buildtypes.VMWARE_ESX_IMAGE):
            genClass = ConvertedImageGenerator
        else:
            raise TypeError("Invalid Windows image type %s" % imageType)
        generator = genClass(self, data)
        try:
            generator.run()
        finally:
            generator.destroy()


class ImageGenerator(object):
    """
    Base class for all Windows image generators.
    """

    tempDir = '/srv/rbuilder/tmp'

    def __init__(self, parent, jobData):
        self.parent = parent
        self.jobData = jobData
        self.installJob = None
        self.workDir = tempfile.mkdtemp(dir=self.tempDir, prefix='imagegen-')

    def destroy(self):
        #util.rmtree(self.workDir)
        pass

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
        log.info("Sending status: %s %s", code, text)
        self.parent.sendStatus(code, text)

    def setConfiguration(self):
        data = self.jobData

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

        # Install job
        self.installJob = install_job.InstallJob(self.conaryClient,
                [self.troveTup])

        # WIG service
        self.wigServiceUrl = data['windowsBuildService']
        self.wigClient = backend.WigBackendClient(self.wigServiceUrl)

        # Mint service
        self.imageBase = ('%sapi/products/%s/images/%d/' % (data['outputUrl'],
            data['project']['hostname'], data['buildId']) ).encode('utf8')
        self.uploadBase = '%suploadBuild/%d/' % ( data['outputUrl'],
                data['buildId'],)
        self.imageToken = data['outputToken'].encode('ascii')

        self.stepList = STEP_LIST[:]
        self.setStepList()

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


class IsoGenerator(ImageGenerator):

    def run(self):
        self.setConfiguration()
        self.runJob()
        self.upload()
        self.sendStatus(iconst.WIG_JOB_DONE, "Image built")

    def setStepList(self):
        self.stepList = [
                iconst.WIG_JOB_QUEUED,
                iconst.WIG_JOB_FETCHING,
                iconst.WIG_JOB_SENDING,
                iconst.WIG_JOB_RUNNING,
                iconst.WIG_JOB_UPLOADING,
                iconst.WIG_JOB_DONE,
                ]

    def runJob(self):
        E = builder.ElementMaker()

        self.sendStatus(iconst.WIG_JOB_FETCHING, "Retrieving image contents")
        self.installJob.load()

        isoDir = os.path.join(self.workDir, 'iso')
        updateDir = os.path.join(isoDir, 'rPath/DeploymentUpdate')

        # Gather a list of files to fetch so that we fail fast if something is
        # missing and so that the progress reporting has an accurate total.
        files = self.installJob.getFilesByClass(install_job.WIMData)
        if not files:
            raise RuntimeError("A WIM must be present in order to build "
                    "Windows images")
        self.wimData = files[0]

        files = self.installJob.getRegularFilesByName('/platform-isokit.zip')
        if not files:
            raise RuntimeError("A platform-isokit.zip must be present in "
                    "order to build Installable ISO images")
        self.isokitData = files[0]

        msis = self.installJob.getFilesByClass(install_job.MSIData)
        self.fileCount = 2 + len(msis)
        self.filesTransferred = 0

        # Download isokit first and extract the basic ISO directory structure.
        self.unpackIsokit()

        osName = self.wimData.version
        if osName.startswith('2003'):
            # XXX FIXME
            raise NotImplementedError
        else:
            # 2008, 2008R2
            winFirstBootPath = 'C:\\Windows\\Setup\\Scripts\\SetupComplete.cmd'
            winUpdateDir = 'C:\\ProgramData\\rPath\\Updates\\DeploymentUpdate'

        # Download WIM directly into the output directory.
        progressCallback = self._startFileProgress(self.wimData)
        outF = open(isoDir + '/sources/image.wim', 'wb')
        self.wimData.storeContents(outF, progressCallback)
        outF.close()

        # Download and store MSIs.
        criticalPackageList = []
        packageList = []
        rtisPath = None
        for msiData in msis:
            name = os.path.basename(msiData.fileTup.path)

            # Append package to either the critical or regular package list.
            if msiData.isCritical():
                targetList = criticalPackageList
            else:
                targetList = packageList
            pkgXml = msiData.getPackageXML(seqNum=len(targetList))
            targetList.append(pkgXml)

            # Store MSI directly to the output directory.
            relPath = os.path.join(msiData.getProductCode(), name)
            destPath = os.path.join(updateDir, relPath)
            util.mkdirChain(os.path.dirname(destPath))

            outF = open(destPath, 'wb')
            progressCallback = self._startFileProgress(msiData)
            msiData.storeContents(outF, progressCallback)
            outF.close()

            # Remember the path to rTIS so it can be pre-installed on first
            # boot.
            if msiData.troveTuple[0].lower() == 'rtis:msi':
                rtisPath = relPath

        # Write batch script to copy MSIs and prepare rTIS bootstrap.
        fobj = open(isoDir + '/rPath/copymsi.bat', 'w')
        fobj.write('xcopy /e /y '
                '%%binpath%%\\DeploymentUpdate %(winUpdateDir)s\\\r\n'
                % dict(winUpdateDir=winUpdateDir))
        fobj.write('md %(winFirstBootDir)s\r\n'
                % dict(winFirstBootDir=winFirstBootPath.rsplit('\\', 1)[0]))
        fobj.write('copy /y %%binpath%%\\firstboot.bat '
                '"%(winFirstBootPath)s"\r\n'
                % dict(winFirstBootPath=winFirstBootPath))
        fobj.close()

        # Write first-boot script to bootstrap rTIS.
        fobj = open(isoDir + '/rPath/firstboot.bat', 'w')
        if rtisPath:
            fobj.write('msiexec /i '
                    '"%(winUpdateDir)s\\%(rtisPath)s" '
                    '/quiet /norestart '
                    '/l*v "%(winUpdateDir)s\\%(rtisLog)s" '
                    '\r\n' % dict(
                        winUpdateDir=winUpdateDir,
                        rtisPath=rtisPath,
                        rtisLog=rtisPath.rsplit('.', 1)[0] + '.Install.log',
                        ))
        fobj.close()

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
        fobj = open(updateDir + '/servicing.xml', 'w')
        fobj.write(doc)
        fobj.close()

        # Build ISO
        last = [time.time()]
        self.sendStatus(iconst.WIG_JOB_RUNNING, "Creating ISO", "0%")
        def _mkisofs_callback(pipe, line):
            if '% done' in line:
                if time.time() - last[0] < 2:
                    return
                last[0] = time.time()
                percent = line.split('% done')[0].strip()
                percent = int(float(percent))
                self.sendStatus(iconst.WIG_JOB_RUNNING,
                        "Creating ISO", "%d%%" % percent)
        logCall(['mkisofs',
            '-udf',
            '-b', 'boot/etfsboot.com',
            '-no-emul-boot',
            '-f', # follow symlinks
            '-o', self.workDir + '/output.iso',
            isoDir,
            ], callback=_mkisofs_callback)

    def _startFileProgress(self, fileData):
        """Report that a file transfer has started and return a callback that
        callers can use to update the progress.
        """
        name = os.path.basename(fileData.fileTup.path)
        statusString = "Transferring file " + name
        progressString = "%d/%d;%%d%%%%" % (self.filesTransferred,
                self.fileCount)
        self.sendStatus(iconst.WIG_JOB_SENDING, statusString,
                progressString % 0)
        last = [time.time()]
        interval = 2
        def callback(percent):
            now = time.time()
            if now - last[0] < interval:
                return
            last[0] = now
            self.sendStatus(iconst.WIG_JOB_SENDING, statusString,
                    progressString % int(percent))
        self.filesTransferred += 1
        return callback

    def unpackIsokit(self):
        ikData = self.isokitData
        ikPath = os.path.join(self.workDir, 'isokit.zip')
        outF = open(ikPath, 'wb')
        progressCallback = self._startFileProgress(ikData)
        ikData.storeContents(outF, progressCallback)
        outF.close()

        zf = zipfile.ZipFile(ikPath, 'r')
        for name in zf.namelist():
            norm = os.path.normpath(name)
            if not norm.startswith('isoKit/'):
                raise RuntimeError("Invalid isokit.zip")
            path = os.path.join(self.workDir, norm)
            if name.endswith('/'):
                util.mkdirChain(path)
            else:
                util.mkdirChain(os.path.dirname(path))
                f_in = zf.open(name)
                f_out = open(path, 'wb')
                util.copyfileobj(f_in, f_out)
                f_in.close()
                f_out.close()
        zf.close()

        # Move directory structures into place
        isoDir = os.path.join(self.workDir, 'iso')
        ikDir = os.path.join(self.workDir, 'isoKit')
        osName = self.wimData.version
        os.rename(ikDir + '/ISO', isoDir)
        os.rename(ikDir + '/os/' + osName, isoDir + '/rPath/os')

    def upload(self):
        kind = 'iso'
        title = "Installable CD/DVD (ISO)"
        outputName = '%s.%s' % (self.jobData['baseFileName'], kind)
        fObj = open(self.workDir + '/output.iso', 'rb')
        fileSize = os.fstat(fObj.fileno()).st_size
        self.postResults([(fObj, fileSize, outputName, title)])


class WbsGenerator(ImageGenerator):
    """
    Base class for generators that require use of a rPath Windows Build Service.
    """

    def run(self):
        self.setConfiguration()
        self.makeJob()

        if not self.runJob():
            return

        self.convert()
        self.sendStatus(iconst.WIG_JOB_DONE, "Image built")

    def convert(self):
        """Convert image to final format and upload."""
        raise NotImplementedError

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


class WimGenerator(WbsGenerator):

    def setStepList(self):
        self.stepList.remove(iconst.WIG_JOB_CONVERTING)

    def convert(self):
        kind = 'wim'
        title = "Windows Image (WIM)"
        size, fobj = self.wigClient.getResults(kind)
        outputName = '%s.%s' % (self.jobData['baseFileName'], kind)
        self.postResults([(fobj, size, outputName, title)])
        self.wigClient.cleanup()


class ConvertedImageGenerator(WbsGenerator):

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
            self.wigClient.cleanup()
        finally:
            converter.destroy()



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
