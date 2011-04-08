from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class ServerVersions(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    django_version = TextField
    debug_toolbar_version = TextField
    _xobj = XObjMetadata

class Timer(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    user_cpu_time = TextField
    total_cpu_time = TextField
    system_cpu_time = TextField
    elapsed_time = TextField
    context_switches = TextField
    _xobj = XObjMetadata

class Metrics(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

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

