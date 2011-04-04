#  pyflakes=ignore
from fields import *  # pyflakes=ignore
from xobj import xobj

class Network(xobj.XObj):
    """XObj Class Stub"""
    ipv6_address = CharField
    network_id = AutoField
    dns_name = CharField
    required = NullBooleanField
    system = ForeignKey
    device_name = CharField
    netmask = CharField
    port_type = CharField
    created_date = DateTimeUtcField
    active = NullBooleanField
    ip_address = CharField

class Zone(xobj.XObj):
    """XObj Class Stub"""
    zone_id = AutoField
    description = CharField
    created_date = DateTimeUtcField
    name = CharField

class SystemJobs(xobj.XObj):
    """XObj Class Stub"""
    job = [Job]

class ConfigurationDescriptor(xobj.XObj):
    """XObj Class Stub"""

class Cache(xobj.XObj):
    """XObj Class Stub"""

class SystemState(xobj.XObj):
    """XObj Class Stub"""
    description = CharField
    system_state_id = AutoField
    created_date = DateTimeUtcField
    name = CharField

class ManagementNode(xobj.XObj):
    """XObj Class Stub"""
    management_interface = ForeignKey
    appliance = ForeignKey
    ssl_client_key = CharField
    system_type = ForeignKey
    generated_uuid = CharField
    ssl_server_certificate = CharField
    managing_zone = ForeignKey
    hostname = CharField
    system_id = AutoField
    launching_user = ForeignKey
    state_change_date = DateTimeUtcField
    launch_date = DateTimeUtcField
    local = NullBooleanField
    registration_date = DateTimeUtcField
    description = CharField
    ssl_client_certificate = CharField
    target_system_id = CharField
    target_system_name = CharField
    zone = ForeignKey
    credentials = TextField
    configuration = TextField
    node_jid = CharField
    agent_port = IntegerField
    stage = ForeignKey
    name = CharField
    system_ptr = OneToOneField
    local_uuid = CharField
    target_system_state = CharField
    major_version = ForeignKey
    current_state = SerializedForeignKey
    target = ForeignKey
    target_system_description = CharField
    created_date = DateTimeUtcField

class SystemTypes(xobj.XObj):
    """XObj Class Stub"""
    systemtype = [SystemType]

class Version(xobj.XObj):
    """XObj Class Stub"""
    full = TextField
    ordering = TextField
    flavor = TextField
    revision = TextField
    version_id = AutoField
    label = TextField

class SystemEvents(xobj.XObj):
    """XObj Class Stub"""
    systemevent = [SystemEvent]

class Inventory(xobj.XObj):
    """XObj Class Stub"""
    system_states = HrefField
    inventory_systems = HrefField
    log = HrefField
    management_nodes = HrefField
    infrastructure_systems = HrefField
    image_import_metadata_descriptor = HrefField
    zones = HrefField
    job_states = HrefField
    systems = HrefField
    management_interfaces = HrefField
    event_types = HrefField
    networks = HrefField
    system_types = HrefField

class SystemLog(xobj.XObj):
    """XObj Class Stub"""
    system_log_id = AutoField
    system = DeferredForeignKey

class EventTypes(xobj.XObj):
    """XObj Class Stub"""
    eventtype = [EventType]

class Pk(xobj.XObj):
    """XObj Class Stub"""

class ErrorResponse(xobj.XObj):
    """XObj Class Stub"""
    code = TextField
    traceback = TextField
    message = TextField
    product_code = TextField

class SystemEvent(xobj.XObj):
    """XObj Class Stub"""
    priority = SmallIntegerField
    event_type = DeferredForeignKey
    event_data = TextField
    time_enabled = DateTimeUtcField
    system = DeferredForeignKey
    time_created = DateTimeUtcField
    system_event_id = AutoField

class Zones(xobj.XObj):
    """XObj Class Stub"""
    zone = [Zone]

class Jobs(xobj.XObj):
    """XObj Class Stub"""
    job = [Job]

class InstalledSoftware(xobj.XObj):
    """XObj Class Stub"""
    trove = [Trove]

