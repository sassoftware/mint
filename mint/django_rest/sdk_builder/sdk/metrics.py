from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import SDKClassMeta, toUnderscore  # pyflakes=ignore
from xobj.xobj import XObj, XObjMetadata  # pyflakes=ignore

REGISTRY = {}
TYPEMAP = {}

class ServerVersions(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='server_versions')
    debug_toolbar_version = 'TextField'
    django_version = 'TextField'

class Timer(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='timer')
    context_switches = 'TextField'
    elapsed_time = 'TextField'
    system_cpu_time = 'TextField'
    total_cpu_time = 'TextField'
    user_cpu_time = 'TextField'

class Metrics(object):
    """
    """
    __metaclass__ = SDKClassMeta
    _xobj = XObjMetadata(tag='metrics')