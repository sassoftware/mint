from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class FilterDescriptor(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='filter_descriptor')

class ChosenMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='chosen_members')

class SystemTag(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='system_tag')
    inclusion_method = 'InclusionMethod'
    query_tag = 'QueryTag'
    system = 'System'
    system_tag_id = 'AutoField'

class ChildMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='child_members')

class CollectionId(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='collection')

class InclusionMethod(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='inclusion_method')
    inclusion_method_id = 'AutoField'
    name = 'TextField'

class FilteredMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='filtered_members')

class QueryTag(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='query_tag')
    name = 'TextField'
    query_set = 'QuerySet'
    query_tag_id = 'AutoField'

class AllMembers(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='all_members')

class FilterEntry(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='filter_entry')
    field = 'TextField'
    filter_entry_id = 'AutoField'
    operator = 'TextField'
    value = 'TextField'

class QuerySet(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='query_set')
    can_modify = 'BooleanField'
    created_date = 'DateTimeUtcField'
    description = 'TextField'
    modified_date = 'DateTimeUtcField'
    name = 'TextField'
    query_set_id = 'AutoField'
    resource_type = 'TextField'

class QuerySets(object):
    """
    """
    __metaclass__ = SDKClassMeta
    query_set = ['QuerySet']
    _xobj = XObjMetadata(tag='query_sets',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
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