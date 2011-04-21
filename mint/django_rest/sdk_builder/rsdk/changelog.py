from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class ChangeLogEntry(object):
    """
    """
    __metaclass__ = SDKClassMeta
    entry_text = 'TextField'
    entry_date = 'DateTimeUtcField'
    change_log_entry_id = 'AutoField'
    change_log = 'ChangeLog'
    _xobj = XObjMetadata(tag='change_log_entry')

@register
class ChangeLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    resource_type = 'TextField'
    resource_id = 'IntegerField'
    change_log_id = 'AutoField'
    _xobj = XObjMetadata(tag='change_log')

@register
class ChangeLogs(object):
    """
    """
    __metaclass__ = SDKClassMeta
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
    _xobj = XObjMetadata(tag='change_logs',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
    change_log = ['ChangeLog']

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

