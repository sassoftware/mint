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
from mint.django_rest.rbuilder import modellib
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
        factory = JobHandlerRegistry.getHandlerFactory(job.job_type.name)
        if factory is None:
            return job
        jhandler = factory(self)
        jhandler.processResults(job)
        return job

    @exposed
    def addJob(self, job):
        factory = JobHandlerRegistry.getHandlerFactory(job.job_type.name)
        if factory is None:
            raise errors.InvalidData()
        jhandler = factory(self)
        jhandler.create(job)
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

class BaseJobHandler(AbstractHandler):
    __slots__ = []

    def create(self, job):
        uuid, rmakeJob = self.createRmakeJob(job)
        job.setValuesFromRmakeJob(rmakeJob)
        job.job_token = str(rmakeJob.data.getObject().data['authToken'])
        job.save()
        # Blank out the descriptor data, we don't need it in the return
        # value
        job.descriptor_data = None
        self.linkRelatedResource(job)

    def createRmakeJob(self, job):
        cli = self.mgr.mgr.repeaterMgr.repeaterClient
        method = self.getRepeaterMethod(cli, job)
        methodArgs, methodKwargs = self.getRepeaterMethodArgs(job)
        return method(*methodArgs, **methodKwargs)

    def getRepeaterMethodArgs(self, job):
        return (), {}

    def linkRelatedResource(self, job):
        pass

class ResultsProcessingMixIn(object):
    __slots__ = []
    ResultsTag = None

    # Results processing API
    def _init(self):
        self.results = None

    def processResults(self, job):
        if job.oldModel is None:
            # We won't allow job creation to happen here
            raise errors.InvalidData()
        self.results = self.getJobResults(job)
        self.validateJobResults(job)
        self.processJobResults(job)

    def getJobResults(self, job):
        results = getattr(job.results, self.ResultsTag, None)
        return results

    def validateJobResults(self, job):
        jobState = modellib.Cache.get(models.JobState, pk=job.job_state_id)
        if self.results is None and jobState.name == jobState.COMPLETED:
            raise errors.InvalidData()

    def loadDescriptorData(self, job):
        descriptor = smartdescriptor.ConfigurationDescriptor(fromStream=job._descriptor)
        descriptorData = smartdescriptor.DescriptorData(
            fromStream=job._descriptor_data, descriptor=descriptor)
        return descriptorData


class DescriptorJobHandler(BaseJobHandler, ResultsProcessingMixIn):
    __slots__ = [ 'results', ]

    def extractDescriptorData(self, job):
        "Executed when the job is created"
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
        return descriptor, descriptorDataObj

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

