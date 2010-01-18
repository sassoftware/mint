#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

from mint.rest.modellib import Model
from mint.rest.modellib import fields

class ModuleHook(Model):
    url = fields.CharField()

class ModuleHooks(Model):
    class Meta(object):
        name = 'moduleHooks'
    moduleHooks = fields.ListField(ModuleHook, displayName='moduleHooks')

