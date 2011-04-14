from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class SystemLogEntry(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_log_entry')
    entry = 'CharField'
    entry_date = 'DateTimeUtcField'
    system_log = 'SystemLog'
    system_log_entry_id = 'AutoField'

class Targets(object):
    """
    """
    __metaclass__ = SDKClassMeta
    targetid = 'IntegerField'
    targetname = 'CharField'
    targettype = 'CharField'

class SystemTargetCredentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    credentials = 'TargetCredentials'
    id = 'AutoField'
    system = 'System'

class SystemType(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_type',attributes={'id':str})
    created_date = 'DateTimeUtcField'
    creation_descriptor = 'XMLField'
    description = 'CharField'
    infrastructure = 'BooleanField'
    name = 'CharField'
    system_type_id = 'AutoField'

class JobState(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='job_state',attributes={'id':str})
    job_state_id = 'AutoField'
    name = 'CharField'

class System(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system',attributes={'id':str},elements=['networks'])
    agent_port = 'IntegerField'
    appliance = 'Products'
    configuration = 'TextField'
    created_date = 'DateTimeUtcField'
    credentials = 'TextField'
    current_state = 'SystemState'
    description = 'CharField'
    generated_uuid = 'CharField'
    hostname = 'CharField'
    launch_date = 'DateTimeUtcField'
    launching_user = 'Users'
    local_uuid = 'CharField'
    major_version = 'Versions'
    management_interface = 'ManagementInterface'
    managing_zone = 'Zone'
    name = 'CharField'
    registration_date = 'DateTimeUtcField'
    ssl_client_certificate = 'CharField'
    ssl_client_key = 'CharField'
    ssl_server_certificate = 'CharField'
    stage = 'Stage'
    state_change_date = 'DateTimeUtcField'
    system_id = 'AutoField'
    system_type = 'SystemType'
    target = 'Targets'
    target_system_description = 'CharField'
    target_system_id = 'CharField'
    target_system_name = 'CharField'
    target_system_state = 'CharField'

class Trove(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='trove')
    flavor = 'TextField'
    is_top_level = 'BooleanField'
    last_available_update_refresh = 'DateTimeUtcField'
    name = 'TextField'
    out_of_date = 'NullBooleanField'
    trove_id = 'AutoField'
    version = 'Version'

class SystemJob(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='__systemjob')
    event_uuid = 'CharField'
    job = 'Job'
    system = 'System'
    system_job_id = 'AutoField'

class Stage(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='stage')
    label = 'TextField'
    major_version = 'Versions'
    name = 'CharField'
    stage_id = 'AutoField'

class Configuration(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='configuration',attributes={'id':str})

class Credentials(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='credentials',attributes={'id':str},elements=['ssl_client_certificate', 'ssl_client_key'])

class JobSystem(object):
    """
    """
    __metaclass__ = SDKClassMeta
    id = 'AutoField'
    job = 'Jobs'
    system_id = 'IntegerField'

class Job(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='job',attributes={'id':str})
    event_type = 'InlinedForeignKey'
    job_id = 'AutoField'
    job_state = 'InlinedDeferredForeignKey'
    job_uuid = 'CharField'
    status_code = 'IntegerField'
    status_detail = 'TextField'
    status_text = 'TextField'
    time_created = 'DateTimeUtcField'
    time_updated = 'DateTimeUtcField'

class ManagementInterface(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='management_interface',attributes={'id':str})
    created_date = 'DateTimeUtcField'
    credentials_descriptor = 'XMLField'
    credentials_readonly = 'NullBooleanField'
    description = 'CharField'
    management_interface_id = 'AutoField'
    name = 'CharField'
    port = 'IntegerField'

class EventType(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='event_type')
    description = 'CharField'
    event_type_id = 'AutoField'
    name = 'CharField'
    priority = 'SmallIntegerField'

class SystemEvent(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_event',attributes={'id':str})
    event_data = 'TextField'
    event_type = 'EventType'
    priority = 'SmallIntegerField'
    system = 'System'
    system_event_id = 'AutoField'
    time_created = 'DateTimeUtcField'
    time_enabled = 'DateTimeUtcField'

class ErrorResponse(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='fault')
    code = 'TextField'
    message = 'TextField'
    product_code = 'TextField'
    traceback = 'TextField'

class Pk(object):
    """
    """
    __metaclass__ = SDKClassMeta

class SystemLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system = 'System'
    system_log_id = 'AutoField'

class Inventory(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='inventory')
    event_types = 'HrefField'
    image_import_metadata_descriptor = 'HrefField'
    infrastructure_systems = 'HrefField'
    inventory_systems = 'HrefField'
    job_states = 'HrefField'
    log = 'HrefField'
    management_interfaces = 'HrefField'
    management_nodes = 'HrefField'
    networks = 'HrefField'
    system_states = 'HrefField'
    system_types = 'HrefField'
    systems = 'HrefField'
    zones = 'HrefField'

class Version(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='version')
    flavor = 'TextField'
    full = 'TextField'
    label = 'TextField'
    ordering = 'TextField'
    revision = 'TextField'
    version_id = 'AutoField'

class ManagementNode(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='management_node',attributes={'id':str},elements=['networks'])
    agent_port = 'IntegerField'
    appliance = 'Products'
    configuration = 'TextField'
    created_date = 'DateTimeUtcField'
    credentials = 'TextField'
    current_state = 'SystemState'
    description = 'CharField'
    generated_uuid = 'CharField'
    hostname = 'CharField'
    launch_date = 'DateTimeUtcField'
    launching_user = 'Users'
    local = 'NullBooleanField'
    local_uuid = 'CharField'
    major_version = 'Versions'
    management_interface = 'ManagementInterface'
    managing_zone = 'Zone'
    name = 'CharField'
    node_jid = 'CharField'
    registration_date = 'DateTimeUtcField'
    ssl_client_certificate = 'CharField'
    ssl_client_key = 'CharField'
    ssl_server_certificate = 'CharField'
    stage = 'Stage'
    state_change_date = 'DateTimeUtcField'
    system_id = 'AutoField'
    system_ptr = 'OneToOneField'
    system_type = 'SystemType'
    target = 'Targets'
    target_system_description = 'CharField'
    target_system_id = 'CharField'
    target_system_name = 'CharField'
    target_system_state = 'CharField'
    zone = 'Zone'

class SystemState(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(attributes={'id':str})
    created_date = 'DateTimeUtcField'
    description = 'CharField'
    name = 'CharField'
    system_state_id = 'AutoField'

class Cache(object):
    """
    """
    __metaclass__ = SDKClassMeta

class ConfigurationDescriptor(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='configuration_descriptor',attributes={'id':str})

class Zone(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='zone',attributes={'id':str})
    created_date = 'DateTimeUtcField'
    description = 'CharField'
    name = 'CharField'
    zone_id = 'AutoField'

class Network(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='network',attributes={'id':str})
    active = 'NullBooleanField'
    created_date = 'DateTimeUtcField'
    device_name = 'CharField'
    dns_name = 'CharField'
    ip_address = 'CharField'
    ipv6_address = 'CharField'
    netmask = 'CharField'
    network_id = 'AutoField'
    port_type = 'CharField'
    required = 'NullBooleanField'
    system = 'System'

class SystemJobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    job = ['Job']
    _xobj = XObjMetadata(tag='system_jobs')

class SystemTypes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_type = ['SystemType']
    _xobj = XObjMetadata(tag='system_types',elements=['system_type'])

class SystemEvents(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_event = ['SystemEvent']
    _xobj = XObjMetadata(tag='system_events')

class EventTypes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    event_type = ['EventType']
    _xobj = XObjMetadata(tag='event_types')

class Zones(object):
    """
    """
    __metaclass__ = SDKClassMeta
    zone = ['Zone']
    _xobj = XObjMetadata(tag='zones',elements=['zone'])

class Jobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    job = ['Job']
    _xobj = XObjMetadata(tag='jobs',attributes={'id':str},elements=['job'])

class InstalledSoftware(object):
    """
    """
    __metaclass__ = SDKClassMeta
    trove = ['Trove']
    _xobj = XObjMetadata(tag='installed_software',attributes={'id':str})

class SystemsLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_log_entry = ['SystemLogEntry']
    _xobj = XObjMetadata(tag='systems_log')

class ManagementInterfaces(object):
    """
    """
    __metaclass__ = SDKClassMeta
    management_interface = ['ManagementInterface']
    _xobj = XObjMetadata(tag='management_interfaces',elements=['management_interface'])

class SystemStates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system_state = ['SystemState']
    _xobj = XObjMetadata(tag='system_states')

class ManagementNodes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    management_node = ['ManagementNode']
    _xobj = XObjMetadata(tag='management_nodes')

class Networks(object):
    """
    """
    __metaclass__ = SDKClassMeta
    network = ['Network']
    _xobj = XObjMetadata(tag='networks',elements=['network', 'systems'])
    systems = 'HrefField'

class JobStates(object):
    """
    """
    __metaclass__ = SDKClassMeta
    job_state = ['JobState']
    _xobj = XObjMetadata(tag='job_states',elements=['job_state'])

class Systems(object):
    """
    """
    __metaclass__ = SDKClassMeta
    system = ['System']
    _xobj = XObjMetadata(tag='systems',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'