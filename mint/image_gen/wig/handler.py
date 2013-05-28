#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import logging
import json

from mint import jobstatus
from mint.image_gen import constants as iconst
from mint.image_gen import handler

log = logging.getLogger(__name__)


class WigHandler(handler.BaseImageHandler):

    jobType = iconst.WIG_JOB
    firstState = 'run'

    def setup(self):
        # Collect parameters needed for pushing status updates to rBuilder API.
        self.jobData = jobData = json.loads(self.getData())
        self.imageBase = 'http://localhost/api/v1/images/%d/' % (
                jobData['buildId'])
        self.imageToken = jobData['outputToken'].encode('ascii')

    def run(self):
        self.setStatus(iconst.WIG_JOB_QUEUED, "Waiting for processing {0/4}")

        # Find a build service to run the job on
        d = self.dispatcher.wig_coordinator.getBuildService()
        d.addCallback(self._run_gotService)
        return d

    def _run_gotService(self, url):
        self.jobData['windowsBuildService'] = url
        blob = json.dumps(self.jobData)
        task = self.newTask('image', iconst.WIG_TASK, blob)

        # Copy task status changes to job status
        self.watchTask(task, self._mirrorTaskStatus)
        # Exit job handler when task completes
        d = self.waitForTask(task)
        d.addCallback(lambda _: 'done')
        return d

    def _translateCode(self, code):
        if code == iconst.WIG_JOB_QUEUED:
            return jobstatus.WAITING
        elif code < 200:
            return jobstatus.RUNNING
        elif code < 300:
            return jobstatus.FINISHED
        else:
            return jobstatus.FAILED
