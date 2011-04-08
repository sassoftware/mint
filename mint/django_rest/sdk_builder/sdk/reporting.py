from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import RegistryMeta  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class RepositoryLogStatus(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    logoffset = IntegerField
    logname = CharField
    inode = IntegerField

class Report(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    _xobj = XObjMetadata

class Reports(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    

class SystemUpdate(XObj):
    """
    """
    __metaclass__ = RegistryMeta
    
    update_user = CharField
    server_name = CharField
    repository_name = CharField
    _updatetime = DecimalField
    _systemupdateid = AutoField

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

