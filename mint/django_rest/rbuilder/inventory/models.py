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

from django.conf import settings
from django.db import connection, models
from django.db.backends import signals

from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

Cache = modellib.Cache
XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly

def hasTemporaryTables():
    drvname = connection.client.executable_name
    if drvname == 'sqlite3':
        # Bummer. sqlite3 won't report temp tables in sqlite_master, so django
        # won't report them in introspection.table_names
        cu = connection.cursor()
        ret = list(cu.execute("SELECT 1 FROM sqlite_temp_master WHERE type='table'"))
        return bool(ret)
    elif drvname == 'psql':
        return 'inventory_tmp' in connection.introspection.table_names()
    else:
        raise Exception("Unsupported driver")

def createTemporaryTables(**kwargs):
    if not hasTemporaryTables():
        cu = connection.cursor()
        cu.execute("""
            CREATE TEMPORARY TABLE inventory_tmp (
                res_id INTEGER NOT NULL,
                depth INTEGER NOT NULL
        )""")
# This registers the function to be executed when the connection is created
signals.connection_created.connect(createTemporaryTables)

class Pk(object):
    def __init__(self, pk):
        self.pk = pk


class Fault(modellib.XObjModel):
    class Meta:
        abstract = True
    code = models.IntegerField(null=True)
    message = models.CharField(max_length=8092, null=True)
    traceback = models.TextField(null=True)

