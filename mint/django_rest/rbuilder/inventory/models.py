#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import datetime
import sys
import urllib
import urlparse
from dateutil import tz

from conary import versions
from conary.deps import deps

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

class Inventory(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory',
                elements = ['zones', 'systems', 'log', "systemStates"])

    def __init__(self):
        self.zones = modellib.XObjHrefModel('zones/')
        self.systems = modellib.XObjHrefModel('systems/')
        self.log = modellib.XObjHrefModel('log/')
        self.systemStates = modellib.XObjHrefModel('systemStates/')

class Systems(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems',
                elements=['system', 'eventTypes'])
    list_fields = ['system']
    system = []
    
    def __init__(self):
        self.eventTypes = modellib.XObjHrefModel('eventTypes/')
        
    def save(self):
        return [s.save() for s in self.system]
    
class SystemStates(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systemStates',
                elements=['systemState'])
    list_fields = ['systemState']
    systemState = []

    def save(self):
        return [s.save() for s in self.systemState]
    
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
    
class Zones(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='zones',
                elements=['zone'])
    list_fields = ['zone']
    
class Zone(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_zone'
    _xobj = xobj.XObjMetadata(
                tag = 'zone',
                attributes = {'id':str})
    # We really don't need to display all systems associated with a zone at
    # this level. We may want to do it in another view.
    _xobj_hidden_accessors = set(['systems', ])

    zone_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092, unique=True)
    description = models.CharField(max_length=8092, null=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)

class SystemState(modellib.XObjIdModel):
    serialize_accessors = False
    class Meta:
        db_table = 'inventory_system_state'
        
    _xobj = xobj.XObjMetadata(
                tag = 'currentState',
                attributes = {'id':str})

    UNMANAGED = "unmanaged"
    UNMANAGED_DESC = "Unmanaged"
    
    REGISTERED = "registered"
    REGISTERED_DESC = "Polling"
    
    RESPONSIVE = "responsive"
    RESPONSIVE_DESC = "Online"
    
    NONRESPONSIVE = "non-responsive-unknown"
    NONRESPONSIVE_DESC = "Not responding: unknown"
    
    NONRESPONSIVE_NET = "non-responsive-net"
    NONRESPONSIVE_NET_DESC = "Not responding: network unreachable"
    
    NONRESPONSIVE_HOST = "non-responsive-host"
    NONRESPONSIVE_HOST_DESC = "Not responding: host unreachable"
    
    NONRESPONSIVE_SHUTDOWN = "non-responsive-shutdown"
    NONRESPONSIVE_SHUTDOWN_DESC = "Not responding: shutdown"
    
    NONRESPONSIVE_SUSPENDED = "non-responsive-suspended"
    NONRESPONSIVE_SUSPENDED_DESC = "Not responding: suspended"
    
    DEAD = "dead"
    DEAD_DESC = "Stale"
    
    MOTHBALLED = "mothballed"
    MOTHBALLED_DESC = "Retired"

    STATE_CHOICES = (
        (UNMANAGED, UNMANAGED_DESC),
        (REGISTERED, REGISTERED_DESC),
        (RESPONSIVE, RESPONSIVE_DESC),
        (NONRESPONSIVE, NONRESPONSIVE_DESC),
        (NONRESPONSIVE_NET, NONRESPONSIVE_NET_DESC),
        (NONRESPONSIVE_HOST, NONRESPONSIVE_HOST_DESC),
        (NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SHUTDOWN_DESC),
        (NONRESPONSIVE_SUSPENDED, NONRESPONSIVE_SUSPENDED_DESC),
        (DEAD, DEAD_DESC),
        (MOTHBALLED, MOTHBALLED_DESC),
    )

    system_state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092, unique=True,
        choices=STATE_CHOICES)
    description = models.CharField(max_length=8092)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)

    load_fields = [ name ]

