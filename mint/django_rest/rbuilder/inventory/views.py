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
from mint.django_rest.rbuilder.inventory import versionmgr

MANAGER_CLASS = systemdbmgr.SystemDBManager

class AbstractInventoryService(resource.Resource):

    def __init__(self):
        self.sysMgr = MANAGER_CLASS(cfg=None)
        self.versionMgr = versionmgr.VersionManager(cfg=None)
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.sysMgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
        self.versionMgr = versionmgr.VersionManager(
            cfg=getattr(request, 'cfg', None))
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
        return self.sysMgr.getSystemsLog()
    
class InventoryManagementNodeService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, management_node_id=None):
        return self.get(management_node_id)
    
    def get(self, management_node_id=None):
        if management_node_id:
            return self.sysMgr.getManagementNode(management_node_id)
        else:
            return self.sysMgr.getManagementNodes()
        
    @requires('managementNode')
    @return_xml
    def create(self, request, managementNode):
        managementNode = self.sysMgr.addManagementNode(managementNode)
        return managementNode

class InventorySystemsService(AbstractInventoryService):

    @return_xml
    def read(self, request, system_id=None):
        return self.get(system_id)
    
    def get(self, system_id=None):
        if system_id:
            return self.sysMgr.getSystem(system_id)
        else:
            return self.sysMgr.getSystems()

    @requires('system')
    @return_xml
    def create(self, request, system):
        system = self.sysMgr.addSystem(system)
        return system
    
    @requires('systems')
    @return_xml
    def update(self, request, systems):
        systems = self.sysMgr.addSystems(systems.system)
        return self.sysMgr.getSystems()

    def delete(self, request, system):
        system = self.sysMgr.deleteSystem(system)
        response = HttpResponse(status=204)
        return response

    def launch(self, instanceId, targetType, targetName):
        return self.sysMgr.launchSystem(instanceId, targetType, targetName)

class InventorySystemsSystemEventService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system_id, system_event_id=None):
        return self.get(system_id)
        
    def get(self, system_id, system_event_id=None):
        if system_event_id:
            return self.sysMgr.getSystemSystemEvent(system_id, system_event_id)
        else:
            return self.sysMgr.getSystemSystemEvents(system_id)
        
    @requires('systemEvent')
    @return_xml
    def create(self, request, system_id, systemEvent):
        systemEvent = self.sysMgr.addSystemSystemEvent(system_id, systemEvent)
        return systemEvent

class InventorySystemsSystemLogService(AbstractInventoryService):

    def read(self, request, system, format='xml'):
        managedSystem = self.sysMgr.getSystem(system)
        systemLog = self.sysMgr.getSystemLog(managedSystem)

        if format == 'xml':
            func = lambda x, req: systemLog
            func = return_xml(func)
            return func(None, request)
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
        response = HttpResponse()
        response.write('<html>%s</html>' % user)
        return response

    def get(self, user):
        user = rbuildermodels.Users.objects.get(username=user)
        return user

class InventorySystemEventsService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system_event_id=None):
        return self.get(system_event_id)
        
    def get(self, system_event_id=None):
        if system_event_id:
            return self.sysMgr.getSystemEvent(system_event_id)
        else:
            return self.sysMgr.getSystemEvents()

class InventorySystemEventsByTypeService(AbstractInventoryService):

    @return_xml
    def read(self, request, event_type):
        # TODO, something for real
        return None

class InventorySystemsInstalledSoftwareService(AbstractInventoryService):
    @return_xml
    def read(self, request, system_id):
        system = self.sysMgr.getSystem(system_id)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

    @requires('installedSoftware')
    @return_xml
    def create(self, request, system_id, installedSoftware):
        system = self.sysMgr.getSystem(system_id)
        self.versionMgr.set_installed_software(system, installedSoftware.trove)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

class InventoryEventTypesService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, event_type_id=None):
        return self.get(event_type_id)
        
    def get(self, event_type_id=None):
        if event_type_id:
            return self.sysMgr.getEventType(event_type_id)
        else:
            return self.sysMgr.getEventTypes()

class InventoryJobsService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system, job_uuid=None):
        return self.sysMgr.getSystemJobs(system, job_uuid)
