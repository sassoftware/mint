from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class PackageSourceJob(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    package_source_job_id = AutoField
    created_date = DateTimeUtcField
    job_data = TextField
    package_source = DeferredForeignKey
    job = ForeignKey
    package_action_type = ForeignKey
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageVersionUrl(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    url = TextField
    _xobj = XObjMetadata
    package_version = DeferredForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    downloaded_date = DateTimeUtcField
    file_size = IntegerField
    package_version_url_id = AutoField
    file_path = TextField

class PackageBuild(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    created_by = ForeignKey
    created_date = DateTimeUtcField
    _xobj = XObjMetadata
    package_build_id = AutoField
    package_source = DeferredForeignKey

class PackageVersion(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    description = TextField
    license = TextField
    package = DeferredForeignKey
    _xobj = XObjMetadata
    committed = BooleanField
    created_by = ForeignKey
    created_date = DateTimeUtcField
    consumable = BooleanField
    package_version_id = AutoField
    name = TextField

class PackageVersionJob(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    package_version_job_id = AutoField
    _xobj = XObjMetadata
    package_version = DeferredForeignKey
    job_data = TextField
    created_by = ForeignKey
    job = ForeignKey
    package_action_type = ForeignKey
    created_date = DateTimeUtcField

class PackageVersionAction(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    visible = BooleanField
    _xobj = XObjMetadata
    package_version = ForeignKey
    enabled = BooleanField
    descriptor = TextField
    package_action_type = ForeignKey
    created_date = DateTimeUtcField
    package_version_action_id = AutoField

class Package(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    name = CharField
    _xobj = XObjMetadata
    created_by = ForeignKey
    package_id = AutoField
    created_date = DateTimeUtcField
    description = TextField

class PackageSourceAction(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    descriptor = TextField
    _xobj = XObjMetadata
    enabled = BooleanField
    package_source = ForeignKey
    visible = BooleanField
    package_action_type = ForeignKey
    created_date = DateTimeUtcField
    package_source_action_id = AutoField

class PackageActionType(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    description = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata
    package_action_type_id = AutoField
    name = TextField

class PackageBuildJob(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    _xobj = XObjMetadata
    job_data = TextField
    created_by = ForeignKey
    job = ForeignKey
    package_action_type = ForeignKey
    package_build = DeferredForeignKey
    created_date = DateTimeUtcField
    package_build_job_id = AutoField

class PackageBuildAction(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    visible = BooleanField
    _xobj = XObjMetadata
    enabled = BooleanField
    descriptor = TextField
    package_action_type = ForeignKey
    package_build = ForeignKey
    created_date = DateTimeUtcField
    package_build_action_id = AutoField

class PackageSource(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    built = BooleanField
    package_source_id = AutoField
    package_version = DeferredForeignKey
    trove = ForeignKey
    created_by = ForeignKey
    _xobj = XObjMetadata
    created_date = DateTimeUtcField

class JobData(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class PackageVersions(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    PackageVersion = [PackageVersion]
    filter_by = TextField
    start_index = IntegerField

class PackageBuildJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    PackageBuildJob = [PackageBuildJob]

class PackageBuilds(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    PackageBuild = [PackageBuild]
    start_index = IntegerField

class PackageActionTypes(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    filter_by = TextField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    PackageActionType = [PackageActionType]
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    end_index = IntegerField
    start_index = IntegerField

class PackageSources(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    PackageSource = [PackageSource]
    filter_by = TextField
    start_index = IntegerField

class Packages(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    Package = [Package]
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

class PackageVersionUrls(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    PackageVersionUrl = [PackageVersionUrl]
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

class AllPackageVersions(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    PackageVersion = [PackageVersion]
    filter_by = TextField
    start_index = IntegerField

class PackageSourceJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    PackageSourceJob = [PackageSourceJob]

class PackageVersionJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    PackageVersionJob = [PackageVersionJob]

