#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import os
import robj
import time
from conary.lib import util as cny_util
from robj.lib import xutil
from xobj import xobj


class WigBackendClient(object):
    """Client for interfacing directly to a Windows Build Service."""

    def __init__(self, url):
        self.api = robj.connect(url, logging=False, maxClients=1)
        self.image = None

    def startJob(self, files):
        """Start a new image build job."""
        # Create image resource
        self.api.images.append({'createdBy': 'nobody'})
        self.image = self.api.images[-1]

        # Upload image files
        for path, filetype in files:
            self.addFile(path, filetype)

        # Initiate job
        self.image.imageJob = self.dataFromObject({
            'type': 'image',
            'createdBy': 'nobody',
            }, tag='job', method='POST')

        return self.image.imageJob

    def watchJob(self):
        """Yield status updates until the image job is done."""
        job = self.image.imageJob
        lastStatus = None
        while True:
            if job.status != lastStatus:
                lastStatus = job.status
                yield job.status
            if job.status not in ('Queued', 'Running'):
                break
            time.sleep(1)
            job.refresh(force=True)

    def finishJob(self):
        """Retrieve image results and clean up job."""
        job = self.image.imageJob

        # Fetch results
        results = job.resultResource
        if not results.elements:
            raise RuntimeError("No files in job result")

        for resFile in results.resultFiles:
            name = resFile._root.path
            size = int(resFile.size)
            infile = resFile.path
            outfile = open(name, 'wb')
            copied = cny_util.copyfileobj(infile, outfile)
            if copied != size:
                raise RuntimeError("File %r is wrong size: expected %s, got %s"
                        % (name, size, copied))

        # Cleanup
        job.delete()
        self.image.delete()

    def dataFromObject(self, data, tag, method='POST',
            contentType='application/xml'):
        xobjData = xutil.XObjify(data, tag)
        content = xobj.toxml(xobjData, tag)
        return robj.HTTPData(content, method, contentType)

    def addFile(self, path, filetype):
        name = os.path.basename(path)
        print 'Adding file', name
        fobj = open(path, 'rb')
        size = os.fstat(fobj.fileno()).st_size

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
