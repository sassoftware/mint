#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from django.http import HttpResponse
from django_restapi import resource

from mint.django_rest.deco import requires, return_xml, requires_auth, requires_admin
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
    
    @requires_auth
    @return_xml
    def read(self, request):
        return self.mgr.getSystemsLog()
    
class InventorySystemStateService(AbstractInventoryService):
    
    @return_xml
    def read(self, request, system_state_id=None):
        return self.get(system_state_id)
    
    def get(self, system_state_id=None):
        if system_state_id:
            return self.mgr.getSystemState(system_state_id)
        else:
            return self.mgr.getSystemStates()
    
class InventoryZoneService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, zone_id=None):
        return self.get(zone_id)
    
    def get(self, zone_id=None):
        if zone_id:
            return self.mgr.getZone(zone_id)
        else:
            return self.mgr.getZones()

    @requires_admin
    @requires('zone')
    @return_xml
    def create(self, request, zone):
        zone = self.mgr.addZone(zone)
        return zone
    
    @requires_admin
    @requires('zone')
    @return_xml
    def update(self, request, zone_id, zone):
        oldZone = self.mgr.getZone(zone_id)
        if not oldZone:
            return HttpResponse(status=404)
        self.mgr.updateZone(zone)
        return self.mgr.getZone(zone_id)
    
    @requires_admin
    def delete(self, request, zone_id):
        zone = self.get(zone_id)
        if zone:
            self.mgr.deleteZone(zone)
        response = HttpResponse(status=204)
        return response
    
class InventoryManagementNodeService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, zone_id, management_node_id=None):
        return self.get(zone_id, management_node_id)
    
    def get(self, zone_id, management_node_id=None):
        if management_node_id:
            return self.mgr.getManagementNode(zone_id, management_node_id)
        else:
            return self.mgr.getManagementNodes(zone_id)
        
    @requires_admin
    @requires('managementNode')
    @return_xml
    def create(self, request, zone_id, managementNode):
        managementNode = self.mgr.addManagementNode(zone_id, managementNode)
        return managementNode

class InventorySystemsService(AbstractInventoryService):

    @requires_auth
    @return_xml
    def read(self, request):
        return self.get()

    def get(self):
        return self.mgr.getSystems()

    # this must remain public for rpath-tools
    @requires('system')
    @return_xml
    def create(self, request, system):
        system = self.mgr.addSystem(system, generateCertificates=True)
        return system
    
    # this must remain public for rpath-tools
    @requires('systems')
    @return_xml
    def update(self, request, systems):
        systems = self.mgr.addSystems(systems.system)
        return self.mgr.getSystems()

    def launch(self, instanceId, targetType, targetName):
        return self.mgr.launchSystem(instanceId, targetType, targetName)

class InventorySystemsSystemService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystem(system_id)

    @requires('system')
    @return_xml
    def update(self, request, system_id, system):
        oldSystem = self.mgr.getSystem(system_id)
        if not oldSystem:
            return HttpResponse(status=404)
        # This really should be an update
        self.mgr.updateSystem(system)
        return self.mgr.getSystem(system_id)

    @requires_admin
    def delete(self, request, system_id):
        self.mgr.deleteSystem(system_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsSystemEventService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, system_id, system_event_id=None):
        return self.get(system_id)
        
    def get(self, system_id, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemSystemEvent(system_id, system_event_id)
        else:
            return self.mgr.getSystemSystemEvents(system_id)
        
    @requires_auth
    @requires('systemEvent')
    @return_xml
    def create(self, request, system_id, systemEvent):
        systemEvent = self.mgr.addSystemSystemEvent(system_id, systemEvent)
        return systemEvent

class InventorySystemsSystemLogService(AbstractInventoryService):

    @requires_auth
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

    # used by modeelib
    def get(self, user):
        user = rbuildermodels.Users.objects.get(username=user)
        return user

class InventorySystemEventsService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, system_event_id=None):
        return self.get(system_event_id)
        
    def get(self, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemEvent(system_event_id)
        else:
            return self.mgr.getSystemEvents()

class InventorySystemsInstalledSoftwareService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, system_id):
        system = self.mgr.getSystem(system_id)
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

class InventorySystemJobsService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, system):
        return self.get(system)

    def get(self, system):
        return self.mgr.getSystemJobs(system)

class InventoryJobsService(AbstractInventoryService):
    
    @requires_auth
    @return_xml
    def read(self, request, job_id=None):
        return self.get(job_id)

    def get(self, job_id):
        if job_id:
            return self.mgr.getJob(job_id)
        else:
            return self.mgr.getJobs()

class InventoryJobStatesService(AbstractInventoryService):

    @requires_auth
    @return_xml
    def read(self, request, job_state=None):
        return self.get(job_state)

    def get(self, job_state):
        if job_state:
            return self.mgr.getJobState(job_state)
        else:
            return self.mgr.getJobStates()

class InventoryJobStatesJobsService(AbstractInventoryService):

    @requires_auth
    @return_xml
    def read(self, request, job_state):
        return self.get(job_state)

    def get(self, job_state):
        return self.mgr.getJobsByJobState(job_state)

