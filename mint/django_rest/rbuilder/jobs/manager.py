#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import inspect
import os
import weakref
import StringIO
import urlparse
from django.core import urlresolvers

from xobj import xobj
from smartform import descriptor as smartdescriptor

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.targets import models as targetmodels

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
        factory = JobUpdateHandlerRegistry.getHandlerFactory(job.job_type.name)
        if factory is None:
            return job
        jhandler = factory(self)
        jhandler.run(job)
        return job

    @exposed
    def addJob(self, job):
        factory = JobCreationHandlerRegistry.getHandlerFactory(job.job_type.name)
        if factory is None:
            raise errors.InvalidData()
        jhandler = factory(self)
        jhandler.run(job)
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

class AbstractHandler(object):
    __slots__ = [ 'mgrRef', ]

    def __init__(self, mgr):
        self.mgrRef = weakref.ref(mgr)
        self._init()

    def _init(self):
        pass

    @property
    def mgr(self):
        return self.mgrRef()

class BaseJobUpdater(AbstractHandler):
    __slots__ = [ 'results', ]
    ResultsTag = None

    def _init(self):
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

class HandlerRegistry(object):
    """
    Generic registry for factories.
    """
    __slots__ = []
    class __metaclass__(type):
        _registry = {}
        def __new__(mcs, name, bases, attributes):
            if '__slots__' not in attributes:
                attributes.update(__slots__=[])
            cls = type.__new__(mcs, name, bases, attributes)
            baseHandlerClass = cls.BaseHandlerClass
            if baseHandlerClass is None:
                return cls
            for fname, fval in attributes.items():
                if fname == 'BaseHandlerClass':
                    continue
                if inspect.isclass(fval) and issubclass(fval, baseHandlerClass):
                    mcs._registry[fval.jobType] = fval
            return cls
    BaseHandlerClass = None

    @classmethod
    def getHandlerFactory(cls, jobType):
        return cls.__metaclass__._registry.get(jobType)

class JobUpdateHandlerRegistry(HandlerRegistry):
    BaseHandlerClass = BaseJobUpdater

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

class BaseJobCreator(AbstractHandler):
    __slots__ = []

    def run(self, job):
        uuid, rmakeJob = self.createRmakeJob(job)
        job.setValuesFromRmakeJob(rmakeJob)
        job.save()
        # Blank out the descriptor data, we don't need it in the return
        # value
        job.descriptor_data = None
        self.linkRelatedResource(job)

    def createRmakeJob(self, job):
        cli = self.mgr.mgr.repeaterMgr.repeaterClient
        method = self.getRepeaterMethod(cli)
        methodArgs, methodKwargs = self.getRepeaterMethodArgs(job)
        return method(*methodArgs, **methodKwargs)

    def linkRelatedResource(self, job):
        pass

class DescriptorJobCreator(BaseJobCreator):

    def getRepeaterMethodArgs(self, job):
        descriptorId = job.descriptor.id
        # Strip the server-side portion
        descriptorId = urlparse.urlsplit(descriptorId).path
        descriptorDataXobj = job.descriptor_data
        descriptorDataXml = xobj.toxml(descriptorDataXobj)
        descriptor = self.getDescriptor(descriptorId)

        # Save the original URL for the descriptor
        descriptor.setId(descriptorId)

        # Related resources are linked to jobs through a many-to-many
        # relationship
        job._relatedResource = self.getRelatedResource(descriptor)
        job._relatedThroughModel = self.getRelatedThroughModel(descriptor)

        descriptor.setRootElement("descriptor_data")
        descriptorDataObj = smartdescriptor.DescriptorData(
            fromStream=descriptorDataXml,
            descriptor=descriptor,
            validate=False)
        # Serialize descriptor for the job
        sio = StringIO.StringIO()
        descriptor.serialize(sio)
        job._descriptor = sio.getvalue()
        job._descriptor_data = descriptorDataXml
        return (descriptor, descriptorDataObj), {}

    def getRelatedResource(self, descriptor):
        descriptorId = descriptor.getId()
        # Strip the descriptor part, hopefully that gives us a resource
        descriptorId = os.path.dirname(descriptorId)
        try:
            match = urlresolvers.resolve(descriptorId)
        except urlresolvers.Resolver404:
            return None
        return match.func.get(**match.kwargs)

    def getDescriptor(self, descriptorId):
        return None

    def linkRelatedResource(self, job):
        if job._relatedResource is None:
            return
        model = job._relatedThroughModel(job=job)
        # Find the name of the related field
        relatedClass = job._relatedResource.__class__
        relatedFields = [ x for x in job._relatedThroughModel._meta.fields
            if x.rel and x.rel.to == relatedClass ]
        if not relatedFields:
            return
        relatedFieldName = relatedFields[0].name
        setattr(model, relatedFieldName, job._relatedResource)
        model.save()

class JobCreationHandlerRegistry(HandlerRegistry):
    BaseHandlerClass = BaseJobCreator

    class TargetCreator(DescriptorJobCreator):
        jobType = models.EventType.TARGET_CREATE

        def getDescriptor(self, descriptorId):
            # XXX
            targetTypeId = os.path.basename(os.path.dirname(descriptorId))
            targetTypeId = int(targetTypeId)
            descr = self.mgr.mgr.getDescriptorCreateTargetByTargetType(targetTypeId)
            return descr

        def getRepeaterMethod(self, cli):
            return cli.targets.create

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTargetType

    class TargetCredentialsConfigurator(DescriptorJobCreator):
        jobType = models.EventType.TARGET_CONFIGURE_CREDENTIALS

        def getDescriptor(self, descriptorId):
            # XXX
            targetId = os.path.basename(os.path.dirname(descriptorId))
            targetId = int(targetId)
            descr = self.mgr.mgr.getDescriptorConfigureCredentials(targetId)
            return descr

        def getRepeaterMethod(self, cli):
            # XXX
            return cli.targets.configure

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTarget

