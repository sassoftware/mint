#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import os
import robj
import time
from robj.lib import xutil
from xobj import xobj


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
        while True:
            next = (job.status, job.message, int(job.progress))
            if last != next:
                last = next
                yield next
            if job.status not in ('Queued', 'Running'):
                break
            time.sleep(1)
            job.refresh(force=True)

    def getJobUrl(self):
        return self.image.imageJob.id

    def getResults(self):
        """Return a file handle to the result image."""
        results = self.image.imageJob.resultResource
        if not results.elements:
            raise RuntimeError("No files in job result")

        resFile = results.resultFiles[0]
        name = resFile._root.path
        size = int(resFile.size)
        fobj = resFile.path
        return name, size, fobj

    def cleanup(self):
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
