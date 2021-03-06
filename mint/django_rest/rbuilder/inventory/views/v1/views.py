#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from mint.django_rest.deco import requires, return_xml, access, \
    HttpAuthenticationRequired, Flags
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS
from mint.django_rest.rbuilder import service
from django_restapi import resource
from mint.django_rest.rbuilder.rbac.rbacauth import rbac, manual_rbac
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.users import models as usersmodels

import os 
import time

##############################################
# rbac decorators

def rbac_can_write_system_id(view, request, system_id, *args, **kwargs):
    '''is the system ID writeable by the user?'''
    obj = view.mgr.getSystem(system_id)
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, obj, MODMEMBERS)

def rbac_can_read_system_id(view, request, system_id, *args, **kwargs):
    '''is the system ID readable by the user?'''
    obj = view.mgr.getSystem(system_id)
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, obj, READMEMBERS)


##############################################
# view classes
 
# FIXME: why does this exist?
class RestDbPassthrough(resource.Resource):
    pass

class BaseInventoryService(service.BaseAuthService):    
    def _check_uuid_auth(self, request, kwargs):
        headerName = 'X-rBuilder-Event-UUID'
        eventUuid = self.getHeaderValue(request, headerName)
        if not eventUuid:
            return None
        # Check if this system has such an event uuid
        systemId = kwargs['system_id']
        sjobs = models.SystemJob.objects.filter(
            system__pk=systemId, event_uuid=eventUuid)
        if not sjobs:
            return False
        self._setMintAuth(request)
        return True

class InventoryService(BaseInventoryService):
    """
    <inventory>
        ...
    </inventory>
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        inventory = models.Inventory()
        return inventory

class InventoryLogService(BaseInventoryService):
   
    @access.authenticated 
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getSystemsLog()
    
class InventorySystemStatesService(BaseInventoryService):
    """
    <system_states> 
        <system_state id="http://hostname/api/inventory/system_states/1/">
        ...
        </system_state>
        <system_state id="http://hostname/api/inventory/system_states/2/">
        ...
        </system_state>
    </system_states>
    """
   
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getSystemStates()

class InventorySystemStateService(BaseInventoryService):
    """
    <system_states> 
        <system_state id="http://hostname/api/inventory/system_states/1/">
        ...
        </system_state>
        <system_state id="http://hostname/api/inventory/system_states/2/">
        ...
        </system_state>
    </system_states>
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_state_id):
        return self.get(system_state_id)

    def get(self, system_state_id):
        return self.mgr.getSystemState(system_state_id)

class InventoryZonesService(BaseInventoryService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self, zone_id=None):
        return self.mgr.getZones()

    @access.admin
    @requires('zone')
    @return_xml
    def rest_POST(self, request, zone):
        zone = self.mgr.addZone(zone)
        return zone

class InventoryZoneService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, zone_id):
        return self.get(zone_id)

    def get(self, zone_id):
        return self.mgr.getZone(zone_id)

    @access.admin
    @requires('zone')
    @return_xml
    def rest_PUT(self, request, zone_id, zone):
        oldZone = self.mgr.getZone(zone_id)
        if not oldZone:
            return HttpResponseNotFound()
        self.mgr.updateZone(zone)
        return self.mgr.getZone(zone_id)
    
    @access.admin
    def rest_DELETE(self, request, zone_id):
        zone = self.get(zone_id)
        if zone:
            self.mgr.deleteZone(zone)
        response = HttpResponse(status=204)
        return response
    
class InventoryManagementNodesService(BaseInventoryService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getManagementNodes()

    @access.admin
    @requires('management_node')
    @return_xml
    def rest_POST(self, request, management_node):
        managementNode = self.mgr.addManagementNode(management_node)
        return managementNode

    @access.localhost
    @requires('management_nodes')
    @return_xml
    def rest_PUT(self, request, management_nodes):
        self.mgr.synchronizeZones(management_nodes)
        return self.mgr.getManagementNodes()


class InventoryManagementNodeService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, management_node_id):
        return self.get(management_node_id)

    def get(self, management_node_id):
        return self.mgr.getManagementNode(management_node_id)
    
    # NOTE: unclear whether this belongs to InventoryManagementNodesService
    # in addition to here
    #
    # @access.localhost
    # @requires('management_nodes')
    # @return_xml
    # def rest_PUT(self, request, management_nodes):
    #     self.mgr.synchronizeZones(management_nodes)
    #     return self.mgr.getManagementNodes()


