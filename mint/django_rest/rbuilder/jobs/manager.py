#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import inspect
import os
import StringIO
import sys
import time
import urlparse
import uuid
import weakref
import exceptions
from django.core import urlresolvers
from django.db import IntegrityError, transaction

from smartform import descriptor as smartdescriptor

from mint import urltypes
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.images import models as imagemodels
from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.logerror import logErrorAndEmail

exposed = basemanager.exposed

import logging
log = logging.getLogger(__name__)

class JobManager(basemanager.BaseManager):

    @exposed
    def getJobs(self):
        return self._jobsFromIterator(models.Job.objects.all())

    @exposed
    def getJob(self, job_uuid):
        return models.Job.objects.get(job_uuid=job_uuid)

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
        job.created_by = job.modified_by = extraArgs.get('forUser', self.user)
        typename = job.job_type.name
        factory = JobHandlerRegistry.getHandlerFactory(typename)
        if factory is None:
            raise errors.InvalidData(msg="no factory for job type: %s" % typename)
        jhandler = factory(self)
        jhandler.create(job, extraArgs)
        for system_job in job.systems.all():
            system_job.system.updateDerivedData()
        return job

    @exposed
    def deleteJob(self, jobId):
        job = models.Job.objects.get(pk=jobId)
        systems = job.systems.all()
        job.delete()
        for system_job in systems:
            system_job.job.updateDerivedData()

    @exposed
    def getJobStates(self):
        jobStates = models.JobStates()
        jobStates.job_state = models.JobState.objects.all()
        return jobStates

    @exposed
    def getJobStateByName(self, name):
        return modellib.Cache.get(models.JobState, name=name)

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
            jobs.job.append(job)
        return jobs

    @classmethod
    def systemModelForSystem(cls, system, topLevelItems):
        systemModelLines = []
        systemModelLines.extend("install %s" % x.strip() for x in topLevelItems)
        return "\n".join(systemModelLines)

    @exposed
    def finishJob(self, job):
        return self.updateJobState(job, stateName=models.JobState.COMPLETED,
            statusText="Completed", statusCode=200)

    @exposed
    def updateJobState(self, job, stateName=models.JobState.COMPLETED,
            statusText="Completed", statusCode=200):
        job.update(job_state = self.getJobStateByName(stateName),
            status_text = statusText,
            status_code = statusCode)

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
        # Tentatively supply a jobUuid, to make sure we have a stable
        # URL back to the job
        job.job_uuid = str(uuid.uuid4())
        uuid_, rmakeJob = self.createRmakeJob(job)
        job.job_uuid = str(uuid_)
        job.setDefaultValues()
        if rmakeJob is not None:
            jobToken = rmakeJob.data.getObject().data.get('authToken')
            if jobToken:
                job.job_token = str(jobToken)
        job.save()
        # Blank out the descriptor data, we don't need it in the return
        # value
        job.descriptor_data = None
        self.linkRelatedResource(job)
        self.postCreateJob(job)

    def createRmakeJob(self, job):
        cli = self.mgr.mgr.repeaterMgr.repeaterClient
        method = self.getRepeaterMethod(cli, job)
        methodArgs, methodKwargs = self.getRepeaterMethodArgs(cli, job)
        methodKwargs.update(uuid=job.job_uuid)
        return method(*methodArgs, **methodKwargs)

    def getRepeaterMethodArgs(self, cli, job):
        return (), {}

    def linkRelatedResource(self, job):
        pass

    def postCreateJob(self, job):
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
            raise errors.InvalidData(msg="no model")
        # Flush job state to the DB, it is needed by processJobResults
        models.Job.objects.filter(job_id=job.job_id).update(
            job_state=job.job_state)
        self.results = self.getJobResults(job)
        self.validateJobResults(job)
        self.processJobResults(job)
        for system_job in job.systems.all():
            system_job.system.updateDerivedData()
        job.save()

    def getJobResults(self, job):
        if job.results is None:
            return None
        return job.results.find(self.ResultsTag)

    def validateJobResults(self, job):
        jobState = modellib.Cache.get(models.JobState, pk=job.job_state_id)
        if self.results is None and jobState.name == jobState.COMPLETED:
            raise errors.InvalidData(msg = "missing results")

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
            e_type, e_value, e_tb = sys.exc_info()
            log.error("Error processing job %s %s",
                job.job_uuid, e)
            try:
                handled = self.handleError(job, e)
            except exceptions.AttributeError:
                handled = False
            if handled:
                return None
            logErrorAndEmail(self.mgr.cfg, e_type, e_value, e_tb,
                'jobs handler', dict(), doEmail=True)
            self.handleErrorDefault(job, e)
            return None

        # save the results from rmake to the DB
        if not isinstance(resources, list):
            resources = [ resources ]
        for resource in resources:
            tag = resource._xobj.tag

            # XXX this is ugly. We should have a more extensible way to
            # handle this
            if tag == 'image':
                models.JobImageArtifact(job=job, image=resource).save()
            elif tag not in set(['target', 'system']):
                raise Exception("internal error, don't know how to save resource: %s" % tag)
        job.results = models.JobResults()
        job.results.result = [ modellib.HrefFieldFromModel(x) for x in resources ]
        return resources[0]

    def _createTargetConfiguration(self, job, targetType):
        descriptorData = self.loadDescriptorData(job)
        driverClass = self.mgr.mgr.targetsManager.getDriverClass(targetType)

        cloudName = driverClass.getCloudNameFromDescriptorData(descriptorData)
        config = driverClass.getTargetConfigFromDescriptorData(descriptorData)
        return targetType, cloudName, config

    def handleErrorDefault(self, job, exc):
        job.status_text = "Unknown exception, please check logs"
        job.status_code = 500

class DescriptorJobHandler(BaseJobHandler, ResultsProcessingMixIn):
    __slots__ = [ 'results', 'descriptor', 'descriptorData', ]

    def _init(self):
        ResultsProcessingMixIn._init(self)
        self.descriptor = self.descriptorData = None

    def extractDescriptorData(self, job):
        "Executed when the job is created"

        descriptor = None
        descriptorDataObj = None
        descriptorId = 1
        descriptorDataXml = ''
        descriptorDataObj = None

        if isinstance(job.descriptor, smartdescriptor.ConfigurationDescriptor):
            # path for direct python API usage, such as target system import
            # not yet patched up for supplying descriptor data
            descriptor = job.descriptor
            descriptorDataObj = None
            descriptor = self.getDescriptor(job.descriptor.id)
        else:
            descriptorId = job.descriptor.attrib['id']
            # Strip the server-side portion
            descriptorId = urlparse.urlsplit(descriptorId).path
            descriptor = self.getDescriptor(descriptorId)

        descriptorDataXml = modellib.Etree.tostring(job.descriptor_data,
                xmlDeclaration=True, prettyPrint=False)

        # Save the original URL for the descriptor
        self._setDescriptorId(descriptorId, descriptor)

        # Related resources are linked to jobs through a many-to-many
        # relationship
        job._relatedResource = self.getRelatedResource(descriptor)
        job._relatedThroughModel = self.getRelatedThroughModel(descriptor)
        try:
            descriptorDataObj = self._processDescriptor(descriptor, descriptorDataXml)
        except smartdescriptor.errors.ConstraintsValidationError, e:
            raise errors.InvalidData(msg=str(e))

        descrXml = self._serializeDescriptor(descriptor)
        job._descriptor = descrXml
        if hasattr(descriptorDataObj, 'toxml'):
            # Re-serialize descriptor data to make sure extra fields get
            # filtered out
            descriptorDataXml = descriptorDataObj.toxml()
        job._descriptor_data = descriptorDataXml

        return descriptor, descriptorDataObj

    def _setDescriptorId(self, descriptorId, descriptor):
        descriptor.setId(descriptorId)

    def _processDescriptor(self, descriptor, descriptorDataXml):
        descriptor.setRootElement("descriptor_data")
        # This will also validate the descriptor data
        descriptorDataObj = smartdescriptor.DescriptorData(
            fromStream=descriptorDataXml,
            descriptor=descriptor)
        return descriptorDataObj

    def _serializeDescriptor(self, descriptor):
        # Serialize descriptor for the job
        sio = StringIO.StringIO()
        descriptor.serialize(sio)
        return sio.getvalue()

    def getRelatedResource(self, descriptor):
        descriptorId = descriptor.getId()
        try:
            match = self.splitResourceId(descriptorId)
        except errors.InvalidData:
            return None
        return match.func.get(**match.kwargs)

    def getDescriptor(self, descriptorId):
        raise NotImplementedError()

    def linkRelatedResource(self, job):
        if job._relatedResource is None:
            return
        # It's possible to link multiple resources to a job
        relatedResources = job._relatedResource
        if not isinstance(relatedResources, list):
            relatedResources = [ relatedResources ]
        relatedClass = relatedResources[0].__class__
        for relatedResource in relatedResources:
            model = job._relatedThroughModel(job=job)
            # Find the name of the related field
            relatedFields = [ x for x in job._relatedThroughModel._meta.fields
                if x.rel and x.rel.to == relatedClass ]
            if not relatedFields:
                return
            relatedFieldName = relatedFields[0].name
            setattr(model, relatedFieldName, relatedResource)
            self.postprocessRelatedResource(job, model)
            model.save()

    def postprocessRelatedResource(self, job, model):
        pass

    @classmethod
    def splitResourceId(cls, resourceId):
        try:
            match = urlresolvers.resolve(resourceId)
        except urlresolvers.Resolver404:
            raise errors.InvalidData(msg="unable to resolve resource id: %s" % resourceId)

        return match


