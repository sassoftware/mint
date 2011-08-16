#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys

from django.db import models

from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
import urlparse
from xobj import xobj

XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly
APIImmutable = modellib.APIImmutable

# ==========================================================
# descriptors needed to launch certain jobs, when adding
# items here also update DESCRIPTOR_MAP below and make
# sure the descriptor serving service for your resource
# (ex: system, image, etc) knows about the new type

# no parameters required for assimilation --- just
# uses the management_interface credentials directly

system_assimilate_descriptor = """
<descriptor>
</descriptor>
"""

image_builds_descriptor = """
<descriptor>
</descriptor>
"""

# ==========================================================

class Actions(modellib.XObjModel):
    class Meta:
        abstract = True
        
    list_fields = ['action']
    
class JobDescriptor(modellib.XObjIdModel):
    '''URL to fetch a smartforms descriptor from'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='descriptor', attributes={'id':str})
    id = models.TextField(null=True)
    
    def serialize(self, request):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model.id = self.get_absolute_url(request)
        return xobj_model

    def get_absolute_url(self, request, *args, **kwargs):
        # this may serve systems, images, etc
        fullpath = request.get_full_path()
        return request.build_absolute_uri(
            urlparse.urljoin(fullpath, "descriptors/%s" % self.id)
        )

# NOTE: this being an id model is bogus, and is only so we can
# override serializaiton

class Action(modellib.XObjIdModel):
    '''Represents the ability to spawn a job, and how to do it'''
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='action', attributes={'type':str})
    
    type        = models.CharField(max_length=1026)
    name        = models.CharField(max_length=1026)
    description = models.TextField()
    descriptor  = JobDescriptor()

    #def serialize(self, request=None):
    #    # TODO: supply actual values
    #    xobj_model = modellib.XObjIdModel.serialize(self, request)
    #    xobj_model.descriptor.id = '9001'
    #    return xobj_model

class Jobs(modellib.Collection):
    
    XSL = 'jobs.xsl'
    
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
        return request.build_absolute_uri(request.get_full_path())

class Job(modellib.XObjIdModel):
    
    XSL = 'job.xsl'
    
    class Meta:
        db_table = 'jobs_job'
    _xobj = xobj.XObjMetadata(
                tag = 'job',
                attributes = {'id':str})
    _xobj_hidden_accessors = set([
        "package_version_jobs",
        "package_source_jobs",
        "package_build_jobs"])

    objects = modellib.JobManager()

    # The URL will contain the UUID, so there's no point in exposing job_id
    job_id = D(XObjHidden(models.AutoField(primary_key=True)),
        "the database id of the job")
    job_uuid = D(models.CharField(max_length=64, unique=True),
        "a UUID for job tracking purposes")
    job_state = D(modellib.DeferredForeignKey("JobState", 
        text_field='name', related_name='jobs'),
        "the current state of the job")
    status_code = D(models.IntegerField(default=100),
        "the current status code of the job, typically an http status code")
    status_text = D(models.TextField(default='Initializing'),
        "the message associated with the current status")
    status_detail = D(XObjHidden(models.TextField(null=True)),
        "documentation missing")
    job_type = D(APIImmutable(modellib.DeferredForeignKey("EventType",
        text_field='name', related_name="jobs", null=False)),
        "The job type")
    descriptor = D(XObjHidden(models.TextField(null=True)),
        " ")
    descriptor_data = D(XObjHidden(models.TextField(null=True)),
        " ")
    time_created = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the job was created (UTC)")
    time_updated =  D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the job was updated (UTC)")
    job_description = D(modellib.SyntheticField(),
        "a description of the job")


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

    def setValuesFromRmake(self):
        runningState = modellib.Cache.get(JobState,
            name=JobState.RUNNING)
        if self.job_state_id != runningState.pk:
            return
        completedState = modellib.Cache.get(JobState,
            name=JobState.COMPLETED)
        failedState = modellib.Cache.get(JobState,
            name=JobState.FAILED)
        # This job is still running, we need to poll rmake to get its
        # status
        job = self.getRmakeJob()
        if job:
            self.status_code = job.status.code
            self.status_text = job.status.text
            self.status_detail = job.status.detail
            if job.status.final:
                if job.status.completed:
                    self.job_state = completedState
                else:
                    self.job_state = failedState
            self.save()

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            if isinstance(parents[0], JobState):
                self.view_name = 'JobStateJobs'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

    def get_url_key(self, *args, **kwargs):
        return [ self.job_uuid ]

    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        self.setValuesFromRmake()
        xobj_model.job_description = self.job_type.description
        return xobj_model

class JobStates(modellib.Collection):
    
    XSL = 'jobStates.xsl'
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'job_states',
                elements=['job_state'])
    list_fields = ['job_state']
    job_state = []

class JobState(modellib.XObjIdModel):
    
    XSL = 'jobState.xsl'
    
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
    name = D(models.CharField(max_length=64, unique=True, choices=choices), "the name of the job state")

    load_fields = [ name ]

class EventTypes(modellib.XObjModel):

    XSL = 'eventTypes.xsl'

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'event_types')
    list_fields = ['event_type']
    event_type = []

    def save(self):
        return [s.save() for s in self.event_type]

class EventType(modellib.XObjIdModel):
    
    XSL = 'eventType.xsl'
    
    class Meta:
        db_table = 'jobs_job_type'
        managed = False
    _xobj = xobj.XObjMetadata(tag='event_type')
    
     # hide jobs, see https://issues.rpath.com/browse/RBL-7151
    _xobj_hidden_accessors = set(['jobs'])

    # on-demand events need to be > 100 to be dispatched immediately
    # DO NOT CHANGE POLL PRIORITIES HERE WITHOUT CHANGING IN schema.py also
    ON_DEMAND_BASE = 100
    
    SYSTEM_POLL = "system poll"
    SYSTEM_POLL_PRIORITY = 50
    SYSTEM_POLL_DESC = "System synchronization"
    RESOURCE_TYPE = 'System'
    
    SYSTEM_POLL_IMMEDIATE = "immediate system poll"
    SYSTEM_POLL_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_POLL_IMMEDIATE_DESC = "On-demand system synchronization"
    RESOURCE_TYPE = 'System'
    
    SYSTEM_REGISTRATION = "system registration"
    SYSTEM_REGISTRATION_PRIORITY = ON_DEMAND_BASE + 10
    SYSTEM_REGISTRATION_DESC = "System registration"
    RESOURCE_TYPE = 'System'

    SYSTEM_APPLY_UPDATE = 'system apply update'
    SYSTEM_APPLY_UPDATE_PRIORITY = 50
    SYSTEM_APPLY_UPDATE_DESCRIPTION = 'Scheduled system update'
    RESOURCE_TYPE = 'System'
        
    SYSTEM_APPLY_UPDATE_IMMEDIATE = 'immediate system apply update'
    SYSTEM_APPLY_UPDATE_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_APPLY_UPDATE_IMMEDIATE_DESCRIPTION = \
        'System update'
    RESOURCE_TYPE = 'System'    

    SYSTEM_SHUTDOWN = 'system shutdown'
    SYSTEM_SHUTDOWN_PRIORITY = 50
    SYSTEM_SHUTDOWN_DESCRIPTION = 'Scheduled system shutdown'
    RESOURCE_TYPE = 'System'

    SYSTEM_DETECT_MANAGEMENT_INTERFACE = 'system detect management interface'
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_PRIORITY = 50
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_DESC = \
        "System management interface detection"
    RESOURCE_TYPE = 'System'
        
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE = \
        'immediate system detect management interface'
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_PRIORITY = 105
    SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_DESC = \
        "On-demand system management interface detection"
    RESOURCE_TYPE = 'System'    

    SYSTEM_SHUTDOWN_IMMEDIATE = 'immediate system shutdown'
    SYSTEM_SHUTDOWN_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_SHUTDOWN_IMMEDIATE_DESCRIPTION = \
        'System shutdown'
    RESOURCE_TYPE = 'System'    

    LAUNCH_WAIT_FOR_NETWORK = 'system launch wait'
    LAUNCH_WAIT_FOR_NETWORK_DESCRIPTION = "Launched system network data discovery"
    LAUNCH_WAIT_FOR_NETWORK_PRIORITY = ON_DEMAND_BASE + 5
    RESOURCE_TYPE = 'System'
    
    SYSTEM_CONFIG_IMMEDIATE = 'immediate system configuration'
    SYSTEM_CONFIG_IMMEDIATE_DESCRIPTION = "Update system configuration"
    SYSTEM_CONFIG_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    RESOURCE_TYPE='System'

    SYSTEM_ASSIMILATE             = 'system assimilation'
    SYSTEM_ASSIMILATE_DESCRIPTION = 'System assimilation'
    RESOURCE_TYPE='System'
    
    IMAGE_BUILDS = 'image builds'
    IMAGE_BUILDS_DESCRIPTION = 'Image builds'
    RESOURCE_TYPE = 'Image'
        
    job_type_id = D(models.AutoField(primary_key=True), "the database id of the  type")
    EVENT_TYPES = (
        (SYSTEM_REGISTRATION, SYSTEM_REGISTRATION_DESC),
        (SYSTEM_POLL_IMMEDIATE, SYSTEM_POLL_IMMEDIATE_DESC),
        (SYSTEM_POLL, SYSTEM_POLL_DESC),
        (SYSTEM_APPLY_UPDATE, SYSTEM_APPLY_UPDATE_DESCRIPTION),
        (SYSTEM_APPLY_UPDATE_IMMEDIATE,
         SYSTEM_APPLY_UPDATE_IMMEDIATE_DESCRIPTION),
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
        (SYSTEM_CONFIG_IMMEDIATE,
         SYSTEM_CONFIG_IMMEDIATE_DESCRIPTION),
        (SYSTEM_ASSIMILATE, SYSTEM_ASSIMILATE_DESCRIPTION),
        (IMAGE_BUILDS, IMAGE_BUILDS_DESCRIPTION)
    )

    # what smartform descriptor templates are needed to launch jobs of
    # certain types?
    DESCRIPTOR_MAP = {
        SYSTEM_ASSIMILATE : system_assimilate_descriptor,
        IMAGE_BUILDS : image_builds_descriptor
    }
    
    
    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True,
        choices=EVENT_TYPES)), "the event type name (read-only)")
    description = D(models.CharField(max_length=8092), "the event type description")
    priority = D(models.SmallIntegerField(db_index=True), "the event type priority where > priority wins")
    resource_type = D(models.TextField(), "the resource type for the job")

    @property
    def requiresManagementInterface(self):
        if self.name in \
            [self.SYSTEM_REGISTRATION,
             self.SYSTEM_POLL_IMMEDIATE,
             self.SYSTEM_POLL,
             self.SYSTEM_APPLY_UPDATE,
             self.SYSTEM_APPLY_UPDATE_IMMEDIATE,
             self.SYSTEM_SHUTDOWN,
             self.SYSTEM_SHUTDOWN_IMMEDIATE,
             self.SYSTEM_CONFIG_IMMEDIATE,
             self.SYSTEM_ASSIMILATE,
            ]:
            return True
        else:
            return False

    @classmethod
    def makeAction(cls, name):
        '''Return a related Action object for spawning this jobtype'''
        obj        = cls.objects.get(name=name)
        action  = Action(
            type        = obj.job_type_id,
            name        = name,
            description = obj.description
        )
        action.descriptor = JobDescriptor(id=obj.job_type_id)
        return action

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj