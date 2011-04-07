from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from xobj.xobj import XObj


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

