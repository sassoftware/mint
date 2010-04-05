#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse
from django_restapi import resource

from mint.django_rest.deco import requires
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import systemdbmgr

MANAGER_CLASS = systemdbmgr.SystemDBManager

class InventoryService(resource.Resource):

    def __init__(self):
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.sysMgr = MANAGER_CLASS(request.cfg)
        return resource.Resource.__call__(self, request, *args, **kw)

class InventorySystemsService(InventoryService):

    def read(self, request):
        systems = self.sysMgr.getSystems()
        resp = [str((s.id, s.registrationDate)) for s in systems]
        return HttpResponse(str(resp))
    
    @requires('system', models.ManagedSystems)
    def create(self, request, system):
        return self.sysMgr.registerSystem(system)

    def launch(self, instanceId, targetType, targetName):
        return self.sysMgr.launchSystem(instanceId, targetType, targetName)
        
