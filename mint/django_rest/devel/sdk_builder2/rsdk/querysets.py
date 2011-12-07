from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class FilterDescriptor(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'filter_descriptor',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class ChosenMembers(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'chosen_members',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class ChildMembers(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'child_members',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class CollectionId(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'collection_id',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class InclusionMethod(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'inclusion_method',
        elements = [
            Field('inclusion_method_id', AutoField),
            Field('name', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class FilteredMembers(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'filtered_members',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class AllMembers(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'all_members',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class FilterEntry(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'filter_entry',
        elements = [
            Field('operator', TextField),
            Field('field', TextField),
            Field('filter_entry_id', AutoField),
            Field('value', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class QuerySet(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'query_set',
        elements = [
            Field('modified_date', DateTimeUtcField),
            Field('name', TextField),
            Field('can_modify', BooleanField),
            Field('query_set_id', AutoField),
            Field('created_date', DateTimeUtcField),
            Field('resource_type', TextField),
            Field('description', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class QuerySets(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'query_sets',
        elements = [
            Field('QuerySets', [QuerySet])
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

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

