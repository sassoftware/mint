from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class SystemLogEntry(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_log_entry_id = 'AutoField'
    system_log = 'SystemLog'
    entry_date = 'DateTimeUtcField'
    entry = 'CharField'
    _xobj = XObjMetadata(tag='system_log_entry')

@register
class Targets(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targettype = 'CharField'
    targetname = 'CharField'
    targetid = 'IntegerField'

@register
class SystemTargetCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system = 'System'
    id = 'AutoField'
    credentials = 'rbuilder.TargetCredentials'

@register
class SystemType(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_type_id = 'AutoField'
    name = 'CharField'
    infrastructure = 'BooleanField'
    description = 'CharField'
    creation_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='system_type',attributes={'id':str})

@register
class JobState(object):
    """
    """
    __metaclass__ = SDKClassMeta
    name = 'CharField'
    job_state_id = 'AutoField'
    _xobj = XObjMetadata(tag='job_state',attributes={'id':str})

@register
class System(object):
    """
    """
    __metaclass__ = SDKClassMeta
    target_system_state = 'CharField'
    target_system_name = 'CharField'
    target_system_id = 'CharField'
    target_system_description = 'CharField'
    target = 'rbuilder.Targets'
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
    major_version = 'rbuilder.Versions'
    local_uuid = 'CharField'
    launching_user = 'rbuilder.Users'
    launch_date = 'DateTimeUtcField'
    hostname = 'CharField'
    generated_uuid = 'CharField'
    description = 'CharField'
    current_state = 'SystemState'
    credentials = 'TextField'
    created_date = 'DateTimeUtcField'
    configuration = 'TextField'
    appliance = 'rbuilder.Products'
    agent_port = 'IntegerField'
    _xobj = XObjMetadata(tag='system',attributes={'id':str},elements=['networks'])

@register
class Trove(object):
    """
    """
    __metaclass__ = SDKClassMeta
    version = 'Version'
    trove_id = 'AutoField'
    out_of_date = 'NullBooleanField'
    name = 'TextField'
    last_available_update_refresh = 'DateTimeUtcField'
    is_top_level = 'BooleanField'
    flavor = 'TextField'
    _xobj = XObjMetadata(tag='trove')

@register
class SystemJob(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_job_id = 'AutoField'
    system = 'System'
    job = 'Job'
    event_uuid = 'CharField'
    _xobj = XObjMetadata(tag='__systemjob')

@register
class Stage(object):
    """
    """
    __metaclass__ = SDKClassMeta
    stage_id = 'AutoField'
    name = 'CharField'
    major_version = 'rbuilder.Versions'
    label = 'TextField'
    _xobj = XObjMetadata(tag='stage')

@register
class Configuration(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='configuration',attributes={'id':str})

@register
class Credentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='credentials',attributes={'id':str},elements=['ssl_client_certificate', 'ssl_client_key'])

@register
class JobSystem(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_id = 'IntegerField'
    job = 'Jobs'
    id = 'AutoField'

@register
class Job(object):
    """
    """
    __metaclass__ = SDKClassMeta
    time_updated = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    status_text = 'TextField'
    status_detail = 'TextField'
    status_code = 'IntegerField'
    job_uuid = 'CharField'
    job_state = 'InlinedDeferredForeignKey'
    job_id = 'AutoField'
    event_type = 'InlinedForeignKey'
    _xobj = XObjMetadata(tag='job',attributes={'id':str})

@register
class ManagementInterface(object):
    """
    """
    __metaclass__ = SDKClassMeta
    port = 'IntegerField'
    name = 'CharField'
    management_interface_id = 'AutoField'
    description = 'CharField'
    credentials_readonly = 'NullBooleanField'
    credentials_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='management_interface',attributes={'id':str})

@register
class EventType(object):
    """
    """
    __metaclass__ = SDKClassMeta
    priority = 'SmallIntegerField'
    name = 'CharField'
    event_type_id = 'AutoField'
    description = 'CharField'
    _xobj = XObjMetadata(tag='event_type')

@register
class SystemEvent(object):
    """
    """
    __metaclass__ = SDKClassMeta
    time_enabled = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    system_event_id = 'AutoField'
    system = 'System'
    priority = 'SmallIntegerField'
    event_type = 'EventType'
    event_data = 'TextField'
    _xobj = XObjMetadata(tag='system_event',attributes={'id':str})

@register
class ErrorResponse(object):
    """
    """
    __metaclass__ = SDKClassMeta
    traceback = 'TextField'
    product_code = 'TextField'
    message = 'TextField'
    code = 'TextField'
    _xobj = XObjMetadata(tag='fault')

@register
class Pk(object):
    """
    """
    __metaclass__ = SDKClassMeta

@register
class SystemLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_log_id = 'AutoField'
    system = 'System'

@register
class Inventory(object):
    """
    """
    __metaclass__ = SDKClassMeta
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
    _xobj = XObjMetadata(tag='inventory')

@register
class Version(object):
    """
    """
    __metaclass__ = SDKClassMeta
    version_id = 'AutoField'
    revision = 'TextField'
    ordering = 'TextField'
    label = 'TextField'
    full = 'TextField'
    flavor = 'TextField'
    _xobj = XObjMetadata(tag='version')

@register
class ManagementNode(object):
    """
    """
    __metaclass__ = SDKClassMeta
    zone = 'Zone'
    target_system_state = 'CharField'
    target_system_name = 'CharField'
    target_system_id = 'CharField'
    target_system_description = 'CharField'
    target = 'rbuilder.Targets'
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
    major_version = 'rbuilder.Versions'
    local_uuid = 'CharField'
    local = 'NullBooleanField'
    launching_user = 'rbuilder.Users'
    launch_date = 'DateTimeUtcField'
    hostname = 'CharField'
    generated_uuid = 'CharField'
    description = 'CharField'
    current_state = 'SystemState'
    credentials = 'TextField'
    created_date = 'DateTimeUtcField'
    configuration = 'TextField'
    appliance = 'rbuilder.Products'
    agent_port = 'IntegerField'
    _xobj = XObjMetadata(tag='management_node',attributes={'id':str},elements=['networks'])

@register
class SystemState(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_state_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(attributes={'id':str})

@register
class Cache(object):
    """
    """
    __metaclass__ = SDKClassMeta

@register
class ConfigurationDescriptor(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='configuration_descriptor',attributes={'id':str})

@register
class Zone(object):
    """
    """
    __metaclass__ = SDKClassMeta
    zone_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='zone',attributes={'id':str})

@register
class Network(object):
    """
    """
    __metaclass__ = SDKClassMeta
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
    _xobj = XObjMetadata(tag='network',attributes={'id':str})

@register
class SystemJobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_jobs')
    job = ['Job']

@register
class SystemTypes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_types',elements=['system_type'])
    system_type = ['SystemType']

@register
class SystemEvents(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_events')
    system_event = ['SystemEvent']

@register
class EventTypes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='event_types')
    event_type = ['EventType']

@register
class Zones(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='zones',elements=['zone'])
    zone = ['Zone']

@register
class Jobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='jobs',attributes={'id':str},elements=['job'])
    job = ['Job']

@register
class InstalledSoftware(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='installed_software',attributes={'id':str})
    trove = ['Trove']

@register
class SystemsLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='systems_log')
    system_log_entry = ['SystemLogEntry']

@register
class ManagementInterfaces(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='management_interfaces',elements=['management_interface'])
    management_interface = ['ManagementInterface']

@register
class SystemStates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_states')
    system_state = ['SystemState']

@register
class ManagementNodes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='management_nodes')
    management_node = ['ManagementNode']

@register
class Networks(object):
    """
    """
    __metaclass__ = SDKClassMeta
    systems = 'HrefField'
    _xobj = XObjMetadata(tag='networks',elements=['network', 'systems'])
    network = ['Network']

@register
class JobStates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='job_states',elements=['job_state'])
    job_state = ['JobState']

@register
class Systems(object):
    """
    """
    __metaclass__ = SDKClassMeta
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
    _xobj = XObjMetadata(tag='systems',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    system = ['System']

GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

