#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import inspect
import weakref

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.inventory import models as inventorymodels

exposed = basemanager.exposed

class JobManager(basemanager.BaseManager):

    @exposed
    def getJobs(self):
        return self._jobsFromIterator(models.Job.objects.all())

    @exposed
    def getJob(self, job_uuid):
        return self._fillIn(models.Job.objects.get(job_uuid=job_uuid))

    @exposed
    def updateJob(self, job_uuid, job):
        if not job.pk:
            raise errors.ResourceNotFound()
        factory = JobUpdateHandlerRegistry.getJobHandlerFactory(job.job_type.name)
        if factory is None:
            return job
        jhandler = factory(self)
        jhandler.run(job)
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

    @exposed
    def getJobsByJobState(self, job_state_id):
        jobState = models.JobState.objects.get(pk=job_state_id)
        return self._jobsFromIterator(models.Job.objects.filter(
            job_state=jobState))

    @exposed
    def getSystemJobsByState(self, system_id, job_state_id):
        system = inventorymodels.System.objects.get(pk=system_id)
        jobState = models.JobState.objects.get(pk=job_state_id)
        return self._jobsFromIterator(system.jobs.filter(job_state=jobState))

    @exposed
    def getSystemJobs(self, system_id):
        system = inventorymodels.System.objects.get(pk=system_id)
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

class BaseJobUpdater(object):
    __slots__ = [ 'mgrRef', 'results', ]
    ResultsTag = None
    def __init__(self, mgr):
        self.mgrRef = weakref.ref(mgr)
        self.results = None

    def getJobResults(self, job):
        results = getattr(job.results, self.ResultsTag, None)
        return results

    def validateJobResults(self):
        if self.results is None:
            raise errors.InvalidData()

    def run(self, job):
        self.results = self.getJobResults(job)
        self.validateJobResults()
        self.processJobResults()

class ActionJobUpdater(BaseJobUpdater):
    __slots__ = []

    def getJobResults(self, job):
        results = getattr(job.results, self.descriptorData, None)
        return results

class JobUpdateHandlerRegistry(object):
    __slots__ = []
    class __metaclass__(type):
        _registry = {}
        def __new__(mcs, name, bases, attributes):
            if '__slots__' not in attributes:
                attributes.update(__slots__=[])
            cls = type.__new__(mcs, name, bases, attributes)
            for fname, fval in attributes.items():
                if inspect.isclass(fval) and issubclass(fval, BaseJobUpdater):
                    mcs._registry[fval.jobType] = fval
            return cls

    @classmethod
    def getJobHandlerFactory(cls, jobType):
        return cls.__metaclass__._registry.get(jobType)

    class TargetRefreshImages(BaseJobUpdater):
        jobType = models.EventType.TARGET_REFRESH_IMAGES
        ResultsTag = 'images'

        def processJobResults(self):
            pass

    class TargetRefreshSystems(BaseJobUpdater):
        jobType = models.EventType.TARGET_REFRESH_SYSTEMS
        ResultsTag = 'instances'

    class TargetDeployImage(ActionJobUpdater):
        jobType = models.EventType.TARGET_DEPLOY_IMAGE

    class TargetLaunchSystem(ActionJobUpdater):
        jobType = models.EventType.TARGET_LAUNCH_SYSTEM
