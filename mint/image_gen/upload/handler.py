#
# Copyright (c) 2011 rPath, Inc.
#

import logging
from collections import namedtuple

from rmake3.lib import chutney
from mint import jobstatus
from mint.image_gen import constants as iconst
from mint.image_gen import handler
from mint.image_gen import util

log = logging.getLogger('image_upload')


ImageUploadParams = namedtuple('ImageUploadParams', 'imageURL image')
chutney.register(ImageUploadParams)


class ImageUploadHandler(handler.BaseImageHandler):

    jobType = iconst.IUP_JOB
    firstState = 'run'

    def setup(self):
        self.params = self.getData()
        self.imageBase = self.params.imageURL.asString()
        self.imageToken = self.params.imageURL.headers[
                'X-rBuilder-OutputToken']
        self.toUpload = list(self.params.image.files)
        self.log = util.getLogSender(self.clock, self._uploadLog, 'upload')

    def close(self):
        if self.log:
            for lh in self.log.handlers:
                lh.close()
            self.log = None
        handler.BaseImageHandler.close(self)

    def run(self):
        self.setStatus(iconst.IUP_JOB_QUEUED, "Waiting for processing")
        task = self.newTask('upload', iconst.IUP_TASK, self.job.data)

        # Copy task status changes to job status
        self.watchTask(task, self._mirrorTaskStatus)
        # Exit job handler when task completes
        d = self.waitForTask(task)
        d.addCallback(lambda _: 'done')
        return d

    def _translateCode(self, code):
        if code == iconst.IUP_JOB_QUEUED:
            return jobstatus.WAITING
        elif code < 200:
            return jobstatus.RUNNING
        elif code < 300:
            return jobstatus.FINISHED
        else:
            return jobstatus.FAILED