class InventorySystemTypesService(BaseInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getSystemTypes()
        
class InventorySystemTypeService(BaseInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_type_id):
        return self.get(system_type_id)

    def get(self, system_type_id):
        return self.mgr.getSystemType(system_type_id)
        
    # FIXME: consider removing support
    @access.admin
    @requires('system_type')
    @return_xml
    def rest_PUT(self, request, system_type_id, system_type):
        old = self.get(system_type_id)
        if not old:
            return HttpResponseNotFound()
        if int(system_type_id) != system_type.pk:
            return HttpResponseNotFound()
        self.mgr.updateSystemType(system_type)
        return self.get(system_type_id)
    
class InventorySystemTypeSystemsService(BaseInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_type_id, system_id=None):
        return self.get(system_type_id)

    def get(self, system_type_id):
        return self.mgr.getSystemTypeSystems(system_type_id)
    
class InventoryZoneManagementNodesService(BaseInventoryService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request, zone_id):
        return self.get(zone_id)
    
    def get(self, zone_id):
        return self.mgr.getManagementNodesForZone(zone_id)
        
    # FIXME: consider removing support
    @access.admin
    @requires('management_node')
    @return_xml
    def rest_POST(self, request, zone_id, management_node):
        managementNode = self.mgr.addManagementNodeForZone(zone_id,
            management_node)
        return managementNode

class InventoryZoneManagementNodeService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, zone_id, management_node_id):
        return self.get(zone_id, management_node_id)

    def get(self, zone_id, management_node_id):
        return self.mgr.getManagementNodeForZone(zone_id, management_node_id)


class InventoryNetworksService(BaseInventoryService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getNetworks()
        
class InventoryNetworkService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, network_id):
        return self.get(network_id)

    def get(self, network_id):
        return self.mgr.getNetwork(network_id)
        
    @access.admin
    @requires('network')
    @return_xml
    def rest_PUT(self, request, network_id, network):
        oldNetwork = self.get(network_id)
        if not oldNetwork:
            return HttpResponseNotFound()
        if int(network_id) != network.pk:
            return HttpResponseNotFound()
        # This really should be an update
        self.mgr.updateNetwork(network)
        return self.get(network_id)
    
    @access.admin
    def rest_DELETE(self, request, network_id):
        self.mgr.deleteNetwork(network_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsService(BaseInventoryService):
    """
    <system id="http://hostname/api/inventory/systems/1/">
        ...
    </system>
    """
    # has manual rbac, inlined
    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request):
        user = request._authUser
        systems = self.get()
        tv = all(self.mgr.userHasRbacPermission(user, obj, READMEMBERS) for obj in systems.system)
        if tv:
            qs = querymodels.QuerySet.objects.get(name='All Systems')
            url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
            return HttpResponseRedirect(url)
        raise PermissionDenied()

    def get(self):
        return self.mgr.getSystems()

    # this must remain public for rpath-tools
    @access.anonymous
    @requires(['system', 'systems'])
    @return_xml
    def rest_POST(self, request, system=None, systems=None):
        # FIXME -- determine if request._authUser is available if authentication is supplied
        # but method is still anonymous <-- MPD
        authUser = getattr(request, '_authUser', None)
        if system is not None:
            system = self.mgr.addSystem(system, generateCertificates=True, for_user=authUser)
            return system
        systems = self.mgr.addSystems(systems.system, for_user=authUser)
        return self.mgr.getSystems()

class InventoryInventorySystemsService(BaseInventoryService):
   
    # if you want to get this data as a non-admin you must use the
    # query set 
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getInventorySystems()

class InventoryInfrastructureSystemsService(BaseInventoryService):

    @access.authenticated
    @access.localhost
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getInfrastructureSystems()

# NOTE: rbac_can_create_system does not exist because registration (temporarily)
# must be anonymous for rpath_register.   
   
class InventorySystemsSystemService(BaseInventoryService):

    @return_xml
    @rbac(READMEMBERS)
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystem(system_id)

    # must remain accessible by rpath-register
    @access.auth_token
    @access.authenticated
    @requires('system')
    @return_xml
    def rest_PUT(self, request, system_id, system):
        oldSystem = self.mgr.getSystem(system_id)
        if not oldSystem:
            return HttpResponseNotFound()
        if oldSystem.pk != system.pk:
            raise PermissionDenied()
        # This is a terrible place to put logic, but until we decide to pass
        # the request into the manager, we don't have a way around it
        mb = models.SystemState.MOTHBALLED
        if oldSystem.current_state.name != mb and \
                system.current_state.name == mb:
            if not request._is_admin:
                return HttpAuthenticationRequired
        # This really should be an update
        authUser = getattr(request, '_authUser', None)
        self.mgr.updateSystem(system, for_user=authUser)
        return self.mgr.getSystem(system_id)

    @rbac(rbac_can_write_system_id)
    def rest_DELETE(self, request, system_id):
        self.mgr.deleteSystem(system_id)
        response = HttpResponse(status=204)
        return response

