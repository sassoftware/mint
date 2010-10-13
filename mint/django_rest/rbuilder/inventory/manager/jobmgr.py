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
        return self._jobsFromIterator(models.Job.objects.all())

    @base.exposed
    def getJob(self, job_id):
        return self._fillIn(models.Job.objects.get(pk=job_id))

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
        jobState = models.JobState.objects.get(pk=job_state_id)
        return self._jobsFromIterator(models.Job.objects.filter(
            job_state=jobState))

    @base.exposed
    def getSystemJobsByState(self, system_id, job_state_id):
        system = models.System.objects.get(pk=system_id)
        jobState = models.JobState.objects.get(pk=job_state_id)
        return self._jobsFromIterator(system.jobs.filter(job_state=jobState))

    @base.exposed
    def getSystemJobs(self, system_id):
        system = models.System.objects.get(pk=system_id)
        return self._jobsFromIterator(system.jobs.all())

    @classmethod
    def _jobsFromIterator(cls, iterator):
        jobs = models.Jobs()
        for job in iterator:
            jobs.job.append(cls._fillIn(job))
        return jobs

    @classmethod
    def _fillIn(cls, job):
        job.setValuesFromRmake()
        return job
