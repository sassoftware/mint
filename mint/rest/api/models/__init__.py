#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
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