class Inventory(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory')

    def __init__(self):
        self.zones = modellib.XObjHrefModel('zones')
        self.management_nodes = modellib.XObjHrefModel('management_nodes')
        self.management_interfaces = modellib.XObjHrefModel('management_interfaces')
        self.system_types = modellib.XObjHrefModel('system_types')
        self.networks = modellib.XObjHrefModel('networks')
        self.systems = modellib.XObjHrefModel('systems')
        self.log = modellib.XObjHrefModel('log')
        self.event_types = modellib.XObjHrefModel('event_types')
        self.system_states = modellib.XObjHrefModel('system_states')
        self.job_states = modellib.XObjHrefModel('job_states')
        self.inventory_systems = modellib.XObjHrefModel('inventory_systems')
        self.infrastructure_systems = modellib.XObjHrefModel('infrastructure_systems')
        self.image_import_metadata_descriptor = modellib.XObjHrefModel('image_import_metadata_descriptor')

class Systems(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems')
    list_fields = ['system']
    system = []
    objects = modellib.SystemsManager()

    def __init__(self):
        self.event_types = modellib.XObjHrefModel('../event_types')

    def save(self):
        return [s.save() for s in self.system]
    
class SystemStates(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'system_states')
    list_fields = ['system_state']
    system_state = []

    def save(self):
        return [s.save() for s in self.system_state]
    
class ManagementNodes(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'management_nodes')
    list_fields = ['management_node']
    management_node = []

    objects = modellib.ManagementNodesManager()

    def save(self):
        return [s.save() for s in self.management_node]
    
class EventTypes(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'event_types')
    list_fields = ['event_type']
    event_type = []

    def save(self):
        return [s.save() for s in self.event_type]
    
class SystemsLog(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='systemsLog')
    list_fields = ['system_log_entry']
    system_log_entry = []

class SystemEvents(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'system_events')
    list_fields = ['system_event']
    system_event = []

    def save(self):
        return [s.save() for s in self.system_event]

class Networks(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='networks',
                elements=['network', 'systems'])
    list_fields = ['network']
    
    def __init__(self):
        self.systems = modellib.XObjHrefModel('../systems')
    
class Zones(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='zones',
                elements=['zone'])
    list_fields = ['zone']
    
class Credentials(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'credentials',
                attributes = {'id':str})
    objects = modellib.CredentialsManager()
    view_name = 'SystemCredentials'

    def __init__(self, system, *args, **kwargs):
        self._system = system
        modellib.XObjIdModel.__init__(self, *args, **kwargs)

    def to_xml(self, request=None):
        self.id = self.get_absolute_url(request, model=self,
            parents=[self._system])
        return xobj.toxml(self)
    
class Configuration(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'configuration',
                attributes = {'id':str})
    objects = modellib.ConfigurationManager()
    view_name = 'SystemConfiguration'

    def __init__(self, system, *args, **kwargs):
        self._system = system
        modellib.XObjIdModel.__init__(self, *args, **kwargs)

    def to_xml(self, request=None):
        self.id = self.get_absolute_url(request, model=self,
            parents=[self._system])
        return xobj.toxml(self)
    
class ConfigurationDescriptor(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'configuration_descriptor',
                attributes = {'id':str})
    objects = modellib.ConfigurationDescriptorManager()
    view_name = 'SystemConfigurationDescriptor'

    def __init__(self, system, *args, **kwargs):
        self._system = system
        modellib.XObjIdModel.__init__(self, *args, **kwargs)

    def to_xml(self, request=None):
        self.id = self.get_absolute_url(request, model=self,
            parents=[self._system])
        return xobj.toxml(self)

class Zone(modellib.XObjIdModel):
    LOCAL_ZONE = "Local rBuilder"
    class Meta:
        db_table = 'inventory_zone'
    _xobj = xobj.XObjMetadata(
                tag = 'zone',
                attributes = {'id':str})
    
    # Don't inline all the systems now.  Do not remove this code!
    # See https://issues.rpath.com/browse/RBL-7236 and 
    # https://issues.rpath.com/browse/RBL-7237 for more info
    _xobj_hidden_accessors = set(['systems',])

    zone_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092, unique=True)
    description = models.CharField(max_length=8092, null=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    
    load_fields = [ name ]

class SystemState(modellib.XObjIdModel):
    serialize_accessors = False
    class Meta:
        db_table = 'inventory_system_state'
        
    _xobj = xobj.XObjMetadata(
                tag = 'currentState',
                attributes = {'id':str})

    UNMANAGED = "unmanaged"
    UNMANAGED_DESC = "Unmanaged"
    
    UNMANAGED_CREDENTIALS_REQUIRED = "unmanaged-credentials"
    UNMANAGED_CREDENTIALS_REQUIRED_DESC = "Unmanaged: Invalid credentials"
    
    REGISTERED = "registered"
    REGISTERED_DESC = "Initial synchronization pending"
    
    RESPONSIVE = "responsive"
    RESPONSIVE_DESC = "Online"
    
    NONRESPONSIVE = "non-responsive-unknown"
    NONRESPONSIVE_DESC = "Not responding: Unknown"
    
    NONRESPONSIVE_NET = "non-responsive-net"
    NONRESPONSIVE_NET_DESC = "Not responding: Network unreachable"
    
    NONRESPONSIVE_HOST = "non-responsive-host"
    NONRESPONSIVE_HOST_DESC = "Not responding: Host unreachable"
    
    NONRESPONSIVE_SHUTDOWN = "non-responsive-shutdown"
    NONRESPONSIVE_SHUTDOWN_DESC = "Not responding: Hhutdown"
    
    NONRESPONSIVE_SUSPENDED = "non-responsive-suspended"
    NONRESPONSIVE_SUSPENDED_DESC = "Not responding: Suspended"
    
    NONRESPONSIVE_CREDENTIALS = "non-responsive-credentials"
    NONRESPONSIVE_CREDENTIALS_DESC = "Not responding: Invalid credentials"
    
    DEAD = "dead"
    DEAD_DESC = "Stale"
    
    MOTHBALLED = "mothballed"
    MOTHBALLED_DESC = "Retired"

    STATE_CHOICES = (
        (UNMANAGED, UNMANAGED_DESC),
        (UNMANAGED_CREDENTIALS_REQUIRED, UNMANAGED_CREDENTIALS_REQUIRED_DESC),
        (REGISTERED, REGISTERED_DESC),
        (RESPONSIVE, RESPONSIVE_DESC),
        (NONRESPONSIVE, NONRESPONSIVE_DESC),
        (NONRESPONSIVE_NET, NONRESPONSIVE_NET_DESC),
        (NONRESPONSIVE_HOST, NONRESPONSIVE_HOST_DESC),
        (NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SHUTDOWN_DESC),
        (NONRESPONSIVE_SUSPENDED, NONRESPONSIVE_SUSPENDED_DESC),
        (NONRESPONSIVE_CREDENTIALS, NONRESPONSIVE_CREDENTIALS_DESC),
        (DEAD, DEAD_DESC),
        (MOTHBALLED, MOTHBALLED_DESC),
    )

    system_state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092, unique=True,
        choices=STATE_CHOICES)
    description = models.CharField(max_length=8092)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)

    load_fields = [ name ]

