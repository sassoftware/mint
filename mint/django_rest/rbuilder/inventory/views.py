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
from mint.django_rest.rbuilder.inventory import manager

MANAGER_CLASS = manager.Manager

class AbstractInventoryService(resource.Resource):

    def __init__(self):
        self.mgr = MANAGER_CLASS(cfg=None)
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.mgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
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
        return self.mgr.getSystemsLog()
    
class InventoryZoneService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, zone_id=None):
        return self.get(zone_id)
    
    def get(self, zone_id=None):
        if zone_id:
            return self.mgr.getZone(zone_id)
        else:
            return self.mgr.getZones()
        
    @requires('zone')
    @return_xml
    def create(self, request, zone):
        zone = self.mgr.addZone(zone)
        return zone
    
class InventoryManagementNodeService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, zone_id, management_node_id=None):
        return self.get(zone_id, management_node_id)
    
    def get(self, zone_id, management_node_id=None):
        if management_node_id:
            return self.mgr.getManagementNode(zone_id, management_node_id)
        else:
            return self.mgr.getManagementNodes(zone_id)
        
    @requires('managementNode')
    @return_xml
    def create(self, request, managementNode):
        managementNode = self.mgr.addManagementNode(managementNode)
        return managementNode

class InventorySystemsService(AbstractInventoryService):

    @return_xml
    def read(self, request):
        return self.get()

    def get(self):
        return self.mgr.getSystems()

    @requires('system')
    @return_xml
    def create(self, request, system):
        system = self.mgr.addSystem(system)
        return system
    
    @requires('systems')
    @return_xml
    def update(self, request, systems):
        systems = self.mgr.addSystems(systems.system)
        return self.mgr.getSystems()

    def delete(self, request, system):
        system = self.mgr.deleteSystem(system)
        response = HttpResponse(status=204)
        return response

    def launch(self, instanceId, targetType, targetName):
        return self.mgr.launchSystem(instanceId, targetType, targetName)

class InventorySystemsSystemService(AbstractInventoryService):
    @return_xml
    def read(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystem(system_id)

    @requires('system', save=False)
    @return_xml
    def update(self, request, system_id, system):
        oldSystem = self.mgr.getSystem(system_id)
        if not oldSystem:
            return HttpResponse(status=404)
        # This really should be an update
        self.mgr.updateSystem(system)
        return self.mgr.getSystem(system_id)

    def delete(self, request, system_id):
        system = self.mgr.deleteSystem(system_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsSystemEventService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system_id, system_event_id=None):
        return self.get(system_id)
        
    def get(self, system_id, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemSystemEvent(system_id, system_event_id)
        else:
            return self.mgr.getSystemSystemEvents(system_id)
        
    @requires('systemEvent')
    @return_xml
    def create(self, request, system_id, systemEvent):
        systemEvent = self.mgr.addSystemSystemEvent(system_id, systemEvent)
        return systemEvent

class InventorySystemsSystemLogService(AbstractInventoryService):

    def read(self, request, system, format='xml'):
        managedSystem = self.mgr.getSystem(system)
        systemLog = self.mgr.getSystemLog(managedSystem)

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
            return self.mgr.getSystemEvent(system_event_id)
        else:
            return self.mgr.getSystemEvents()

class InventorySystemEventsByTypeService(AbstractInventoryService):

    @return_xml
    def read(self, request, event_type):
        # TODO, something for real
        return None

class InventorySystemsInstalledSoftwareService(AbstractInventoryService):
    @return_xml
    def read(self, request, system_id):
        system = self.mgr.getSystem(system_id)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

    @requires('installedSoftware')
    @return_xml
    def create(self, request, system_id, installedSoftware):
        system = self.mgr.getSystem(system_id)
        self.mgr.setInstalledSoftware(system, installedSoftware.trove)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

class InventoryEventTypesService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, event_type_id=None):
        return self.get(event_type_id)
        
    def get(self, event_type_id=None):
        if event_type_id:
            return self.mgr.getEventType(event_type_id)
        else:
            return self.mgr.getEventTypes()

class InventoryJobsService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system, job_uuid=None):
        return self.mgr.getSystemJobs(system, job_uuid)
