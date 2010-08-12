#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import sys
import datetime
from dateutil import tz

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

class Inventory(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory',
                elements = ['systems', 'log'])

    def __init__(self):
        self.systems = modellib.XObjHrefModel('systems/')
        self.log = modellib.XObjHrefModel('log/')

class Systems(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems')
    list_fields = ['system']
    system = []

    def save(self):
        return [s.save() for s in self.system]
    
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
    versions = models.ManyToManyField('Version', null=True)
    management_node = models.ForeignKey('ManagementNode', null=True,
                        related_name='system_set')

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

class SystemEventType(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event_type'
        
    POLL = "poll"
    POLL_PRIORITY = 50
    POLL_DESC = "standard polling event"
    
    POLL_NOW = "poll_now"
    POLL_NOW_PRIORITY = 90
    POLL_NOW_DESC = "on-demand polling event"
    
    ACTIVATION = "activation"
    ACTIVATION_PRIORITY = 100
    ACTIVATION_DESC = "on-demand activation event"
        
    system_event_type_id = models.AutoField(primary_key=True)
    EVENT_TYPES = (
        (ACTIVATION, ACTIVATION_DESC),
        (POLL_NOW, POLL_NOW_DESC),
        (POLL, POLL_DESC),
    )
    name = models.CharField(max_length=8092, db_index=True, choices=EVENT_TYPES)
    description = models.CharField(max_length=8092)
    priority = models.SmallIntegerField(db_index=True)
    
class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    system_event_id = models.AutoField(primary_key=True)
    system = modellib.DeferrableForeignKey(System, db_index=True,
        related_name='system_event', deferred=True)
    event_type = modellib.DeferrableForeignKey(SystemEventType, deferred=True)
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_enabled = modellib.DateTimeUtcField(
        default=datetime.datetime.now(tz.tzutc()), db_index=True)
    priority = models.SmallIntegerField(db_index=True)

# TODO: is this needed, or should we just use a recursive fk on ManagedSystem?
class ManagementNode(modellib.XObjModel):
    system = models.OneToOneField(System)
    # TODO: what extra columns might we want to store about a management node,
    # if any?

class Network(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_network'
    _xobj = xobj.XObjMetadata(
                tag='network')
    network_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System, related_name='networks')
    ip_address = models.CharField(max_length=15)
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
    system = modellib.DeferrableForeignKey(System, deferred=True,
        related_name='system_log')

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

class Version(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_version'
        unique_together = (('name', 'version', 'flavor'),)
    version_id = models.AutoField(primary_key=True)
    name = models.TextField()
    version = models.TextField()
    flavor = models.TextField()
    available_updates = models.ManyToManyField('self',
        through='AvailableUpdate', symmetrical=False,
        related_name = 'availableUpdates_set')

class AvailableUpdate(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_available_update'
        unique_together = (('software_version', 
                            'software_version_available_update'),)
    available_update_id = models.AutoField(primary_key=True)
    software_version = models.ForeignKey(Version,
        related_name='software_version_set')
    # This column is nullable, which basically means that the last time an
    # update was checked for, none was found.
    software_version_available_update = models.ForeignKey(Version,
        related_name = 'software_version_available_update_set')
    last_refreshed = modellib.DateTimeUtcField(auto_now_add=True)

class SystemJob(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_job'
    system_job_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System, related_name='system_jobs')
    job_uuid = models.CharField(max_length=64)

class Job(modellib.XObjModel):
    class Meta:
        abstract = True

    status_choices = (
        ('Queued', 'Queued'),
        ('Running', 'Running'),
        ('Failed', 'Failed'),
        ('Completed', 'Completed'),
    )

    uuid = models.CharField(max_length=64)
    status = models.CharField(16, choices=status_choices)
    created = modellib.DateTimeUtcField(auto_now_add=True)
    modified = modellib.DateTimeUtcField(auto_now_add=True)
    created_by = models.ForeignKey(rbuildermodels.Users)
    expiration = modellib.DateTimeUtcField(auto_now_add=True)
    status_message = models.TextField()
    cloud_name = models.CharField(max_length=64)
    cloud_type = models.CharField(max_length=64)
    instance_id = models.CharField(max_length=255)
    image_id = models.CharField(max_length=255)
    fault = models.ForeignKey('ErrorResponse', null=True)
    result_resource = modellib.XObjHrefModel()

class JobHistory(modellib.XObjModel):
    class Meta:
        abstract = True
    job_history_id = models.AutoField(primary_key=True)
    timestamp = modellib.DateTimeUtcField(auto_now_add=True)
    content = models.TextField()

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