class ManagementInterfaces(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='management_interfaces',
                elements=['management_interface'])
    list_fields = ['management_interface']
    
class ManagementInterface(modellib.XObjIdModel):
    XSL = "managementInterface.xsl"
    class Meta:
        db_table = 'inventory_management_interface'
        
    # Don't inline all the systems now.  Do not remove this code!
    # See https://issues.rpath.com/browse/RBL-7883 for more info
    _xobj_hidden_accessors = set(['systems',])
        
    _xobj = xobj.XObjMetadata(
                tag = 'management_interface',
                attributes = {'id':str})

    CIM = "cim"
    CIM_DESC = "Common Information Model (CIM)"
    CIM_PORT = 8443
    WMI = "wmi"
    WMI_PORT = 135
    WMI_DESC = "Windows Management Instrumentation (WMI)"

    CHOICES = (
        (CIM, CIM_DESC),
        (WMI, WMI_DESC),
    )
        
    management_interface_id = D(models.AutoField(primary_key=True), "the database ID for the management interface")
    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True, choices=CHOICES)), "the name of the management interface")
    description = D(models.CharField(max_length=8092), "the description of the management interface")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the management interface was added to inventory (UTC)")
    port = D(models.IntegerField(null=False), "the port used by the management interface")
    credentials_descriptor = D(models.XMLField(), "the descriptor of available fields to set credentials for the management interface")
    credentials_readonly = D(models.NullBooleanField(), "whether or not the management interface has readonly credentials")
    
    load_fields = [name]

class SystemTypes(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='system_types',
                elements=['system_type'])
    list_fields = ['system_type']
    
class SystemType(modellib.XObjIdModel):
    XSL = "systemType.xsl"
    class Meta:
        db_table = 'inventory_system_type'
    _xobj = xobj.XObjMetadata(
                tag = 'system_type',
                attributes = {'id':str})
    
    # Don't inline all the systems now.  Do not remove this code!
    # See https://issues.rpath.com/browse/RBL-7372 for more info
    _xobj_hidden_accessors = set(['systems',])
        
    INVENTORY = "inventory"
    INVENTORY_DESC = "Inventory"
    INFRASTRUCTURE_MANAGEMENT_NODE = "infrastructure-management-node"
    INFRASTRUCTURE_MANAGEMENT_NODE_DESC = "rPath Update Service (Infrastructure)"
    INFRASTRUCTURE_WINDOWS_BUILD_NODE = "infrastructure-windows-build-node"
    INFRASTRUCTURE_WINDOWS_BUILD_NODE_DESC = "rPath Windows Build Service (Infrastructure)"

    CHOICES = (
        (INVENTORY, INVENTORY_DESC),
        (INFRASTRUCTURE_MANAGEMENT_NODE, INFRASTRUCTURE_MANAGEMENT_NODE_DESC),
        (INFRASTRUCTURE_WINDOWS_BUILD_NODE, INFRASTRUCTURE_WINDOWS_BUILD_NODE_DESC),
    )
        
    system_type_id = D(models.AutoField(primary_key=True), "the database ID for the system type")
    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True, choices=CHOICES)), "the name of the system type")
    description = D(models.CharField(max_length=8092), "the description of the system type")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the system type was added to inventory (UTC)")
    infrastructure = D(models.BooleanField(), "whether or not the system type is infrastructure")
    creation_descriptor = D(models.XMLField(), "the descriptor of available fields to create systems of this type")

    load_fields = [ name ]

