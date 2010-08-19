#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import sys
import datetime
from dateutil import tz

from django.db import models
from django.core import exceptions

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

class Inventory(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory',
                elements = ['managementNodes', 'systems', 'log', "eventTypes"])

    def __init__(self):
        self.managementNodes = modellib.XObjHrefModel('managementNodes/')
        self.systems = modellib.XObjHrefModel('systems/')
        self.log = modellib.XObjHrefModel('log/')
        self.eventTypes = modellib.XObjHrefModel('eventTypes/')

class Systems(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems',
                elements=['system'])
    list_fields = ['system']
    system = []

    def save(self):
        return [s.save() for s in self.system]
    
class ManagementNodes(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'managementNodes',
                elements=['managementNode'])
    list_fields = ['managementNode']
    managementNode = []

    def save(self):
        return [s.save() for s in self.managementNode]
    
class EventTypes(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'eventTypes',
                elements=['eventType'])
    list_fields = ['eventType']
    eventType = []

    def save(self):
        return [s.save() for s in self.eventType]
    
class SystemsLog(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='systemsLog')
    list_fields = ['systemLogEntry']
    systemLogEntry = []

class SystemEvents(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systemEvents')
    list_fields = ['systemEvent']
    systemEvent = []

    def save(self):
        return [s.save() for s in self.systemEvent]

class Networks(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='networks',
                elements=['network'])
    list_fields = ['network']

class System(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system'
    _xobj = xobj.XObjMetadata(
                tag = 'system',
                attributes = {'id':str},
                elements = ['networks'])
    
    UNMANAGED = "unmanaged"
    ACTIVATED = "activated"
    RESPONSIVE = "responsive"
    SHUTDOWN = "shutdown"
    NONRESPONSIVE = "non-responsive"
    DEAD = "dead"
    MOTHBALLED = "mothballed"
    
    system_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092)
    description = models.CharField(max_length=8092, null=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    # Launch date is nullable, we may get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = modellib.DateTimeUtcField(null=True)
    target = models.ForeignKey(rbuildermodels.Targets, null=True)
    target_system_id = models.CharField(max_length=255, null=True)
    reservation_id = models.CharField(max_length=255, null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)
    activation_date = modellib.DateTimeUtcField(null=True)
    generated_uuid = models.CharField(max_length=64, unique=True, null=True)
    local_uuid = models.CharField(max_length=64, null=True)
    ssl_client_certificate = models.CharField(max_length=8092, null=True)
    ssl_client_key = models.CharField(max_length=8092, null=True)
    ssl_server_certificate = models.CharField(max_length=8092, null=True)
    scheduled_event_start_date = modellib.DateTimeUtcField(null=True)
    launching_user = models.ForeignKey(rbuildermodels.Users, null=True)
    available = models.NullBooleanField()
    activated = models.NullBooleanField()
    STATE_CHOICES = (
        (UNMANAGED, UNMANAGED),
        (ACTIVATED, ACTIVATED),
        (RESPONSIVE, RESPONSIVE),
        (SHUTDOWN, SHUTDOWN),
        (NONRESPONSIVE, NONRESPONSIVE),
        (DEAD, DEAD),
        (MOTHBALLED, MOTHBALLED),
    )
    current_state = models.CharField(max_length=32, choices=STATE_CHOICES, null=True)
    installed_software = models.ManyToManyField('Trove', null=True)
    is_management_node = models.NullBooleanField()
    # the management node managing this system.
    managing_node = models.ForeignKey('ManagementNode', null=True,
                        related_name='systems')

    load_fields = [local_uuid]

    def addJobs(self):
        return
        # Put these imports here for now so they don't break anything
        # globally.
        from rmake3 import client
        RMAKE_ADDRESS = 'http://localhost:9998'
        rmake_client = client.RmakeClient(RMAKE_ADDRESS)

        job_uuids = [sj.job_uuid for sj in self.system_jobs.all()]
        rmake_jobs = rmake_client.getJobs(job_uuids)

        for rmake_job in rmake_jobs:
            # TODO, make a models.Job instance

            # add it to the system
            pass

class EventType(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_event_type'
        
    # on-demand events need to be > 100 to be dispatched immediately
    # DO NOT CHANGE POLL PRIORITIES HERE WITHOUT CHANGING IN schema.py also
    ON_DEMAND_BASE = 100
    
    SYSTEM_POLL = "system poll"
    SYSTEM_POLL_PRIORITY = 50
    SYSTEM_POLL_DESC = "standard system polling event"
    
    SYSTEM_POLL_IMMEDIATE = "immediate system poll"
    SYSTEM_POLL_IMMEDIATE_PRIORITY = ON_DEMAND_BASE +5
    SYSTEM_POLL_IMMEDIATE_DESC = "on-demand system polling event"
    
    SYSTEM_ACTIVATION = "system activation"
    SYSTEM_ACTIVATION_PRIORITY = ON_DEMAND_BASE +10
    SYSTEM_ACTIVATION_DESC = "on-demand system activation event"
        
    event_type_id = models.AutoField(primary_key=True)
    EVENT_TYPES = (
        (SYSTEM_ACTIVATION, SYSTEM_ACTIVATION_DESC),
        (SYSTEM_POLL_IMMEDIATE, SYSTEM_POLL_IMMEDIATE_DESC),
        (SYSTEM_POLL, SYSTEM_POLL_DESC),
    )
    name = models.CharField(max_length=8092, db_index=True, choices=EVENT_TYPES)
    description = models.CharField(max_length=8092)
    priority = models.SmallIntegerField(db_index=True)

class Job(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_job'
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.CharField(max_length=64)
    event_type = models.ForeignKey(EventType)
    time_created = modellib.DateTimeUtcField(auto_now_add=True)

class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    _xobj = xobj.XObjMetadata(
                tag = 'systemEvent',
                attributes = {'id':str})
    
    system_event_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, db_index=True,
        related_name='system_events')
    event_type = modellib.DeferredForeignKey(EventType)
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_enabled = modellib.DateTimeUtcField(
        default=datetime.datetime.now(tz.tzutc()), db_index=True)
    priority = models.SmallIntegerField(db_index=True)
    
    def dispatchImmediately(self):
        return self.event_type.priority >= EventType.ON_DEMAND_BASE

class ManagementNode(System):
    class Meta:
        db_table = 'inventory_management_node'
    _xobj = xobj.XObjMetadata(
                tag = 'managementNode',
                attributes = {'id':str})
    local = models.NullBooleanField()
    
    load_ignore_fields = ["system_ptr"]
    
    def save(self, *args, **kw):
        self.is_management_node = True
        modellib.XObjModel.save(self, *args, **kw)

class Network(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_network'
    _xobj = xobj.XObjMetadata(
                tag='network')
    network_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System, related_name='networks')
    ip_address = models.CharField(max_length=15, null=True)
    # TODO: how long should this be?
    ipv6_address = models.CharField(max_length=32, null=True)
    device_name = models.CharField(max_length=255) 
    public_dns_name = models.CharField(max_length=255, db_index=True)
    netmask = models.CharField(max_length=20, null=True)
    port_type = models.CharField(max_length=32, null=True)
    primary = models.NullBooleanField()
    # TODO: add all the other fields we need about a network

    load_fields = [ip_address, public_dns_name]

    def natural_key(self):
        return self.ip_address, self.public_dns_name

class SystemLog(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_log'
    system_log_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, related_name='system_log')

    def get_absolute_url(self, request, pk=None):
        try:
            pk = self.system.pk
        except exceptions.ObjectDoesNotExist:
            pk = pk
        return modellib.XObjIdModel.get_absolute_url(self, request, pk)

class SystemLogEntry(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='systemLogEntry')
    class Meta:
        db_table = 'inventory_system_log_entry'
        ordering = ['entry_date']
        
    ADDED = "System added to inventory"
    ACTIVATED = "System activated via ractivate"
    MANUALLY_ACTIVATED = "System manually activated via rBuilder"
    POLLED = "System polled."
    FETCHED = "System data fetched."
    choices = (
        (ADDED, ADDED),
        (ACTIVATED, ACTIVATED),
        (MANUALLY_ACTIVATED, MANUALLY_ACTIVATED),
        (POLLED, POLLED),
        (FETCHED, FETCHED),
    )

    system_log_entry_id = models.AutoField(primary_key=True)
    system_log = models.ForeignKey(SystemLog,
        related_name='system_log_entries')
    entry = models.CharField(max_length=8092, choices=choices)
    entry_date = modellib.DateTimeUtcField(auto_now_add=True)

class Trove(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_trove'
        unique_together = (('name', 'version', 'flavor'),)
    trove_id = models.AutoField(primary_key=True)
    name = models.TextField()
    version = modellib.SerializedForeignKey('Version')
    flavor = models.TextField()
    is_top_level = models.BooleanField()
    last_available_update_refresh = modellib.DateTimeUtcField(
        auto_now_add=True)
    available_updates = models.ManyToManyField('Version',
        related_name='available_updates')

    def _is_top_level_group(self):
        return self.name.startswith('group-') and \
            self.name.endswith('-appliance')

    def save(self, *args, **kw):
        if self._is_top_level_group():
            self.is_top_level = True
        else:
            self.is_top_level = False
        modellib.XObjModel.save(self, *args, **kw)

class Version(modellib.XObjModel):
    serialize_accessors = False
    class Meta:
        db_table = 'inventory_version'
    version_id = models.AutoField(primary_key=True)
    full = models.TextField()
    label = models.TextField()
    revision = models.TextField()
    ordering = models.TextField()
    flavor = models.TextField()

class SystemJob(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_job'
    system_job_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System)
    job = models.ForeignKey(Job)

class ErrorResponse(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='fault')
    class Meta:
        abstract = True
    code = models.TextField()
    message = models.TextField()
    traceback = models.TextField()
    product_code = models.TextField()

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
for mod_obj in rbuildermodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