class _TargetDescriptorJobHandler(DescriptorJobHandler):
    __slots__ = [ 'target', ]

    def _init(self):
        DescriptorJobHandler._init(self)
        self.target = None

    def getDescriptor(self, descriptorId):
        match = self.splitResourceId(descriptorId)
        targetId = int(match.kwargs['target_id'])
        self._setTarget(targetId)
        descr = self._getDescriptorMethod()(targetId)
        return descr

    def _setTarget(self, targetId):
        target = self.mgr.mgr.getTargetById(targetId)
        self.target = target

    def getRelatedResource(self, descriptor):
        return self.target

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

    def _buildTargetCredentialsFromDb(self, cli, job):
        creds = self.mgr.mgr.getTargetCredentialsForCurrentUser(self.target)
        if creds is None:
            raise errors.InvalidData(msg="missing credentials")
        return self._buildTargetCredentials(cli, job, creds)

    def _buildTargetCredentials(self, cli, job, creds):
        rbUser = self.mgr.auth.username
        rbUserId = self.mgr.auth.userId
        isAdmin = self.mgr.auth.admin
        userCredentials = cli.targets.TargetUserCredentials(
            credentials=creds,
            rbUser=rbUser,
            rbUserId=rbUserId,
            isAdmin=isAdmin)
        return userCredentials


