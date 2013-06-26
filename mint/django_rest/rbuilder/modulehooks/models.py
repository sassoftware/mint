#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys

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


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
