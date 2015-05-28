#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
