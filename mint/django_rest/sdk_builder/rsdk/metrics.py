from rsdk.Fields import *  # pyflakes=ignore
from rsdk.sdk import SDKClassMeta, toUnderscore, register, DynamicImportResolver  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

@register
class ServerVersions(object):
    """ """

    __metaclass__ = SDKClassMeta
    django_version = 'TextField'
    debug_toolbar_version = 'TextField'
    _xobj = XObjMetadata(tag='server_versions')

@register
class Timer(object):
    """ """

    __metaclass__ = SDKClassMeta
    user_cpu_time = 'TextField'
    total_cpu_time = 'TextField'
    system_cpu_time = 'TextField'
    elapsed_time = 'TextField'
    context_switches = 'TextField'
    _xobj = XObjMetadata(tag='timer')

@register
class Metrics(object):
    """ """

    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='metrics')

# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
for tag in REGISTRY.keys():
    if tag in GLOBALS:
        TYPEMAP[toUnderscore(tag)] = GLOBALS[tag]

