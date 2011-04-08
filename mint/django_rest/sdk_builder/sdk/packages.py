from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class PackageSourceJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_source_job_id = AutoField
    package_source = DeferredForeignKey
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    modified_by = Users
    job_data = TextField
    job = Job
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageJobSerializerMixin(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class PackageVersionUrl(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    url = TextField
    package_version_url_id = AutoField
    package_version = DeferredForeignKey
    modified_date = DateTimeUtcField
    modified_by = Users
    file_size = IntegerField
    file_path = TextField
    downloaded_date = DateTimeUtcField
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageBuild(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_source = DeferredForeignKey
    package_build_id = AutoField
    modified_date = DateTimeUtcField
    modified_by = Users
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageVersion(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_version_id = AutoField
    package = DeferredForeignKey
    name = TextField
    modified_date = DateTimeUtcField
    modified_by = Users
    license = TextField
    description = TextField
    created_date = DateTimeUtcField
    created_by = Users
    consumable = BooleanField
    committed = BooleanField
    _xobj = XObjMetadata

class PackageVersionJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_version_job_id = AutoField
    package_version = DeferredForeignKey
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    modified_by = Users
    job_data = TextField
    job = Job
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageVersionAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = BooleanField
    package_version_action_id = AutoField
    package_version = PackageVersion
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class Package(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_id = AutoField
    name = CharField
    modified_date = DateTimeUtcField
    modified_by = Users
    description = TextField
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageSourceAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = BooleanField
    package_source_action_id = AutoField
    package_source = PackageSource
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageActionType(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_action_type_id = AutoField
    name = TextField
    modified_date = DateTimeUtcField
    description = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageBuildJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_build_job_id = AutoField
    package_build = DeferredForeignKey
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    modified_by = Users
    job_data = TextField
    job = Job
    created_date = DateTimeUtcField
    created_by = Users
    _xobj = XObjMetadata

class PackageBuildAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = BooleanField
    package_build_action_id = AutoField
    package_build = PackageBuild
    package_action_type = PackageActionType
    modified_date = DateTimeUtcField
    enabled = BooleanField
    descriptor = TextField
    created_date = DateTimeUtcField
    _xobj = XObjMetadata

class PackageSource(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    trove = Trove
    package_version = DeferredForeignKey
    package_source_id = AutoField
    modified_date = DateTimeUtcField
    modified_by = Users
    created_date = DateTimeUtcField
    created_by = Users
    built = BooleanField
    _xobj = XObjMetadata

class JobData(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class PackageVersions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_version = ['PackageVersion']

class PackageBuildJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata
    package_build_job = ['PackageBuildJob']

class PackageBuilds(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_build = ['PackageBuild']

class PackageActionTypes(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_action_type = ['PackageActionType']

class PackageSourceJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata
    package_source_job = ['PackageSourceJob']

class PackageSources(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_source = ['PackageSource']

class Packages(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package = ['Package']

class PackageVersionUrls(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_version_url = ['PackageVersionUrl']

class AllPackageVersions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
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
    package_version = ['PackageVersion']

class PackageVersionJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata
    package_version_job = ['PackageVersionJob']

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[tag.lower()] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls = GLOBALS[tag]
            refCls = GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