class System(modellib.XObjIdModel):
    XSL = "system.xsl"
    class Meta:
        db_table = 'inventory_system'
    # XXX this is hopefully a temporary solution to not serialize the FK
    # part of a many-to-many relationship
    _xobj_hidden_accessors = set(['systemjob_set', 'target_credentials',
        'managementnode', 'jobsystem_set', ])
    _xobj_hidden_m2m = set()
    _xobj = xobj.XObjMetadata(
                tag = 'system',
                attributes = {'id':str},
                elements = ['networks', ])
    """
      networks - a collection of network resources exposed by the system
      system_events - a link to the collection of system events currently active on this sytem
    """
    # need our own object manager for dup detection
    objects = modellib.SystemManager()
    system_id = D(models.AutoField(primary_key=True),
        "the database ID for the system")
    name = D(models.CharField(max_length=8092),
        "the system name")
    description = D(models.CharField(max_length=8092, null=True),
        "the system description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the system was added to inventory (UTC)")
    hostname = D(models.CharField(max_length=8092, null=True),
        "the system hostname")
    # Launch date is nullable, we may get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was deployed (only applies if system is on a virtual target)")
    target = D(modellib.ForeignKey(rbuildermodels.Targets, null=True, text_field="targetname"),
        "the virtual target the system was deployed to (only applies if system is on a virtual target)")
    target_system_id = D(models.CharField(max_length=255,
            null=True),
        "the system ID as reported by its target (only applies if system is on a virtual target)")
    target_system_name = D(APIReadOnly(models.CharField(max_length=255,
            null=True)),
        "the system name as reported by its target (only applies if system is on a virtual target)")
    target_system_description = D(APIReadOnly(models.CharField(max_length=1024,
            null=True)),
        "the system description as reported by its target (only applies if system is on a virtual target)")
    target_system_state = D(APIReadOnly(models.CharField(max_length=64,
            null=True)),
        "the system state as reported by its target (only applies if system is on a virtual target)")
    registration_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was registered in inventory (UTC)")
    generated_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID that is randomly generated")
    local_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID created from the system hardware profile")
    ssl_client_certificate = D(APIReadOnly(models.CharField(
            max_length=8092, null=True)),
        "an x509 certificate of an authorized client that can use the system's CIM broker")
    ssl_client_key = D(XObjHidden(APIReadOnly(models.CharField(
        max_length=8092, null=True))),
        "an x509 private key of an authorized client that can use the system's CIM broker")
    ssl_server_certificate = D(models.CharField(max_length=8092, null=True),
        "an x509 public certificate of the system's CIM broker")
    launching_user = D(modellib.ForeignKey(rbuildermodels.Users, null=True, text_field="username"),
        "the user that deployed the system (only applies if system is on a virtual target)")
    current_state = D(modellib.SerializedForeignKey(
            SystemState, null=True, related_name='systems'),
        "the current state of the system")
    installed_software = D(models.ManyToManyField('Trove', null=True),
        "a collection of top-level items installed on the system")
    managing_zone = D(modellib.ForeignKey(Zone, null=False,
            related_name='systems', text_field="name"),
        "a link to the management zone in which this system resides")
    jobs = models.ManyToManyField("Job", through="SystemJob")
    agent_port = D(models.IntegerField(null=True),
          "the port used by the system's CIM broker")
    state_change_date = XObjHidden(APIReadOnly(modellib.DateTimeUtcField(
        auto_now_add=True, default=datetime.datetime.now(tz.tzutc()))))
    event_uuid = D(modellib.SyntheticField(),
        "a UUID used to link system events with their returned responses")
    boot_uuid = D(modellib.SyntheticField(),
        "a UUID used for tracking systems registering at startup time")
    management_interface = D(modellib.ForeignKey(ManagementInterface, null=True, related_name='systems', text_field="description"),
        "the management interface used to communicate with the system")
    credentials = APIReadOnly(XObjHidden(models.TextField(null=True)))
    system_type = D(modellib.ForeignKey(SystemType, null=False,
        related_name='systems', text_field='description'),
        "the type of the system")
    stage = D(APIReadOnly(modellib.ForeignKey("Stage", null=True, text_field='name')),
        "the appliance stage of the system")
    major_version = D(APIReadOnly(modellib.ForeignKey(rbuildermodels.Versions, null=True,
        text_field='name')),
        "the appliance major version of the system")
    appliance = D(APIReadOnly(modellib.ForeignKey(rbuildermodels.Products, null=True,
        text_field='shortname')),
        "the appliance of the system")
    configuration = APIReadOnly(XObjHidden(models.TextField(null=True)))
    configuration_descriptor = D(APIReadOnly(modellib.SyntheticField()), 
        "the descriptor of available fields to set system configuration parameters")

    load_fields = [local_uuid]

    # We need to distinguish between an <installed_software> node not being
    # present at all, and being present and empty
    new_versions = None
    lastJob = None
    oldModel = None

    def save(self, *args, **kw):
        if self.current_state_id is None:
            self.current_state = SystemState.objects.get(
                name = SystemState.UNMANAGED)
        if not self.name:
            self.name = self.hostname and self.hostname or ''
        if not self.agent_port and self.management_interface:
            self.agent_port = self.management_interface.port
        if self.system_type_id is None:
            self.system_type = SystemType.objects.get(
                name = SystemType.INVENTORY)
        modellib.XObjIdModel.save(self, *args, **kw)
        self.createLog()

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

    _RunningJobStateIds = None
    @property
    def runningJobStateIds(self):
        if self._RunningJobStateIds is None:
            self.__class__._RunningJobStateIds = set(
                Cache.get(JobState, name=x).job_state_id
                    for x in [ JobState.RUNNING, JobState.QUEUED ])
        return self.__class__._RunningJobStateIds

    def areJobsActive(self, iterable):
        for job in iterable:
            if job.job_state_id in self.runningJobStateIds:
                return True
        return False

    def hasRunningJobs(self):
        return bool(self.jobs.filter(job_state__name=JobState.RUNNING))

    _runningJobState = None
    @property
    def runningJobState(self):
        if self._runningJobState is None:
            self.__class__._runningJobState = \
                Cache.get(JobState, name=JobState.RUNNING)
        return self.__class__._runningJobState

    def areJobsRunning(self, jobs):
        return bool([j for j in jobs \
            if j.job_state_id == self.runningJobState.job_state_id])

    def serialize(self, request=None, values=None):
        # We are going to replace the jobs node with hrefs. But DO NOT mark
        # the jobs m2m relationship as hidden, or else the bulk load fails
        if values is None:
            jobs = self.jobs.all()
        else:
            # We're popping the jobs data structure from values because its
            # only purpose is to prevent repeated database hits when we bulk
            # load
            jobs = [ x[0] for x in values.pop('jobs', []) ]
        xobj_model = modellib.XObjIdModel.serialize(self, request,
            values=values)
        xobj_model.has_active_jobs = self.areJobsActive(jobs)
        xobj_model.has_running_jobs = self.areJobsRunning(jobs)

        if request:
            class CredentialsHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='credentials',
                            attributes={'href':str})

                def __init__(self, href):
                    self.href = href
                    
            class ConfigurationHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='configuration',
                            attributes={'href':str})

                def __init__(self, href):
                    self.href = href
                    
            class ConfigurationDescriptorHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='configuration_descriptor',
                            attributes={'href':str})

                def __init__(self, href):
                    self.href = href

            xobj_model.credentials = CredentialsHref(request.build_absolute_uri(
                '%s/credentials' % self.get_absolute_url(request)))
            
            xobj_model.configuration = ConfigurationHref(request.build_absolute_uri(
                '%s/configuration' % self.get_absolute_url(request)))
            
            xobj_model.configuration_descriptor = ConfigurationDescriptorHref(request.build_absolute_uri(
                '%s/configuration_descriptor' % self.get_absolute_url(request)))

        class JobsHref(modellib.XObjIdModel):
            _xobj = xobj.XObjMetadata(tag='jobs',
                elements = ['queued_jobs', 'completed_jobs',
                    'running_jobs', 'failed_jobs'],
                attributes = {'id':str})

            def __init__(self, request, system):
                self.view_name = 'SystemJobs'
                self.id = self.get_absolute_url(request, parents=[system],
                    model=xobj_model)
                self.view_name = 'SystemJobStateJobs'
                parents = [system, Cache.get(JobState, name=JobState.QUEUED)]
                self.queued_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(JobState, name=JobState.COMPLETED)]
                self.completed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(JobState, name=JobState.RUNNING)]
                self.running_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(JobState, name=JobState.FAILED)]
                self.failed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))
                self.view_name = None

        xobj_model.jobs = JobsHref(request, self)

        # Set out of date flag on xobj_model
        out_of_date = False
        for trove in self.installed_software.all():
            if trove.out_of_date:
                out_of_date = True
                break
        xobj_model.out_of_date = out_of_date

        return xobj_model

