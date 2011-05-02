#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager

exposed = basemanager.exposed

class JobManager(BaseManager):

    @exposed
    def getJobs(self):
        pass

    @exposed
    def getJob(self, jobId):
        pass

    @exposed
    def updateJob(self, jobId, job):
        pass

    @exposed
    def addJob(self, job):
        pass
