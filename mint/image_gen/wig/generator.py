#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import hashlib
import os
import re
import StringIO
import tempfile
import time
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
from mint.image_gen import constants as iconst
from mint.image_gen.util import FileWithProgress
from mint.image_gen.wig import backend
from mint.image_gen.wig import bootable
from mint.image_gen.wig import install_job

log = logging.getLogger('wig')

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
        util.rmtree(self.workDir)

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

        # Mint service
        self.imageBase = ('%sapi/products/%s/images/%d/' % (data['outputUrl'],
            data['project']['hostname'], data['buildId']) ).encode('utf8')
        self.uploadBase = '%suploadBuild/%d/' % ( data['outputUrl'],
                data['buildId'],)
        self.imageToken = data['outputToken'].encode('ascii')

        self.stepList = STEP_LIST[:]
        self.setStepList()

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


class WbsGenerator(ImageGenerator):
    """
    Base class for generators that require use of a rPath Windows Build Service.
    """

    def run(self):
        self.setConfiguration()
        self.wigClient = backend.WigBackendClient(self.wigServiceUrl)
        self.makeJob()

        if not self.runJob():
            return

        self.convert()
        self.sendStatus(iconst.WIG_JOB_DONE, "Image built")

    def convert(self):
        """Convert image to final format and upload."""
        raise NotImplementedError

    def makeJob(self):
        self.sendStatus(iconst.WIG_JOB_FETCHING, "Retrieving image contents")
        self.installJob.load()
        self.wigClient.createJob()
        self.wigClient.setImageType(self.imageType)

        files = self.installJob.getFilesByClass(install_job.WIMData)
        if not files:
            raise RuntimeError("A WIM must be present in order to build "
                    "Windows images")
        self.wimData = files[0]

        regName = self.wimData.version + self.wimData.arch + '.reg'
        files = self.installJob.getRegularFilesByName(regName)
        if not files:
            raise RuntimeError("Registry file %s was not found" % regName)
        regData = files[0]

        msis = self.installJob.getFilesByClass(install_job.MSIData)
        self.fileCount = 2 + len(msis)
        self.filesTransferred = 0

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
