#
# Copyright (c) 2011 rPath, Inc.
#

import os
import robj
import time
from robj.lib import xutil
from xobj import xobj

from mint import buildtypes


class WigBackendClient(object):
    """Client for interfacing directly to a Windows Build Service."""

    def __init__(self, url):
        self.api = robj.connect(url, logging=False, maxClients=1)
        self.image = None

    def createJob(self):
        # Create image resource
        self.api.images.append({'createdBy': 'nobody'})
        self.image = self.api.images[-1]

    def startJob(self):
        # Initiate job
        self.image.imageJob = self.dataFromObject({
            'type': 'image',
            'createdBy': 'nobody',
            }, tag='job', method='POST')

        return self.image.imageJob

    def watchJob(self):
        """Yield status updates until the image job is done."""
        job = self.image.imageJob
        last = None
        errors = 0
        maxErrors = 10
        while True:
            next = (job.status, job.message, int(job.progress))
            if last != next:
                last = next
                yield next
            if job.status not in ('Queued', 'Running'):
                break
            time.sleep(10)
            try:
                job.refresh(force=True)
            except:
                if errors >= maxErrors:
                    raise
                errors += 1

    def getJobUrl(self):
        return self.image.imageJob.id

    def getResults(self, kind):
        """Return a file handle to the result image."""
        results = self.image.imageJob.resultResource
        if not results.resultFiles.resultFile:
            raise RuntimeError("No files in job result")

        for resFile in results.resultFiles:
            if resFile.type == kind:
                break
        else:
            raise RuntimeError("No %r file in job result" % (kind,))

        size = int(resFile.size)
        fobj = resFile.path
        return size, fobj

    def getLog(self):
        """Return contents of the job log."""
        return self.image.imageJob.logs.read()

    def setImageType(self, imageType):
        config = self.image.jobConfig
        config.iso = config.vhd = 'false'
        if imageType == buildtypes.WINDOWS_ISO:
            config.iso = 'true'
        elif imageType == buildtypes.WINDOWS_WIM:
            pass
        else:
            # Assume we need a VHD for the next layer up to convert into
            # something else.
            config.vhd = 'true'
        config.persist()

    def setOSVersion(self, osVersion):
        config = self.image.jobConfig
        config.osVersion = osVersion
        config.persist()

    def cleanup(self):
        if self.image:
            self.image.imageJob.delete()
            self.image.delete()
            self.image = None

    def dataFromObject(self, data, tag, method='POST',
            contentType='application/xml'):
        xobjData = xutil.XObjify(data, tag)
        content = xobj.toxml(xobjData, tag)
        return robj.HTTPData(content, method, contentType)

    def addFile(self, path, filetype):
        name = os.path.basename(path)
        fobj = open(path, 'rb')
        size = os.fstat(fobj.fileno()).st_size
        self.addFileStream(fobj, filetype, name, size)

    def addFileStream(self, fobj, filetype, name, size):
        # Create file resource
        self.image.files.append({
            'path': name,
            'type': filetype,
            'size': str(size),
            })
        file_res = self.image.files[-1]

        # PUT file contents
        data = robj.HTTPData(data=fobj, size=size, chunked=False)
        file_res.path = data
