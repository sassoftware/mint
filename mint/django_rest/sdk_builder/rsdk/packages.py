from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class PackageSourceJob(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_source_job_id = 'AutoField'
    package_source = 'PackageSource'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    job_data = 'TextField'
    job = 'inventory.Job'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package_source_job')

@register
class PackageJobSerializerMixin(object):
    """ """

    __metaclass__ = SDKClassMeta

@register
class PackageVersionUrl(object):
    """ """

    __metaclass__ = SDKClassMeta
    url = 'TextField'
    package_version_url_id = 'AutoField'
    package_version = 'PackageVersion'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    file_size = 'IntegerField'
    file_path = 'TextField'
    downloaded_date = 'DateTimeUtcField'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package_version_url')

@register
class PackageBuild(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_source = 'PackageSource'
    package_build_id = 'AutoField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package_build')

@register
class PackageVersion(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_version_id = 'AutoField'
    package = 'Package'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    license = 'TextField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    consumable = 'BooleanField'
    committed = 'BooleanField'
    _xobj = XObjMetadata(tag='package_version')

@register
class PackageVersionJob(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_version_job_id = 'AutoField'
    package_version = 'PackageVersion'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    job_data = 'TextField'
    job = 'inventory.Job'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package_version_job')

@register
class PackageVersionAction(object):
    """ """

    __metaclass__ = SDKClassMeta
    visible = 'BooleanField'
    package_version_action_id = 'AutoField'
    package_version = 'PackageVersion'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='package_version_action')

@register
class Package(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_id = 'AutoField'
    name = 'CharField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package')

@register
class PackageSourceAction(object):
    """ """

    __metaclass__ = SDKClassMeta
    visible = 'BooleanField'
    package_source_action_id = 'AutoField'
    package_source = 'PackageSource'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='package_source_action')

@register
class PackageActionType(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_action_type_id = 'AutoField'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='package_action_type')

@register
class PackageBuildJob(object):
    """ """

    __metaclass__ = SDKClassMeta
    package_build_job_id = 'AutoField'
    package_build = 'PackageBuild'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    job_data = 'TextField'
    job = 'inventory.Job'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    _xobj = XObjMetadata(tag='package_build_job')

@register
class PackageBuildAction(object):
    """ """

    __metaclass__ = SDKClassMeta
    visible = 'BooleanField'
    package_build_action_id = 'AutoField'
    package_build = 'PackageBuild'
    package_action_type = 'PackageActionType'
    modified_date = 'DateTimeUtcField'
    enabled = 'BooleanField'
    descriptor = 'TextField'
    created_date = 'DateTimeUtcField'
    _xobj = XObjMetadata(tag='package_build_action')

@register
class PackageSource(object):
    """ """

    __metaclass__ = SDKClassMeta
    trove = 'inventory.Trove'
    package_version = 'PackageVersion'
    package_source_id = 'AutoField'
    modified_date = 'DateTimeUtcField'
    modified_by = 'rbuilder.Users'
    created_date = 'DateTimeUtcField'
    created_by = 'rbuilder.Users'
    built = 'BooleanField'
    _xobj = XObjMetadata(tag='package_source')

@register
class JobData(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='job_data')

@register
class PackageVersions(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_versions')
    package_version = ['PackageVersion']

@register
class PackageBuildJobs(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_build_jobs')
    package_build_job = ['PackageBuildJob']

@register
class PackageBuilds(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_builds')
    package_build = ['PackageBuild']

@register
class PackageActionTypes(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_action_types')
    package_action_type = ['PackageActionType']

@register
class PackageSourceJobs(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_source_jobs')
    package_source_job = ['PackageSourceJob']

@register
class PackageSources(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_sources')
    package_source = ['PackageSource']

@register
class Packages(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='packages')
    package = ['Package']

@register
class PackageVersionUrls(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version_urls')
    package_version_url = ['PackageVersionUrl']

@register
class AllPackageVersions(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_versions')
    package_version = ['PackageVersion']

@register
class PackageVersionJobs(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='package_version_jobs')
    package_version_job = ['PackageVersionJob']

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

