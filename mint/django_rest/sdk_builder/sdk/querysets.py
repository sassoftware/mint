from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta
from xobj.xobj import XObj, XObjMetadata

REGISTRY = {}
TYPEMAP = {}

class FilterDescriptor(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class ChosenMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class SystemTag(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    system_tag_id = AutoField
    system = System
    query_tag = QueryTag
    inclusion_method = SerializedForeignKey
    _xobj = XObjMetadata

class ChildMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class CollectionId(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class InclusionMethod(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    name = TextField
    inclusion_method_id = AutoField
    _xobj = XObjMetadata

class FilteredMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class QueryTag(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    query_tag_id = AutoField
    query_set = QuerySet
    name = TextField
    _xobj = XObjMetadata

class AllMembers(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class FilterEntry(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    value = TextField
    operator = TextField
    filter_entry_id = AutoField
    field = TextField
    _xobj = XObjMetadata

class QuerySet(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    resource_type = TextField
    query_set_id = AutoField
    name = TextField
    modified_date = DateTimeUtcField
    description = TextField
    created_date = DateTimeUtcField
    can_modify = BooleanField
    _xobj = XObjMetadata

class QuerySets(XObj):
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
    query_set = ['QuerySet']

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