class JobHandlerRegistry(HandlerRegistry):
    BaseHandlerClass = BaseJobHandler

    class TargetRefreshImages(DescriptorJobHandler):
        jobType = models.EventType.TARGET_REFRESH_IMAGES
        ResultsTag = 'images'

        def processJobResults(self, job):
            pass

    class TargetRefreshSystems(DescriptorJobHandler):
        jobType = models.EventType.TARGET_REFRESH_SYSTEMS
        ResultsTag = 'instances'

    class TargetDeployImage(DescriptorJobHandler):
        jobType = models.EventType.TARGET_DEPLOY_IMAGE

    class TargetLaunchSystem(DescriptorJobHandler):
        jobType = models.EventType.TARGET_LAUNCH_SYSTEM


    class TargetCreator(DescriptorJobHandler):
        __slots__ = [ 'targetType', ]
        jobType = models.EventType.TARGET_CREATE
        ResultsTag = 'target'

        def _init(self):
            self.targetType = None

        def getDescriptor(self, descriptorId):
            # XXX
            targetTypeId = os.path.basename(os.path.dirname(descriptorId))
            targetTypeId = int(targetTypeId)
            self._setTargetType(targetTypeId)
            descr = self.mgr.mgr.getDescriptorCreateTargetByTargetType(targetTypeId)
            return descr

        def _setTargetType(self, targetTypeId):
            self.targetType = modellib.Cache.get(targetmodels.TargetType,
                pk=targetTypeId)

        def getRepeaterMethod(self, cli, job):
            descriptor, descriptorData = self.extractDescriptorData(job)
            targetType, targetName, targetData = self._createTargetConfiguration(job)
            zone = targetData.pop('zone')
            targetConfiguration = cli.targets.TargetConfiguration(targetType.name,
                targetName, targetData.get('alias'), targetData)
            userCredentials = None
            cli.targets.configure(zone, targetConfiguration, userCredentials)
            return cli.targets.checkCreate

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTargetType

        def processJobResults(self, job):
            jobState = modellib.Cache.get(models.JobState, pk=job.job_state_id)
            if jobState.name != jobState.COMPLETED:
                job.results = None
                return None
            targetType, targetName, targetData = self._createTargetConfiguration(job)
            target = self._createTarget(targetType, targetName, targetData)
            # XXX technically this should be saved to the DB
            # Also the xml should not be <results id="blah"/>, but
            # <results><target id="blah"/></results>
            job.results = modellib.HrefFieldFromModel(target)
            return target

        def _createTargetConfiguration(self, job):
            descriptorData = self.loadDescriptorData(job)
            if self.targetType is None:
                targetTypeId = job.jobtargettype_set.all()[0].target_type_id
                self._setTargetType(targetTypeId)
            driverClass = self.mgr.mgr.targetsManager.getDriverClass(self.targetType)

            cloudName = driverClass.getCloudNameFromDescriptorData(descriptorData)
            config = dict((k.getName(), k.getValue())
                for k in descriptorData.getFields())
            return self.targetType, cloudName, config

        def _createTarget(self, targetType, targetName, config):
            return self.mgr.mgr.createTarget(targetType, targetName, config)


    class TargetCredentialsConfigurator(DescriptorJobHandler):
        __slots__ = [ 'target', ]
        jobType = models.EventType.TARGET_CONFIGURE_CREDENTIALS
        ResultsTag = 'target'

        def _init(self):
            self.target = None

        def getDescriptor(self, descriptorId):
            # XXX
            targetId = os.path.basename(os.path.dirname(descriptorId))
            targetId = int(targetId)
            self._setTarget(targetId)
            descr = self.mgr.mgr.getDescriptorConfigureCredentials(targetId)
            return descr

        def _setTarget(self, targetId):
            target = modellib.Cache.get(targetmodels.Target, pk=targetId)
            self.target = target

        def _buildTargetConfiguration(self, cli):
            targetData = self.mgr.mgr.getTargetConfiguration(self.target)
            targetTypeName = modellib.Cache.get(targetmodels.TargetType,
                pk=self.target.target_type_id).name
            targetConfiguration = cli.targets.TargetConfiguration(
                targetTypeName, self.target.name, targetData.get('alias'),
                targetData)
            return targetConfiguration

        def _buildTargetCredentials(self, cli, creds):
            userCredentials = cli.targets.TargetUserCredentials(
                credentials=creds,
                rbUser=self.mgr.auth.username,
                rbUserId=self.mgr.auth.userId,
                isAdmin=self.mgr.auth.admin)
            return userCredentials

        def getRepeaterMethod(self, cli, job):
            descriptor, descriptorData = self.extractDescriptorData(job)
            creds = dict((k.getName(), k.getValue())
                for k in descriptorData.getFields())
            targetConfiguration = self._buildTargetConfiguration(cli)
            targetUserCredentials = self._buildTargetCredentials(cli, creds)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone, targetConfiguration,
                targetUserCredentials)
            return cli.targets.checkCredentials

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTarget

        def processJobResults(self, job):
            jobState = modellib.Cache.get(models.JobState, pk=job.job_state_id)
            if jobState.name != jobState.COMPLETED:
                job.results = None
                return None
            target = self._setTargetUserCredentials(job)
            # XXX technically this should be saved to the DB
            # Also the xml should not be <results id="blah"/>, but
            # <results><target id="blah"/></results>
            job.results = modellib.HrefFieldFromModel(target)
            return target

        def _setTargetUserCredentials(self, job):
            targetId = job.jobtarget_set.all()[0].target_id
            self._setTarget(targetId)
            descriptorData = self.loadDescriptorData(job)
            creds = dict((k.getName(), k.getValue())
                for k in descriptorData.getFields())
            self.mgr.mgr.setTargetUserCredentials(self.target, creds)
            return self.target
