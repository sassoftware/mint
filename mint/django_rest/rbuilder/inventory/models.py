
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import sys
import urllib
import urlparse
import re

from conary import versions
from conary.deps import deps

from django.db import models
from django.db.backends import signals

from mint.django_rest import timeutils
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.projects.models import Project, ProjectVersion, Stage
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from ..targets import manager as tmgr
from xobj import xobj

Cache = modellib.Cache
XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly

def hasTemporaryTables(connection):
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

def createTemporaryTables(connection=None, **kwargs):
    if not hasTemporaryTables(connection):
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

    def get_url_key(self, *args, **kwargs):
        return self.pk

class Inventory(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory')

    zones = D(modellib.HrefField('zones'), "an entry point into the inventory management zones collection")
    management_nodes = D(modellib.HrefField('management_nodes'), "an entry point into the inventory management nodes collection (rPath Update Services)")
    management_interfaces = D(modellib.HrefField('management_interfaces'), "an entry point into the collection of management interfaces (CIM, WMI, etc.)")
    system_types = D(modellib.HrefField('system_types'), "an entry point into the inventory system types collection")
    networks = D(modellib.HrefField('networks'), "an entry point into the inventory system networks collection")
    systems = D(modellib.HrefField('systems'), "an entry point into the collection of all systems (all systems in inventory_systems and infrastructure systems combined)")
    log = D(modellib.HrefField('log'), "an entry point into inventory logging")
    event_types = D(modellib.HrefField('event_types'), "an entry point into the inventory events collection")
    system_states = D(modellib.HrefField('system_states'), "an entry point into the inventory system states collection")
    job_states = D(modellib.HrefField('job_states'), "an entry point into the inventory job states collection")
    inventory_systems = D(modellib.HrefField('inventory_systems'), "an entry point into the collection of inventory systems (all systems visible in the UI under Systems)")
    infrastructure_systems = D(modellib.HrefField('infrastructure_systems'), "an entry point into the collection of infrastructure systems (all systems visible in the UI under Infrastructure)")
    image_import_metadata_descriptor = D(modellib.HrefField('image_import_metadata_descriptor'), 'No documentation')

class Systems(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems')
    list_fields = ['system']
    system = []
    objects = modellib.SystemsManager()
    view_name = 'Systems'

    def __init__(self):
        modellib.Collection.__init__(self)

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
    
class SystemsLog(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='systems_log')
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
    
    systems = D(modellib.HrefField('../systems'), "an entry point into system inventory")
    
class Credentials(modellib.XObjIdModel):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'credentials',
                attributes = {'id':str},
                elements = [
                    'ssl_client_certificate',
                    'ssl_client_key',
                ])
    objects = modellib.CredentialsManager()
    view_name = 'SystemCredentials'

    def __init__(self, system, *args, **kwargs):
        self._system = system
        modellib.XObjIdModel.__init__(self, *args, **kwargs)

    def to_xml(self, request=None, xobj_model=None):
        self.id = self.get_absolute_url(request, parents=[self._system])
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

    def to_xml(self, request=None, xobj_model=None):
        self.id = self.get_absolute_url(request, parents=[self._system])
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

    def to_xml(self, request=None, xobj_model=None):
        self.id = self.get_absolute_url(request, parents=[self._system])
        return xobj.toxml(self)

class SystemState(modellib.XObjIdModel):
    
    serialize_accessors = False
    class Meta:
        db_table = 'inventory_system_state'
        
    _xobj = xobj.XObjMetadata(
                attributes = {'id':str})

    UNMANAGED = "unmanaged"
    UNMANAGED_DESC = "Unmanaged"
    
    UNMANAGED_CREDENTIALS_REQUIRED = "unmanaged-credentials"
    UNMANAGED_CREDENTIALS_REQUIRED_DESC = "Unmanaged: Invalid credentials"
    
    REGISTERED = "registered"
    REGISTERED_DESC = "Registered"
    
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

    system_state_id = D(models.AutoField(primary_key=True), "the database id for the state")
    name = D(models.CharField(max_length=8092, unique=True,
        choices=STATE_CHOICES), "the state name")
    description = D(models.CharField(max_length=8092), "the state description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the state was created (UTC)")

    load_fields = [ name ]

class ManagementInterfaces(modellib.XObjModel):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='management_interfaces',
                elements=['management_interface'])
    list_fields = ['management_interface']
    
