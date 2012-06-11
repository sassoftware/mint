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
from mint.rest.api.models.capsules import *
from mint.rest.api.models.members import *
from mint.rest.api.models.siteauth import *
from mint.rest.api.models.users import *
from mint.rest.api.models.repos import *
from mint.rest.api.models.descriptor import *
from mint.rest.api.models.platforms import *
from mint.rest.api.models.products import *
from mint.rest.api.models.productversions import *
from mint.rest.api.models.images import *

class RbuilderStatus(Model):
    id                      = fields.AbsoluteUrlField(isAttribute=True)
    version                 = fields.CharField()
    conaryVersion           = fields.CharField()
    rmakeVersion            = fields.CharField()
    userName                = fields.CharField()
    hostName                = fields.CharField()
    isRBO                   = fields.BooleanField()
    identity                = fields.ModelField(Identity)
    rmcService              = RMCUrlField()
    products                = fields.UrlField('products', None)
    users                   = fields.UrlField('users', None)
    platforms               = fields.UrlField('platforms', None)
    registration            = fields.UrlField('registration', None)
    reports                 = fields.UrlField('reports/', None)
    maintMode               = fields.BooleanField()
    proddefSchemaVersion    = fields.CharField()

    def get_absolute_url(self):
        return '',

class Fault(Model):
    code = fields.IntegerField()
    message = fields.CharField()
    traceback = fields.CharField()
