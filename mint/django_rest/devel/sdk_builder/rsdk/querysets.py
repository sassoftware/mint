from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class FilterDescriptor(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='filter_descriptor')

@register
class ChosenMembers(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='chosen_members')

@register
class SystemTag(SDKModel):
    """ """

    system_tag_id = 'AutoField'
    system = 'inventory.System'
    query_tag = 'QueryTag'
    inclusion_method = 'InclusionMethod'
    _xobj = XObjMetadata(tag='system_tag')

@register
class ChildMembers(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='child_members')

@register
class CollectionId(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='collection')

@register
class InclusionMethod(SDKModel):
    """ """

    name = 'TextField'
    inclusion_method_id = 'AutoField'
    _xobj = XObjMetadata(tag='inclusion_method')

@register
class FilteredMembers(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='filtered_members')

@register
class QueryTag(SDKModel):
    """ """

    query_tag_id = 'AutoField'
    query_set = 'QuerySet'
    name = 'TextField'
    _xobj = XObjMetadata(tag='query_tag')

@register
class AllMembers(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='all_members')

@register
class FilterEntry(SDKModel):
    """ """

    value = 'TextField'
    operator = 'TextField'
    filter_entry_id = 'AutoField'
    field = 'TextField'
    _xobj = XObjMetadata(tag='filter_entry')

@register
class QuerySet(SDKModel):
    """ """

    resource_type = 'TextField'
    query_set_id = 'AutoField'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    can_modify = 'BooleanField'
    _xobj = XObjMetadata(tag='query_set')

@register
class QuerySets(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='query_sets')
    query_set = ['QuerySet']

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

