from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import RegistryMeta
from xobj.xobj import XObj, XObjMetadata


REGISTRY = {}

class ChangeLogEntry(XObj, XObjMixin):
    """
    """
    entry_text = TextField
    entry_date = DateTimeUtcField
    change_log_entry_id = AutoField
    change_log = ForeignKey
    _xobj = XObjMetadata

class ChangeLog(XObj, XObjMixin):
    """
    """
    resource_type = TextField
    resource_id = IntegerField
    change_log_id = AutoField
    _xobj = XObjMetadata

class ChangeLogs(XObj, XObjMixin):
    """
    """
    start_index = IntegerField
    previous_page = TextField
    per_page = IntegerField
    order_by = TextField
    num_pages = IntegerField
    next_page = TextField
    limit = TextField
    full_collection = TextField
    filter_by = TextField
    end_index = IntegerField
    count = IntegerField
    _xobj = XObjMetadata
    change_log = ['ChangeLog']

# DO NOT TOUCH #
GLOBALS = globals()
for k, v in REGISTRY.items():
    for _k, _v in v.items():
        if _v in GLOBALS:
            setattr(GLOBALS[k], _k, GLOBALS[_v])