class ManagementInterface(modellib.XObjIdModel):
    
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
    SSH = "ssh"
    SSH_PORT = 22
    SSH_DESC = "Secure Shell (SSH)"

    CHOICES = (
        (CIM, CIM_DESC),
        (WMI, WMI_DESC),
        (SSH, SSH_DESC),
    )
        
    management_interface_id = D(models.AutoField(primary_key=True), "the database ID for the management interface")
    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True, choices=CHOICES)), "the name of the management interface")
    description = D(models.CharField(max_length=8092), "the description of the management interface")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the management interface was added to inventory (UTC)")
    port = D(models.IntegerField(null=False), "the port used by the management interface")
    credentials_descriptor = D(modellib.XMLField(), "the descriptor of available fields to set credentials for the management interface")
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
    creation_descriptor = D(modellib.XMLField(), "the descriptor of available fields to create systems of this type")

    load_fields = [ name ]

class NetworkAddress(modellib.XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
            tag = 'network_address',
    )
    address = D(models.CharField(max_length=8092),
        "The address to use for contacting the system")
    pinned = D(models.BooleanField(),
        "true if the address is pinned")

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.address == other.address and
                bool(self.pinned) == bool(other.pinned))

class AssimilationParameters(modellib.XObjModel):
    '''Used to install management S/W on a system already in inventory'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
        tag = 'assimilation_parameters',
        elements = ['assimilation_credential']
    )
    list_fields = ['assimilation_credential']

class AssimilationCredential(modellib.XObjModel):
    '''One of many login credentials to try when using AssimilationParameters'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
       tag = 'assimilation_credential'
    )

    ssh_username = D(models.CharField(max_length=100), "OS username")
    ssh_password = D(models.CharField(max_length=512), "OS or SSH key password")
    ssh_key      = D(models.TextField(null=True), "SSH key")

