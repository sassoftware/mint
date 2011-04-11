from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class FilterDescriptor(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='filter_descriptor')

class ChosenMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='chosen_members')

class SystemTag(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_tag_id = 'AutoField'
    system = 'System'
    query_tag = 'QueryTag'
    inclusion_method = 'SerializedForeignKey'
    _xobj = xobj.XObjMetadata(tag='system_tag')

class ChildMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='child_members')

class CollectionId(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='collection')

class InclusionMethod(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    name = 'TextField'
    inclusion_method_id = 'AutoField'
    _xobj = xobj.XObjMetadata(tag='inclusion_method')

class FilteredMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='filtered_members')

class QueryTag(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    query_tag_id = 'AutoField'
    query_set = 'QuerySet'
    name = 'TextField'
    _xobj = xobj.XObjMetadata(tag='query_tag')

class AllMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = xobj.XObjMetadata(tag='all_members')

class FilterEntry(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    value = 'TextField'
    operator = 'TextField'
    filter_entry_id = 'AutoField'
    field = 'TextField'
    _xobj = xobj.XObjMetadata(tag='filter_entry')

class QuerySet(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    resource_type = 'TextField'
    query_set_id = 'AutoField'
    name = 'TextField'
    modified_date = 'DateTimeUtcField'
    description = 'TextField'
    created_date = 'DateTimeUtcField'
    can_modify = 'BooleanField'
    _xobj = xobj.XObjMetadata(tag='query_set')

class QuerySets(XObj):
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
    _xobj = xobj.XObjMetadata(tag='query_sets',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    query_set = ['QuerySet']

# DO NOT TOUCH #
GLOBALS = globals()
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls = GLOBALS[tag]
            refCls = GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

