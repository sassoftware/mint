#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import inspect
import os
import re
import weakref
import StringIO
import time
import urlparse
from django.core import urlresolvers
from django.db import IntegrityError, transaction

from xobj import xobj
from smartform import descriptor as smartdescriptor

from mint import buildtypes, urltypes
from mint.lib import uuid
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.images import models as imagemodels
from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.targets import models as targetmodels

exposed = basemanager.exposed

import logging
log = logging.getLogger(__name__)

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
    def addJob(self, job, **extraArgs):
        """
        extraArgs can be used for passing additional information that ties
        the job to a particular resource (or verifies it). For instance,
        the identity of the related resource may be present both in the
        job URL and in the descriptor URL, and they should match
        """
        job.created_by = self.user
        factory = JobHandlerRegistry.getHandlerFactory(job.job_type.name)
        if factory is None:
            raise errors.InvalidData()
        jhandler = factory(self)
        jhandler.create(job, extraArgs)
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

    @exposed
    def waitForRmakeJob(self, jobUuid, timeout=10, interval=1):
        cli = self.mgr.repeaterMgr.repeaterClient
        end = time.time() + timeout
        while time.time() < end:
            job = cli.getJob(jobUuid)
            if job.status.final:
                return job
            time.sleep(interval)
        # Even if we timed out, we'll still return the job, it's up to
        # the caller to decide what to do
        return job

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
    __slots__ = [ 'mgrRef', 'extraArgs', ]

    def __init__(self, mgr):
        self.mgrRef = weakref.ref(mgr)
        self.extraArgs = {}
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

    def create(self, job, extraArgs=None):
        self.extraArgs.update(extraArgs or {})
        uuid_, rmakeJob = self.createRmakeJob(job)
        job.setValuesFromRmakeJob(rmakeJob)
        jobToken = rmakeJob.data.getObject().data.get('authToken')
        if jobToken:
            job.job_token = str(jobToken)
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
        job.save()

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

    def processJobResults(self, job):
        jobState = modellib.Cache.get(models.JobState, pk=job.job_state_id)
        if jobState.name != jobState.COMPLETED:
            job.results = None
            return None
        tsid = transaction.savepoint()
        try:
            resources = self._processJobResults(job)
        except Exception, e:
            transaction.savepoint_rollback(tsid)
            log.error("Error processing job %s %s",
                job.job_uuid, e)
            self.handleError(job, e)
            return None
        # XXX technically this should be saved to the DB
        # Also the xml should not be <results id="blah"/>, but
        # <results><target id="blah"/></results>
        job.results = modellib.HrefFieldFromModel(resources)
        return resources

    def _createTargetConfiguration(self, job, targetType):
        descriptorData = self.loadDescriptorData(job)
        driverClass = self.mgr.mgr.targetsManager.getDriverClass(targetType)

        cloudName = driverClass.getCloudNameFromDescriptorData(descriptorData)
        config = dict((k.getName(), k.getValue())
            for k in descriptorData.getFields())
        return targetType, cloudName, config

        if self.targetType is None:
            targetTypeId = job.jobtargettype_set.all()[0].target_type_id
            self._setTargetType(targetTypeId)

    def handleError(self, job, exc):
        job.status_text = "Unknown exception, please check logs"
        job.status_code = 500

