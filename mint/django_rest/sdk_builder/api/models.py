class Network(xobj.XObj):
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
    zone_id = AutoField
    description = CharField
    created_date = DateTimeUtcField
    name = CharField

class SystemState(xobj.XObj):
    description = CharField
    system_state_id = AutoField
    created_date = DateTimeUtcField
    name = CharField

class ManagementNode(xobj.XObj):
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

class Version(xobj.XObj):
    full = TextField
    ordering = TextField
    flavor = TextField
    revision = TextField
    version_id = AutoField
    label = TextField

class Inventory(xobj.XObj):
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
    system_log_id = AutoField
    system = DeferredForeignKey

class ErrorResponse(xobj.XObj):
    code = TextField
    traceback = TextField
    message = TextField
    product_code = TextField

class SystemEvent(xobj.XObj):
    priority = SmallIntegerField
    event_type = DeferredForeignKey
    event_data = TextField
    time_enabled = DateTimeUtcField
    system = DeferredForeignKey
    time_created = DateTimeUtcField
    system_event_id = AutoField

class EventType(xobj.XObj):
    name = CharField
    priority = SmallIntegerField
    event_type_id = AutoField
    description = CharField

class ManagementInterface(xobj.XObj):
    credentials_descriptor = XMLField
    name = CharField
    created_date = DateTimeUtcField
    management_interface_id = AutoField
    description = CharField
    port = IntegerField
    credentials_readonly = NullBooleanField

class Job(xobj.XObj):
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
    job = ForeignKey
    system_id = IntegerField
    id = AutoField

class Stage(xobj.XObj):
    stage_id = AutoField
    name = CharField
    major_version = ForeignKey
    label = TextField

class SystemJob(xobj.XObj):
    system_job_id = AutoField
    system = ForeignKey
    job = DeferredForeignKey
    event_uuid = CharField

class Trove(xobj.XObj):
    version = SerializedForeignKey
    name = TextField
    is_top_level = BooleanField
    flavor = TextField
    trove_id = AutoField
    last_available_update_refresh = DateTimeUtcField

class System(xobj.XObj):
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

class JobState(xobj.XObj):
    job_state_id = AutoField
    name = CharField

class SystemType(xobj.XObj):
    infrastructure = BooleanField
    description = CharField
    created_date = DateTimeUtcField
    system_type_id = AutoField
    creation_descriptor = XMLField
    name = CharField

class SystemTargetCredentials(xobj.XObj):
    credentials = ForeignKey
    id = AutoField
    system = ForeignKey

class Targets(xobj.XObj):
    targettype = CharField
    targetname = CharField
    targetid = IntegerField

class SystemLogEntry(xobj.XObj):
    system_log_entry_id = AutoField
    system_log = ForeignKey
    entry_date = DateTimeUtcField
    entry = CharField

class Networks(xobj.XObj):
    systems = HrefField
    network = [Network]

class Systems(xobj.XObj):
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

