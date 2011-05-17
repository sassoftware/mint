from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class RepositoryLogStatus(SDKModel):
    """ """

    logoffset = 'IntegerField'
    logname = 'CharField'
    inode = 'IntegerField'

@register
class Report(SDKModel):
    """ """

    _xobj = XObjMetadata(elements=['name', 'description', 'descriptor', 'data', 'timeCreated'])

@register
class Reports(SDKModel):
    """ """


@register
class SystemUpdate(SDKModel):
    """ """

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