class InventorySystemsSystemEventService(BaseInventoryService):
    
    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id, system_event_id=None):
        return self.get(system_id)
        
    def get(self, system_id, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemSystemEvent(system_id, system_event_id)
        else:
            return self.mgr.getSystemSystemEvents(system_id)
        
    @rbac(rbac_can_write_system_id)
    @requires('system_event')
    @return_xml
    def rest_POST(self, request, system_id, system_event):
        systemEvent = self.mgr.addSystemSystemEvent(system_id, system_event)
        return systemEvent

class InventorySystemsSystemLogService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
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

class InventoryUsersService(BaseInventoryService):

    # used by modellib
    def get(self, user):
        user = usersmodels.Users.objects.get(user_name=user)
        return user

class InventorySystemEventsService(BaseInventoryService):
 
    # TODO -- this may reveal too much info, consider
    # checking what event the system is related to
    # for a single object and otherwise require
    # admin for the full collection?
    @access.authenticated   
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self, system_event_id=None):
        return self.mgr.getSystemEvents()

class InventorySystemEventService(BaseInventoryService):

    # TODO -- this may reveal too much info, consider
    # checking what event the system is related to
    # for a single object and otherwise require
    # admin for the full collection?
    @access.authenticated   
    @return_xml
    def rest_GET(self, request, system_event_id):
        return self.get(system_event_id)

    def get(self, system_event_id):
        return self.mgr.getSystemEvent(system_event_id)


class InventorySystemConfigurationServices(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    def rest_GET(self, request, system_id):
        body = self.get(system_id)
        return HttpResponse(status=200, content=body)

    @rbac(rbac_can_write_system_id)
    def rest_PUT(self, request, system_id):
        body = self.mgr.saveSystemConfiguration(system_id, request.raw_post_data)
        return HttpResponse(status=200, content=body)
    
    @rbac(rbac_can_write_system_id)
    def rest_POST(self, request, system_id):
        body = self.mgr.saveSystemConfiguration(system_id, request.raw_post_data)
        return HttpResponse(status=200, content=body)

    def get(self, system_id):
        return self.mgr.getSystemConfiguration(system_id)
    
class InventorySystemConfigurationDescriptorServices(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    def rest_GET(self, request, system_id):
        response = HttpResponse(status=200, content=self.get(system_id))
        response['Content-Type'] = 'text/xml'
        return response
    
    def get(self, system_id):
        return self.mgr.getSystemConfigurationDescriptor(system_id)

class InventoryEventTypesService(BaseInventoryService):
    """
    <event_types>
        <event_type id="http://hostname/api/inventory/event_types/1/">
            ...
        </event_type>
        <event_type id="http://hostname/api/inventory/event_types/2/">
            ...
        </event_type>
    </event_types>
    """
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getEventTypes()

class InventoryEventTypeService(BaseInventoryService):
    """
    <event_types>
        <event_type id="http://hostname/api/inventory/event_types/1/">
            ...
        </event_type>
        <event_type id="http://hostname/api/inventory/event_types/2/">
            ...
        </event_type>
    </event_types>
    """
    @access.anonymous
    @return_xml
    def rest_GET(self, request, event_type_id):
        return self.get(event_type_id)

    def get(self, event_type_id):
        return self.mgr.getEventType(event_type_id)
        
    # FIXME: consider dropping support for this as code
    # changes are also required for this to be meaningful
    @access.admin
    @requires('event_type')
    @return_xml
    def rest_PUT(self, request, event_type_id, event_type):
        old_event_type = self.get(event_type_id)
        if not old_event_type:
            return HttpResponseNotFound()
        # This really should be an update
        self.mgr.updateEventType(event_type)
        return self.get(event_type_id)

class InventorySystemJobsService(BaseInventoryService):
    
    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        '''list the jobs running on this system'''
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystemJobs(system_id)

    @rbac(rbac_can_write_system_id)
    @requires('job', flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, system_id, job):
        '''request starting a job on this system'''
        system = self.mgr.getSystem(system_id)
        return self.mgr.addJob(job, system_id=system_id)

class InventorySystemJobDescriptorService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id, descriptor_type):
        '''
        Get a smartform descriptor for starting a action on
        InventorySystemJobsService.  An action is not *quite* a job.
        It's a request to start a job.
        '''
        content = self.get(system_id, descriptor_type, request.GET.copy())
        return content

    def get(self, system_id, descriptor_type, parameters=None):
        descriptor = self.mgr.getSystemDescriptorForAction(system_id,
            descriptor_type, parameters=parameters)
        return self.mgr.serializeDescriptor(descriptor)

class InventorySystemJobStatesService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id, job_state_id):
        return self.get(system_id, job_state_id)

    def get(self, system_id, job_state_id):
        return self.mgr.getSystemJobsByState(system_id, job_state_id)
        

class InventorySystemTagsService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystemTags(system_id)

class InventorySystemTagService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id, system_tag_id):
        return self.get(system_id, system_tag_id)

    def get(self, system_id, system_tag_id):
        return self.mgr.getSystemTag(system_id, system_tag_id)