class System(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'inventory_system'

    view_name = 'System'

    # XXX this is hopefully a temporary solution to not serialize the FK
    # part of a many-to-many relationship
    _xobj_hidden_accessors = set(['systemjob_set', 'target_credentials',
        'managementnode', 'jobsystem_set', 'tags', 'surveys',
        'desired_top_level_items'])
    _xobj_hidden_m2m = set()
    _xobj = xobj.XObjMetadata(
                tag = 'system',
                attributes = {'id':str},
                elements = ['networks', ])
    # avoid expanding launching_user as, for now, rpath_models can't
    # deal with it and registration is affected when set
    _xobj_summary_view_hide = [ 'launching_user' ]
    _queryset_resource_type = 'system'

    """
    networks - a collection of network resources exposed by the system
    system_events - a link to the collection of system events currently 
    active on this sytem
    """
    # need our own object manager for dup detection
    objects = modellib.SystemManager()
    system_id = D(models.AutoField(primary_key=True),
        "the database ID for the system", short="System ID")
    name = D(models.CharField(max_length=8092),
        "the system name", short="System name")
    description = D(models.CharField(max_length=8092, null=True),
        "the system description", short="System description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the system was added to inventory (UTC)")
    hostname = D(models.CharField(max_length=8092, null=True),
        "the system hostname", short="System hostname")
    # Launch date is nullable, we may get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was deployed (only applies if system is on a "
        "virtual target)", short="System launch date")
    target = D(modellib.ForeignKey(targetmodels.Target, null=True, 
        text_field="name"),
        "the virtual target the system was deployed to (only applies if "
        "system is on a virtual target)")
    target_system_id = D(models.CharField(max_length=255,
            null=True),
        "the system ID as reported by its target (only applies if system is "
        "on a virtual target)", short="System target system ID")
    target_system_name = D(APIReadOnly(models.CharField(max_length=255,
            null=True)),
        "the system name as reported by its target (only applies if system "
        "is on a virtual target)", short="System target system name")
    target_system_description = D(APIReadOnly(models.CharField(max_length=1024,
            null=True)),
        "the system description as reported by its target (only applies if "
        "system is on a virtual target)", short="System target system description")
    target_system_state = D(APIReadOnly(models.CharField(max_length=64,
            null=True)),
        "the system state as reported by its target (only applies if system "
        "is on a virtual target)", short="System target system state")
    registration_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was registered in inventory (UTC)", short="System registration date")
    generated_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID that is randomly generated", short="System UUID")
    local_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID created from the system hardware profile", short="System local UUID")
    ssl_client_certificate = D(modellib.SyntheticField(),
        "an x509 certificate of an authorized client that can use the "
        "system's CIM broker")
    _ssl_client_certificate = XObjHidden(APIReadOnly(models.CharField(
        max_length=8092, null=True, db_column='ssl_client_certificate')))
    ssl_client_key = D(XObjHidden(modellib.SyntheticField()),
        "an x509 private key of an authorized client that can use the "
        "system's CIM broker")
    _ssl_client_key = XObjHidden(APIReadOnly(models.CharField(
        max_length=8092, null=True, db_column='ssl_client_key')))
    ssl_server_certificate = D(models.CharField(max_length=8092, null=True),
        "an x509 public certificate of the system's CIM broker")
    launching_user = D(modellib.ForeignKey(usersmodels.User, null=True, 
        text_field="user_name"),
        "the user that deployed the system (only applies if system is on a "
        "virtual target)")
    current_state = D(modellib.SerializedForeignKey(
            SystemState, null=True, related_name='systems'),
        "the current state of the system", short="System state")
    managing_zone = D(modellib.ForeignKey(zmodels.Zone, null=False,
            related_name='systems', text_field="name"),
        "a link to the management zone in which this system resides")
    jobs = models.ManyToManyField(jobmodels.Job, through="SystemJob") #, related_name='systems')
    agent_port = D(models.IntegerField(null=True),
          "the port used by the system's CIM broker", short="System agent port")
    state_change_date = XObjHidden(APIReadOnly(modellib.DateTimeUtcField(
        auto_now_add=True, default=timeutils.now())))
    event_uuid = D(XObjHidden(modellib.SyntheticField()),
        "a UUID used to link system events with their returned responses")
    boot_uuid = D(XObjHidden(modellib.SyntheticField()),
        "a UUID used for tracking systems registering at startup time")
    management_interface = D(modellib.ForeignKey(ManagementInterface, 
        null=True, related_name='systems', text_field="description"),
        "the management interface used to communicate with the system")
    credentials = APIReadOnly(XObjHidden(models.TextField(null=True)))
    system_type = D(modellib.ForeignKey(SystemType, null=False,
        related_name='systems', text_field='description'),
        "the type of the system")
    project_branch_stage = D(APIReadOnly(modellib.DeferredForeignKey(Stage, null=True, 
        db_column="stage_id", text_field='name', related_name="+")),
        "the project stage of the system")
    project_branch = D(APIReadOnly(modellib.DeferredForeignKey(ProjectVersion, null=True,
        db_column="major_version_id", text_field='name', related_name="systems")),
        "the project major version of the system")
    project = D(APIReadOnly(modellib.DeferredForeignKey(Project, null=True,
        text_field='short_name', related_name="+")),
        "the project of the system")
    configuration = APIReadOnly(XObjHidden(models.TextField(null=True)))
    configuration_descriptor = D(XObjHidden(modellib.SyntheticField()),
        "the descriptor of available fields to set system configuration "
        "parameters")
    network_address = D(NetworkAddress, "Network address for this system", short="System network address")
    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available on the system")
    source_image = D(APIReadOnly(models.ForeignKey('images.Image', null=True,
         related_name='systems')), 
         'rBuilder image used to deploy the system, if any')
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='created_by'), 
        "User who created system",
        short="System created by")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='modified_by'),
        "User who last modified system",
        short="System last modified by")
    modified_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was last modified", short="System modified date")
    latest_survey = modellib.DeferredForeignKey('inventory.Survey',
        null=True, related_name='+', on_delete=models.SET_NULL)
    survey = D(XObjHidden(modellib.SyntheticField()),
        "survey specified at registration time")

    # Note the camel-case here. It is intentional, this is a field sent
    # only by catalog-service via rmake, to simplify creation of system
    # objects (otherwise we'd have to create networks too and we may
    # change the way we deal with them)
    dnsName = XObjHidden(modellib.SyntheticField())
    targetType = XObjHidden(modellib.SyntheticField())
    targetName = XObjHidden(modellib.SyntheticField())

    # these fields are derived from job & trove state
    # stored here so serialization speed is acceptable
    # call updateDerivedData() to recalculate
    has_running_jobs = D(models.BooleanField(default=False, null=False), 'whether the system has running jobs', short="System running jobs")
    has_active_jobs = D(models.BooleanField(default=False, null=False), 'whether the system has active (queued/unqueud) jobs', short='System active jobs')
    out_of_date  = D(models.BooleanField(default=False, null=False), 'whether the system has pending updates', short='System out of date')
    
    configuration_applied = D(models.BooleanField(default=False, null=False), 'whether any configuraiton has been applied for this system', short='System configuration applied')
    configuration_set = D(models.BooleanField(default=False, null=False), 'whether any configuration has been saved (but not necc. applied) for this system', short='System configuration saved')

    # FIXME: OUT OF DATE -- installed software no longer used, can purge some of this?
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
        self.createNetworks()

    def createLog(self):
        system_log, created = SystemLog.objects.get_or_create(system=self)
        if created:
            system_log.save()
        return system_log

    def _matchNetwork(self, address, **kwargs):
        ret = self.networks.filter(ip_address=address, **kwargs)
        if ret:
            return ret[0]
        ret = self.networks.filter(dns_name=address, **kwargs)
        if ret:
            return ret[0]
        return None

    def createNetworks(self):
        # * oldNetAddr is the state of the system in the db, before any
        #   fields from the xobj model were copied
        # * self.network_address comes originally from the DB, and updated
        #   from the xobj model
        # * curNetAddr is the state of the network in the db, which may
        #   have been altered since we loaded the object.
       
        if self.network_address is not None:
            dnsName = self.network_address.address
            address = re.compile('^[a-zA-Z0-9:._-]+$')
            if dnsName and not re.match(address, dnsName):
                raise errors.InvalidData(msg="invalid hostname/DNS name")

        currentNw = self.__class__.extractNetworkToUse(self)
        curNetAddr = self.newNetworkAddress(currentNw)
        if self.oldModel is None:
            oldNetAddr = None
        else:
            oldNetAddr = getattr(self.oldModel, 'network_address', None)
        if self.network_address is None or curNetAddr == self.network_address:
            # This is calling the custom __eq__, and also covers
            # None==None
            return

        if self.network_address.pinned:
            # We only have to remove the pinned network address. The
            # client maintains the rest
            self.networks.filter(pinned=True).delete()
        else:
            self.networks.all().delete()
 

        nw = Network(system=self, dns_name=dnsName, 
            pinned=self.network_address.pinned)
        nw.save()

    @property
    def isRegistrationIncomplete(self):
        """
        Return True if local_uuid is missing (due to possible bugs in
        rpath-tools).
        """
        return self.generated_uuid is not None and not bool(self.local_uuid)

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
                Cache.get(jobmodels.JobState, name=x).job_state_id
                    for x in [ jobmodels.JobState.RUNNING, 
                        jobmodels.JobState.QUEUED ])
        return self.__class__._RunningJobStateIds

    def areJobsActive(self, iterable):
        for job in iterable:
            if job.job_state_id in self.runningJobStateIds:
                return True
        return False

    def hasRunningJobs(self):
        return bool(self.jobs.filter(job_state__name=jobmodels.JobState.RUNNING))

    _runningJobState = None
    @property
    def runningJobState(self):
        if self._runningJobState is None:
            self.__class__._runningJobState = \
                Cache.get(jobmodels.JobState, name=jobmodels.JobState.RUNNING)
        return self.__class__._runningJobState

    def areJobsRunning(self, jobs):
        return bool([j for j in jobs \
            if j.job_state_id == self.runningJobState.job_state_id])

    def updateDerivedData(self):
        # call this to update cached data about the system record, so that it does not
        # have to be called at serialization time.

        jobs = []
        # if system was not saved yet, self.system_id is None
        if self.system_id is not None:
            jobs = self.jobs.filter(job_state__job_state_id__in=self.runningJobStateIds)

        self.has_active_jobs  = self.areJobsActive(jobs)
        self.has_running_jobs = self.areJobsRunning(jobs)
        self.out_of_date      = self.isOutOfDate()
        self.save()

    def isOutOfDate(self):
        for x in self.desired_top_level_items.all():
            troveSpec = x.trove_spec
            (name, rest) = troveSpec.split('=')
            (version, flavor) = rest.split("[")
            flavor = flavor.replace("]","")
            troves = Trove.objects.filter(name=name, version=version, flavor=flavor)
            # FIXME: this is also incomplete, we must make sure the trove is a member of the stage
            for x in troves:
                # should just get one back, but anyway...
                if x.out_of_date:
                    return True
        return False

    def serialize(self, request=None):
        
        # hide some data in collapsed collections 
        summarize = getattr(self, '_summarize', False)

        xobj_model = modellib.XObjIdModel.serialize(self, request)

        if request:
            class CredentialsHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='credentials',
                            attributes={'id':str})

                def __init__(self, href):
                    self.id = href
                    
            class ConfigurationHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='configuration',
                            attributes={'id':str})

                def __init__(self, href):
                    self.id = href
                    
            class ConfigurationDescriptorHref(object): 
                _xobj = xobj.XObjMetadata(
                            tag='configuration_descriptor',
                            attributes={'id':str})

                def __init__(self, href):
                    self.id = href

            class SurveysHref(object):
                _xobj = xobj.XObjMetadata(
                            tag='surveys',
                            attributes={'id':str})

                def __init__(self, href):
                    self.id = href

            
            if not summarize:
                xobj_model.credentials = CredentialsHref(request.build_absolute_uri(
                    '%s/credentials' % self.get_absolute_url(request)))
            
                xobj_model.configuration = ConfigurationHref(request.build_absolute_uri(
                    '%s/configuration' % self.get_absolute_url(request)))
            
                xobj_model.configuration_descriptor = ConfigurationDescriptorHref(request.build_absolute_uri(
                    '%s/configuration_descriptor' % self.get_absolute_url(request)))
                
                xobj_model.surveys = SurveysHref(request.build_absolute_uri(
                    '%s/surveys' % self.get_absolute_url(request)))

        class JobsHref(modellib.XObjIdModel):
            _xobj = xobj.XObjMetadata(tag='jobs',
                elements = ['queued_jobs', 'completed_jobs',
                    'running_jobs', 'failed_jobs'],
                attributes = {'id':str})

            def __init__(self, request, system):
                self.view_name = 'SystemJobs'
                self.id = self.get_absolute_url(request, parents=[system])
                self.view_name = 'SystemJobStateJobs'
                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.QUEUED)]
                self.queued_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.COMPLETED)]
                self.completed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.RUNNING)]
                self.running_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.FAILED)]
                self.failed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))
                self.view_name = None

        # old and busted slow way
        # 
        if not summarize:
            xobj_model.jobs = JobsHref(request, self)

        xobj_model.network_address = self.__class__.extractNetworkAddress(self)
        return xobj_model

    @classmethod
    def extractNetworkToUse(cls, system):
        trueSet = set([ "True", "true" ])
        if hasattr(system.networks, 'all'):
            networks = system.networks.all()
        else:
            networks = system.networks.network
            for net in networks:
                net.pinned = (net.pinned in trueSet)
                net.active = (net.active in trueSet)

        # first look for user pinned nets
        nets = [ x for x in networks if x.pinned ]
        if nets:
            return nets[0]

        # now look for a non-pinned active net
        nets = [ x for x in networks if x.active ]
        if nets:
            return nets[0]

        # If we only have one network, return that one and hope for the best
        if len(networks) == 1:
            return networks[0]
        return None

    @classmethod
    def extractNetworkAddress(cls, system):
        nw = cls.extractNetworkToUse(system)
        return cls.newNetworkAddress(nw)

    @classmethod
    def newNetworkAddress(cls, network):
        if network is None:
            return None
        pinned = network.pinned
        address = network.ip_address or network.dns_name

        return NetworkAddress(address=address, pinned=pinned)

    def computeSyntheticFields(self, sender, **kwargs):
        ''' Compute non-database fields.'''
        self._computeActions()
        self.ssl_client_certificate = self._ssl_client_certificate

    def _computeActions(self):
        '''What actions are available on the system?'''

        self.actions = actions = jobmodels.Actions()
        actions.action = []
        assimEnabled = bool(self.management_interface_id and
            self.management_interface.name == 'ssh')
        scanEnabled = bool(self.management_interface_id and
            self.management_interface.name in ('cim', 'wmi'))
        configureEnabled = False
        # Disable config action if no config is saved, or if the system
        # is based on a system model
        if self.latest_survey is not None:
            configureEnabled = bool((self.configuration is not None) and \
                not self.latest_survey.has_system_model)
        else:
            # no survey taken, legacy system in inventory, don't disable
            # the action because it would be confusing, next registration will
            # survey it.
            configureEnabled = bool(self.configuration is not None)

        capture_enabled = False
        if self.target_id:
            drvCls = targetmodels.Target.getDriverClassForTargetId(
                self.target_id)
            capture_enabled = hasattr(drvCls, "drvCaptureSystem")

        actions.action.extend([
            jobmodels.EventType.makeAction(
                jobmodels.EventType.SYSTEM_ASSIMILATE,
                actionName="Assimilate system",
                actionDescription="Assimilate system",
                descriptorModel=self,
                descriptorHref="descriptors/assimilation",
                enabled=assimEnabled,
            ),
            jobmodels.EventType.makeAction(
                jobmodels.EventType.SYSTEM_SCAN,
                actionName="System scan",
                descriptorModel=self,
                descriptorHref="descriptors/survey_scan",
                enabled=scanEnabled,
            ),
            jobmodels.EventType.makeAction(
                jobmodels.EventType.SYSTEM_CAPTURE,
                actionName="System capture",
                descriptorModel=self,
                descriptorHref="descriptors/capture",
                enabled=capture_enabled,
            ),
            jobmodels.EventType.makeAction(
                jobmodels.EventType.SYSTEM_UPDATE,
                actionName="Update Software",
                descriptorModel=self,
                descriptorHref="descriptors/update",
                enabled=True,
            ),
            jobmodels.EventType.makeAction(
                jobmodels.EventType.SYSTEM_CONFIGURE,
                actionName="Apply system configuration",
                descriptorModel=self,
                descriptorHref="descriptors/configure", 
                enabled=configureEnabled,
            ),
        ])

        return actions

    def hasSourceImage(self):
        return bool(getattr(self, 'source_image', None))

