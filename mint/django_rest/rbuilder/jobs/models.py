#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.inventory import survey_models

from xobj import xobj

XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly

class JobSystemArtifact(modellib.XObjModel):
    class Meta:
        db_table = 'jobs_created_system'
        unique_together = [ 'job', 'system' ]
    _xobj = xobj.XObjMetadata(tag = 'system_artifact')
    
    creation_id = XObjHidden(models.AutoField(primary_key=True))
    job         = XObjHidden(modellib.ForeignKey('Job', db_column='job_id', related_name='created_systems'))
    system      = modellib.ForeignKey('inventory.System', db_column='system_id', related_name='+')

class JobImageArtifact(modellib.XObjModel):
    class Meta:
        db_table = 'jobs_created_image'
        unique_together = [ 'job', 'image' ]
    _xobj = xobj.XObjMetadata(tag = 'image_artifact')

    creation_id = XObjHidden(models.AutoField(primary_key=True))
    job         = XObjHidden(modellib.ForeignKey('Job', db_column='job_id', related_name='created_images'))
    image       = modellib.ForeignKey('images.Image', db_column='image_id', related_name='+')

class JobSurveyArtifact(modellib.XObjModel):
    class Meta:
        db_table = 'jobs_created_survey'
        unique_together = [ 'job', 'survey' ]
    _xobj = xobj.XObjMetadata(tag = 'survey_artifact')

    id = XObjHidden(models.AutoField(primary_key=True))
    job = XObjHidden(modellib.ForeignKey('Job', related_name='created_surveys'))
    survey = modellib.ForeignKey(survey_models.Survey, related_name='created_surveys')


class ActionResources(modellib.UnpaginatedCollection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'resources')
    list_fields = ['resource']
    resource = []

class JobCreatedResources(modellib.UnpaginatedCollection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'created_resources')
    list_fields = ['resource']
    resource = []

class Actions(modellib.XObjModel):
    class Meta:
        abstract = True

    list_fields = ['action']

class Action(modellib.XObjModel):
    '''Represents the ability to spawn a job, and how to do it'''
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='action', attributes={})

    job_type    = modellib.HrefField()
    key         = models.CharField(max_length=1026)
    name        = models.CharField(max_length=1026)
    description = models.TextField()
    descriptor  = modellib.HrefField()
    enabled     = models.BooleanField(default=True)
    resources   = modellib.SyntheticField()

class Jobs(modellib.Collection):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'jobs',
                elements=['job'],
                attributes={'id':str})
    list_fields = ['job']
    job = []
 
    def get_absolute_url(self, request, *args, **kwargs):
        """
        This implementation of get_absolute_url is a bit different since the
        jobs collection can be serialized on it's own from 2 different places
        (/api/inventory/jobs or /api/inventory/systems/{systemId}/jobs).  We
        need to ask the request to build the id for us based on the path.
        """
        uri = request.build_absolute_uri(request.get_full_path())
        # hack to remove possible query options
        return uri.split("?")[0]



class Job(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'jobs_job'
    _xobj = xobj.XObjMetadata(
                tag = 'job',
                attributes = {'id':str})
    _xobj_explicit_accessors = set(['systems'])

    #objects = modellib.JobManager()

    # The URL will contain the UUID, so there's no point in exposing job_id
    job_id = D(XObjHidden(models.AutoField(primary_key=True)),
        "the database id of the job")
    job_uuid = D(models.CharField(max_length=64, unique=True),
        "a UUID for job tracking purposes, must be unique")
    job_token = D(XObjHidden(APIReadOnly(
        models.CharField(max_length=64, null=True, unique=True))),
        "cookie token for updating this job")
    job_state = D(modellib.DeferredForeignKey("JobState",
        text_field='name', related_name='jobs'),
        "the current state of the job")
    status_code = D(models.IntegerField(default=100),
        "the current status code of the job, typically an http status code")
    status_text = D(models.TextField(default='Initializing'),
        "the message associated with the current status, defaults to 'Initializing'")
    status_detail = D(XObjHidden(models.TextField(null=True)),
        "documentation missing")
    job_type = D(modellib.DeferredForeignKey("EventType",
        text_field='name', related_name="jobs", null=False),
        "The job type, cannot be null")
    _descriptor = D(XObjHidden(models.TextField(null=True, db_column="descriptor")),
        " ")
    _descriptor_data = D(XObjHidden(models.TextField(null=True, db_column="descriptor_data")),
        " ")
    descriptor = D(modellib.SyntheticField(), "")
    descriptor_data = D(modellib.SyntheticField(), "")
    time_created = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the job was created (UTC)")
    time_updated =  D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the job was updated (UTC)")
    job_description = D(modellib.SyntheticField(),
        "a description of the job")
    results = modellib.SyntheticField()
    created_resources = modellib.SyntheticField()

    created_by = D(modellib.APIReadOnly(modellib.DeferredForeignKey(
            usermodels.User, related_name="jobs", null=True,
            db_column="created_by")),
        "The user who initiated the job")


    load_fields = [ job_uuid ]

    def getRmakeJob(self):
        # XXX we should be using the repeater client for this
        import rmake3
        RMAKE_ADDRESS = 'http://localhost:9998'
        rmakeClient = rmake3.client.RmakeClient(RMAKE_ADDRESS)
        try:
            rmakeJobs = rmakeClient.getJobs([self.job_uuid])
        except rmake3.errors.OpenError:
            return None 
        if rmakeJobs:
            return rmakeJobs[0]
        return None

    def setDefaultValues(self):
        runningState = modellib.Cache.get(JobState,
            name=JobState.RUNNING)
        self.job_state = runningState
        self.status_code = 100
        self.status_text = "Running"

    def setValuesFromRmake(self):
        runningState = modellib.Cache.get(JobState,
            name=JobState.RUNNING)
        if self.job_state_id != runningState.pk:
            return
        # This job is still running, we need to poll rmake to get its
        # status
        job = self.getRmakeJob()
        if job:
            self.setValuesFromRmakeJob(job)

    def setValuesFromRmakeJob(self, job):
        runningState = modellib.Cache.get(JobState,
            name=JobState.RUNNING)
        completedState = modellib.Cache.get(JobState,
            name=JobState.COMPLETED)
        failedState = modellib.Cache.get(JobState,
            name=JobState.FAILED)
        self.job_uuid = str(job.job_uuid)
        self.status_code = job.status.code
        self.status_text = job.status.text
        self.status_detail = job.status.detail
        if job.status.final:
            if job.status.completed:
                self.job_state = completedState
            else:
                self.job_state = failedState
        elif self.job_state_id is None:
            self.job_state = runningState

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            if isinstance(parents[0], JobState):
                self.view_name = 'JobStateJobs'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

    def get_url_key(self, *args, **kwargs):
        return [ self.job_uuid ]

    def computeSyntheticFields(self, *args, **kwargs):

        # removes some layers of nesting by not showing the artifact records
        # but instead presenting a unified collection of results containing
        # multiple types of resources
        self.created_resources = JobCreatedResources()
        resources = []
        resources.extend([ x.image for x in self.created_images.all() ])
        resources.extend([ x.system for x in self.created_systems.all() ])
        resources2 = []
        for r in resources:
            res = modellib.HrefFieldFromModel(r, tag=r._xobj.tag)
            resources2.append(res)
        self.created_resources.resource = resources2

    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        self.setValuesFromRmake()
        xobj_model.job_description = self.job_type.description

        return xobj_model

class JobStates(modellib.Collection):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'job_states',
                elements=['job_state'])
    list_fields = ['job_state']
    job_state = []

class JobState(modellib.XObjIdModel):
    
    class Meta:
        db_table = "jobs_job_state"
        managed = False
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    choices = (
        (QUEUED, QUEUED),
        (RUNNING, RUNNING),
        (COMPLETED, COMPLETED),
        (FAILED, FAILED),
    )
    _xobj = xobj.XObjMetadata(tag='job_state',
                attributes = {'id':str})

    job_state_id = D(models.AutoField(primary_key=True), "the database ID for the job state")
    name = D(models.CharField(max_length=64, unique=True, choices=choices),
        "the name of the job state, must be unique")

    load_fields = [ name ]

class EventTypes(modellib.XObjModel):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'event_types')
    list_fields = ['event_type']
    event_type = []

    def save(self):
        return [s.save() for s in self.event_type]

