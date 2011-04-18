from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register  # pyflakes=ignore
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
for tag, clsAttrs in REGISTRY.items():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]
    for attrName, refClsOrName in clsAttrs.items():
        if refClsOrName in GLOBALS:
            cls, refCls = GLOBALS[tag], GLOBALS[refClsOrName]
            if isinstance(getattr(cls, attrName), list):
                setattr(cls, attrName, [refCls])
            else:
                setattr(cls, attrName, refCls)

