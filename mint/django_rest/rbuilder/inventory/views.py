#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from django.http import HttpResponse, HttpResponseNotAllowed
from django_restapi import resource

from mint.django_rest.deco import requires, return_xml, access, ACCESS, HttpAuthenticationRequired
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import manager

MANAGER_CLASS = manager.Manager

def undefined(function):
    function.undefined = True
    return function

class AbstractInventoryService(resource.Resource):

    def __init__(self):
        self.mgr = MANAGER_CLASS(cfg=None)
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.mgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
        return resource.Resource.__call__(self, request, *args, **kw)

    def read(self, request, *args, **kwargs):
        return self._auth(self.rest_GET, request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self._auth(self.rest_POST, request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._auth(self.rest_PUT, request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self._auth(self.rest_DELETE, request, *args, **kwargs)

    # Overwrite these functions when inheriting
    @undefined
    @access.anonymous
    def rest_GET(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_POST(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_PUT(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_DELETE(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())


    @classmethod
    def _getPermittedMethods(cls):
        methods = [ 'GET', 'POST', 'PUT', 'DELETE' ]
        # Methods of this class are undefined
        return [ x for x in methods
            if not getattr(getattr(cls, 'rest_%s' % x), 'undefined', False) ]
        

    @classmethod
    def _auth(cls, method, request, *args, **kwargs):
        """
        Verify authentication and run the specified method
        """
        # By default, everything has to be authenticated
        access = getattr(method, 'ACCESS', ACCESS.AUTHENTICATED)
        # If authentication is present, but it's bad, simply give up, even if
        # we're allowing anonymous access
        if request._auth != (None, None) and not request._is_authenticated:
            return HttpAuthenticationRequired
        if access & ACCESS.EVENT_UUID:
            # Event UUID authentication is special - it can be compounded with
            # regular authentication or admin
            headerName = 'X-rBuilder-Event-UUID'
            # HTTP_THANK_YOU_DJANGO_FOR_MANGLING_THE_HEADERS
            mangledHeaderName = 'HTTP_' + headerName.replace('-', '_').upper()
            eventUuid = request.META.get(headerName,
                request.META.get(mangledHeaderName))
            if eventUuid:
                # Check if this system has such an event uuid
                systemId = kwargs['system_id']
                sjobs = models.SystemJob.objects.filter(
                    system__pk=systemId, event_uuid=eventUuid)
                if not sjobs:
                    return HttpAuthenticationRequired
            elif cls._check_not_authenticated(request, access) \
                    or cls._check_not_admin(request, access):
                return HttpAuthenticationRequired
        elif cls._check_not_authenticated(request, access):
            return HttpAuthenticationRequired
        elif cls._check_not_admin(request, access):
            return HttpAuthenticationRequired
        return method(request, *args, **kwargs)

    @classmethod
    def _check_not_authenticated(cls, request, access):
        return access & ACCESS.AUTHENTICATED and not request._is_authenticated

    @classmethod
    def _check_not_admin(cls, request, access):
        return access & ACCESS.ADMIN and not request._is_admin

class InventoryService(AbstractInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        inventory = models.Inventory()
        return inventory

class InventoryLogService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getSystemsLog()
    
class InventorySystemStateService(AbstractInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_state_id=None):
        return self.get(system_state_id)
    
    def get(self, system_state_id=None):
        if system_state_id:
            return self.mgr.getSystemState(system_state_id)
        else:
            return self.mgr.getSystemStates()
    
class InventoryZoneService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, zone_id=None):
        return self.get(zone_id)
    
    def get(self, zone_id=None):
        if zone_id:
            return self.mgr.getZone(zone_id)
        else:
            return self.mgr.getZones()

    @access.admin
    @requires('zone')
    @return_xml
    def rest_POST(self, request, zone):
        zone = self.mgr.addZone(zone)
        return zone
    
    @access.admin
    @requires('zone')
    @return_xml
    def rest_PUT(self, request, zone_id, zone):
        oldZone = self.mgr.getZone(zone_id)
        if not oldZone:
            return HttpResponse(status=404)
        self.mgr.updateZone(zone)
        return self.mgr.getZone(zone_id)
    
    @access.admin
    def rest_DELETE(self, request, zone_id):
        zone = self.get(zone_id)
        if zone:
            self.mgr.deleteZone(zone)
        response = HttpResponse(status=204)
        return response
    
class InventoryManagementNodeService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, management_node_id=None):
        return self.get(management_node_id)
    
    def get(self, management_node_id=None):
        if management_node_id:
            return self.mgr.getManagementNode(management_node_id)
        else:
            return self.mgr.getManagementNodes()
        
    @access.admin
    @requires('management_node')
    @return_xml
    def rest_POST(self, request, management_node):
        managementNode = self.mgr.addManagementNode(management_node)
        return managementNode
    
class InventoryZoneManagementNodeService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, zone_id, management_node_id=None):
        return self.get(zone_id, management_node_id)
    
    def get(self, zone_id, management_node_id=None):
        if management_node_id:
            return self.mgr.getManagementNodeForZone(zone_id, management_node_id)
        else:
            return self.mgr.getManagementNodesForZone(zone_id)
        
    @access.admin
    @requires('management_node')
    @return_xml
    def rest_POST(self, request, zone_id, management_node):
        managementNode = self.mgr.addManagementNodeForZone(zone_id,
            management_node)
        return managementNode

class InventoryNetworkService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, network_id=None):
        return self.get(network_id)
    
    def get(self, network_id=None):
        if network_id:
            return self.mgr.getNetwork(network_id)
        else:
            return self.mgr.getNetworks()
        
    @access.admin
    @requires('network')
    @return_xml
    def rest_PUT(self, request, network_id, network):
        oldNetwork = self.get(network_id)
        if not oldNetwork:
            return HttpResponse(status=404)
        if int(network_id) != network.pk:
            return HttpResponse(status=404)
        # This really should be an update
        self.mgr.updateNetwork(network)
        return self.get(network_id)
    
    @access.admin
    def rest_DELETE(self, request, network_id):
        self.mgr.deleteNetwork(network_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsService(AbstractInventoryService):

    @return_xml
    def rest_GET(self, request):
        return self.mgr.getSystems(request)

    def get(self):
        return self.mgr.getSystems(request=None)

    # this must remain public for rpath-tools
    @access.anonymous
    @requires(['system', 'systems'])
    @return_xml
    def rest_POST(self, request, system=None, systems=None):
        if system is not None:
            system = self.mgr.addSystem(system, generateCertificates=True)
            return system
        systems = self.mgr.addSystems(systems.system)
        return self.mgr.getSystems(request)

class InventorySystemsSystemService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystem(system_id)

    @access.event_uuid
    @access.authenticated
    @requires('system')
    @return_xml
    def rest_PUT(self, request, system_id, system):
        oldSystem = self.mgr.getSystem(system_id)
        if not oldSystem:
            return HttpResponse(status=404)
        # This is a terrible place to put logic, but until we decide to pass
        # the request into the manager, we don't have a way around it
        mb = models.SystemState.MOTHBALLED
        if oldSystem.current_state.name != mb and \
                system.current_state.name == mb:
            if not request._is_admin:
                return HttpAuthenticationRequired
        # This really should be an update
        self.mgr.updateSystem(system)
        return self.mgr.getSystem(system_id)

    @access.admin
    def rest_DELETE(self, request, system_id):
        self.mgr.deleteSystem(system_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsSystemEventService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, system_id, system_event_id=None):
        return self.get(system_id)
        
    def get(self, system_id, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemSystemEvent(system_id, system_event_id)
        else:
            return self.mgr.getSystemSystemEvents(system_id)
        
    @requires('system_event')
    @return_xml
    def rest_POST(self, request, system_id, system_event):
        systemEvent = self.mgr.addSystemSystemEvent(system_id, system_event)
        return systemEvent

class InventorySystemsSystemLogService(AbstractInventoryService):

    def rest_GET(self, request, system_id, format='xml'):
        managedSystem = self.mgr.getSystem(system_id)
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
    
    @return_xml
    def rest_GET(self, request, system_event_id=None):
        return self.get(system_event_id)
        
    def get(self, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemEvent(system_event_id)
        else:
            return self.mgr.getSystemEvents()

class InventorySystemsInstalledSoftwareService(AbstractInventoryService):
    
    @return_xml
    def rest_GET(self, request, system_id):
        system = self.mgr.getSystem(system_id)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

class InventoryEventTypesService(AbstractInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, event_type_id=None):
        return self.get(event_type_id)
        
    def get(self, event_type_id=None):
        if event_type_id:
            return self.mgr.getEventType(event_type_id)
        else:
            return self.mgr.getEventTypes()
        
    @access.admin
    @requires('event_type')
    @return_xml
    def rest_PUT(self, request, event_type_id, event_type):
        old_event_type = self.get(event_type_id)
        if not old_event_type:
            return HttpResponse(status=404)
        # This really should be an update
        self.mgr.updateEventType(event_type)
        return self.get(event_type_id)

class InventorySystemJobsService(AbstractInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_id, job_id=None):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystemJobs(system_id)

class InventoryJobsService(AbstractInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_id=None):
        return self.get(job_id)

    def get(self, job_id):
        if job_id:
            return self.mgr.getJob(job_id)
        else:
            return self.mgr.getJobs()

class InventoryJobStatesService(AbstractInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id=None):
        return self.get(job_state_id)

    def get(self, job_state_id):
        if job_state_id:
            return self.mgr.getJobState(job_state_id)
        else:
            return self.mgr.getJobStates()

class InventoryJobStatesJobsService(AbstractInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id):
        return self.get(job_state_id)

    def get(self, job_state_id):
        return self.mgr.getJobsByJobState(job_state_id)

class InventorySystemJobStatesService(AbstractInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_id, job_state_id):
        return self.get(system_id, job_state_id)

    def get(self, system_id, job_state_id):
        return self.mgr.getSystemJobsByState(system_id, job_state_id)