class EventType(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'jobs_job_type'
        managed = False
    _xobj = xobj.XObjMetadata(tag='event_type')
    
    # hide jobs, see https://issues.rpath.com/browse/RBL-7151
    _xobj_explicit_accessors = set(['system_events', ])

    # on-demand events need to be > 100 to be dispatched immediately
    # DO NOT CHANGE POLL PRIORITIES HERE WITHOUT CHANGING IN schema.py also
    ON_DEMAND_BASE = 100
    
    # resource type == system #########################################

    SYSTEM_REGISTRATION = "system registration"
    SYSTEM_REGISTRATION_PRIORITY = 70
    SYSTEM_REGISTRATION_DESC = "System registration"

    SYSTEM_REGISTRATION_IMMEDIATE = "immediate system registration"
    SYSTEM_REGISTRATION_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 10
    SYSTEM_REGISTRATION_IMMEDIATE_DESC = "On-demand system registration"


    SYSTEM_APPLY_UPDATE = 'system apply update'
    SYSTEM_APPLY_UPDATE_PRIORITY = 50
    SYSTEM_APPLY_UPDATE_DESCRIPTION = 'Scheduled system update'
        
    SYSTEM_SHUTDOWN = 'system shutdown'
    SYSTEM_SHUTDOWN_PRIORITY = 50
    SYSTEM_SHUTDOWN_DESCRIPTION = 'Scheduled system shutdown'

    SYSTEM_DETECT_MANAGEMENT_INTERFACE = 'system detect management interface'
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_PRIORITY = 50
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_DESC = \
        "System management interface detection"
        
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE = \
        'immediate system detect management interface'
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_PRIORITY = 105
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_DESC = \
        "On-demand system management interface detection"

    SYSTEM_SHUTDOWN_IMMEDIATE = 'immediate system shutdown'
    SYSTEM_SHUTDOWN_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_SHUTDOWN_IMMEDIATE_DESCRIPTION = \
        'System shutdown'

    LAUNCH_WAIT_FOR_NETWORK = 'system launch wait'
    LAUNCH_WAIT_FOR_NETWORK_DESCRIPTION = "Launched system network data discovery"
    LAUNCH_WAIT_FOR_NETWORK_PRIORITY = ON_DEMAND_BASE + 5
    
    SYSTEM_CONFIG_IMMEDIATE = 'immediate system configuration'
    SYSTEM_CONFIG_IMMEDIATE_DESCRIPTION = "Update system configuration"
    SYSTEM_CONFIG_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5

    SYSTEM_ASSIMILATE             = 'system assimilation'
    SYSTEM_ASSIMILATE_DESCRIPTION = 'System assimilation'

    SYSTEM_CAPTURE = 'system capture'
    SYSTEM_CAPTURE_DESCRIPTION = "Capture a system's image"

    SYSTEM_UPDATE = 'system update software'
    SYSTEM_UPDATE_DESCRIPTION = 'Update your system'

    SYSTEM_SCAN = 'system scan'
    SYSTEM_SCAN_DESCRIPTION = 'Scan system'

    # resource type = image ##########################################
    IMAGE_BUILDS = 'image builds'
    IMAGE_BUILDS_DESCRIPTION = 'Image builds'

    IMAGE_CANCEL_BUILD = 'image build cancellation'
    IMAGE_CANCEL_BUILD_DESCRIPTION = 'Cancel an image build'
     
    # resource type = queryset #######################################
    # these codes are not in the db because queryset jobs are (so far)
    # not backgroundable.
    QUERYSET_INVALIDATE              = 'refresh queryset'
    QUERYSET_INVALIDATE_DESCRIPTION  = 'Refresh queryset'

    TARGET_REFRESH_IMAGES = 'refresh target images'
    TARGET_REFRESH_IMAGES_DESCRIPTION = 'Refresh target images'
    TARGET_REFRESH_SYSTEMS = 'refresh target systems'
    TARGET_REFRESH_SYSTEMS_DESCRIPTION = 'Refresh target systems'
    TARGET_DEPLOY_IMAGE = 'deploy image on target'
    TARGET_DEPLOY_IMAGE_DESCRIPTION = 'Deploy image on target'
    TARGET_LAUNCH_SYSTEM = 'launch system on target'
    TARGET_LAUNCH_SYSTEM_DESCRIPTION = 'Launch system on target'
    TARGET_CREATE = 'create target'
    TARGET_CREATE_DESCRIPTION = 'Create target'
    TARGET_CONFIGURE_CREDENTIALS = 'configure target credentials'
    TARGET_CONFIGURE_CREDENTIALS_DESCRIPTION = 'Configure target credentials for the current user'
    TARGET_CONFIGURE = 'configure target'
    TARGET_CONFIGURE_DESCRIPTION = 'Configure target'
    
    SYSTEM_CONFIGURE             = 'system apply configuration'
    SYSTEM_CONFIGURE_DESCRIPTION = 'Apply system configuration'

    job_type_id = D(models.AutoField(primary_key=True), "the database id of the  type")
    EVENT_TYPES = (
        (SYSTEM_REGISTRATION, SYSTEM_REGISTRATION_DESC),
        (SYSTEM_APPLY_UPDATE, SYSTEM_APPLY_UPDATE_DESCRIPTION),
        (SYSTEM_SHUTDOWN,
         SYSTEM_SHUTDOWN_DESCRIPTION),
        (SYSTEM_SHUTDOWN_IMMEDIATE,
         SYSTEM_SHUTDOWN_IMMEDIATE_DESCRIPTION),
        (LAUNCH_WAIT_FOR_NETWORK,
         LAUNCH_WAIT_FOR_NETWORK_DESCRIPTION),
        (SYSTEM_DETECT_MANAGEMENT_INTERFACE,
         SYSTEM_DETECT_MANAGEMENT_INTERFACE_DESC),
        (SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE,
         SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_DESC),
        (SYSTEM_ASSIMILATE, SYSTEM_ASSIMILATE_DESCRIPTION),
        (SYSTEM_CAPTURE, SYSTEM_CAPTURE_DESCRIPTION),
        (SYSTEM_UPDATE, SYSTEM_UPDATE_DESCRIPTION),
        (IMAGE_BUILDS, IMAGE_BUILDS_DESCRIPTION),
        (QUERYSET_INVALIDATE, QUERYSET_INVALIDATE_DESCRIPTION),
        (TARGET_REFRESH_IMAGES, TARGET_REFRESH_IMAGES_DESCRIPTION),
        (TARGET_REFRESH_SYSTEMS, TARGET_REFRESH_SYSTEMS_DESCRIPTION),
        (TARGET_DEPLOY_IMAGE, TARGET_DEPLOY_IMAGE_DESCRIPTION),
        (TARGET_LAUNCH_SYSTEM, TARGET_LAUNCH_SYSTEM_DESCRIPTION),
        (TARGET_CREATE, TARGET_CREATE_DESCRIPTION),
        (TARGET_CONFIGURE_CREDENTIALS, TARGET_CONFIGURE_CREDENTIALS_DESCRIPTION),
        (SYSTEM_CONFIGURE, SYSTEM_CONFIGURE_DESCRIPTION)
    )

    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True,
        choices=EVENT_TYPES)), "the event type name (read-only), must be unique")
    description = D(models.CharField(max_length=8092), "the event type description")
    priority = D(models.SmallIntegerField(db_index=True), "the event type priority where > priority wins")
    resource_type = D(models.TextField(), "the resource type for the job")

    @property
    def requiresManagementInterface(self):
        if self.name in \
            [self.SYSTEM_REGISTRATION,
             self.SYSTEM_APPLY_UPDATE,
             self.SYSTEM_SHUTDOWN,
             self.SYSTEM_SHUTDOWN_IMMEDIATE,
             self.SYSTEM_ASSIMILATE,
             self.SYSTEM_CONFIGURE
            ]:
            return True
        else:
            return False

    @classmethod
    def makeAction(cls, jobTypeName, actionName=None, actionDescription=None,
            actionKey=None,
            enabled=True, descriptorModel=None, descriptorHref=None,
            descriptorHrefValues=None, descriptorViewName=None,
            resources=None):
        '''Return a related Action object for spawning this jobtype'''
        obj = modellib.Cache.get(cls, name=jobTypeName)
        if actionKey is None:
            actionKey = jobTypeName.replace(' ', '_')
        defaultActionName = jobTypeName
        defaultActionDescription = obj.description
        if actionName is None:
            actionName = defaultActionName
        if actionDescription is None:
            actionDescription = defaultActionDescription
        action = Action(
            key = actionKey,
            job_type = modellib.HrefFieldFromModel(obj),
            name = actionName,
            description = actionDescription,
            enabled = enabled,
        )
        # XXX This is too complicated
        if descriptorModel is not None:
            action.descriptor = modellib.HrefFieldFromModel(descriptorModel,
                viewName=descriptorViewName)
            action.descriptor.href = descriptorHref
            action.descriptor.values = descriptorHrefValues
        else:
            action.descriptor = modellib.HrefField("descriptors/%s",
                values=(obj.job_type_id, ))
        if resources:
            #action.resources = modellib.HrefFieldFromModel(model=resources[0])
            action.resources = ActionResources()
            for resource in resources:
                action.resources.resource.append(
                    modellib.HrefFieldFromModel(resource, tag=resource._xobj.tag))
        return action
    


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
