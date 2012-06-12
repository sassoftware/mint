from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore
from xobj2.xobj2 import XObj, XObjMetadata, Field  # pyflakes=ignore

REGISTRY = {}

@register
class ServerVersions(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'server_versions',
        elements = [
            Field('debug_toolbar_version', TextField),
            Field('django_version', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class Timer(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'timer',
        elements = [
            Field('elapsed_time', TextField),
            Field('total_cpu_time', TextField),
            Field('user_cpu_time', TextField),
            Field('context_switches', TextField),
            Field('system_cpu_time', TextField)
        ],
        attributes = dict(
    
        ),
    )

@register
class Metrics(SDKModel):
    """ """
    _xobjMeta = XObjMetadata(
        tag = 'metrics',
        elements = [
    
        ],
        attributes = dict(
    
        ),
    )

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()

