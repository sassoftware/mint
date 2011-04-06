from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class RepositoryLogStatus(XObj, XObjMixin):
    """
    """
    inode = IntegerField
    logname = CharField
    logoffset = IntegerField

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
    updateUser = CharField
    _updatetime = DecimalField
    serverName = CharField
    repositoryName = CharField
    _systemupdateid = AutoField

