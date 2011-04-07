from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import GetSetXMLAttrMeta
from xobj.xobj import XObj


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

