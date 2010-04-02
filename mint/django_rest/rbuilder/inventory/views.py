#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse
from django_restapi import resource

from mint.django_rest.deco import requires
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import systemmgr

MANAGER_CLASS = systemdbmgr.SystemDBManager

class InventoryService(resouce.Resource):

    def __init__(self):
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        return resource.Resource(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.sysMgr = MANAGER_CLASS(request.cfg)
        return resource.Resource.__call__(self, request, *args, **kw)

class InventorySystemsService(InventoryService):

    def read(self, request):
        self.sysMgr.getSystem()
        return HttpResponse()
    
    @requires('system', models.Systems)
    def create(self, request, system):
        return self.sysMgr.registerSystem(system)
        
