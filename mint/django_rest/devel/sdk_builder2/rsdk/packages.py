from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class PackageJobSerializerMixin(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_job_serializer_mixin',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class PackageActionType(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_action_type',
        elements = [
            Field('modified_date', DateTimeUtcField),
            Field('created_date', DateTimeUtcField),
            Field('name', TextField),
            Field('package_action_type_id', AutoField),
            Field('description', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class JobData(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'job_data',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class PackageVersions(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_versions',
        elements = [
            Field('PackageVersions', [created_by])
        ],
        attributes = dict(
            count=int,
            num_pages=str,
            next_page=str,
            order_by=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class PackageBuildJobs(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_build_jobs',
        elements = [
            Field('PackageBuildJobs', [package_build])
        ],
        attributes = dict(
    
        ),
    )

@register
class PackageBuilds(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_builds',
        elements = [
            Field('PackageBuilds', [package_source])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class PackageActionTypes(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_action_types',
        elements = [
            Field('PackageActionTypes', [PackageActionType])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class PackageSourceJobs(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_source_jobs',
        elements = [
            Field('PackageSourceJobs', [created_by])
        ],
        attributes = dict(
    
        ),
    )

@register
class PackageSources(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_sources',
        elements = [
            Field('PackageSources', [created_by])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class Packages(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'packages',
        elements = [
            Field('Packages', [created_by])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class PackageVersionUrls(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_version_urls',
        elements = [
            Field('PackageVersionUrls', [created_by])
        ],
        attributes = dict(
            count=int,
            next_page=str,
            num_pages=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            order_by=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class AllPackageVersions(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'all_package_versions',
        elements = [
            Field('AllPackageVersions', [created_by])
        ],
        attributes = dict(
            count=int,
            num_pages=str,
            next_page=str,
            order_by=str,
            previous_page=str,
            full_collection=str,
            filter_by=str,
            limit=str,
            per_page=str,
            end_index=str,
            start_index=str
        ),
    )

@register
class PackageVersionJobs(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'package_version_jobs',
        elements = [
            Field('PackageVersionJobs', [package_action_type])
        ],
        attributes = dict(
    
        ),
    )

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

