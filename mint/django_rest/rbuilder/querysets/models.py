#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.inventory import models as inventorymodels

from xobj import xobj

OPERATOR_CHOICES = [(k, v) for k, v in modellib.filterTermMap.items()]

class QuerySets(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "query_sets")
    list_fields = ["query_set"]
    query_set = []

class QuerySet(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = "query_set")

    query_set_id = models.AutoField(primary_key=True)
    name = models.TextField()
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    modified_date = modellib.DateTimeUtcField(auto_now_add=True)
    children = models.ManyToManyField("self", symmetrical=False)
    filter_entries = models.ManyToManyField("FilterEntry")
    resource_type = models.TextField()

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request, values)

        self.view_name = 'QuerySetAllResult'
        xobjModel.allMembers = self.get_absolute_url(request)
        self.view_name = 'QuerySetChosenResult'
        xobjModel.chosenMembers = self.get_absolute_url(request)
        self.view_name = 'QuerySetFilteredResult'
        xobjModel.filteredMembers = self.get_absolute_url(request)

        return xobjModel

class FilterEntry(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = "filter_entry")

    filter_entry_id = models.AutoField(primary_key=True)
    field = models.TextField()
    operator = models.TextField(choices=OPERATOR_CHOICES)
    value = models.TextField()

class QueryTag(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = 'query_tag')

    query_tag_id = models.AutoField(primary_key=True)
    query_set = modellib.ForeignKey("QuerySet", related_name="querytags", null=True)
    query_tag = models.TextField()

class InclusionMethod(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag = 'includsion_method')

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
