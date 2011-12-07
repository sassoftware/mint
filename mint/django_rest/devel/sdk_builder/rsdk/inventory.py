from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class SystemLogEntry(SDKModel):
    """ """

    system_log_entry_id = 'AutoField'
    system_log = 'SystemLog'
    entry_date = 'DateTimeUtcField'
    entry = 'CharField'
    _xobj = XObjMetadata(tag='system_log_entry')

@register
class Targets(SDKModel):
    """ """

    targettype = 'CharField'
    targetname = 'CharField'
    targetid = 'IntegerField'

@register
class SystemTargetCredentials(SDKModel):
    """ """

    system = 'System'
    id = 'AutoField'
    credentials = 'rbuilder.TargetCredentials'

@register
class SystemType(SDKModel):
    """ """

    system_type_id = 'AutoField'
    name = 'CharField'
    infrastructure = 'BooleanField'
    description = 'CharField'
    creation_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='system_type')

@register
class JobState(SDKModel):
    """ """

    name = 'CharField'
    job_state_id = 'AutoField'
    _xobj = XObjMetadata(tag='job_state')

@register
class System(SDKModel):
    """ """

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
    _xobj = XObjMetadata(tag='system',elements=['networks'])

@register
class Trove(SDKModel):
    """ """

    version = 'Version'
    trove_id = 'AutoField'
    out_of_date = 'NullBooleanField'
    name = 'TextField'
    last_available_update_refresh = 'DateTimeUtcField'
    is_top_level = 'BooleanField'
    flavor = 'TextField'
    _xobj = XObjMetadata(tag='trove')

@register
class SystemJob(SDKModel):
    """ """

    system_job_id = 'AutoField'
    system = 'System'
    job = 'Job'
    event_uuid = 'CharField'
    _xobj = XObjMetadata(tag='__systemjob')

@register
class Stage(SDKModel):
    """ """

    stage_id = 'AutoField'
    name = 'CharField'
    major_version = 'rbuilder.Versions'
    label = 'TextField'
    _xobj = XObjMetadata(tag='stage')

@register
class Configuration(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='configuration')

@register
class Credentials(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='credentials',elements=['ssl_client_certificate', 'ssl_client_key'])

@register
class JobSystem(SDKModel):
    """ """

    system_id = 'IntegerField'
    job = 'Jobs'
    id = 'AutoField'

@register
class Job(SDKModel):
    """ """

    time_updated = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    status_text = 'TextField'
    status_detail = 'TextField'
    status_code = 'IntegerField'
    job_uuid = 'CharField'
    job_state = 'InlinedDeferredForeignKey'
    job_id = 'AutoField'
    event_type = 'InlinedForeignKey'
    _xobj = XObjMetadata(tag='job')

@register
class ManagementInterface(SDKModel):
    """ """

    port = 'IntegerField'
    name = 'CharField'
    management_interface_id = 'AutoField'
    description = 'CharField'
    credentials_readonly = 'NullBooleanField'
    credentials_descriptor = 'XMLField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='management_interface')

@register
class EventType(SDKModel):
    """ """

    priority = 'SmallIntegerField'
    name = 'CharField'
    event_type_id = 'AutoField'
    description = 'CharField'
    _xobj = XObjMetadata(tag='event_type')

@register
class SystemEvent(SDKModel):
    """ """

    time_enabled = 'DateTimeUtcField'
    time_created = 'DateTimeUtcField'
    system_event_id = 'AutoField'
    system = 'System'
    priority = 'SmallIntegerField'
    event_type = 'EventType'
    event_data = 'TextField'
    _xobj = XObjMetadata(tag='system_event')

@register
class ErrorResponse(SDKModel):
    """ """

    traceback = 'TextField'
    product_code = 'TextField'
    message = 'TextField'
    code = 'TextField'
    _xobj = XObjMetadata(tag='fault')

@register
class Pk(SDKModel):
    """ """


@register
class SystemLog(SDKModel):
    """ """

    system_log_id = 'AutoField'
    system = 'System'

@register
class Inventory(SDKModel):
    """ """

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
class Version(SDKModel):
    """ """

    version_id = 'AutoField'
    revision = 'TextField'
    ordering = 'TextField'
    label = 'TextField'
    full = 'TextField'
    flavor = 'TextField'
    _xobj = XObjMetadata(tag='version')

@register
class ManagementNode(SDKModel):
    """ """

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
    _xobj = XObjMetadata(tag='management_node',elements=['networks'])

@register
class SystemState(SDKModel):
    """ """

    system_state_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'

@register
class Cache(SDKModel):
    """ """


@register
class ConfigurationDescriptor(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='configuration_descriptor')

@register
class Zone(SDKModel):
    """ """

    zone_id = 'AutoField'
    name = 'CharField'
    description = 'CharField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='zone')

@register
class Network(SDKModel):
    """ """

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
    _xobj = XObjMetadata(tag='network')

@register
class SystemJobs(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='system_jobs')
    job = ['Job']

@register
class SystemTypes(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='system_types',elements=['system_type'])
    system_type = ['SystemType']

@register
class SystemEvents(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='system_events')
    system_event = ['SystemEvent']

@register
class EventTypes(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='event_types')
    event_type = ['EventType']

@register
class Zones(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='zones',elements=['zone'])
    zone = ['Zone']

@register
class Jobs(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='jobs',elements=['job'])
    job = ['Job']

@register
class InstalledSoftware(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='installed_software')
    trove = ['Trove']

@register
class SystemsLog(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='systems_log')
    system_log_entry = ['SystemLogEntry']

@register
class ManagementInterfaces(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='management_interfaces',elements=['management_interface'])
    management_interface = ['ManagementInterface']

@register
class SystemStates(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='system_states')
    system_state = ['SystemState']

@register
class ManagementNodes(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='management_nodes')
    management_node = ['ManagementNode']

@register
class Networks(SDKModel):
    """ """

    systems = 'HrefField'
    _xobj = XObjMetadata(tag='networks',elements=['network', 'systems'])
    network = ['Network']

@register
class JobStates(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='job_states',elements=['job_state'])
    job_state = ['JobState']

@register
class Systems(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='systems')
    system = ['System']

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

