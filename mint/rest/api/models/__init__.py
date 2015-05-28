#!/usr/bin/python
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


from mint.rest.modellib import Model
from mint.rest.modellib import fields

class RMCUrlField(fields.CalculatedField):
    def getValue(self, controller, request, class_, parent, value):
        return request.getHostWithProtocol() + '/catalog' 

from mint.rest.api.models.builddefinitions import *
from mint.rest.api.models.members import *
from mint.rest.api.models.users import *
from mint.rest.api.models.repos import *
from mint.rest.api.models.descriptor import *
from mint.rest.api.models.platforms import *
from mint.rest.api.models.products import *
from mint.rest.api.models.productversions import *
from mint.rest.api.models.images import *
from mint.rest.api.models.modulehooks import *

class Fault(Model):
    code = fields.IntegerField()
    message = fields.CharField()
    traceback = fields.CharField()