class ManagementNode(System):
    class Meta:
        db_table = 'inventory_zone_management_node'
    _xobj = xobj.XObjMetadata(
                tag = 'management_node',
                attributes = {'id':str})
    local = models.NullBooleanField()
    zone = modellib.ForeignKey(Zone, related_name='management_nodes')
    node_jid = models.CharField(max_length=64, null=True)
    load_fields = [ node_jid ]

    # ignore auto generated ptr from inheritance
    load_ignore_fields = ["system_ptr"]
    
    # need our own object manager for dup detection
    objects = modellib.ManagementNodeManager()
    
    def save(self, *args, **kw):
        self.system_type = SystemType.objects.get(
            name = SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        System.save(self, *args, **kw)

class SystemTargetCredentials(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_target_credentials'
        unique_together = [ ('system', 'credentials') ]

    system = modellib.ForeignKey(System, null=False,
        related_name = 'target_credentials')
    credentials = modellib.ForeignKey(rbuildermodels.TargetCredentials,
        null=False, related_name = 'systems')

class InstalledSoftware(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='installed_software',
                attributes=dict(id = str))
    list_fields = ['trove']
    objects = modellib.InstalledSoftwareManager()

    def get_absolute_url(self, request, parents=None, model=None):
        if parents:
            return modellib.XObjIdModel.get_absolute_url(self, request,
                parents=parents, model=model)
        return request.build_absolute_uri(request.get_full_path())

class EventType(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_event_type'
    _xobj = xobj.XObjMetadata(tag='event_type')
    
     # hide jobs, see https://issues.rpath.com/browse/RBL-7151
    _xobj_hidden_accessors = set(['jobs'])

    # on-demand events need to be > 100 to be dispatched immediately
    # DO NOT CHANGE POLL PRIORITIES HERE WITHOUT CHANGING IN schema.py also
    ON_DEMAND_BASE = 100
    
    SYSTEM_POLL = "system poll"
    SYSTEM_POLL_PRIORITY = 50
    SYSTEM_POLL_DESC = "System synchronization"
    
    SYSTEM_POLL_IMMEDIATE = "immediate system poll"
    SYSTEM_POLL_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_POLL_IMMEDIATE_DESC = "On-demand system synchronization"
    
    SYSTEM_REGISTRATION = "system registration"
    SYSTEM_REGISTRATION_PRIORITY = ON_DEMAND_BASE + 10
    SYSTEM_REGISTRATION_DESC = "System registration"

    SYSTEM_APPLY_UPDATE = 'system apply update'
    SYSTEM_APPLY_UPDATE_PRIORITY = 50
    SYSTEM_APPLY_UPDATE_DESCRIPTION = 'Scheduled system update'
        
    SYSTEM_APPLY_UPDATE_IMMEDIATE = 'immediate system apply update'
    SYSTEM_APPLY_UPDATE_IMMEDIATE_PRIORITY = ON_DEMAND_BASE + 5
    SYSTEM_APPLY_UPDATE_IMMEDIATE_DESCRIPTION = \
        'System update'

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
        (LAUNCH_WAIT_FOR_NETWORK,
         LAUNCH_WAIT_FOR_NETWORK_DESCRIPTION),
        (SYSTEM_DETECT_MANAGEMENT_INTERFACE,
         SYSTEM_DETECT_MANAGEMENT_INTERFACE_DESC),
        (SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE,
         SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE_DESC),
        (SYSTEM_CONFIG_IMMEDIATE,
         SYSTEM_CONFIG_IMMEDIATE_DESCRIPTION),
    )
    name = APIReadOnly(models.CharField(max_length=8092, unique=True,
        choices=EVENT_TYPES))
    description = models.CharField(max_length=8092)
    priority = models.SmallIntegerField(db_index=True)

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
            ]:
            return True
        else:
            return False

class JobStates(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'job_states',
                elements=['job_state'])
    list_fields = ['job_state']
    job_state = []

class JobState(modellib.XObjIdModel):
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
    _xobj = xobj.XObjMetadata(tag='job_state',
                attributes = {'id':str})

    job_state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True, choices=choices)

    load_fields = [ name ]