class System(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system'
    # XXX this is hopefully a temporary solution to not serialize the FK
    # part of a many-to-many relationship
    _xobj_hidden_accessors = set(['systemjob_set', 'target_credentials', ])
    _xobj_hidden_m2m = set(['system_jobs'])
    _xobj = xobj.XObjMetadata(
                tag = 'system',
                attributes = {'id':str},
                elements = ['networks', ])
    
    # need our own object manager for dup detection
    objects = modellib.SystemManager()
    system_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092)
    description = models.CharField(max_length=8092, null=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    hostname = models.CharField(max_length=8092, null=True)
    # Launch date is nullable, we may get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = modellib.DateTimeUtcField(null=True)
    target = models.ForeignKey(rbuildermodels.Targets, null=True)
    target_system_id = modellib.APIReadOnlyCharField(max_length=255, null=True)
    target_system_name = modellib.APIReadOnlyCharField(max_length=255, null=True)
    target_system_description = modellib.APIReadOnlyCharField(max_length=1024, null=True)
    target_system_state = modellib.APIReadOnlyCharField(max_length=64, null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)
    registration_date = modellib.DateTimeUtcField(null=True)
    generated_uuid = models.CharField(max_length=64, unique=True, null=True)
    local_uuid = models.CharField(max_length=64, null=True)
    ssl_client_certificate = modellib.APIReadOnlyCharField(max_length=8092, null=True)
    ssl_client_key = modellib.XObjHiddenCharField(max_length=8092, null=True)
    ssl_server_certificate = models.CharField(max_length=8092, null=True)
    scheduled_event_start_date = modellib.DateTimeUtcField(null=True)
    launching_user = models.ForeignKey(rbuildermodels.Users, null=True)
    current_state = modellib.SerializedForeignKey(SystemState, null=True, related_name='systems')
    installed_software = models.ManyToManyField('Trove', null=True)
    management_node = models.NullBooleanField()
    #TO-DO should this ever be nullable?
    managing_zone = models.ForeignKey('Zone', null=True, related_name='systems')
    system_jobs = models.ManyToManyField("Job", through="SystemJob")
    event_uuid = modellib.SyntheticField()

    load_fields = [local_uuid]

    new_versions = []
    lastJob = None
    oldModel = None

    def save(self, *args, **kw):
        if self.current_state_id is None:
            self.current_state = SystemState.objects.get(
                name = SystemState.UNMANAGED)
        if not self.name:
            self.name = self.hostname and self.hostname or ''
        modellib.XObjIdModel.save(self, *args, **kw)
        self.createLog()

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

    def createLog(self):
        system_log, created = SystemLog.objects.get_or_create(system=self)
        if created:
            system_log.save()
        return system_log

    @property
    def isRegistered(self):
        """
        Return True is the system is registered
        """
        return (self.local_uuid is not None and self.generated_uuid is not None)

    @property
    def isNewRegistration(self):
        """
        Return True if this object is a new registration.
        Relies on the presence of oldModel, which is set when we de-serialize
        the XML from clients.
        """
        if not self.isRegistered:
            return False
        om = self.oldModel
        if om is None:
            return True
        # This should also cover the empty string case
        if not om.local_uuid or not om.generated_uuid:
            return True
        return False

class ManagementNode(System):
    class Meta:
        db_table = 'inventory_zone_management_node'
    _xobj = xobj.XObjMetadata(
                tag = 'managementNode',
                attributes = {'id':str})
    local = models.NullBooleanField()
    zone = models.ForeignKey(Zone, related_name='managementNodes')
    node_jid = models.CharField(max_length=64, null=True)
    
    # ignore auto generated ptr from inheritance
    load_ignore_fields = ["system_ptr"]
    
    # need our own object manager for dup detection
    objects = modellib.ManagementNodeManager()
    
    def save(self, *args, **kw):
        self.management_node = True
        System.save(self, *args, **kw)

class SystemTargetCredentials(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_target_credentials'
        unique_together = [ ('system', 'credentials') ]

    system = models.ForeignKey(System, null=False,
        related_name = 'target_credentials')
    credentials = models.ForeignKey(rbuildermodels.TargetCredentials,
        null=False, related_name = 'systems')

class InstalledSoftware(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='installedSoftware',
                elements=['trove'])
    list_fields = ['trove']

class EventType(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_event_type'
    _xobj = xobj.XObjMetadata(tag='event_type')

    # on-demand events need to be > 100 to be dispatched immediately
    # DO NOT CHANGE POLL PRIORITIES HERE WITHOUT CHANGING IN schema.py also
    ON_DEMAND_BASE = 100
    
    SYSTEM_POLL = "system poll"
    SYSTEM_POLL_PRIORITY = 50
    SYSTEM_POLL_DESC = "standard system polling event"
    
    SYSTEM_POLL_IMMEDIATE = "immediate system poll"
    SYSTEM_POLL_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_POLL_IMMEDIATE_DESC = "on-demand system polling event"
    
    SYSTEM_REGISTRATION = "system registration"
    SYSTEM_REGISTRATION_PRIORITY = ON_DEMAND_BASE + 10
    SYSTEM_REGISTRATION_DESC = "on-demand system registration event"

    SYSTEM_APPLY_UPDATE = 'system apply update'
    SYSTEM_APPLY_UPDATE_PRIORITY = 50
    SYSTEM_APPLY_UPDATE_DESCRIPTION = 'apply an update to a system'
        
    SYSTEM_APPLY_UPDATE_IMMEDIATE = 'immediate system apply update'
    SYSTEM_APPLY_UPDATE_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_APPLY_UPDATE_IMMEDIATE_DESCRIPTION = \
        'on-demand apply an update to a system'

    SYSTEM_SHUTDOWN = 'system shutdown'
    SYSTEM_SHUTDOWN_PRIORITY = 50
    SYSTEM_SHUTDOWN_DESCRIPTION = 'shutdown a system'

    SYSTEM_SHUTDOWN_IMMEDIATE = 'immediate system shutdown'
    SYSTEM_SHUTDOWN_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_SHUTDOWN_IMMEDIATE_DESCRIPTION = \
        'on-demand shutdown a system'
        
    event_type_id = models.AutoField(primary_key=True)
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
    )
    name = models.CharField(max_length=8092, unique=True, choices=EVENT_TYPES)
    description = models.CharField(max_length=8092)
    priority = models.SmallIntegerField(db_index=True)

class JobState(modellib.XObjModel):
    class Meta:
        db_table = "inventory_job_state"
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
    _xobj = xobj.XObjMetadata(tag='job_state')

    job_state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True, choices=choices)

    load_fields = [ name ]

class Job(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_job'
    _xobj = xobj.XObjMetadata(tag='job')
    objects = modellib.JobManager()

    job_id = models.AutoField(primary_key=True)
    job_uuid = models.CharField(max_length=64, unique=True)
    job_state = modellib.InlinedForeignKey(JobState, visible='name')
    event_type = modellib.APIReadOnlyInlinedForeignKey(EventType, visible='name')
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_updated =  modellib.DateTimeUtcField(auto_now_add=True)

    load_fields = [ job_uuid ]

class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    _xobj = xobj.XObjMetadata(
                tag = 'systemEvent',
                attributes = {'id':str})
    
    system_event_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, db_index=True,
        related_name='system_events')
    event_type = modellib.DeferredForeignKey(EventType,
        related_name='system_events')
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_enabled = modellib.DateTimeUtcField(
        default=datetime.datetime.now(tz.tzutc()), db_index=True)
    priority = models.SmallIntegerField(db_index=True)
    event_data = models.TextField(null=True)

    def dispatchImmediately(self):
        return self.event_type.priority >= EventType.ON_DEMAND_BASE

    def get_absolute_url(self, request, parent=None): 
        if isinstance(parent, EventType):
            self.view_name = 'SystemEventsByType'
        elif isinstance(parent, System):
            self.view_name = 'SystemsSystemEvent'
        return modellib.XObjIdModel.get_absolute_url(self, request, parent)

    def save(self, *args, **kw):
        if not self.priority:
            self.priority = self.event_type.priority
        modellib.XObjIdModel.save(self, *args, **kw)

class Network(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_network'
        unique_together = (('system', 'dns_name', 'ip_address', 'ipv6_address'),)
        
    _xobj = xobj.XObjMetadata(
                tag='network')
    network_id = models.AutoField(primary_key=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    system = models.ForeignKey(System, related_name='networks')
    ip_address = models.CharField(max_length=15, null=True)
    # TODO: how long should this be?
    ipv6_address = models.CharField(max_length=32, null=True)
    device_name = models.CharField(max_length=255) 
    dns_name = models.CharField(max_length=255, db_index=True)
    netmask = models.CharField(max_length=20, null=True)
    port_type = models.CharField(max_length=32, null=True)
    active = models.NullBooleanField()
    required = models.NullBooleanField()

    load_fields = [ip_address, dns_name]

    def natural_key(self):
        return self.ip_address, self.dns_name

class SystemLog(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_log'
    system_log_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, related_name='system_log')

    def get_absolute_url(self, request, parent=None):
        if not parent:
            parent = self.system
        if isinstance(parent, System):
            view_name = 'SystemLog'
        return modellib.XObjIdModel.get_absolute_url(self, request, parent)

class SystemLogEntry(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='systemLogEntry')
    class Meta:
        db_table = 'inventory_system_log_entry'
        ordering = ['entry_date']
        
    ADDED = "System added to inventory"
    REGISTERED = "System registered via rpath-tools"
    MANUALLY_REGISTERED = "System manually registered via rBuilder"
    POLLED = "System polled."
    FETCHED = "System data fetched."
    choices = (
        (ADDED, ADDED),
        (REGISTERED, REGISTERED),
        (MANUALLY_REGISTERED, MANUALLY_REGISTERED),
        (POLLED, POLLED),
        (FETCHED, FETCHED),
    )

    system_log_entry_id = models.AutoField(primary_key=True)
    system_log = models.ForeignKey(SystemLog,
        related_name='system_log_entries')
    entry = models.CharField(max_length=8092, choices=choices)
    entry_date = modellib.DateTimeUtcField(auto_now_add=True)

class Trove(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_trove'
        unique_together = (('name', 'version', 'flavor'),)

    objects = modellib.TroveManager()

    _xobj = xobj.XObjMetadata(tag='trove')
    trove_id = models.AutoField(primary_key=True)
    name = models.TextField()
    version = modellib.SerializedForeignKey('Version')
    flavor = models.TextField()
    is_top_level = models.BooleanField()
    last_available_update_refresh = modellib.DateTimeUtcField(
        null=True)
    available_updates = models.ManyToManyField('Version',
        related_name='available_updates')

    load_fields = [ name, version, flavor ]

    def get_absolute_url(self, request):
        # Build an id to crest
        conary_version = self.version.conaryVersion
        label = conary_version.trailingLabel()
        revision = conary_version.trailingRevision()
        shortname = label.getHost().split('.')[0]
        path = "repos/%s/api/trove/%s=/%s/%s[%s]" % \
            (shortname, self.name, label.asString(),
             revision.asString(), self.flavor)
        path = urllib.quote(path)

        if request:
            scheme, netloc = urlparse.urlparse(
                request.build_absolute_uri())[0:2]
            url = urlparse.urlunparse((scheme, netloc, path, '', '', ''))
            return url
        else:
            return path

    def _is_top_level_group(self):
        return self.name.startswith('group-') and \
            self.name.endswith('-appliance')

    def save(self, *args, **kw):
        self.is_top_level = self._is_top_level_group()
        if self.flavor is None:
            self.flavor = ''
        modellib.XObjModel.save(self, *args, **kw)

    def getFlavor(self):
        if not self.flavor:
            return None
        return deps.parseFlavor(self.flavor)

    def getLabel(self):
        if not self.version.label:
            return None
        return versions.Label(self.version.label)

    def getVersion(self):
        return self.version.conaryVersion

    def getNVF(self):
        return self.name, self.version.conaryVersion, self.getFlavor()

class Version(modellib.XObjModel):
    serialize_accessors = False
    class Meta:
        db_table = 'inventory_version'
        unique_together = [ ('full', 'ordering', 'flavor'), ]

    objects = modellib.VersionManager()

    _xobj = xobj.XObjMetadata(tag='version')

    version_id = models.AutoField(primary_key=True)
    full = models.TextField()
    label = models.TextField()
    revision = models.TextField()
    ordering = models.TextField()
    flavor = models.TextField()

    load_fields = [ full, ordering, flavor ]

    @property
    def conaryVersion(self):
        v = versions.VersionFromString(self.full,
            timeStamps = [ float(self.ordering) ] )
        return v

    def fromConaryVersion(self, version):
        self.full = str(version)
        self.label = str(version.trailingLabel())
        self.revision = str(version.trailingRevision())
        self.ordering = str(version.timeStamps()[0])

    def save(self, *args, **kwargs):
        # If the object is incomplete, fill in the missing information
        if not self.label or not self.revision:
            v = self.conaryVersion
            self.fromConaryVersion(v)
        if self.flavor is None:
            self.flavor = ''
        return super(Version, self).save(*args, **kwargs)

class SystemJobs(modellib.XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = 'system_jobs')
    list_fields = ['job']
    job = []

class SystemJob(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_job'
    # XXX This class should never be serialized directly, but unless an _xobj
    # field is added, we have no access to it from modellib
    _xobj = xobj.XObjMetadata(tag='__systemJob')
    system_job_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System)
    job = modellib.DeferredForeignKey(Job, unique=True, related_name='systems')
    event_uuid = modellib.XObjHiddenCharField(max_length=64, unique=True)

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
