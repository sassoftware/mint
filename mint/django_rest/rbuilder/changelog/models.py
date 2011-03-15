#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys

from django.db import models
from django.core import exceptions

from mint.django_rest.rbuilder import modellib
# from mint.django_rest.rbuilder.inventory import models as inventorymodels

from xobj import xobj


class ChangeLogs(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "change_logs")
    list_fields = ['change_log']

class ChangeLog(modellib.XObjIdModel):
    class Meta:
        db_table = "changelog_change_log"
    _xobj = xobj.XObjMetadata(
                tag = "change_log")

    change_log_id = models.AutoField(primary_key=True)
    resource_type = models.TextField()
    resource_id = models.IntegerField()

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request, values)
        resourceIdModel = modellib.XObjIdModel()
        resourceIdModel.view_name = getattr(
            modellib.type_map[self.resource_type], 'view_name', None)
        try:
            resourceIdModel._parents = [modellib.type_map[self.resource_type].objects.get(
                pk=self.resource_id)]
        except exceptions.ObjectDoesNotExist:
            pass
        setattr(xobjModel, self.resource_type, resourceIdModel.serialize(request))
        return xobjModel

class ChangeLogEntry(modellib.XObjIdModel):
    class Meta:
        db_table = "changelog_change_log_entry"
    _xobj = xobj.XObjMetadata(
                tag = "change_log_entry")

    change_log_entry_id = models.AutoField(primary_key=True)
    change_log = modellib.ForeignKey(ChangeLog, refName='id',
        related_name='change_log_entries')
    entry_date = modellib.DateTimeUtcField(auto_now_add=True)
    entry_text = models.TextField()
    # field_name = models.TextField()
    # old_value = models.TextField(null=True)
    # new_value = models.TextField()

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