class EventType(xobj.XObj):
    """XObj Class Stub"""
    name = CharField
    priority = SmallIntegerField
    event_type_id = AutoField
    description = CharField

class ManagementInterface(xobj.XObj):
    """XObj Class Stub"""
    credentials_descriptor = XMLField
    name = CharField
    created_date = DateTimeUtcField
    management_interface_id = AutoField
    description = CharField
    port = IntegerField
    credentials_readonly = NullBooleanField

class Job(xobj.XObj):
    """XObj Class Stub"""
    time_updated = DateTimeUtcField
    job_id = AutoField
    status_code = IntegerField
    job_state = InlinedDeferredForeignKey
    time_created = DateTimeUtcField
    status_detail = TextField
    status_text = TextField
    job_uuid = CharField
    event_type = InlinedForeignKey

class JobSystem(xobj.XObj):
    """XObj Class Stub"""
    job = ForeignKey
    system_id = IntegerField
    id = AutoField

class Credentials(xobj.XObj):
    """XObj Class Stub"""

class Configuration(xobj.XObj):
    """XObj Class Stub"""

class Stage(xobj.XObj):
    """XObj Class Stub"""
    stage_id = AutoField
    name = CharField
    major_version = ForeignKey
    label = TextField

class SystemJob(xobj.XObj):
    """XObj Class Stub"""
    system_job_id = AutoField
    system = ForeignKey
    job = DeferredForeignKey
    event_uuid = CharField

class Trove(xobj.XObj):
    """XObj Class Stub"""
    version = SerializedForeignKey
    name = TextField
    is_top_level = BooleanField
    flavor = TextField
    trove_id = AutoField
    last_available_update_refresh = DateTimeUtcField

class System(xobj.XObj):
    """XObj Class Stub"""
    management_interface = ForeignKey
    registration_date = DateTimeUtcField
    description = CharField
    appliance = ForeignKey
    ssl_client_certificate = CharField
    target_system_id = CharField
    ssl_client_key = CharField
    target_system_name = CharField
    major_version = ForeignKey
    system_type = ForeignKey
    credentials = TextField
    generated_uuid = CharField
    configuration = TextField
    agent_port = IntegerField
    stage = ForeignKey
    name = CharField
    ssl_server_certificate = CharField
    local_uuid = CharField
    managing_zone = ForeignKey
    hostname = CharField
    current_state = SerializedForeignKey
    target_system_state = CharField
    system_id = AutoField
    launching_user = ForeignKey
    target = ForeignKey
    state_change_date = DateTimeUtcField
    launch_date = DateTimeUtcField
    target_system_description = CharField
    created_date = DateTimeUtcField

class SystemsLog(xobj.XObj):
    """XObj Class Stub"""
    systemlogentry = [SystemLogEntry]

class JobState(xobj.XObj):
    """XObj Class Stub"""
    job_state_id = AutoField
    name = CharField

class ManagementInterfaces(xobj.XObj):
    """XObj Class Stub"""
    managementinterface = [ManagementInterface]

class SystemType(xobj.XObj):
    """XObj Class Stub"""
    infrastructure = BooleanField
    description = CharField
    created_date = DateTimeUtcField
    system_type_id = AutoField
    creation_descriptor = XMLField
    name = CharField

class SystemStates(xobj.XObj):
    """XObj Class Stub"""
    systemstate = [SystemState]

class SystemTargetCredentials(xobj.XObj):
    """XObj Class Stub"""
    credentials = ForeignKey
    id = AutoField
    system = ForeignKey

class Targets(xobj.XObj):
    """XObj Class Stub"""
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class ManagementNodes(xobj.XObj):
    """XObj Class Stub"""
    managementnode = [ManagementNode]

class SystemLogEntry(xobj.XObj):
    """XObj Class Stub"""
    system_log_entry_id = AutoField
    system_log = ForeignKey
    entry_date = DateTimeUtcField
    entry = CharField

class Networks(xobj.XObj):
    """XObj Class Stub"""
    systems = HrefField
    network = [Network]

class JobStates(xobj.XObj):
    """XObj Class Stub"""
    jobstate = [JobState]

class Systems(xobj.XObj):
    """XObj Class Stub"""
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    system = [System]
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

