from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class SystemLogEntry(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_log_entry_id = 'AutoField'
    system_log = 'SystemLog'
    entry_date = 'DateTimeUtcField'
    entry = 'CharField'
    _xobj = xobj.XObjMetadata(tag='system_log_entry')

class Targets(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    targettype = 'CharField'
    targetname = 'CharField'
    targetid = 'IntegerField'

class SystemTargetCredentials(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system = 'System'
    id = 'AutoField'
    credentials = 'TargetCredentials'

class SystemType(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_type_id = 'AutoField'
    name = 'CharField'
    infrastructure = 'BooleanField'
    description = 'CharField'
    creation_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='system_type',attributes={'id':str})

class JobState(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    name = 'CharField'
    job_state_id = 'AutoField'
    _xobj = xobj.XObjMetadata(tag='job_state',attributes={'id':str})

class System(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    target_system_state = 'CharField'
    target_system_name = 'CharField'
    target_system_id = 'CharField'
    target_system_description = 'CharField'
    target = 'Targets'
    system_type = 'SystemType'
    system_id = 'AutoField'
    state_change_date = 'DateTimeUtcField'
    stage = 'Stage'
    ssl_server_certificate = 'CharField'
    ssl_client_key = 'CharField'
    ssl_client_certificate = 'CharField'
    registration_date = 'DateTimeUtcField'
    name = 'CharField'
    managing_zone = 'Zone'
    management_interface = 'ManagementInterface'
    major_version = 'Versions'
    local_uuid = 'CharField'
    launching_user = 'Users'
    launch_date = 'DateTimeUtcField'
    hostname = 'CharField'
    generated_uuid = 'CharField'
    description = 'CharField'
    current_state = 'SerializedForeignKey'
    credentials = 'TextField'
    created_date = 'DateTimeUtcField'
    configuration = 'TextField'
    appliance = 'Products'
    agent_port = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='system',attributes={'id':str},elements=['networks'])

class Trove(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    version = 'SerializedForeignKey'
    trove_id = 'AutoField'
    out_of_date = 'NullBooleanField'
    name = 'TextField'
    last_available_update_refresh = 'DateTimeUtcField'
    is_top_level = 'BooleanField'
    flavor = 'TextField'
    _xobj = xobj.XObjMetadata(tag='trove')

class SystemJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_job_id = 'AutoField'
    system = 'System'
    job = 'Job'
    event_uuid = 'CharField'
    _xobj = xobj.XObjMetadata(tag='__systemjob')

class Stage(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    stage_id = 'AutoField'
    name = 'CharField'
    major_version = 'Versions'
    label = 'TextField'
    _xobj = xobj.XObjMetadata(tag='stage')

class Configuration(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='configuration',attributes={'id':str})

class Credentials(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='credentials',attributes={'id':str},elements=['ssl_client_certificate', 'ssl_client_key'])

class JobSystem(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_id = 'IntegerField'
    job = 'Jobs'
    id = 'AutoField'

class Job(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    time_updated = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    status_text = 'TextField'
    status_detail = 'TextField'
    status_code = 'IntegerField'
    job_uuid = 'CharField'
    job_state = 'InlinedDeferredForeignKey'
    job_id = 'AutoField'
    event_type = 'InlinedForeignKey'
    _xobj = xobj.XObjMetadata(tag='job',attributes={'id':str})

class ManagementInterface(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    port = 'IntegerField'
    name = 'CharField'
    management_interface_id = 'AutoField'
    description = 'CharField'
    credentials_readonly = 'NullBooleanField'
    credentials_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='management_interface',attributes={'id':str})

class EventType(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    priority = 'SmallIntegerField'
    name = 'CharField'
    event_type_id = 'AutoField'
    description = 'CharField'
    _xobj = xobj.XObjMetadata(tag='event_type')

class SystemEvent(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    time_enabled = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    system_event_id = 'AutoField'
    system = 'System'
    priority = 'SmallIntegerField'
    event_type = 'EventType'
    event_data = 'TextField'
    _xobj = xobj.XObjMetadata(tag='system_event',attributes={'id':str})

class ErrorResponse(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    traceback = 'TextField'
    product_code = 'TextField'
    message = 'TextField'
    code = 'TextField'
    _xobj = xobj.XObjMetadata(tag='fault')

class Pk(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class SystemLog(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_log_id = 'AutoField'
    system = 'System'

class Inventory(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    zones = 'HrefField'
    systems = 'HrefField'
    system_types = 'HrefField'
    system_states = 'HrefField'
    networks = 'HrefField'
    management_nodes = 'HrefField'
    management_interfaces = 'HrefField'
    log = 'HrefField'
    job_states = 'HrefField'
    inventory_systems = 'HrefField'
    infrastructure_systems = 'HrefField'
    image_import_metadata_descriptor = 'HrefField'
    event_types = 'HrefField'
    _xobj = xobj.XObjMetadata(tag='inventory')

class Version(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    version_id = 'AutoField'
    revision = 'TextField'
    ordering = 'TextField'
    label = 'TextField'
    full = 'TextField'
    flavor = 'TextField'
    _xobj = xobj.XObjMetadata(tag='version')

class ManagementNode(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    zone = 'Zone'
    target_system_state = 'CharField'
    target_system_name = 'CharField'
    target_system_id = 'CharField'
    target_system_description = 'CharField'
    target = 'Targets'
    system_type = 'SystemType'
    system_ptr = 'OneToOneField'
    system_id = 'AutoField'
    state_change_date = 'DateTimeUtcField'
    stage = 'Stage'
    ssl_server_certificate = 'CharField'
    ssl_client_key = 'CharField'
    ssl_client_certificate = 'CharField'
    registration_date = 'DateTimeUtcField'
    node_jid = 'CharField'
    name = 'CharField'
    managing_zone = 'Zone'
    management_interface = 'ManagementInterface'
    major_version = 'Versions'
    local_uuid = 'CharField'
    local = 'NullBooleanField'
    launching_user = 'Users'
    launch_date = 'DateTimeUtcField'
    hostname = 'CharField'
    generated_uuid = 'CharField'
    description = 'CharField'
    current_state = 'SerializedForeignKey'
    credentials = 'TextField'
    created_date = 'DateTimeUtcField'
    configuration = 'TextField'
    appliance = 'Products'
    agent_port = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='management_node',attributes={'id':str},elements=['networks'])

class SystemState(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_state_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(attributes={'id':str})

class Cache(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class ConfigurationDescriptor(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='configuration_descriptor',attributes={'id':str})

class Zone(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    zone_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='zone',attributes={'id':str})

class Network(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system = 'System'
    required = 'NullBooleanField'
    port_type = 'CharField'
    network_id = 'AutoField'
    netmask = 'CharField'
    ipv6_address = 'CharField'
    ip_address = 'CharField'
    dns_name = 'CharField'
    device_name = 'CharField'
    created_date = 'DateTimeUtcField'
    active = 'NullBooleanField'
    _xobj = xobj.XObjMetadata(tag='network',attributes={'id':str})

class SystemJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='system_jobs')
    job = ['Job']

class SystemTypes(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='system_types',elements=['system_type'])
    system_type = ['SystemType']

class SystemEvents(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='system_events')
    system_event = ['SystemEvent']

class EventTypes(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='event_types')
    event_type = ['EventType']

class Zones(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='zones',elements=['zone'])
    zone = ['Zone']

class Jobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='jobs',attributes={'id':str},elements=['job'])
    job = ['Job']

class InstalledSoftware(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='installed_software',attributes={'id':str})
    trove = ['Trove']

class SystemsLog(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='systems_log')
    system_log_entry = ['SystemLogEntry']

class ManagementInterfaces(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='management_interfaces',elements=['management_interface'])
    management_interface = ['ManagementInterface']

class SystemStates(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='system_states')
    system_state = ['SystemState']

class ManagementNodes(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='management_nodes')
    management_node = ['ManagementNode']

class Networks(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    systems = 'HrefField'
    _xobj = xobj.XObjMetadata(tag='networks',elements=['network', 'systems'])
    network = ['Network']

class JobStates(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='job_states',elements=['job_state'])
    job_state = ['JobState']

class Systems(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='systems',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    system = ['System']

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls = GLOBALS[tag]
            refCls = GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

