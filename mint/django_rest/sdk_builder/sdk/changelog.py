from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class ChangeLogEntry(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    entry_text = TextField
    entry_date = DateTimeUtcField
    change_log_entry_id = AutoField
    change_log = ChangeLog
    _xobj = xobj.XObjMetadata(tag='change_log_entry')

class ChangeLog(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    resource_type = TextField
    resource_id = IntegerField
    change_log_id = AutoField
    _xobj = xobj.XObjMetadata(tag='change_log')

class ChangeLogs(XObj):
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
    _xobj = xobj.XObjMetadata(tag='change_logs',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    change_log = ['ChangeLog']

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

