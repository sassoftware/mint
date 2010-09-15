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
    def getJobState(self, job_state_id):
        return models.JobState.objects.get(pk=job_state_id)

    @base.exposed
    def getJobsByJobState(self, job_state_id):
        jobs = models.Jobs()
        jobState = models.JobState.objects.get(pk=job_state_id)
        for job in models.Job.objects.filter(job_state=jobState):
            jobs.job.append(job)
        return jobs

    @base.exposed
    def getSystemJobsByState(self, system_id, job_state_id):
        jobs = models.Jobs()
        system = models.System.objects.get(pk=system_id)
        jobState = models.JobState.objects.get(pk=job_state_id)
        for job in system.jobs.filter(job_state=jobState):
            jobs.job.append(job)
        return jobs

    @base.exposed
    def getAllSystemJobsByState(self, job_state_id):
        jobs = models.Jobs()
        jobState = models.JobState.objects.get(pk=job_state_id)
        for job in models.Job.objects.filter(job_state=jobState):
            jobs.job.append(job)
        return jobs
    
    @base.exposed
    def getSystemJobs(self, system_id):
        jobs = models.Jobs()
        system = models.System.objects.get(pk=system_id)
        for job in system.jobs.all():
            jobs.job.append(job)
        return jobs


