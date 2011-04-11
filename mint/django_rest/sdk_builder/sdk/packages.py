from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class PackageSourceJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_source_job_id = 'AutoField'
    package_source = 'PackageSource'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    job_data = 'TextField'
    job = 'Job'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package_source_job')

class PackageJobSerializerMixin(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class PackageVersionUrl(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    url = 'TextField'
    package_version_url_id = 'AutoField'
    package_version = 'PackageVersion'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    file_size = 'IntegerField'
    file_path = 'TextField'
    downloaded_date = 'DateTimeUtcField'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package_version_url')

class PackageBuild(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_source = 'PackageSource'
    package_build_id = 'AutoField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package_build')

class PackageVersion(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_version_id = 'AutoField'
    package = 'Package'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    license = 'TextField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    consumable = 'BooleanField'
    committed = 'BooleanField'
    _xobj = xobj.XObjMetadata(tag='package_version')

class PackageVersionJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_version_job_id = 'AutoField'
    package_version = 'PackageVersion'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    job_data = 'TextField'
    job = 'Job'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package_version_job')

class PackageVersionAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = 'BooleanField'
    package_version_action_id = 'AutoField'
    package_version = 'PackageVersion'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='package_version_action')

class Package(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_id = 'AutoField'
    name = 'CharField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package')

class PackageSourceAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = 'BooleanField'
    package_source_action_id = 'AutoField'
    package_source = 'PackageSource'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='package_source_action')

class PackageActionType(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_action_type_id = 'AutoField'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='package_action_type')

class PackageBuildJob(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    package_build_job_id = 'AutoField'
    package_build = 'PackageBuild'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    job_data = 'TextField'
    job = 'Job'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    _xobj = xobj.XObjMetadata(tag='package_build_job')

class PackageBuildAction(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    visible = 'BooleanField'
    package_build_action_id = 'AutoField'
    package_build = 'PackageBuild'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = xobj.XObjMetadata(tag='package_build_action')

class PackageSource(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    trove = 'Trove'
    package_version = 'PackageVersion'
    package_source_id = 'AutoField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'Users'
    created_date = 'DateTimeUtcField'
    created_by = 'Users'
    built = 'BooleanField'
    _xobj = xobj.XObjMetadata(tag='package_source')

class JobData(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='job_data')

class PackageVersions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_versions',attributes={'next_page':str,'previous_page':str,'full_collection':str,'filter_by':str,'per_page':str,'order_by':str,'start_index':str,'count':int,'num_pages':str,'end_index':str,'limit':str})
    package_version = ['PackageVersion']

class PackageBuildJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='package_build_jobs')
    package_build_job = ['PackageBuildJob']

class PackageBuilds(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_builds',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    package_build = ['PackageBuild']

class PackageActionTypes(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_action_types',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    package_action_type = ['PackageActionType']

class PackageSourceJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='package_source_jobs')
    package_source_job = ['PackageSourceJob']

class PackageSources(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_sources',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    package_source = ['PackageSource']

class Packages(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='packages',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    package = ['Package']

class PackageVersionUrls(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_version_urls',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    package_version_url = ['PackageVersionUrl']

class AllPackageVersions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    start_index = 'IntegerField'
    previous_page = 'TextField'
    per_page = 'IntegerField'
    order_by = 'TextField'
    num_pages = 'IntegerField'
    next_page = 'TextField'
    limit = 'TextField'
    full_collection = 'TextField'
    filter_by = 'TextField'
    end_index = 'IntegerField'
    count = 'IntegerField'
    _xobj = xobj.XObjMetadata(tag='package_versions',attributes={'next_page':str,'previous_page':str,'full_collection':str,'filter_by':str,'per_page':str,'order_by':str,'start_index':str,'count':int,'num_pages':str,'end_index':str,'limit':str})
    package_version = ['PackageVersion']

class PackageVersionJobs(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='package_version_jobs')
    package_version_job = ['PackageVersionJob']

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls, refCls = GLOBALS[tag], GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

