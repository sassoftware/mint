#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import hashlib
import json
import os
import restlib.client
from conary import conarycfg
from conary import conaryclient
from conary import files as cny_files
from conary import trove as cny_trove
from conary import trovetup
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from rmake3.worker import plug_worker
from xml.etree import ElementTree as ET

from mint.image_gen import constants as iconst
from mint.image_gen.wig import backend


class WigTask(plug_worker.TaskHandler):

    taskType = iconst.WIG_TASK

    def run(self):
        self.sendStatus(iconst.WIG_JOB_FETCHING,
                "Retrieving image contents {1/4}")
        self.setConfiguration()
        self.makeJob()

        self.sendStatus(iconst.WIG_JOB_RUNNING, "Processing image {2/4}")
        self.runJob()

        self.sendStatus(iconst.WIG_JOB_UPLOADING,
                "Transferring image result {3/4}")
        self.postResults()

        self.sendStatus(iconst.WIG_JOB_DONE, "Image built {4/4}")

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
        jobList = self.getTroveJobList()

        # Fetch all trove contents in one go (for now)
        print 'Retrieving image contents'
        repos = self.conaryClient.getRepos()
        cs = repos.createChangeSet(jobList, recurse=False, withFiles=True,
                withFileContents=True)

        interestingFiles = self.filterFiles(cs)

        self.wigClient.createJob()
        for pathId, fileId, path, kind, fileInfo in sorted(interestingFiles):
            print pathId.encode('hex'), fileId.encode('hex'), path
            size = fileInfo.contents.size()
            name = os.path.basename(path)
            contType, contents = cs.getFileContents(pathId, fileId)
            fobj = contents.get()
            self.wigClient.addFileStream(fobj, kind, name, size)

    def filterFiles(self, cs):
        # Select files that can be given to the windows build service.
        interestingFiles = []
        for trvCs in cs.iterNewTroveList():
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
                if pathId == cny_trove.CAPSULE_PATHID:
                    # Capsule file -- MSI and WIM are interesting
                    if ext in ('msi', 'wim'):
                        interestingFiles.append((pathId, fileId, path, ext,
                            fileInfo))
                    else:
                        print "Don't know what to do with capsule file %r" % (
                                path,)
                        continue
                else:
                    # Regular file -- rTIS.exe is interesting
                    if path.lower() == '/rtis.exe':
                        continue  # FIXME
                        interestingFiles.append((pathId, fileId, path, 'rtis',
                            fileInfo))
                    else:
                        print "Don't know what to do with regular file %r" % (
                                path,)
                        continue

        return interestingFiles

    def getTroveJobList(self):
        """Get list of byDefault troves"""
        print 'Retrieving trove list'
        repos = self.conaryClient.getRepos()
        trv = repos.getTrove(*self.troveTup, withFiles=False)
        subtroves = sorted(set( [tup for (tup, isDefault, isStrong)
            in trv.iterTroveListInfo() if isDefault] ))
        return [(n, (None, None), (v, f), True) for (n, v, f) in subtroves]

    def runJob(self):
        self.wigClient.startJob()
        for status in self.wigClient.watchJob():
            print status

    def _post(self, method, path, contentType='application/xml', body=None):
        # FIXME: copypata from jobslave, obsoleted by using robj in postResults()
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

        # FIXME: copypasta from jobslave, replace with robj
        root = ET.Element('files')
        fileElem = ET.SubElement(root, 'file')
        ET.SubElement(fileElem, 'title').text = "Windows Image (WIM)"
        ET.SubElement(fileElem, 'size').text = str(size)
        ET.SubElement(fileElem, 'sha1').text = ctx.hexdigest()
        ET.SubElement(fileElem, 'fileName').text = name

        self._post('PUT', 'files', body=ET.tostring(root))

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