class Jobs(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'jobs',
                elements=['job'],
                attributes={'id':str})
    list_fields = ['job']
    job = []
    
    def get_absolute_url(self, request, parents=None, model=None):
        """
        This implementation of get_absolute_url is a bit different since the
        jobs collection can be serialized on it's own from 2 different places
        (/api/inventory/jobs or /api/inventory/systems/{systemId}/jobs).  We
        need to ask the request to build the id for us based on the path.
        """
        return request.build_absolute_uri(request.get_full_path())

class Job(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_job'
    _xobj = xobj.XObjMetadata(
                tag = 'job',
                attributes = {'id':str})

    objects = modellib.JobManager()

    job_id = models.AutoField(primary_key=True)
    job_uuid = models.CharField(max_length=64, unique=True)
    job_state = modellib.InlinedDeferredForeignKey(JobState, visible='name',
        related_name='jobs')
    status_code = models.IntegerField(default=100)
    status_text = models.TextField(default='Initializing')
    status_detail = XObjHidden(models.TextField(null=True))
    event_type = APIReadOnly(modellib.InlinedForeignKey(EventType,
        visible='name', related_name="jobs"))
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_updated =  modellib.DateTimeUtcField(auto_now_add=True)
    job_type = modellib.SyntheticField()
    job_description = modellib.SyntheticField()

    load_fields = [ job_uuid ]

    def getRmakeJob(self):
        # XXX we should be using the repeater client for this
        from rmake3 import client
        RMAKE_ADDRESS = 'http://localhost:9998'
        rmakeClient = client.RmakeClient(RMAKE_ADDRESS)
        rmakeJobs = rmakeClient.getJobs([self.job_uuid])
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

    def get_absolute_url(self, request, parents=None, model=None):
        if parents:
            if isinstance(parents[0], JobState):
                self.view_name = 'JobStateJobs'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, model=model)

    def serialize(self, request=None, values=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request,
            values=values)
        xobj_model.job_type = modellib.Cache.get(self.event_type.__class__,
            pk=self.event_type_id).name
        xobj_model.job_description = modellib.Cache.get(
            self.event_type.__class__, pk=self.event_type_id).description
        xobj_model.event_type = None
        return xobj_model

