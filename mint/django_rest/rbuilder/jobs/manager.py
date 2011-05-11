#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.jobs import models

exposed = basemanager.exposed

class JobManager(BaseManager):

    @exposed
    def getJobs(self):
        jobs = models.Jobs()
        jobs.job = models.Job.objects.all()
        return jobs

    @exposed
    def getJob(self, jobId):
        return models.Job.objects.get(pk=jobId)

    @exposed
    def updateJob(self, jobId, job):
        job.pk = jobId
        job.save()
        return job

    @exposed
    def addJob(self, job):
        job.save()
        return job

    @exposed
    def deleteJob(self, jobId):
        job = models.Job.objects.get(pk=jobId)
        job.delete()

    @exposed
    def getJobStates(self):
        jobStates = models.JobStates()
        jobStates.job_state = models.JobState.objects.all()
        return jobStates

    @exposed
    def getJobState(self, jobStateId):
        jobState = models.JobState.objects.get(pk=jobStateId)
        return jobState
