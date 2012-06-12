from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class RepositoryLogStatus(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'repository_log_status',
        elements = [
            Field('inode', IntegerField),
            Field('logname', CharField),
            Field('logoffset', IntegerField)
        ],
        attributes = dict(
    
        ),
    )

@register
class Report(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'report',
        elements = [
    
        ],
        attributes = dict(
            id=str
        ),
    )

@register
class Reports(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'reports',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

@register
class SystemUpdate(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'system_update',
        elements = [
            Field('updateUser', CharField),
            Field('serverName', CharField),
            Field('repositoryName', CharField),
            Field('_updatetime', DecimalField),
            Field('_systemupdateid', AutoField)
        ],
        attributes = dict(
    
        ),
    )

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

