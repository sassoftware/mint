#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory.manager import base

log = logging.getLogger(__name__)

class JobManager(base.BaseManager):

    @base.exposed
    def getJobs(self):
        jobs = models.Jobs()
        for job in models.Job.objects.all():
            jobs.job.append(job)
        return jobs

    @base.exposed
    def getJob(self, job_id):
        return models.Job.objects.get(pk=job_id)

    @base.exposed
    def getJobStates(self):
        jobStates = models.JobStates()
        for jobState in models.JobState.objects.all():
            jobStates.job_state.append(jobState)
        return jobStates

    @base.exposed
    def getJobState(self, job_state):
        return models.JobState.objects.get(name=job_state)

    @base.exposed
    def getJobsByJobState(self, job_state):
        jobs = models.Jobs()
        jobState = models.JobState.objects.get(job_state)
        for job in models.Job.objects.filter(job_state=jobState):
            jobs.job.append(job)
        return jobs
