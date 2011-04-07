from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from xobj.xobj import XObj


class SystemLogEntry(XObj, XObjMixin):
    """
    """
    system_log_entry_id = AutoField
    system_log = ForeignKey
    entry_date = DateTimeUtcField
    entry = CharField
    _xobj = XObjMetadata

class Targets(XObj, XObjMixin):
    """
    """
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class SystemTargetCredentials(XObj, XObjMixin):
    """
    """
    system = ForeignKey
    id = AutoField
    credentials = ForeignKey

class SystemType(XObj, XObjMixin):
    """
    """
    system_type_id = AutoField
    name = CharField
    infrastructure = BooleanField
    description = CharField
    creation_descriptor = XMLField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class JobState(XObj, XObjMixin):
    """
    """
    name = CharField
    job_state_id = AutoField
    _xobj = XObjMetadata

class System(XObj, XObjMixin):
    """
    """
    target_system_state = CharField
    target_system_name = CharField
    target_system_id = CharField
    target_system_description = CharField
    target = ForeignKey
    system_type = ForeignKey
    system_id = AutoField
    state_change_date = DateTimeUtcField
    stage = ForeignKey
    ssl_server_certificate = CharField
    ssl_client_key = CharField
    ssl_client_certificate = CharField
    registration_date = DateTimeUtcField
    name = CharField
    managing_zone = ForeignKey
    management_interface = ForeignKey
    major_version = ForeignKey
    local_uuid = CharField
    launching_user = ForeignKey
    launch_date = DateTimeUtcField
    hostname = CharField
    generated_uuid = CharField
    description = CharField
    current_state = SerializedForeignKey
    credentials = TextField
    created_date = DateTimeUtcField
    configuration = TextField
    appliance = ForeignKey
    agent_port = IntegerField
    _xobj = XObjMetadata

class Trove(XObj, XObjMixin):
    """
    """
    version = SerializedForeignKey
    trove_id = AutoField
    name = TextField
    last_available_update_refresh = DateTimeUtcField
    is_top_level = BooleanField
    flavor = TextField
    _xobj = XObjMetadata

class SystemJob(XObj, XObjMixin):
    """
    """
    system_job_id = AutoField
    system = ForeignKey
    job = DeferredForeignKey
    event_uuid = CharField
    _xobj = XObjMetadata

class Stage(XObj, XObjMixin):
    """
    """
    stage_id = AutoField
    name = CharField
    major_version = ForeignKey
    label = TextField
    _xobj = XObjMetadata

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
    system_id = IntegerField
    job = ForeignKey
    id = AutoField

class Job(XObj, XObjMixin):
    """
    """
    time_updated = DateTimeUtcField
    time_created = DateTimeUtcField
    status_text = TextField
    status_detail = TextField
    status_code = IntegerField
    job_uuid = CharField
    job_state = InlinedDeferredForeignKey
    job_id = AutoField
    event_type = InlinedForeignKey
    _xobj = XObjMetadata

class ManagementInterface(XObj, XObjMixin):
    """
    """
    port = IntegerField
    name = CharField
    management_interface_id = AutoField
    description = CharField
    credentials_readonly = NullBooleanField
    credentials_descriptor = XMLField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class EventType(XObj, XObjMixin):
    """
    """
    priority = SmallIntegerField
    name = CharField
    event_type_id = AutoField
    description = CharField
    _xobj = XObjMetadata

class SystemEvent(XObj, XObjMixin):
    """
    """
    time_enabled = DateTimeUtcField
    time_created = DateTimeUtcField
    system_event_id = AutoField
    system = DeferredForeignKey
    priority = SmallIntegerField
    event_type = DeferredForeignKey
    event_data = TextField
    _xobj = XObjMetadata

class ErrorResponse(XObj, XObjMixin):
    """
    """
    traceback = TextField
    product_code = TextField
    message = TextField
    code = TextField
    _xobj = XObjMetadata

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
    zones = HrefField
    systems = HrefField
    system_types = HrefField
    system_states = HrefField
    networks = HrefField
    management_nodes = HrefField
    management_interfaces = HrefField
    log = HrefField
    job_states = HrefField
    inventory_systems = HrefField
    infrastructure_systems = HrefField
    image_import_metadata_descriptor = HrefField
    event_types = HrefField
    _xobj = XObjMetadata

class Version(XObj, XObjMixin):
    """
    """
    version_id = AutoField
    revision = TextField
    ordering = TextField
    label = TextField
    full = TextField
    flavor = TextField
    _xobj = XObjMetadata

class ManagementNode(XObj, XObjMixin):
    """
    """
    zone = ForeignKey
    target_system_state = CharField
    target_system_name = CharField
    target_system_id = CharField
    target_system_description = CharField
    target = ForeignKey
    system_type = ForeignKey
    system_ptr = OneToOneField
    system_id = AutoField
    state_change_date = DateTimeUtcField
    stage = ForeignKey
    ssl_server_certificate = CharField
    ssl_client_key = CharField
    ssl_client_certificate = CharField
    registration_date = DateTimeUtcField
    node_jid = CharField
    name = CharField
    managing_zone = ForeignKey
    management_interface = ForeignKey
    major_version = ForeignKey
    local_uuid = CharField
    local = NullBooleanField
    launching_user = ForeignKey
    launch_date = DateTimeUtcField
    hostname = CharField
    generated_uuid = CharField
    description = CharField
    current_state = SerializedForeignKey
    credentials = TextField
    created_date = DateTimeUtcField
    configuration = TextField
    appliance = ForeignKey
    agent_port = IntegerField
    _xobj = XObjMetadata

class SystemState(XObj, XObjMixin):
    """
    """
    system_state_id = AutoField
    name = CharField
    description = CharField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

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
    name = CharField
    description = CharField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class Network(XObj, XObjMixin):
    """
    """
    system = ForeignKey
    required = NullBooleanField
    port_type = CharField
    network_id = AutoField
    netmask = CharField
    ipv6_address = CharField
    ip_address = CharField
    dns_name = CharField
    device_name = CharField
    created_date = DateTimeUtcField
    active = NullBooleanField
    _xobj = XObjMetadata

class SystemJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    job = [Job]

class SystemTypes(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    system_type = [SystemType]

class SystemEvents(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    system_event = [SystemEvent]

class EventTypes(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    event_type = [EventType]

class Zones(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    zone = [Zone]

class Jobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    job = [Job]

class InstalledSoftware(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    trove = [Trove]

class SystemsLog(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    system_log_entry = [SystemLogEntry]

class ManagementInterfaces(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    management_interface = [ManagementInterface]

class SystemStates(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    system_state = [SystemState]

class ManagementNodes(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    management_node = [ManagementNode]

class Networks(XObj, XObjMixin):
    """
    """
    systems = HrefField
    _xobj = XObjMetadata
    network = [Network]

class JobStates(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    job_state = [JobState]

class Systems(XObj, XObjMixin):
    """
    """
    start_index = IntegerField
    previous_page = TextField
    per_page = IntegerField
    order_by = TextField
    num_pages = IntegerField
    next_page = TextField
    limit = TextField
    full_collection = TextField
    filter_by = TextField
    end_index = IntegerField
    count = IntegerField
    _xobj = XObjMetadata
    system = [System]

