from sdk.Fields import *  # pyflakes=ignore
from sdk.rSDK import XObjMixin
from sdk.rSDK import GetSetXMLAttrMeta  # pyflakes=ignore
from xobj.xobj import XObj


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
    system = ForeignKey
    query_tag = ForeignKey
    inclusion_method = SerializedForeignKey
    _xobj = XObjMetadata

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
    name = TextField
    inclusion_method_id = AutoField
    _xobj = XObjMetadata

class FilteredMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class QueryTag(XObj, XObjMixin):
    """
    """
    query_tag_id = AutoField
    query_set = ForeignKey
    name = TextField
    _xobj = XObjMetadata

class AllMembers(XObj, XObjMixin):
    """
    """
    _xobj = XObjMetadata

class FilterEntry(XObj, XObjMixin):
    """
    """
    value = TextField
    operator = TextField
    filter_entry_id = AutoField
    field = TextField
    _xobj = XObjMetadata

class QuerySet(XObj, XObjMixin):
    """
    """
    resource_type = TextField
    query_set_id = AutoField
    name = TextField
    modified_date = DateTimeUtcField
    description = TextField
    created_date = DateTimeUtcField
    can_modify = BooleanField
    _xobj = XObjMetadata

class QuerySets(XObj, XObjMixin):
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
    query_set = [QuerySet]

