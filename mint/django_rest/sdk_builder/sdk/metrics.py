from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore, register  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class ServerVersions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    django_version = 'TextField'
    debug_toolbar_version = 'TextField'
    _xobj = XObjMetadata(tag='server_versions')

@register
class Timer(object):
    """
    """
    __metaclass__ = SDKClassMeta
    user_cpu_time = 'TextField'
    total_cpu_time = 'TextField'
    system_cpu_time = 'TextField'
    elapsed_time = 'TextField'
    context_switches = 'TextField'
    _xobj = XObjMetadata(tag='timer')

@register
class Metrics(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='metrics')

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

