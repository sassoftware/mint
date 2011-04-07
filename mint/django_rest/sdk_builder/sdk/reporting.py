from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import RegistryMeta
from xobj.xobj import XObj, XObjMetadata


REGISTRY = {}

class RepositoryLogStatus(XObj, XObjMixin):
    """
    """
    logoffset = IntegerField
    logname = CharField
    inode = IntegerField

class Report(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class Reports(XObj, XObjMixin):
    """
    """

class SystemUpdate(XObj, XObjMixin):
    """
    """
    update_user = CharField
    server_name = CharField
    repository_name = CharField
    _updatetime = DecimalField
    _systemupdateid = AutoField

# DO NOT TOUCH #
GLOBALS = globals()
for k, v in REGISTRY.items():
    for _k, _v in v.items():
        if _v in GLOBALS:
            setattr(GLOBALS[k], _k, GLOBALS[_v])

