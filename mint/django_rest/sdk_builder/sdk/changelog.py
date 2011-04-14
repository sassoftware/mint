from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class ChangeLogEntry(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='change_log_entry')
    change_log = 'ChangeLog'
    change_log_entry_id = 'AutoField'
    entry_date = 'DateTimeUtcField'
    entry_text = 'TextField'

class ChangeLog(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='change_log')
    change_log_id = 'AutoField'
    resource_id = 'IntegerField'
    resource_type = 'TextField'

class ChangeLogs(object):
    """
    """
    __metaclass__ = SDKClassMeta
    change_log = ['ChangeLog']
    _xobj = XObjMetadata(tag='change_logs',attributes={'count':int,'next_page':str,'num_pages':str,'previous_page':str,'full_collection':str,'filter_by':str,'limit':str,'per_page':str,'order_by':str,'end_index':str,'start_index':str})
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