class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    _xobj = xobj.XObjMetadata(
                tag = 'system_event',
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

    def get_absolute_url(self, request, parents=None, model=None):
        if parents:
            if isinstance(parents[0], EventType):
                self.view_name = 'SystemEventsByType'
            elif isinstance(parents[0], System):
                self.view_name = 'SystemsSystemEvent'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, model=model)

    def save(self, *args, **kw):
        if not self.priority:
            self.priority = self.event_type.priority
        modellib.XObjIdModel.save(self, *args, **kw)

class Network(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_network'
        unique_together = (('system', 'dns_name', 'ip_address', 'ipv6_address'),)
        
    _xobj = xobj.XObjMetadata(
                tag='network',
                attributes = {'id':str})
    network_id = models.AutoField(primary_key=True)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    system = modellib.ForeignKey(System, related_name='networks')
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

    def get_absolute_url(self, request, parents=None, model=None):
        if not parents:
            parents = [self.system]
        if isinstance(parents[0], System):
            self.view_name = 'SystemLog'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, model=model)

class SystemLogEntry(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='system_log_entry')
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
    system_log = modellib.ForeignKey(SystemLog,
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
    out_of_date = models.NullBooleanField()

    load_fields = [ name, version, flavor ]

    def get_absolute_url(self, request, parents=None, model=None):
        """
        model is an optional xobj model to use when computing the URL.
        It helps avoid additional database queries.
        """
        # Build an id to crest
        if model is None:
            conaryVersion = self.version.conaryVersion
        else:
            conaryVersion = Version.getConaryVersion(model.version)
        label = conaryVersion.trailingLabel()
        revision = conaryVersion.trailingRevision()
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
            return deps.parseFlavor('')
        return deps.parseFlavor(self.flavor)

    def getLabel(self):
        if not self.version.label:
            return None
        return versions.Label(self.version.label)

    def getHost(self):
        return self.getLabel().getHost()

    def getVersion(self):
        return self.version.conaryVersion

    def getNVF(self):
        return self.name, self.version.conaryVersion, self.getFlavor()

    def serialize(self, *args, **kwargs):
        xobj_model = modellib.XObjIdModel.serialize(self, *args, **kwargs)
        xobj_model.is_top_level_item = True
        return xobj_model

class Stage(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_stage'
    view_name = 'Stages'
    _xobj = xobj.XObjMetadata(tag='stage')
    _xobj_hidden_accessors = set(['version_set',])

    stage_id = models.AutoField(primary_key=True)
    major_version = models.ForeignKey(rbuildermodels.Versions)
    name = models.CharField(max_length=256)
    label = models.TextField(unique=True)

    def get_absolute_url(self, request, *args, **kwargs):
        parents = [Pk(self.major_version.productId.shortname),
            Pk(self.major_version.name), Pk(self.name)]
        return modellib.XObjIdModel.get_absolute_url(
            self, request, parents)

    def serialize(self, request=None, values=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request, values)
        xobj_model._xobj.text = self.name
        return xobj_model

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
        return self.getConaryVersion(self)

    @classmethod
    def getConaryVersion(cls, model):
        v = versions.VersionFromString(model.full,
            timeStamps = [ float(model.ordering) ] )
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
    system = modellib.ForeignKey(System)
    job = modellib.DeferredForeignKey(Job, unique=True, related_name='systems')
    event_uuid = XObjHidden(models.CharField(max_length=64, unique=True))

class JobSystem(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = 'job_system'
    job = models.ForeignKey(rbuildermodels.Jobs, null=False)
    # Django will insist on removing entries from this table when removing a
    # system, and because there's no primary key, it will fail. So, for now,
    # we don't use a FK for system
    #system = models.ForeignKey(System, null=False)
    system_id = models.IntegerField(null=False)

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
