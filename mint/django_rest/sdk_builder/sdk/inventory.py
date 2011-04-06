from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class SystemLogEntry(XObj, XObjMixin):
    """
    """
    system_log_entry_id = AutoField
    _xobj = XObjMetadata
    system_log = ForeignKey
    entry_date = DateTimeUtcField
    entry = CharField

class Targets(XObj, XObjMixin):
    """
    """
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class SystemTargetCredentials(XObj, XObjMixin):
    """
    """
    credentials = ForeignKey
    id = AutoField
    system = ForeignKey

class SystemType(XObj, XObjMixin):
    """
    """
    infrastructure = BooleanField
    description = CharField
    created_date = DateTimeUtcField
    system_type_id = AutoField
    _xobj = XObjMetadata
    creation_descriptor = XMLField
    name = CharField

class JobState(XObj, XObjMixin):
    """
    """
    job_state_id = AutoField
    name = CharField
    _xobj = XObjMetadata

class System(XObj, XObjMixin):
    """
    """
    management_interface = ForeignKey
    registration_date = DateTimeUtcField
    description = CharField
    _xobj = XObjMetadata
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
    appliance = ForeignKey
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

class Trove(XObj, XObjMixin):
    """
    """
    version = SerializedForeignKey
    name = TextField
    is_top_level = BooleanField
    _xobj = XObjMetadata
    flavor = TextField
    trove_id = AutoField
    last_available_update_refresh = DateTimeUtcField

class SystemJob(XObj, XObjMixin):
    """
    """
    system_job_id = AutoField
    _xobj = XObjMetadata
    system = ForeignKey
    job = DeferredForeignKey
    event_uuid = CharField

class Stage(XObj, XObjMixin):
    """
    """
    stage_id = AutoField
    name = CharField
    _xobj = XObjMetadata
    major_version = ForeignKey
    label = TextField

class Configuration(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class Credentials(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class JobSystem(XObj, XObjMixin):
    """
    """
    job = ForeignKey
    system_id = IntegerField
    id = AutoField

class Job(XObj, XObjMixin):
    """
    """
    time_updated = DateTimeUtcField
    job_id = AutoField
    status_code = IntegerField
    job_state = InlinedDeferredForeignKey
    time_created = DateTimeUtcField
    status_detail = TextField
    _xobj = XObjMetadata
    status_text = TextField
    job_uuid = CharField
    event_type = InlinedForeignKey

class ManagementInterface(XObj, XObjMixin):
    """
    """
    name = CharField
    management_interface_id = AutoField
    _xobj = XObjMetadata
    credentials_readonly = NullBooleanField
    created_date = DateTimeUtcField
    credentials_descriptor = XMLField
    port = IntegerField
    description = CharField

class EventType(XObj, XObjMixin):
    """
    """
    name = CharField
    _xobj = XObjMetadata
    priority = SmallIntegerField
    event_type_id = AutoField
    description = CharField

class SystemEvent(XObj, XObjMixin):
    """
    """
    event_type = DeferredForeignKey
    _xobj = XObjMetadata
    system = DeferredForeignKey
    time_created = DateTimeUtcField
    event_data = TextField
    priority = SmallIntegerField
    time_enabled = DateTimeUtcField
    system_event_id = AutoField

class ErrorResponse(XObj, XObjMixin):
    """
    """
    code = TextField
    _xobj = XObjMetadata
    traceback = TextField
    message = TextField
    product_code = TextField

class Pk(XObj, XObjMixin):
    """
    """

class SystemLog(XObj, XObjMixin):
    """
    """
    system_log_id = AutoField
    system = DeferredForeignKey

class Inventory(XObj, XObjMixin):
    """
    """
    system_states = HrefField
    inventory_systems = HrefField
    log = HrefField
    _xobj = XObjMetadata
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

class Version(XObj, XObjMixin):
    """
    """
    full = TextField
    ordering = TextField
    _xobj = XObjMetadata
    flavor = TextField
    revision = TextField
    version_id = AutoField
    label = TextField

class ManagementNode(XObj, XObjMixin):
    """
    """
    management_interface = ForeignKey
    _xobj = XObjMetadata
    ssl_client_key = CharField
    system_type = ForeignKey
    generated_uuid = CharField
    ssl_server_certificate = CharField
    managing_zone = ForeignKey
    appliance = ForeignKey
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

class SystemState(XObj, XObjMixin):
    """
    """
    description = CharField
    _xobj = XObjMetadata
    system_state_id = AutoField
    created_date = DateTimeUtcField
    name = CharField

class Cache(XObj, XObjMixin):
    """
    """

class ConfigurationDescriptor(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class Zone(XObj, XObjMixin):
    """
    """
    zone_id = AutoField
    _xobj = XObjMetadata
    description = CharField
    created_date = DateTimeUtcField
    name = CharField

class Network(XObj, XObjMixin):
    """
    """
    ipv6_address = CharField
    network_id = AutoField
    dns_name = CharField
    required = NullBooleanField
    system = ForeignKey
    device_name = CharField
    netmask = CharField
    port_type = CharField
    _xobj = XObjMetadata
    active = NullBooleanField
    ip_address = CharField
    created_date = DateTimeUtcField

class SystemJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    Job = [Job]

class SystemTypes(XObj, XObjMixin):
    """
    """
    SystemType = [SystemType]
    _xobj = XObjMetadata

class SystemEvents(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    SystemEvent = [SystemEvent]

class EventTypes(XObj, XObjMixin):
    """
    """
    EventType = [EventType]
    _xobj = XObjMetadata

class Zones(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    Zone = [Zone]

class Jobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    Job = [Job]

class InstalledSoftware(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    Trove = [Trove]

class SystemsLog(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    SystemLogEntry = [SystemLogEntry]

class ManagementInterfaces(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    ManagementInterface = [ManagementInterface]

class SystemStates(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    SystemState = [SystemState]

class ManagementNodes(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    ManagementNode = [ManagementNode]

class Networks(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    systems = HrefField
    Network = [Network]

class JobStates(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    JobState = [JobState]

class Systems(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    System = [System]
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

