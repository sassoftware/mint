from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class ServerVersions(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    debug_toolbar_version = TextField
    django_version = TextField

class Timer(XObj, XObjMixin):
    """
    """
    elapsed_time = TextField
    total_cpu_time = TextField
    user_cpu_time = TextField
    _xobj = XObjMetadata
    context_switches = TextField
    system_cpu_time = TextField

class Metrics(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

