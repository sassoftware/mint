from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class RepositoryLogStatus(object):
    """
    """
    __metaclass__ = SDKClassMeta
    logoffset = 'IntegerField'
    logname = 'CharField'
    inode = 'IntegerField'

@register
class Report(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(attributes={'id':str},elements=['name', 'description', 'descriptor', 'data', 'timeCreated'])

@register
class Reports(object):
    """
    """
    __metaclass__ = SDKClassMeta

@register
class SystemUpdate(object):
    """
    """
    __metaclass__ = SDKClassMeta
    update_user = 'CharField'
    server_name = 'CharField'
    repository_name = 'CharField'
    _updatetime = 'DecimalField'
    _systemupdateid = 'AutoField'

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