class SystemDesiredTopLevelItem(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_desired_top_level_item'
        unique_together = [ ('system', 'trove_spec') ]

    system = modellib.ForeignKey(System, null=False,
        related_name = 'desired_top_level_items')
    trove_spec = D(models.TextField(null=False), "Trove")
    created_date = D(modellib.DateTimeUtcField(null=False, auto_now_add=True),
        "the date the entry was created", short="Entry created date")

class ManagementNode(System):
    
    class Meta:
        db_table = 'inventory_zone_management_node'
    _xobj = xobj.XObjMetadata(
                tag = 'management_node',
                attributes = {'id':str})
    view_name = 'ManagementNode'
    local = D(models.NullBooleanField(), "whether or not this management node is local to the rBuilder")
    zone = D(modellib.ForeignKey(zmodels.Zone, related_name='management_nodes'), "the zone the management node lives in")
    node_jid = D(models.CharField(max_length=64, null=True), "the Jabber ID the management node is using")
    load_fields = [ node_jid ]

    # ignore auto generated ptr from inheritance
    load_ignore_fields = ["system_ptr"]
    
    # need our own object manager for dup detection
    objects = modellib.ManagementNodeManager()
    
    def save(self, *args, **kw):
        self.system_type = SystemType.objects.get(
            name = SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        System.save(self, *args, **kw)

    def _computeActions(self):
        # At least for now, management nodes don't expose actions
        pass

class SystemTargetCredentials(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_target_credentials'
        unique_together = [ ('system', 'credentials') ]

    system = modellib.ForeignKey(System, null=False,
        related_name = 'target_credentials')
    credentials = modellib.ForeignKey(targetmodels.TargetCredentials,
        null=False, related_name = 'systems')

class InstalledSoftware(modellib.XObjIdModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='installed_software',
                attributes=dict(id = str))
    list_fields = ['trove']
    objects = modellib.InstalledSoftwareManager()

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            return modellib.XObjIdModel.get_absolute_url(self, request,
                parents, *args, **kwargs)
        return request.build_absolute_uri(request.get_full_path())


class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    _xobj = xobj.XObjMetadata(
                tag = 'system_event',
                attributes = {'id':str})
    
    system_event_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, db_index=True,
        related_name='system_events')
    event_type = modellib.DeferredForeignKey(jobmodels.EventType,
        related_name='system_events', db_column='job_type_id')
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_enabled = modellib.DateTimeUtcField(
        default=timeutils.now(), db_index=True)
    priority = models.SmallIntegerField(db_index=True)
    event_data = models.TextField(null=True)

    def dispatchImmediately(self):
        return self.event_type.priority >= jobmodels.EventType.ON_DEMAND_BASE

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            if isinstance(parents[0], jobmodels.EventType):
                self.view_name = 'SystemEventsByType'
            elif isinstance(parents[0], System):
                self.view_name = 'SystemsSystemEvent'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

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
    network_id = D(models.AutoField(primary_key=True), "the database ID for the network")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the network was created (UTC)")
    system = D(modellib.ForeignKey(System, related_name='networks'), "documentation missing")
    ip_address = D(models.CharField(max_length=15, null=True), "the network IP address")
    # TODO: how long should this be?
    ipv6_address = D(models.CharField(max_length=32, null=True), "the network IPv6 address")
    device_name = D(models.CharField(max_length=255), "the network device name") 
    dns_name = D(models.CharField(max_length=255, db_index=True), "the network DNS name")
    netmask = D(models.CharField(max_length=20, null=True), "the network netmask")
    port_type = D(models.CharField(max_length=32, null=True), "the network port type")
    active = D(models.NullBooleanField(), "whether or not this is the active network device on the system")
    pinned = D(models.NullBooleanField(db_column="required"), "whether or not a user has pinned this network device be the one used to manage the system")

    load_fields = [ip_address, dns_name]

    def natural_key(self):
        return self.ip_address, self.dns_name

    def save(self, *args, **kwargs):
        """
        Disallow saving of link-local IPs.
        FIXME: Additionally allow edge case where the ip_address field
        is missing but we want to save the model anyway.
        """
        if self.ip_address and self.ip_address.startswith(("169.254", "fe80:")):
            return
        return super(Network, self).save(*args, **kwargs)

class SystemLog(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'inventory_system_log'
    system_log_id = D(models.AutoField(primary_key=True), "the database ID for the system log")
    system = D(modellib.DeferredForeignKey(System, related_name='system_log'), "a entry point to the system this log is for")

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if not parents:
            parents = [self.system]
        if isinstance(parents[0], System):
            self.view_name = 'SystemLog'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

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

    _xobj = xobj.XObjMetadata(tag='trove')
    _xobj_hidden_accessors = set(['package_sources',])
    
    objects = modellib.TroveManager()

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

    def get_absolute_url(self, request, *args, **kwargs):
        """
        model is an optional xobj model to use when computing the URL.
        It helps avoid additional database queries.
        """
        # Build an id to crest
        conaryVersion = self.version.conaryVersion
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

    def __str__(self):
        return "%s=%s" % (self.name, self.getVersion().asString())

    def serialize(self, *args, **kwargs):
        xobj_model = modellib.XObjIdModel.serialize(self, *args, **kwargs)
        xobj_model.is_top_level_item = True
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
    job = modellib.DeferredForeignKey(jobmodels.Job, unique=True, 
        related_name='systems')
    event_uuid = XObjHidden(models.CharField(max_length=64, unique=True))

class JobSystem(modellib.XObjModel):
    class Meta:
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

class Update(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_update'

    view_name = 'Update'

    update_id = D(models.AutoField(primary_key=True),
                  'the update ID for the system', short='Update ID')
    system    = modellib.DeferredForeignKey('inventory.System',
                                            related_name='updates+', db_column='system_id')
    dry_run      = models.BooleanField(default=False)
    specs        = models.TextField()
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        'the date the update was created (UTC)')

# ------------------------
# this stays at the bottom!

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
for mod_obj in rbuildermodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
for mod_obj in usersmodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
