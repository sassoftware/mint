#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.projects import models as projectmodels

Cache = modellib.Cache
XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly

class Label(modellib.XObjIdModel):
    class Meta:
        db_table = "labels"

    label_id = models.AutoField(primary_key=True, 
        db_column="labelid")
    project = XObjHidden(modellib.ForeignKey(projectmodels.Project,
        related_name="labels",
        db_column="projectid"))
    label = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    auth_type = models.CharField(max_length=32, default="none",
        db_column="authtype")
    user_name = models.CharField(max_length=255, null=True,
        db_column="username")
    password = models.CharField(max_length=255, null=True)
    entitlement = models.CharField(max_length=254, null=True)
    
    def save(self, *args, **kwargs):
        if not self.url:
            if self.auth_type != "none":
                self.url = "https://%s/conary/" % self.project.repository_hostname
            else:
                self.url = "http://%s/conary/" % self.project.repository_hostname
            
        return modellib.XObjIdModel.save(self, *args, **kwargs)


class AuthInfo(modellib.XObjModel):
    class Meta:
        abstract = True
    auth_type = models.TextField()
    user_name = models.TextField()
    # TODO: need to make sure password will never show up in a traceback, may
    # need a new field type for protected strings.
    password = models.TextField()
    entitlement = models.TextField()

class RepNameMap(modellib.XObjModel):
    class Meta:
        db_table = "repnamemap"
        unique_together = ("from_name", "to_name")

    from_name = models.CharField(max_length=255,
        db_column="fromname")
    to_name = models.CharField(max_length=255,
        db_column="toname")
    
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
