from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class ChangeLogEntry(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    change_log_entry_id = AutoField
    change_log = ForeignKey
    entry_date = DateTimeUtcField
    entry_text = TextField

class ChangeLog(XObj, XObjMixin):
    """
    """
    change_log_id = AutoField
    resource_id = IntegerField
    _xobj = XObjMetadata
    resource_type = TextField

class ChangeLogs(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    ChangeLog = [ChangeLog]
    _xobj = XObjMetadata
    previous_page = TextField
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

