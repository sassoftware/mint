#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from rmake3.core import handler as rmk_handler
from rmake3.worker import plug_worker

from mint.image_gen import constants as iconst


class WigHandler(rmk_handler.JobHandler):

    jobType = iconst.WIG_JOB
    firstState = 'run'

    def run(self):
        self.setStatus(iconst.WIG_JOB_DONE, "omglolpassed")
        return 'done'


class WigTask(plug_worker.TaskHandler):

    def run(self):
        pass
