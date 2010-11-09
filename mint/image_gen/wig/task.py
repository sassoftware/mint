#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from rmake3.worker import plug_worker

from mint.image_gen import constants as iconst


class WigTask(plug_worker.TaskHandler):

    taskType = iconst.WIG_TASK

    def run(self):
        self.sendStatus(150, "doin stuff")
        import time
        time.sleep(2)
        self.sendStatus(151, "moar stuffs")
        time.sleep(2)
        self.sendStatus(200, "lol wut")
