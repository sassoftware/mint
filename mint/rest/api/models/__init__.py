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


from mint.rest.api.models.members import *
from mint.rest.api.models.identity import *
from mint.rest.api.models.users import *
from mint.rest.api.models.products import *
from mint.rest.api.models.productversions import *
from mint.rest.api.models.images import *
from mint.rest.api.models.repos import *

class RbuilderStatus(Model):
    id            = fields.AbsoluteUrlField(isAttribute=True)
    version       = fields.CharField()
    conaryVersion = fields.CharField()
    isRBO         = fields.BooleanField()
    identity      = fields.ModelField(Identity)
    rmcService    = RMCUrlField()
    products      = fields.UrlField('products', None)
    users         = fields.UrlField('users', None)

    def get_absolute_url(self):
        return '',
