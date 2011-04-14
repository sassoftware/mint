from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class RepositoryLogStatus(object):
    """
    """
    __metaclass__ = SDKClassMeta
    inode = 'IntegerField'
    logname = 'CharField'
    logoffset = 'IntegerField'

class Report(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(attributes={'id':str},elements=['name', 'description', 'descriptor', 'data', 'timeCreated'])

class Reports(object):
    """
    """
    __metaclass__ = SDKClassMeta

class SystemUpdate(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _systemupdateid = 'AutoField'
    _updatetime = 'DecimalField'
    repository_name = 'CharField'
    server_name = 'CharField'
    update_user = 'CharField'