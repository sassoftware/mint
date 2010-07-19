#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime

from django.http import HttpResponse
from django_restapi import resource

from mint.django_rest.deco import requires, returns
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import systemdbmgr

from rpath_models import SystemsHref, Systems, System

MANAGER_CLASS = systemdbmgr.SystemDBManager

class _InventoryService(resource.Resource):

    def __init__(self):
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.sysMgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
        return resource.Resource.__call__(self, request, *args, **kw)

class InventoryService(_InventoryService):

    @returns('inventory')
    def read(self, request):
        inventoryParser = models.inventory().getParser()
        systemsHref = SystemsHref(href=request.build_absolute_uri('systems'))
        inventoryParser.set_systems(systemsHref)
        return inventoryParser

class InventorySystemsService(_InventoryService):

    @returns('systems')
    def read(self, request, system=None):
        if not system:
            systems = self.sysMgr.getSystems()
            systemsParser = Systems.factory()
            systemParsers = [s.getParser() for s in systems]
            [systemsParser.add_system(sp) for sp in systemParsers]
            return systemsParser
        else:
            system = self.sysMgr.getSystem(system)
            return system.getParser()
    
    @requires('system', System)
    @returns('system')
    def create(self, request, system):
        managedSystem = self.sysMgr.activateSystem(system)
        systemParser = managedSystem.getParser()
        return systemParser

    def launch(self, instanceId, targetType, targetName):
        return self.sysMgr.launchSystem(instanceId, targetType, targetName)
