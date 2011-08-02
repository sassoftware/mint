#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj


class ModuleHooks(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['module_hook']
    _xobj = xobj.XObjMetadata(tag='module_hooks')
    

class ModuleHook(modellib.XObjModel):
    url = models.TextField()
    _xobj = xobj.XObjMetadata(tag='module_hook')
