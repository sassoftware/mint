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

class InventoryService(resource.Resource):

    def read(self, request):
        sysMgr = systemmgr.SystemManager(request.cfg)
        return HttpResponse()
    
    @requires('system', models.Systems)
    def create(self, request):
        sysMgr = systemmgr.SystemManager(request.cfg)
        # return systemmgr.SystemManager.addSystem()
