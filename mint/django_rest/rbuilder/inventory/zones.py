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
from xobj import xobj

from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib

class Zones(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='zones',
                elements=['zone'])
    list_fields = ['zone']

class Zone(modellib.XObjIdModel):

    LOCAL_ZONE = "Local rBuilder"
    class Meta:
        db_table = 'inventory_zone'
    _xobj = xobj.XObjMetadata(
                tag = 'zone',
                attributes = {'id':str})

    # Don't inline all the systems now.  Do not remove this code!
    # See https://issues.rpath.com/browse/RBL-7236 and 
    # https://issues.rpath.com/browse/RBL-7237 for more info
    _xobj_hidden_accessors = set(['systems', 'targets', ])

    zone_id = D(models.AutoField(primary_key=True), "the database id for the zone")
    name = D(models.CharField(max_length=8092, unique=True), "the zone name")
    description = D(models.CharField(max_length=8092, null=True), "the zone description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the zone was created (UTC)")

    load_fields = [ name ]

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