class DescriptorJobHandler(BaseJobHandler, ResultsProcessingMixIn):
    __slots__ = [ 'results', 'descriptor', 'descriptorData', ]

    def _init(self):
        ResultsProcessingMixIn._init(self)
        self.descriptor = self.descriptorData = None

    def extractDescriptorData(self, job):
        "Executed when the job is created"
        descriptorId = job.descriptor.id
        # Strip the server-side portion
        descriptorId = urlparse.urlsplit(descriptorId).path
        descriptorDataXobj = job.descriptor_data
        descriptorDataXml = xobj.toxml(descriptorDataXobj)
        descriptor = self.getDescriptor(descriptorId)

        # Save the original URL for the descriptor
        self._setDescriptorId(descriptorId, descriptor)

        # Related resources are linked to jobs through a many-to-many
        # relationship
        job._relatedResource = self.getRelatedResource(descriptor)
        job._relatedThroughModel = self.getRelatedThroughModel(descriptor)

        descriptorDataObj = self._processDescriptor(descriptor, descriptorDataXml)
        descrXml = self._serializeDescriptor(descriptor)
        job._descriptor = descrXml
        job._descriptor_data = descriptorDataXml
        return descriptor, descriptorDataObj

    def _setDescriptorId(self, descriptorId, descriptor):
        descriptor.setId(descriptorId)

    def _processDescriptor(self, descriptor, descriptorDataXml):
        descriptor.setRootElement("descriptor_data")
        descriptorDataObj = smartdescriptor.DescriptorData(
            fromStream=descriptorDataXml,
            descriptor=descriptor,
            validate=False)
        return descriptorDataObj

    def _serializeDescriptor(self, descriptor):
        # Serialize descriptor for the job
        sio = StringIO.StringIO()
        descriptor.serialize(sio)
        return sio.getvalue()

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
        raise NotImplementedError()

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
        self.postprocessRelatedResource(job, model)
        model.save()

    def postprocessRelatedResource(self, job, model):
        pass

class _TargetDescriptorJobHandler(DescriptorJobHandler):
    __slots__ = [ 'target', ]

    def _init(self):
        DescriptorJobHandler._init(self)
        self.target = None

    def getDescriptor(self, descriptorId):
        # XXX
        targetId = os.path.basename(os.path.dirname(descriptorId))
        targetId = int(targetId)
        self._setTarget(targetId)
        descr = self._getDescriptorMethod()(targetId)
        return descr

    def _setTarget(self, targetId):
        target = self.mgr.mgr.getTargetById(targetId)
        self.target = target

    def getRelatedThroughModel(self, descriptor):
        return targetmodels.JobTarget

    def _buildTargetConfigurationFromDb(self, cli):
        targetData = self.mgr.mgr.getTargetConfiguration(self.target)
        targetTypeName = modellib.Cache.get(targetmodels.TargetType,
            pk=self.target.target_type_id).name
        targetConfiguration = cli.targets.TargetConfiguration(
            targetTypeName, self.target.name, targetData.get('alias'),
            targetData)
        return targetConfiguration

    def _buildTargetCredentialsFromDb(self, cli):
        creds = self.mgr.mgr.getTargetCredentialsForCurrentUser(self.target)
        if creds is None:
            raise errors.InvalidData()
        return self._buildTargetCredentials(cli, creds)

    def _buildTargetCredentials(self, cli, creds):
        userCredentials = cli.targets.TargetUserCredentials(
            credentials=creds,
            rbUser=self.mgr.auth.username,
            rbUserId=self.mgr.auth.userId,
            isAdmin=self.mgr.auth.admin)
        return userCredentials


