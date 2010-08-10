#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from django.http import HttpResponse
from django_restapi import resource

from mint.django_rest.deco import requires, return_xml
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import systemdbmgr

MANAGER_CLASS = systemdbmgr.SystemDBManager

class AbstractInventoryService(resource.Resource):

    def __init__(self):
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.sysMgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
        return resource.Resource.__call__(self, request, *args, **kw)

    def read(self, request, *args, **kwargs):
        response = HttpResponse(status=405)
        return response

    def create(self, request, *args, **kwargs):
        response = HttpResponse(status=405)
        return response

    def update(self, request, *args, **kwargs):
        response = HttpResponse(status=405)
        return response

    def delete(self, request, *args, **kwargs):
        response = HttpResponse(status=405)
        return response

class InventoryService(AbstractInventoryService):

    @return_xml
    def read(self, request):
        inventory = models.Inventory()
        return inventory

class InventoryLogService(AbstractInventoryService):
    
    @return_xml
    def read(self, request):
        log = models.Log()
        return log

class InventorySystemsService(AbstractInventoryService):

    @return_xml
    def read(self, request, system_id=None):
        if system_id:
            return self.sysMgr.getSystem(system_id)
        else:
            return self.sysMgr.getSystems()
    
    @requires('system')
    @return_xml
    def create(self, request, system):
        system = self.sysMgr.addSystem(system)
        return system

    def delete(self, request, system):
        system = self.sysMgr.deleteSystem(system)
        response = HttpResponse(status=204)
        return response

    def launch(self, instanceId, targetType, targetName):
        return self.sysMgr.launchSystem(instanceId, targetType, targetName)


class InventorySystemsSystemLogService(AbstractInventoryService):

    def read(self, request, system, format='xml'):
        managedSystem = self.sysMgr.getSystem(system)
        systemLog = self.sysMgr.getSystemLog(managedSystem)

        if format == 'xml':
            parserDecorator = return_xml
            func = parserDecorator(systemLog.getParser)
            return func()
        elif format == 'raw':
            tzSave = os.environ['TZ']
            os.environ['TZ'] = request.environ['TZ']
            time.tzset()
            os.environ['TZ'] = tzSave
            entries = [(time.strftime('%m-%d-%Y %H:%M:%S -- ', time.localtime(log.entry_date)), 
                        log.entry.entry) for \
                       log in systemLog.related_models[models.system_log_entry]]
            strEntries = [' '.join(e) for e in entries]
            strEntries.sort()
            response = HttpResponse(mimetype='text/plain')
            response.write('\n'.join(strEntries))
            return response
        else:
            pass

class InventoryUsersService(AbstractInventoryService):
    
    def read(self, request, user):
        if request:
            response = HttpResponse()
            response.write('<html>%s</html>' % user)
            return response
        else:
            user = rbuildermodels.Users.objects.get(username=user)
            return user

class InventorySystemsEventService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system_event_id=None):
        if system_event_id:
            return self.sysMgr.getSystemEvent(system_event_id)
        else:
            return self.sysMgr.getSystemEvents()

