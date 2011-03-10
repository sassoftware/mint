#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys

from django.db import models

from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.inventory import models as inventorymodels

from xobj import xobj

OPERATOR_CHOICES = [(k, v) for k, v in modellib.filterTermMap.items()]

class AllMembers(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "all_members")
    view_name = "QuerySetAllResult"

class ChosenMembers(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "chosen_members")
    view_name = "QuerySetChosenResult"

class FilteredMembers(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "filtered_members")
    view_name = "QuerySetFilteredResult"

class ChildMembers(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "child_members")
    view_name = "QuerySetChildResult"

class QuerySets(modellib.Collection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "query_sets")
    list_fields = ["query_set"]
    query_set = []

class FilterDescriptor(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "filter_descriptor")
    view_name = "QuerySetFilterDescriptor"

class CollectionId(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='collection')
                

class QuerySet(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = "query_set")

    query_set_id = D(models.AutoField(primary_key=True),
        "The database id for the query set")
    name = D(models.TextField(unique=True),
        "Query set name")
    description = D(models.TextField(null=True),
        "Query set description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "Date the query set was created")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "Date the query set was modified")
    children = D(models.ManyToManyField("self", symmetrical=False),
        "Query sets that are children of this query set")
    filter_entries = D(models.ManyToManyField("FilterEntry"),
        "Defined filter entries for this query set")
    resource_type = D(models.TextField(),
        "Name of the resource this query set operates on")
    can_modify = D(models.BooleanField(default=True),
        "Whether this query set can be deleted through the API.")

    load_fields = [name]

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)

        am = AllMembers()
        am._parents = [self]
        xobjModel.all_members = am.serialize(request)
        cm = ChosenMembers()
        cm._parents = [self]
        xobjModel.chosen_members = cm.serialize(request)
        fm = FilteredMembers()
        fm._parents = [self]
        xobjModel.filtered_members = fm.serialize(request)
        childM = ChildMembers()
        childM._parents = [self]
        xobjModel.child_members = childM.serialize(request)

        fd = FilterDescriptor()
        fd._parents = [self]
        xobjModel.filter_descriptor = fd.serialize(request)

        from mint.django_rest.rbuilder.querysets import manager
        collectionId = CollectionId()
        collectionId.view_name = \
            modellib.type_map[manager.QuerySetManager.resourceCollectionMap[self.resource_type]].view_name
        xobjModel.collection = collectionId.serialize(request)

        xobjModel.is_top_level = self.isTopLevel()

        return xobjModel

    def getFilterBy(self):
        filterBy = []
        for filterEntry in self.filter_entries.all():
            filterStr = '[%s,%s,%s]' % (filterEntry.field, filterEntry.operator,
                filterEntry.value)
            filterBy.append(filterStr)
        return ','.join(filterBy)

    def isTopLevel(self):
        parents = self.__class__.children.through.objects.filter(to_queryset=self)
        if parents:
            return False
        else: 
            return True

class FilterEntry(modellib.XObjIdModel):
    class Meta:
        unique_together = ('field', 'operator', 'value')

    _xobj = xobj.XObjMetadata(
                tag = "filter_entry")

    filter_entry_id = models.AutoField(primary_key=True)
    field = D(models.TextField(),
        "Field this filter operates on.  '.' in field names indicate resource relationships")
    operator = D(models.TextField(choices=OPERATOR_CHOICES),
        "Operator for this filter")
    value = D(models.TextField(null=True),
        "Value for this filter")

    load_fields = [field, operator, value]

class QueryTag(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = 'query_tag')

    query_tag_id = models.AutoField(primary_key=True)
    query_set = modellib.ForeignKey("QuerySet", related_name="querytags", null=True)
    query_tag = models.TextField()

class InclusionMethod(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = 'inclusion_method')

    METHOD_CHOICES = [
        ('chosen', 'Chosen'),
        ('filtered', 'Filtered'),
    ]

    inclusion_method_id = models.AutoField(primary_key=True)
    inclusion_method = models.TextField(choices=METHOD_CHOICES)

class SystemTag(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag = 'system_tag')

    system_tag_id = models.AutoField(primary_key=True)
    system = modellib.ForeignKey(inventorymodels.System)
    query_tag = modellib.ForeignKey(QueryTag)
    inclusion_method = modellib.ForeignKey(InclusionMethod)

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
