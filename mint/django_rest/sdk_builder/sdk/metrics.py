from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import RegistryMeta
from xobj.xobj import XObj, XObjMetadata


REGISTRY = {}

class ServerVersions(XObj, XObjMixin):
    """
    """
    django_version = TextField
    debug_toolbar_version = TextField
    _xobj = XObjMetadata

class Timer(XObj, XObjMixin):
    """
    """
    user_cpu_time = TextField
    total_cpu_time = TextField
    system_cpu_time = TextField
    elapsed_time = TextField
    context_switches = TextField
    _xobj = XObjMetadata

class Metrics(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

# DO NOT TOUCH #
GLOBALS = globals()
for k, v in REGISTRY.items():
    for _k, _v in v.items():
        if _v in GLOBALS:
            setattr(GLOBALS[k], _k, GLOBALS[_v])

