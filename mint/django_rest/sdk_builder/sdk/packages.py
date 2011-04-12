from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class PackageSourceJob(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_source_job')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    job = 'Job'
    job_data = 'TextField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_source = 'PackageSource'
    package_source_job_id = 'AutoField'

class PackageJobSerializerMixin(object):
    """
    """
    __metaclass__ = SDKClassMeta

class PackageVersionUrl(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version_url')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    downloaded_date = 'DateTimeUtcField'
    file_path = 'TextField'
    file_size = 'IntegerField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_version = 'PackageVersion'
    package_version_url_id = 'AutoField'
    url = 'TextField'

class PackageBuild(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_build')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_build_id = 'AutoField'
    package_source = 'PackageSource'

class PackageVersion(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version')
    committed = 'BooleanField'
    consumable = 'BooleanField'
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    description = 'TextField'
    license = 'TextField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    name = 'TextField'
    package = 'Package'
    package_version_id = 'AutoField'

class PackageVersionJob(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version_job')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    job = 'Job'
    job_data = 'TextField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_version = 'PackageVersion'
    package_version_job_id = 'AutoField'

class PackageVersionAction(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version_action')
    created_date = 'DateTimeUtcField'
    descriptor = 'TextField'
    enabled = 'BooleanField'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_version = 'PackageVersion'
    package_version_action_id = 'AutoField'
    visible = 'BooleanField'

class Package(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    description = 'TextField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    name = 'CharField'
    package_id = 'AutoField'

class PackageSourceAction(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_source_action')
    created_date = 'DateTimeUtcField'
    descriptor = 'TextField'
    enabled = 'BooleanField'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_source = 'PackageSource'
    package_source_action_id = 'AutoField'
    visible = 'BooleanField'

class PackageActionType(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_action_type')
    created_date = 'DateTimeUtcField'
    description = 'TextField'
    modified_date = 'DateTimeUtcField'
    name = 'TextField'
    package_action_type_id = 'AutoField'

class PackageBuildJob(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_build_job')
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    job = 'Job'
    job_data = 'TextField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_build = 'PackageBuild'
    package_build_job_id = 'AutoField'

class PackageBuildAction(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_build_action')
    created_date = 'DateTimeUtcField'
    descriptor = 'TextField'
    enabled = 'BooleanField'
    modified_date = 'DateTimeUtcField'
    package_action_type = 'PackageActionType'
    package_build = 'PackageBuild'
    package_build_action_id = 'AutoField'
    visible = 'BooleanField'

class PackageSource(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_source')
    built = 'BooleanField'
    created_by = 'Users'
    created_date = 'DateTimeUtcField'
    modified_by = 'Users'
    modified_date = 'DateTimeUtcField'
    package_source_id = 'AutoField'
    package_version = 'PackageVersion'
    trove = 'Trove'

class JobData(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='job_data')

class PackageVersions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_version = ['PackageVersion']
    _xobj = XObjMetadata(tag='package_versions',attributes={'next_page':str,'previous_page':str,'full_collection':str,'filter_by':str,'per_page':str,'order_by':str,'start_index':str,'count':int,'num_pages':str,'end_index':str,'limit':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class PackageBuildJobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_build_job = ['PackageBuildJob']
    _xobj = XObjMetadata(tag='package_build_jobs')

class PackageBuilds(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_build = ['PackageBuild']
    _xobj = XObjMetadata(tag='package_builds',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class PackageActionTypes(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_action_type = ['PackageActionType']
    _xobj = XObjMetadata(tag='package_action_types',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class PackageSourceJobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_source_job = ['PackageSourceJob']
    _xobj = XObjMetadata(tag='package_source_jobs')

class PackageSources(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_source = ['PackageSource']
    _xobj = XObjMetadata(tag='package_sources',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class Packages(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package = ['Package']
    _xobj = XObjMetadata(tag='packages',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class PackageVersionUrls(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_version_url = ['PackageVersionUrl']
    _xobj = XObjMetadata(tag='package_version_urls',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class AllPackageVersions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_version = ['PackageVersion']
    _xobj = XObjMetadata(tag='package_versions',attributes={'next_page':str,'previous_page':str,'full_collection':str,'filter_by':str,'per_page':str,'order_by':str,'start_index':str,'count':int,'num_pages':str,'end_index':str,'limit':str})
    count = 'IntegerField'
    end_index = 'IntegerField'
    filter_by = 'TextField'
    full_collection = 'TextField'
    limit = 'TextField'
    next_page = 'TextField'
    num_pages = 'IntegerField'
    order_by = 'TextField'
    per_page = 'IntegerField'
    previous_page = 'TextField'
    start_index = 'IntegerField'

class PackageVersionJobs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    package_version_job = ['PackageVersionJob']
    _xobj = XObjMetadata(tag='package_version_jobs')

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

