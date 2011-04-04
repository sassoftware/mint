from sdk import Fields
from sdk import XObjMixin
from sdk import GetSetXMLAttrMeta
from xobj import xobj


class changelog(object):
    """changelog"""

    class ChangeLog(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        change_log_id = Fields.AutoField
        resource_type = Fields.TextField
        resource_id = Fields.IntegerField
    
    class ChangeLogs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        changelog = [ChangeLog]
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class ChangeLogEntry(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        change_log_entry_id = Fields.AutoField
        change_log = Fields.ForeignKey
        entry_date = Fields.DateTimeUtcField
        entry_text = Fields.TextField
    
    class ChangeLogEntry(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        change_log_entry_id = Fields.AutoField
        change_log = Fields.ForeignKey
        entry_date = Fields.DateTimeUtcField
        entry_text = Fields.TextField

class reporting(object):
    """reporting"""

    class SystemUpdate(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        updateuser = Fields.CharField
        _updatetime = Fields.DecimalField
        servername = Fields.CharField
        repositoryname = Fields.CharField
        _systemupdateid = Fields.AutoField
    
    class Reports(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class Report(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class RepositoryLogStatus(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        inode = Fields.IntegerField
        logname = Fields.CharField
        logoffset = Fields.IntegerField

class rbuilder(object):
    """rbuilder"""

    class TargetData(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        name = Fields.CharField
        targetid = Fields.ForeignKey
        value = Fields.TextField
        id = Fields.AutoField
    
    class Pk(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class TargetCredentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        credentials = Fields.TextField
        targetcredentialsid = Fields.AutoField
    
    class Jobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job_id = Fields.AutoField
        job_uuid = Fields.TextField
    
    class Users(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        username = Fields.CharField
        timecreated = Fields.DecimalField
        passwd = Fields.CharField
        userid = Fields.AutoField
        displayemail = Fields.TextField
        blurb = Fields.TextField
        active = Fields.SmallIntegerField
        fullname = Fields.CharField
        salt = Fields.TextField
        email = Fields.CharField
        timeaccessed = Fields.DecimalField
    
    class Releases(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        timemirrored = Fields.DecimalField
        description = Fields.TextField
        timecreated = Fields.DecimalField
        pubreleaseid = Fields.AutoField
        timepublished = Fields.DecimalField
        updatedby = Fields.ForeignKey
        name = Fields.CharField
        version = Fields.CharField
        shouldmirror = Fields.SmallIntegerField
        createdby = Fields.ForeignKey
        timeupdated = Fields.DecimalField
        publishedby = Fields.ForeignKey
        productid = Fields.ForeignKey
    
    class Sessions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        sessionid = Fields.AutoField
        data = Fields.TextField
        sid = Fields.CharField
    
    class Downloads(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        ip = Fields.CharField
        timedownloaded = Fields.CharField
        id = Fields.AutoField
        imageid = Fields.ForeignKey
    
    class Versions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        name = Fields.CharField
        timecreated = Fields.DecimalField
        productversionid = Fields.AutoField
        description = Fields.TextField
        namespace = Fields.CharField
        productid = Fields.ForeignKey
    
    class Members(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        level = Fields.SmallIntegerField
        userid = Fields.ForeignKey
        id = Fields.AutoField
        productid = Fields.ForeignKey
    
    class DatabaseVersion(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        version = Fields.SmallIntegerField
        id = Fields.AutoField
        minor = Fields.SmallIntegerField
    
    class TargetImagesDeployed(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targetid = Fields.ForeignKey
        id = Fields.AutoField
        targetimageid = Fields.CharField
        fileid = Fields.IntegerField
    
    class UserGroupMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        userid = Fields.ForeignKey
        id = Fields.AutoField
        usergroupid = Fields.ForeignKey
    
    class Fault(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        message = Fields.CharField
        code = Fields.IntegerField
        traceback = Fields.TextField
    
    class PkiCertificates(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        is_ca = Fields.BooleanField
        pkey_pem = Fields.TextField
        fingerprint = Fields.TextField
        time_expired = Fields.DateTimeUtcField
        ca_serial_index = Fields.IntegerField
        purpose = Fields.TextField
        x509_pem = Fields.TextField
        issuer_fingerprint = Fields.ForeignKey
        time_issued = Fields.DateTimeUtcField
    
    class Products(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        backupexternal = Fields.SmallIntegerField
        repositoryhostname = Fields.CharField
        domainname = Fields.CharField
        creatorid = Fields.ForeignKey
        hidden = Fields.SmallIntegerField
        description = Fields.TextField
        projecturl = Fields.CharField
        name = Fields.CharField
        timecreated = Fields.DecimalField
        hostname = Fields.CharField
        namespace = Fields.CharField
        commitemail = Fields.CharField
        prodtype = Fields.CharField
        shortname = Fields.CharField
        timemodified = Fields.DecimalField
        productid = Fields.AutoField
    
    class TargetUserCredentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targetid = Fields.ForeignKey
        userid = Fields.ForeignKey
        targetcredentialsid = Fields.ForeignKey
        id = Fields.AutoField
    
    class UserGroups(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        usergroupid = Fields.AutoField
        usergroup = Fields.CharField
    
    class Images(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        status = Fields.IntegerField
        buildtype = Fields.IntegerField
        description = Fields.TextField
        pubreleaseid = Fields.ForeignKey
        deleted = Fields.SmallIntegerField
        trovelastchanged = Fields.DecimalField
        imageid = Fields.AutoField
        timeupdated = Fields.DecimalField
        productversionid = Fields.ForeignKey
        statusmessage = Fields.TextField
        name = Fields.CharField
        stagename = Fields.CharField
        timecreated = Fields.DecimalField
        troveversion = Fields.CharField
        troveflavor = Fields.CharField
        trovename = Fields.CharField
        createdby = Fields.ForeignKey
        updatedby = Fields.ForeignKey
        buildcount = Fields.IntegerField
        productid = Fields.ForeignKey
    
    class Targets(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targettype = Fields.CharField
        targetname = Fields.CharField
        targetid = Fields.IntegerField

class metrics(object):
    """metrics"""

    class Metrics(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class Timer(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        total_cpu_time = Fields.TextField
        user_cpu_time = Fields.TextField
        context_switches = Fields.TextField
        elapsed_time = Fields.TextField
        system_cpu_time = Fields.TextField
    
    class ServerVersions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        debug_toolbar_version = Fields.TextField
        django_version = Fields.TextField

class inventory(object):
    """inventory"""

    class Network(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        ipv6_address = Fields.CharField
        network_id = Fields.AutoField
        dns_name = Fields.CharField
        required = Fields.NullBooleanField
        system = Fields.ForeignKey
        device_name = Fields.CharField
        netmask = Fields.CharField
        port_type = Fields.CharField
        created_date = Fields.DateTimeUtcField
        active = Fields.NullBooleanField
        ip_address = Fields.CharField
    
    class Zone(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        zone_id = Fields.AutoField
        description = Fields.CharField
        created_date = Fields.DateTimeUtcField
        name = Fields.CharField
    
    class SystemJobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job = [Job]
    
    class ConfigurationDescriptor(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class Cache(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class SystemState(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        description = Fields.CharField
        system_state_id = Fields.AutoField
        created_date = Fields.DateTimeUtcField
        name = Fields.CharField
    
    class ManagementNode(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        management_interface = Fields.ForeignKey
        appliance = Fields.ForeignKey
        ssl_client_key = Fields.CharField
        system_type = Fields.ForeignKey
        generated_uuid = Fields.CharField
        ssl_server_certificate = Fields.CharField
        managing_zone = Fields.ForeignKey
        hostname = Fields.CharField
        system_id = Fields.AutoField
        launching_user = Fields.ForeignKey
        state_change_date = Fields.DateTimeUtcField
        launch_date = Fields.DateTimeUtcField
        local = Fields.NullBooleanField
        registration_date = Fields.DateTimeUtcField
        description = Fields.CharField
        ssl_client_certificate = Fields.CharField
        target_system_id = Fields.CharField
        target_system_name = Fields.CharField
        zone = Fields.ForeignKey
        credentials = Fields.TextField
        configuration = Fields.TextField
        node_jid = Fields.CharField
        agent_port = Fields.IntegerField
        stage = Fields.ForeignKey
        name = Fields.CharField
        system_ptr = Fields.OneToOneField
        local_uuid = Fields.CharField
        target_system_state = Fields.CharField
        major_version = Fields.ForeignKey
        current_state = Fields.SerializedForeignKey
        target = Fields.ForeignKey
        target_system_description = Fields.CharField
        created_date = Fields.DateTimeUtcField
    
    class SystemTypes(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        systemtype = [SystemType]
    
    class Version(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        full = Fields.TextField
        ordering = Fields.TextField
        flavor = Fields.TextField
        revision = Fields.TextField
        version_id = Fields.AutoField
        label = Fields.TextField
    
    class SystemEvents(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        systemevent = [SystemEvent]
    
    class Inventory(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        system_states = Fields.HrefField
        inventory_systems = Fields.HrefField
        log = Fields.HrefField
        management_nodes = Fields.HrefField
        infrastructure_systems = Fields.HrefField
        image_import_metadata_descriptor = Fields.HrefField
        zones = Fields.HrefField
        job_states = Fields.HrefField
        systems = Fields.HrefField
        management_interfaces = Fields.HrefField
        event_types = Fields.HrefField
        networks = Fields.HrefField
        system_types = Fields.HrefField
    
    class SystemLog(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        system_log_id = Fields.AutoField
        system = Fields.DeferredForeignKey
    
    class EventTypes(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        eventtype = [EventType]
    
    class Pk(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class ErrorResponse(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        code = Fields.TextField
        traceback = Fields.TextField
        message = Fields.TextField
        product_code = Fields.TextField
    
    class SystemEvent(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        priority = Fields.SmallIntegerField
        event_type = Fields.DeferredForeignKey
        event_data = Fields.TextField
        time_enabled = Fields.DateTimeUtcField
        system = Fields.DeferredForeignKey
        time_created = Fields.DateTimeUtcField
        system_event_id = Fields.AutoField
    
    class Zones(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        zone = [Zone]
    
    class Jobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job = [Job]
    
    class InstalledSoftware(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        trove = [Trove]
    
    class EventType(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        name = Fields.CharField
        priority = Fields.SmallIntegerField
        event_type_id = Fields.AutoField
        description = Fields.CharField
    
    class ManagementInterface(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        credentials_descriptor = Fields.XMLField
        name = Fields.CharField
        created_date = Fields.DateTimeUtcField
        management_interface_id = Fields.AutoField
        description = Fields.CharField
        port = Fields.IntegerField
        credentials_readonly = Fields.NullBooleanField
    
    class Job(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        time_updated = Fields.DateTimeUtcField
        job_id = Fields.AutoField
        status_code = Fields.IntegerField
        job_state = Fields.InlinedDeferredForeignKey
        time_created = Fields.DateTimeUtcField
        status_detail = Fields.TextField
        status_text = Fields.TextField
        job_uuid = Fields.CharField
        event_type = Fields.InlinedForeignKey
    
    class JobSystem(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job = Fields.ForeignKey
        system_id = Fields.IntegerField
        id = Fields.AutoField
    
    class Credentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class Configuration(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class Stage(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        stage_id = Fields.AutoField
        name = Fields.CharField
        major_version = Fields.ForeignKey
        label = Fields.TextField
    
    class SystemJob(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        system_job_id = Fields.AutoField
        system = Fields.ForeignKey
        job = Fields.DeferredForeignKey
        event_uuid = Fields.CharField
    
    class Trove(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        version = Fields.SerializedForeignKey
        name = Fields.TextField
        is_top_level = Fields.BooleanField
        flavor = Fields.TextField
        trove_id = Fields.AutoField
        last_available_update_refresh = Fields.DateTimeUtcField
    
    class System(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        management_interface = Fields.ForeignKey
        registration_date = Fields.DateTimeUtcField
        description = Fields.CharField
        appliance = Fields.ForeignKey
        ssl_client_certificate = Fields.CharField
        target_system_id = Fields.CharField
        ssl_client_key = Fields.CharField
        target_system_name = Fields.CharField
        major_version = Fields.ForeignKey
        system_type = Fields.ForeignKey
        credentials = Fields.TextField
        generated_uuid = Fields.CharField
        configuration = Fields.TextField
        agent_port = Fields.IntegerField
        stage = Fields.ForeignKey
        name = Fields.CharField
        ssl_server_certificate = Fields.CharField
        local_uuid = Fields.CharField
        managing_zone = Fields.ForeignKey
        hostname = Fields.CharField
        current_state = Fields.SerializedForeignKey
        target_system_state = Fields.CharField
        system_id = Fields.AutoField
        launching_user = Fields.ForeignKey
        target = Fields.ForeignKey
        state_change_date = Fields.DateTimeUtcField
        launch_date = Fields.DateTimeUtcField
        target_system_description = Fields.CharField
        created_date = Fields.DateTimeUtcField
    
    class SystemsLog(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        systemlogentry = [SystemLogEntry]
    
    class JobState(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        job_state_id = Fields.AutoField
        name = Fields.CharField
    
    class ManagementInterfaces(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        managementinterface = [ManagementInterface]
    
    class SystemType(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        infrastructure = Fields.BooleanField
        description = Fields.CharField
        created_date = Fields.DateTimeUtcField
        system_type_id = Fields.AutoField
        creation_descriptor = Fields.XMLField
        name = Fields.CharField
    
    class SystemStates(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        systemstate = [SystemState]
    
    class SystemTargetCredentials(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        credentials = Fields.ForeignKey
        id = Fields.AutoField
        system = Fields.ForeignKey
    
    class Targets(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        targettype = Fields.CharField
        targetname = Fields.CharField
        targetid = Fields.IntegerField
    
    class ManagementNodes(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        managementnode = [ManagementNode]
    
    class SystemLogEntry(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        system_log_entry_id = Fields.AutoField
        system_log = Fields.ForeignKey
        entry_date = Fields.DateTimeUtcField
        entry = Fields.CharField
    
    class Networks(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        systems = Fields.HrefField
        network = [Network]
    
    class JobStates(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        jobstate = [JobState]
    
    class Systems(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        system = [System]
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        start_index = Fields.IntegerField

class querysets(object):
    """querysets"""

    class QuerySet(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        name = Fields.TextField
        can_modify = Fields.BooleanField
        created_date = Fields.DateTimeUtcField
        query_set_id = Fields.AutoField
        resource_type = Fields.TextField
        description = Fields.TextField
    
    class FilterEntry(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        value = Fields.TextField
        field = Fields.TextField
        filter_entry_id = Fields.AutoField
        operator = Fields.TextField
    
    class AllMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class QueryTag(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        query_tag_id = Fields.AutoField
        query_set = Fields.ForeignKey
        name = Fields.TextField
    
    class FilteredMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class InclusionMethod(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        inclusion_method_id = Fields.AutoField
        name = Fields.TextField
    
    class CollectionId(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class ChildMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class SystemTag(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        system_tag_id = Fields.AutoField
        system = Fields.ForeignKey
        inclusion_method = Fields.SerializedForeignKey
        query_tag = Fields.ForeignKey
    
    class ChosenMembers(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class FilterDescriptor(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class QuerySets(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        queryset = [QuerySet]
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        start_index = Fields.IntegerField

class packages(object):
    """packages"""

    class PackageVersions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        packageversion = [PackageVersion]
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class PackageBuildJobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        packagebuildjob = [PackageBuildJob]
    
    class PackageBuilds(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        packagebuild = [PackageBuild]
        start_index = Fields.IntegerField
    
    class JobData(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
    
    class PackageActionTypes(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        filter_by = Fields.TextField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        packageactiontype = [PackageActionType]
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        end_index = Fields.IntegerField
        start_index = Fields.IntegerField
    
    class PackageSource(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        built = Fields.BooleanField
        package_source_id = Fields.AutoField
        package_version = Fields.DeferredForeignKey
        trove = Fields.ForeignKey
        created_by = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
    
    class PackageBuildAction(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        visible = Fields.BooleanField
        enabled = Fields.BooleanField
        descriptor = Fields.TextField
        package_action_type = Fields.ForeignKey
        package_build = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
        package_build_action_id = Fields.AutoField
    
    class PackageSources(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        packagesource = [PackageSource]
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class PackageBuildJob(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        job_data = Fields.TextField
        created_by = Fields.ForeignKey
        job = Fields.ForeignKey
        package_action_type = Fields.ForeignKey
        package_build = Fields.DeferredForeignKey
        created_date = Fields.DateTimeUtcField
        package_build_job_id = Fields.AutoField
    
    class Packages(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        package = [Package]
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class PackageActionType(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        description = Fields.TextField
        package_action_type_id = Fields.AutoField
        created_date = Fields.DateTimeUtcField
        name = Fields.TextField
    
    class PackageVersionUrls(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        packageversionurl = [PackageVersionUrl]
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class PackageSourceAction(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        descriptor = Fields.TextField
        enabled = Fields.BooleanField
        package_source = Fields.ForeignKey
        visible = Fields.BooleanField
        package_action_type = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
        package_source_action_id = Fields.AutoField
    
    class Package(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        package_id = Fields.AutoField
        modified_by = Fields.ForeignKey
        name = Fields.CharField
        created_date = Fields.DateTimeUtcField
        created_by = Fields.ForeignKey
        description = Fields.TextField
    
    class AllPackageVersions(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        count = Fields.IntegerField
        next_page = Fields.TextField
        num_pages = Fields.IntegerField
        previous_page = Fields.TextField
        full_collection = Fields.TextField
        end_index = Fields.IntegerField
        limit = Fields.TextField
        order_by = Fields.TextField
        per_page = Fields.IntegerField
        packageversion = [PackageVersion]
        filter_by = Fields.TextField
        start_index = Fields.IntegerField
    
    class PackageVersionAction(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        visible = Fields.BooleanField
        package_version = Fields.ForeignKey
        enabled = Fields.BooleanField
        descriptor = Fields.TextField
        package_action_type = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
        package_version_action_id = Fields.AutoField
    
    class PackageVersionJob(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        package_version_job_id = Fields.AutoField
        package_version = Fields.DeferredForeignKey
        job_data = Fields.TextField
        created_by = Fields.ForeignKey
        job = Fields.ForeignKey
        package_action_type = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
    
    class PackageSourceJobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        packagesourcejob = [PackageSourceJob]
    
    class PackageVersion(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        description = Fields.TextField
        license = Fields.TextField
        package = Fields.DeferredForeignKey
        committed = Fields.BooleanField
        created_by = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
        consumable = Fields.BooleanField
        package_version_id = Fields.AutoField
        name = Fields.TextField
    
    class PackageBuild(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        created_by = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField
        package_build_id = Fields.AutoField
        package_source = Fields.DeferredForeignKey
    
    class PackageVersionUrl(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        url = Fields.TextField
        package_version = Fields.DeferredForeignKey
        created_date = Fields.DateTimeUtcField
        created_by = Fields.ForeignKey
        downloaded_date = Fields.DateTimeUtcField
        file_size = Fields.IntegerField
        package_version_url_id = Fields.AutoField
        file_path = Fields.TextField
    
    class PackageVersionJobs(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        packageversionjob = [PackageVersionJob]
    
    class PackageSourceJob(xobj.XObj, XObjMixin):
        """XObj Class Stub"""
        __metaclass__ = GetSetXMLAttrMeta
        modified_date = Fields.DateTimeUtcField
        modified_by = Fields.ForeignKey
        package_source_job_id = Fields.AutoField
        job_data = Fields.TextField
        package_source = Fields.DeferredForeignKey
        job = Fields.ForeignKey
        package_action_type = Fields.ForeignKey
        created_by = Fields.ForeignKey
        created_date = Fields.DateTimeUtcField

