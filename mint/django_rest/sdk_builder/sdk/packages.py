from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from xobj.xobj import XObj


class PackageSourceJob(XObj, XObjMixin):
    """
    """
    package_source_job_id = AutoField
    package_source = DeferredForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    job_data = TextField
    job = ForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageVersionUrl(XObj, XObjMixin):
    """
    """
    url = TextField
    package_version_url_id = AutoField
    package_version = DeferredForeignKey
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    file_size = IntegerField
    file_path = TextField
    downloaded_date = DateTimeUtcField
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageBuild(XObj, XObjMixin):
    """
    """
    package_source = DeferredForeignKey
    package_build_id = AutoField
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageVersion(XObj, XObjMixin):
    """
    """
    package_version_id = AutoField
    package = DeferredForeignKey
    name = TextField
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    license = TextField
    description = TextField
    created_date = DateTimeUtcField
    created_by = ForeignKey
    consumable = BooleanField
    committed = BooleanField
    _xobj = XObjMetadata

class PackageVersionJob(XObj, XObjMixin):
    """
    """
    package_version_job_id = AutoField
    package_version = DeferredForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    job_data = TextField
    job = ForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageVersionAction(XObj, XObjMixin):
    """
    """
    visible = BooleanField
    package_version_action_id = AutoField
    package_version = ForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class Package(XObj, XObjMixin):
    """
    """
    package_id = AutoField
    name = CharField
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    description = TextField
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageSourceAction(XObj, XObjMixin):
    """
    """
    visible = BooleanField
    package_source_action_id = AutoField
    package_source = ForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageActionType(XObj, XObjMixin):
    """
    """
    package_action_type_id = AutoField
    name = TextField
    modified_date = DateTimeUtcField
    description = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageBuildJob(XObj, XObjMixin):
    """
    """
    package_build_job_id = AutoField
    package_build = DeferredForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    job_data = TextField
    job = ForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    _xobj = XObjMetadata

class PackageBuildAction(XObj, XObjMixin):
    """
    """
    visible = BooleanField
    package_build_action_id = AutoField
    package_build = ForeignKey
    package_action_type = ForeignKey
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageSource(XObj, XObjMixin):
    """
    """
    trove = ForeignKey
    package_version = DeferredForeignKey
    package_source_id = AutoField
    modified_date = DateTimeUtcField
    modified_by = ForeignKey
    created_date = DateTimeUtcField
    created_by = ForeignKey
    built = BooleanField
    _xobj = XObjMetadata

class JobData(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class PackageVersions(XObj, XObjMixin):
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
    package_version = [PackageVersion]

class PackageBuildJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    package_build_job = [PackageBuildJob]

class PackageBuilds(XObj, XObjMixin):
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
    package_build = [PackageBuild]

class PackageActionTypes(XObj, XObjMixin):
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
    package_action_type = [PackageActionType]

class PackageSources(XObj, XObjMixin):
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
    package_source = [PackageSource]

class Packages(XObj, XObjMixin):
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
    package = [Package]

class PackageVersionUrls(XObj, XObjMixin):
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
    package_version_url = [PackageVersionUrl]

class AllPackageVersions(XObj, XObjMixin):
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
    package_version = [PackageVersion]

class PackageSourceJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    package_source_job = [PackageSourceJob]

class PackageVersionJobs(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    package_version_job = [PackageVersionJob]

