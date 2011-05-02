from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class ChangeLogEntry(SDKModel):
    """ """

    entry_text = 'TextField'
    entry_date = 'DateTimeUtcField'
    change_log_entry_id = 'AutoField'
    change_log = 'ChangeLog'
    _xobj = XObjMetadata(tag='change_log_entry')

@register
class ChangeLog(SDKModel):
    """ """

    resource_type = 'TextField'
    resource_id = 'IntegerField'
    change_log_id = 'AutoField'
    _xobj = XObjMetadata(tag='change_log')

@register
class ChangeLogs(SDKModel):
    """ """

    _xobj = XObjMetadata(tag='change_logs')
    change_log = ['ChangeLog']

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