class JobHandlerRegistry(HandlerRegistry):
    BaseHandlerClass = BaseJobHandler

    class TargetRefreshImages(_TargetDescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_REFRESH_IMAGES
        ResultsTag = 'images'

        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorRefreshImages

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentialsFromDb(cli)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)
            return cli.targets.listImages

        def _processJobResults(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            if not hasattr(self.results, 'image'):
                images = []
            else:
                images = self.results.image
                if not isinstance(images, list):
                    images = [ images ]
            self.mgr.mgr.updateTargetImages(self.target, images)
            return self.target

        def _setTargetUserCredentials(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            descriptorData = self.loadDescriptorData(job)
            creds = dict((k.getName(), k.getValue())
                for k in descriptorData.getFields())
            self.mgr.mgr.setTargetUserCredentials(self.target, creds)
            return self.target

    class TargetRefreshSystems(DescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_REFRESH_SYSTEMS
        ResultsTag = 'instances'

    class TargetDeployImage(_TargetDescriptorJobHandler):
        __slots__ = ['image', 'image_file', ]
        jobType = models.EventType.TARGET_DEPLOY_IMAGE

        def getDescriptor(self, descriptorId):
            try:
                match = urlresolvers.resolve(descriptorId)
            except urlresolvers.Resolver404:
                return None

            targetId = int(match.kwargs['target_id'])
            fileId = int(match.kwargs['file_id'])

            self._setTarget(targetId)
            self._setImage(fileId)
            return descriptorId

        def _setDescriptorId(self, descriptorId, descriptor):
            pass

        def _serializeDescriptor(self, descriptor):
            descriptorXml = '<descriptor id="%s"/>' % descriptor
            return descriptorXml

        def _setImage(self, fileId):
            self.image_file = imagemodels.BuildFile.objects.get(file_id=fileId)
            self.image = self.image_file.image

        def _processDescriptor(self, descriptor, descriptorDataXml):
            return descriptorDataXml

        def getRepeaterMethod(self, cli, job):
            self.extractDescriptorData(job)
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentialsFromDb(cli)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)
            return cli.targets.deployImage

        def _getImageBaseFileName(self):
            vals = self.image.image_data.filter(name='baseFileName').values('value')
            if not vals:
                return None
            return vals[0]['value']

        def getRepeaterMethodArgs(self, job):
            # XXX FIXME
            host = self.mgr.mgr.restDb.cfg.siteHost
            imageDownloadUrl = self.mgr.mgr.restDb.imageMgr.getDownloadUrl(self.image_file.file_id)
            hostname = self.image.project.short_name
            baseFileName = self._getImageBaseFileName()
            baseFileName = self.mgr.mgr.restDb.imageMgr._getBaseFileName(
                baseFileName, hostname, self.image.trove_name,
                self.image.trove_version, self.image.trove_flavor,
            )

            urls = self.image_file.buildfilesurlsmap_set.filter(
                url__url_type=urltypes.LOCAL).values('url__url')
            imageFileInfo = dict(
                size=self.image_file.size,
                sha1=self.image_file.sha1,
                fileId=self.image_file.file_id,
                baseFileName=baseFileName,
            )
            if urls:
                imageFileInfo['name'] = os.path.basename(urls[0]['url__url'])
            params = dict(
                descriptorData=job._descriptor_data,
                imageFileInfo=imageFileInfo,
                imageDownloadUrl=imageDownloadUrl,
                targetImageXmlTemplate=self._targetImageXmlTemplate(),
                imageFileUpdateUrl='https://%s/api/v1/images/%s/build_files/%s' % (
                        host, self.image.image_id, self.image_file.file_id),
            )
            return (params, ), {}

        def getRelatedThroughModel(self, descriptor):
            return imagemodels.JobImage

        def getRelatedResource(self, descriptor):
            return self.image

        def _targetImageXmlTemplate(self):
            tmpl = """\
<file>
  <target_images>
    <target_image>
      <target id="/api/v1/targets/%(targetId)s"/>
      %%(image)s
    </target_image>
  </target_images>
</file>"""
            return tmpl % dict(targetId=self.target.target_id)

    class TargetLaunchSystem(DescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_LAUNCH_SYSTEM


    class TargetCreator(DescriptorJobHandler):
        __slots__ = [ 'targetType', ]
        jobType = models.EventType.TARGET_CREATE
        ResultsTag = 'target'

        def _init(self):
            DescriptorJobHandler._init(self)
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

        def _getTargetType(self, job):
            if self.targetType is None:
                targetTypeId = job.jobtargettype_set.all()[0].target_type_id
                self._setTargetType(targetTypeId)
            return self.targetType

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            targetType, targetName, targetData = self._createTargetConfiguration(job, self.targetType)
            zone = targetData.pop('zone')
            targetConfiguration = cli.targets.TargetConfiguration(targetType.name,
                targetName, targetData.get('alias'), targetData)
            userCredentials = None
            cli.targets.configure(zone, targetConfiguration, userCredentials)
            return cli.targets.checkCreate

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTargetType

        def _processJobResults(self, job):
            targetType = self._getTargetType(job)
            targetType, targetName, targetData = self._createTargetConfiguration(job, targetType)
            target = self._createTarget(targetType, targetName, targetData)
            return target

        def handleError(self, job, exc):
            if isinstance(exc, IntegrityError):
                job.status_text = "Duplicate Target"
                job.status_code = 400
            else:
                DescriptorJobHandler.handleError(self, job, exc)

        def _createTarget(self, targetType, targetName, config):
            return self.mgr.mgr.createTarget(targetType, targetName, config)


    class TargetCredentialsConfigurator(_TargetDescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_CONFIGURE_CREDENTIALS
        ResultsTag = 'target'

        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorConfigureCredentials

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            creds = dict((k.getName(), k.getValue())
                for k in self.descriptorData.getFields())
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentials(cli, creds)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)
            return cli.targets.checkCredentials

        def _processJobResults(self, job):
            return self._setTargetUserCredentials(job)

        def _setTargetUserCredentials(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            descriptorData = self.loadDescriptorData(job)
            creds = dict((k.getName(), k.getValue())
                for k in descriptorData.getFields())
            self.mgr.mgr.setTargetUserCredentials(self.target, creds)
            return self.target

    class SystemCapture(_TargetDescriptorJobHandler):
        __slots__ = [ 'system', 'image' ]
        jobType = models.EventType.SYSTEM_CAPTURE
        ResultsTag = 'image'

        def _init(self):
            _TargetDescriptorJobHandler._init(self)
            self.target = self.system = self.image = None

        def getDescriptor(self, descriptorId):
            try:
                match = urlresolvers.resolve(descriptorId)
            except urlresolvers.Resolver404:
                return None

            systemId = int(match.kwargs['system_id'])
            if str(systemId) != str(self.extraArgs.get('system_id')):
                raise errors.InvalidData()
            self._setSystem(systemId)
            descr = self._getDescriptorMethod()(systemId)
            return descr

        def _getDescriptorMethod(self):
            return self.mgr.mgr.sysMgr.getDescriptorCaptureSystem

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentialsFromDb(cli)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)
            return cli.targets.captureSystem

        def getRepeaterMethodArgs(self, job):
            params = dict((x.getName(), x.getValue())
                for x in self.descriptorData.getFields())
            stageId = int(params.pop('stageId'))
            stage = self.mgr.mgr.getStage(stageId)
            imageTitle = params.get('imageTitle')
            image = self.mgr.mgr.createImage(
                name=imageTitle,
                project_branch_stage=stage)
            # XXX FIXME: really, we need to let the user pick the image
            # type
            image._image_type = buildtypes.VMWARE_ESX_IMAGE
            image.architecture = params.get('architecture')
            image.job_uuid = job.job_uuid
            self.image = image = self.mgr.mgr.createImageBuild(image)
            outputToken = image.image_data.get(name='outputToken').value
            host = self.mgr.mgr.restDb.cfg.siteHost
            params['outputToken'] = outputToken
            params['imageUploadUrl'] = 'https://%s/uploadBuild/%s' % (
                host, image.image_id)
            params['imageFilesCommitUrl'] = 'https://%s/api/products/%s/images/%s/files' % (
                host, stage.project.short_name, image.image_id)
            params['image_id'] = 'https://%s/api/v1/images/%s' % (
                host, image.image_id)
            params['imageName'] = "%s.ova" % self._sanitizeString(imageTitle)
            return (self.system.target_system_id, params), {}

        @classmethod
        def _sanitizeString(cls, strobj):
            return re.sub('[^-\w.]', '_', strobj)

        def getRelatedThroughModel(self, descriptor):
            return inventorymodels.SystemJob

        def getRelatedResource(self, descriptor):
            return self.system

        def _setSystem(self, systemId):
            system = inventorymodels.System.objects.get(system_id=systemId)
            self.system = system
            self.target = system.target

        def postprocessRelatedResource(self, job, model):
            model.event_uuid = str(uuid.uuid4())
            self.image.job_uuid = job.job_uuid
            self.image.save()

        def _processJobResults(self, job):
            imageId = getattr(self.results, 'id', None)
            if imageId is None:
                raise errors.InvalidData()
            imageId = int(os.path.basename(imageId))
            image = self.mgr.mgr.getImageBuild(imageId)
            return image
