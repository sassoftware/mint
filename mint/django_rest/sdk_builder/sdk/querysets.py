from rSDK.Fields import *  # pyflakes=ignore
from rSDK import XObjMixin
from rSDK import GetSetXMLAttrMeta
from xobj import xobj


class FilterDescriptor(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class ChosenMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class SystemTag(XObj, XObjMixin):
    """
    """
    system_tag_id = AutoField
    _xobj = XObjMetadata
    system = ForeignKey
    inclusion_method = SerializedForeignKey
    query_tag = ForeignKey

class ChildMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class CollectionId(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class InclusionMethod(XObj, XObjMixin):
    """
    """
    inclusion_method_id = AutoField
    name = TextField
    _xobj = XObjMetadata

class FilteredMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class QueryTag(XObj, XObjMixin):
    """
    """
    query_set = ForeignKey
    name = TextField
    _xobj = XObjMetadata
    query_tag_id = AutoField

class AllMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class FilterEntry(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata
    value = TextField
    field = TextField
    filter_entry_id = AutoField
    operator = TextField

class QuerySet(XObj, XObjMixin):
    """
    """
    modified_date = DateTimeUtcField
    name = TextField
    can_modify = BooleanField
    _xobj = XObjMetadata
    query_set_id = AutoField
    created_date = DateTimeUtcField
    resource_type = TextField
    description = TextField

class QuerySets(XObj, XObjMixin):
    """
    """
    count = IntegerField
    next_page = TextField
    num_pages = IntegerField
    _xobj = XObjMetadata
    previous_page = TextField
    QuerySet = [QuerySet]
    full_collection = TextField
    end_index = IntegerField
    limit = TextField
    order_by = TextField
    per_page = IntegerField
    filter_by = TextField
    start_index = IntegerField