class JobHandlerRegistry(HandlerRegistry):
    BaseHandlerClass = BaseJobHandler

    class TargetRefreshImages(_TargetDescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_REFRESH_IMAGES
        ResultsTag = 'images'

        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorRefreshImages

        def _configureTargetMethod(self, cli, job):
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentialsFromDb(cli, job)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            self._configureTargetMethod(cli, job)
            return cli.targets.listImages

        def _processJobResults(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            images = list(self.results.iterchildren('image'))
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

    class TargetRefreshSystems(TargetRefreshImages):

        __slots__ = []
        jobType = models.EventType.TARGET_REFRESH_SYSTEMS
        ResultsTag = 'instances'
        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorRefreshSystems

        def _buildAllUserCredentialsFromDb(self, cli, job):
            credsList = self.mgr.mgr.getTargetAllUserCredentials(self.target)
            ret = []
            for credId, creds in credsList:
                userCredentials = cli.targets.TargetUserCredentials(
                    credentials=creds,
                    rbUser=None,
                    rbUserId=None,
                    isAdmin=False,
                    opaqueCredentialsId=credId)
                ret.append(userCredentials)
            return ret

        def _configureTargetMethod(self, cli, job):
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetAllUserCredentials = self._buildAllUserCredentialsFromDb(cli, job)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                None, targetAllUserCredentials)

        def getRepeaterMethod(self, cli, job):
            super(JobHandlerRegistry.TargetRefreshSystems, self).getRepeaterMethod(cli, job)
            return cli.targets.listInstances

        def _processJobResults(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            systems = list(self.results.iterchildren('instance'))
            self.mgr.mgr.updateTargetSystems(self.target, systems)
            return self.target


    class TargetDeployImage(_TargetDescriptorJobHandler):
        __slots__ = ['image', 'image_file', ]
        jobType = models.EventType.TARGET_DEPLOY_IMAGE
        ResultsTag = 'image'

        def getDescriptor(self, descriptorId):
            match = self.splitResourceId(descriptorId)

            targetId = int(match.kwargs['target_id'])
            fileId = int(match.kwargs['file_id'])

            self._setTarget(targetId)
            self._setImageFromFileId(fileId)
            return descriptorId

        def _setDescriptorId(self, descriptorId, descriptor):
            pass

        def _serializeDescriptor(self, descriptor):
            descriptorXml = '<descriptor id="%s"/>' % descriptor
            return descriptorXml

        def _setImageFromFileId(self, fileId):
            self.image_file = imagemodels.BuildFile.objects.get(file_id=fileId)
            self.image = self.image_file.image

        def _processDescriptor(self, descriptor, descriptorDataXml):
            return descriptorDataXml

        def _processJobResults(self, job):
            # Nothing to be done, there is another call that posts the
            # image
            images = list(job.images.all())
            if not images:
                raise ImageDeletedError("Image was deleted during deployment")
            self.image = images[0].image
            return self.image

        def handleError(self, job, exc):
            if isinstance(exc, ImageDeletedError):
                job.status_text = str(exc)
                job.status_code = 404
                return True
            return False

        def getRepeaterMethod(self, cli, job):
            self.extractDescriptorData(job)
            targetConfiguration = self._buildTargetConfigurationFromDb(cli)
            targetUserCredentials = self._buildTargetCredentialsFromDb(cli, job)
            zone = self.mgr.mgr.getTargetZone(self.target)
            cli.targets.configure(zone.name, targetConfiguration,
                targetUserCredentials)
            return cli.targets.deployImage

        def _getImageBaseFileName(self):
            vals = self.image.image_data.filter(name='baseFileName').values('value')
            if not vals:
                return None
            return vals[0]['value']

        def getRepeaterMethodArgs(self, cli, job):
            imageDownloadUrl = self.mgr.mgr.restDb.imageMgr.getDownloadUrl(self.image_file.file_id)
            hostname = self.image.project.short_name
            baseFileName = self._getImageBaseFileName()
            troveFlavor = (self.image.trove_flavor or '').encode('ascii')
            baseFileName = self.mgr.mgr.restDb.imageMgr._getBaseFileName(
                baseFileName, hostname, self.image.trove_name,
                self.image.trove_version, troveFlavor,
            )

            urls = self.image_file.urls_map.filter(
                url__url_type=urltypes.LOCAL).values('url__url')
            imageFileInfo = dict(
                architecture=self.image.architecture,
                size=self.image_file.size,
                sha1=self.image_file.sha1,
                fileId=self.image_file.file_id,
                baseFileName=baseFileName,
            )
            if urls:
                imageFileInfo['name'] = os.path.basename(urls[0]['url__url'])
            targetImageIdList = [ x.target_image_id
                for x in self.image_file.targetimagesdeployed_set.all() ]

            params = dict(
                descriptorData=job._descriptor_data,
                imageFileInfo=imageFileInfo,
                imageDownloadUrl=imageDownloadUrl,
                targetImageXmlTemplate=self._targetImageXmlTemplate(),
                imageFileUpdateUrl='http://localhost/api/v1/images/%s/build_files/%s' % (
                        self.image.image_id, self.image_file.file_id),
                targetImageIdList=targetImageIdList,
                imageData = self.mgr.mgr.imagesManager.getImageData(self.image),
            )
            return (params, ), {}

        def getRelatedThroughModel(self, descriptor):
            return imagemodels.JobImage

        def getRelatedResource(self, descriptor):
            imageId = self.extraArgs['imageId']
            relatedResources = [ self.image ]
            if imageId != str(self.image.image_id):
                # We have a base image
                relatedResources.append(
                    imagemodels.Image.objects.get(image_id=imageId))
            return relatedResources

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

    class TargetLaunchSystem(TargetDeployImage):
        __slots__ = []
        jobType = models.EventType.TARGET_LAUNCH_SYSTEM
        ResultsTag = 'systems'

        def getRepeaterMethod(self, cli, job):
            JobHandlerRegistry.TargetDeployImage.getRepeaterMethod(self, cli, job)
            return cli.targets.launchSystem

        def getRepeaterMethodArgs(self, cli, job):
            args, kwargs = JobHandlerRegistry.TargetDeployImage.getRepeaterMethodArgs(self, cli, job)
            params = args[0]
            # Use the original image id, which should be the non-base
            # image
            params.update(systemsCreateUrl =
                "http://localhost/api/v1/jobs/%s/systems" % (job.job_uuid, ))
            return args, kwargs

        def _processJobResults(self, job):
            # Nothing to be done, there is another call that posts the
            # image
            images = list(job.images.all())
            if not images:
                raise ImageDeletedError("Image was deleted during deployment")
            self.image = images[0].image

            systems = self.results.iterchildren('system')

            results = []
            for targetSystem in systems:
                # System XML does not contain a target id, hence duplicate lookup
                # we should fix this
                targetName = modellib.Etree.findBasicChild(
                        targetSystem, 'targetName')
                targetSystemId = modellib.Etree.findBasicChild(
                        targetSystem, 'target_system_id')
                target = targetmodels.Target.objects.get(name=targetName)
                realSystem = inventorymodels.System.objects.get(
                    target = target,
                    target_system_id = targetSystemId,
                )
                # The system may not have network info yet, so don't try
                # to do anything clever here (Mingle #1785)
                results.append(realSystem)

            return results

        def getRelatedResource(self, descriptor):
            imageId = self.extraArgs['imageId']
            if imageId != str(self.image.image_id):
                # image ID in url corresponds to the deferred image
                return [ imagemodels.Image.objects.get(image_id=imageId) ]
            return [ self.image ]

    class TargetCreator(DescriptorJobHandler):
        __slots__ = [ 'targetType', ]
        jobType = models.EventType.TARGET_CREATE
        ResultsTag = 'target'

        def _init(self):
            DescriptorJobHandler._init(self)
            self.targetType = None

        def getDescriptor(self, descriptorId):
            match = self.splitResourceId(descriptorId)

            targetTypeId = int(match.kwargs['target_type_id'])
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

        def getRelatedResource(self, descriptor):
            return self.targetType

        def getRelatedThroughModel(self, descriptor):
            return targetmodels.JobTargetType

        def _processJobResults(self, job):
            targetType = self._getTargetType(job)
            targetType, targetName, targetData = self._createTargetConfiguration(job, targetType)
            target = self._createTarget(targetType, targetName, targetData)
            return target

        def handleError(self, job, exc):
            if isinstance(exc, (IntegrityError, errors.Conflict)):
                job.job_state = self.mgr.getJobStateByName(models.JobState.FAILED)
                job.status_text = "Duplicate Target"
                job.status_code = 409
                return True
            return False

        def _createTarget(self, targetType, targetName, config):
            return self.mgr.mgr.createTarget(targetType, targetName, config)


    class TargetConfigurator(_TargetDescriptorJobHandler):
        __slots__ = []
        jobType = models.EventType.TARGET_CONFIGURE
        ResultsTag = 'target'

        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorTargetConfiguration

        def getRepeaterMethod(self, cli, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            targetType, targetName, targetData = self._createTargetConfiguration(job, self.target.target_type)
            zone = targetData.pop('zone')
            targetConfiguration = cli.targets.TargetConfiguration(targetType.name,
                targetName, targetData.get('alias'), targetData)
            userCredentials = None
            cli.targets.configure(zone, targetConfiguration, userCredentials)
            return cli.targets.checkCreate

        def getRelatedResource(self, descriptor):
            return self.target

        def _processJobResults(self, job):
            targetId = job.target_jobs.all()[0].target_id
            self._setTarget(targetId)
            targetType, targetName, targetData = self._createTargetConfiguration(job, self.target.target_type)
            target = self._createTarget(targetType, targetName, targetData)
            return target

        def _createTarget(self, targetType, targetName, config):
            # We don't allow for the type to change
            return self.mgr.mgr.updateTargetConfiguration(self.target,
                targetName, config)

        def handleError(self, job, exc):
            if isinstance(exc, (IntegrityError, errors.Conflict)):
                job.job_state = self.mgr.getJobStateByName(models.JobState.FAILED)
                job.status_text = "Duplicate Target"
                job.status_code = 409
                return True
            return False

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
            targetUserCredentials = self._buildTargetCredentials(cli, job, creds)
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

    class ImageBuildCancellation(DescriptorJobHandler):
        __slots__ = [ 'image', ]
        jobType = models.EventType.IMAGE_CANCEL_BUILD
        ResultsTag = 'image'

        def createRmakeJob(self, job):
            self.extractDescriptorData(job)
            return job.job_uuid, None

        def getDescriptor(self, descriptorId):
            match = self.splitResourceId(descriptorId)

            imageId = int(match.kwargs['image_id'])
            if str(imageId) != str(self.extraArgs.get('imageId')):
                raise errors.InvalidData(msg = "image id does not match")
            self._setImage(imageId)
            return self.mgr.mgr.imagesManager.getImageDescriptorCancelBuild(imageId)

        def getRelatedResource(self, descriptor):
            return self.image

        def getRelatedThroughModel(self, descriptor):
            return imagemodels.JobImage

        def _setImage(self, imageId):
            image = imagemodels.Image.objects.get(image_id=imageId)
            self.image = image

        def postCreateJob(self, job):
            self.mgr.mgr.cancelImageBuild(self.image, job)

    class TargetLaunchProfileHandler(_TargetDescriptorJobHandler):
        jobType = models.EventType.TARGET_CREATE_LAUNCH_PROFILE
        ResultsTag = 'launch_profile'

        def createRmakeJob(self, job):
            self.descriptor, self.descriptorData = self.extractDescriptorData(job)
            return job.job_uuid, None

        def _getDescriptorMethod(self):
            return self.mgr.mgr.getDescriptorCreateLaunchProfile

        def postCreateJob(self, job):
            try:
                self.mgr.mgr.createTargetLaunchProfile(self.target, job, self.descriptorData)
            except (IntegrityError, errors.Conflict), e:
                self.mgr.mgr.rollback()
                self.mgr.updateJobState(job,
                        stateName=models.JobState.FAILED,
                        statusText=str(e),
                        statusCode=409)
                raise errors.Conflict(msg=job.status_text)
            self.mgr.finishJob(job)

        def handleError(self, job, exc):
            if isinstance(exc, (IntegrityError, errors.Conflict)):
                job.job_state = self.mgr.getJobStateByName(models.JobState.FAILED)
                job.status_text = "Duplicate Launch Profile"
                job.status_code = 409
                return True
            return False


class ImageDeletedError(Exception):
    pass
