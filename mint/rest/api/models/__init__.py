#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import Model
from mint.rest.modellib import fields

class RbuilderStatus(Model):
    version       = fields.CharField()
    conaryVersion = fields.CharField()
    products      = fields.UrlField('products', None)
    users         = fields.UrlField('users', None)

from members import *
from users import *
from products import *
from productversions import *
from images import *
from repos import *
