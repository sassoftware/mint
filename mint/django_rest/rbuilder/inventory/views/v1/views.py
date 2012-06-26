#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from mint.django_rest.deco import requires, return_xml, access, \
    HttpAuthenticationRequired, Flags
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import survey_models
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

def rbac_can_write_survey_uuid(view, request, uuid, *args, **kwargs):
    '''is a survey updateable/removable by a user?'''
    sys = view.mgr.getSurvey(uuid).system
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, sys, MODMEMBERS)

def rbac_can_read_survey_uuid(view, request, uuid, *args, **kwargs):
    '''is a survey readable by a user?'''
    sys = view.mgr.getSurvey(uuid).system
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, sys, READMEMBERS)

def rbac_can_generate_survey(view, request, uuid1, uuid2, *args, **kwargs):
    '''to diff two surveys, need to be able to read both'''
    sys1 = view.mgr.getSurvey(uuid1).system
    sys2 = view.mgr.getSurvey(uuid2).system
    user = request._authUser
    if not view.mgr.userHasRbacPermission(user, sys1, READMEMBERS):
        return False
    return view.mgr.userHasRbacPermission(user, sys2, READMEMBERS)

def rbac_can_read_rpm_package(view, request, id, *args, **kwargs):
    rpm = view.mgr.getSurveyRpmPackage(id)
    return rbac_can_read_system_id(view, request, rpm.survey.system.pk)
     
def rbac_can_read_conary_package(view, request, id, *args, **kwargs):
    conary = view.mgr.getSurveyConaryPackage(id)
    return rbac_can_read_system_id(view, request, conary.survey.system.pk)

def rbac_can_read_windows_package(view, request, id, *args, **kwargs):
    conary = view.mgr.getSurveyWindowsPackage(id)
    return rbac_can_read_system_id(view, request, conary.survey.system.pk)

def rbac_can_read_windows_patch(view, request, id, *args, **kwargs):
    conary = view.mgr.getSurveyWindowsPatch(id)
    return rbac_can_read_system_id(view, request, conary.survey.system.pk)

def rbac_can_read_service(view, request, id, *args, **kwargs):
    service = view.mgr.getSurveyService(id)
    return rbac_can_read_system_id(view, request, service.survey.system.pk)

def rbac_can_read_windows_service(view, request, id, *args, **kwargs):
    service = view.mgr.getSurveyWindowsService(id)
    return rbac_can_read_system_id(view, request, service.survey.system.pk)

def rbac_can_read_survey_tag(view, request, id, *args, **kwargs):
    sys = view.mgr.getSurveyTag(id).survey.system
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, sys, READMEMBERS)

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
        self._setMintAuth()
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

class InventoryManagementInterfacesService(BaseInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getManagementInterfaces()

class InventoryManagementInterfaceService(BaseInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, management_interface_id):
        return self.get(management_interface_id)

    def get(self, management_interface_id):
        return self.mgr.getManagementInterface(management_interface_id)
        
    # FIXME: consider removing support
    # this may be useful for tests but will likely break your
    # rBuilder, so we shouldn't allow it, right?
    @access.admin
    @requires('management_interface')
    @return_xml
    def rest_PUT(self, request, management_interface_id, management_interface):
        old = self.get(management_interface_id)
        if not old:
            return HttpResponseNotFound()
        if int(management_interface_id) != management_interface.pk:
            return HttpResponseNotFound()
        self.mgr.updateManagementInterface(management_interface)
        return self.get(management_interface_id)
    
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
    
class ImageImportMetadataDescriptorService(BaseInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        descriptor = self.mgr.getImageImportMetadataDescriptor()
        return self.mgr.serializeDescriptor(descriptor)

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

class InventorySystemsInstalledSoftwareService(BaseInventoryService):
    
    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        system = self.mgr.getSystem(system_id)
        installedSoftware = models.InstalledSoftware()
        installedSoftware.trove = system.installed_software.all()
        return installedSoftware

    @rbac(rbac_can_write_system_id)
    @requires('installed_software')
    @return_xml
    def rest_PUT(self, request, system_id, installed_software):
        """Initiate a software update on the system, in order to install the
        specified software"""
        self.mgr.updateInstalledSoftware(system_id, installed_software.trove)
        installedSoftware = models.InstalledSoftware()
        return installedSoftware

class InventorySystemCredentialsServices(BaseInventoryService):

    # TODO -- is this too permissive for reading credentials?
    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    @rbac(rbac_can_write_system_id)
    @return_xml
    @requires('credentials')
    def rest_PUT(self, request, system_id, credentials):
        credsDict = {}
        for k, v in credentials.__dict__.items():
            if not k.startswith('_'):
                credsDict[k] = v
        return self.mgr.addSystemCredentials(system_id, credsDict)

    @rbac(rbac_can_write_system_id)
    @return_xml
    @requires('credentials')
    def rest_POST(self, request, system_id, credentials):
        credsDict = {}
        for k, v in credentials.__dict__.items():
            if not k.startswith('_'):
                credsDict[k] = v
        return self.mgr.addSystemCredentials(system_id, credsDict)

    def get(self, system_id):
        return self.mgr.getSystemCredentials(system_id)
    
class InventorySystemConfigurationServices(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    @rbac(rbac_can_write_system_id)
    @return_xml
    @requires('configuration')
    def rest_PUT(self, request, system_id, configuration):
        configDict = {}
        for k, v in configuration.__dict__.items():
            if not k.startswith('_'):
                configDict[k] = v
        return self.mgr.saveSystemConfiguration(system_id, configDict)

    @rbac(rbac_can_write_system_id)
    @return_xml
    @requires('configuration')
    def rest_POST(self, request, system_id, configuration):
        configDict = {}
        for k, v in configuration.__dict__.items():
            if not k.startswith('_'):
                configDict[k] = v
        return self.mgr.saveSystemConfiguration(system_id, configDict)

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
        if job.job_type.name == job.job_type.SYSTEM_ASSIMILATE:
            return self.mgr.scheduleJobAction(system, job)
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

class SurveysService(BaseInventoryService):
    ''' Collection of all surveys on a given system '''

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    @rbac(rbac_can_write_system_id)
    @return_xml
    def rest_POST(self, request, system_id):
        xml = request.raw_post_data
        return self.mgr.addSurveyForSystemFromXml(system_id, xml)

    def get(self, system_id):
        return self.mgr.getSurveysForSystem(system_id)


class SurveyService(BaseInventoryService):
    ''' 
    Access to an individual system survey by UUID
    '''

    @rbac(rbac_can_read_survey_uuid)
    @return_xml
    def rest_GET(self, request, uuid):
        return self.get(uuid)

    def get(self, uuid):
        return self.mgr.getSurvey(uuid)

    @rbac(rbac_can_write_survey_uuid)
    @return_xml
    def rest_PUT(self, request, uuid):
        xml = request.raw_post_data
        return self.mgr.updateSurveyFromXml(uuid, xml)
    
    @rbac(rbac_can_write_survey_uuid)
    @return_xml
    def rest_DELETE(self, request, uuid):
        (found, deleted) = self.mgr.deleteSurvey(uuid)
        if not found:
            return HttpResponseNotFound()
        elif not deleted:
            raise PermissionDenied(msg="Survey is not marked removable")
        else:
            return HttpResponse(status=204)    

class SurveyRpmPackageService(BaseInventoryService):
    ''' The instance of an RPM installed on a given system (per survey) '''

    @rbac(rbac_can_read_rpm_package)
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyRpmPackage(id)

class SurveyConaryPackageService(BaseInventoryService):
    ''' The instance of an Conary pkg installed on a given system (per survey) '''

    @rbac(rbac_can_read_conary_package)
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyConaryPackage(id)

class SurveyWindowsPackageService(BaseInventoryService):
    
    @rbac(rbac_can_read_windows_package)
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsPackage(id)

class SurveyWindowsPatchService(BaseInventoryService):

    @rbac(rbac_can_read_windows_patch)
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsPatch(id)

class SurveyServiceService(BaseInventoryService):
    ''' The instance of an service installed on a given system (per survey) '''

    @rbac(rbac_can_read_service)
    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyService(id)

class SurveyWindowsServiceService(BaseInventoryService):

    @rbac(rbac_can_read_windows_service)
    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsService(id)


class SurveyDiffService(BaseInventoryService):
    ''' Returns XML representing differences between two surveys '''

    @rbac(rbac_can_generate_survey)
    def rest_GET(self, request, uuid1, uuid2):
        result = self.get(uuid1, uuid2, request)
        return HttpResponse(result, status=200, content_type='text/xml')

    def get(self, uuid1, uuid2, request):
        return self.mgr.diffSurvey(uuid1, uuid2, request) 

class SurveyRpmPackageInfoService(BaseInventoryService):
    ''' 
    The definition of an RPM state, shared between many systems.
    For instance, multiple systems could have Foo, v1234, x86.
    Each would have a different install date, but reference the same info.
    '''

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyRpmPackageInfo(id)

class SurveyConaryPackageInfoService(BaseInventoryService):
    ''' The definition of a conary state, shared between many systems '''

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyConaryPackageInfo(id)

class SurveyWindowsPackageInfoService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsPackageInfo(id)

class SurveyWindowsPatchInfoService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsPatchInfo(id)

class SurveyServiceInfoService(BaseInventoryService):
    ''' The definition of a service state, shared between many systems '''

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyServiceInfo(id)

class SurveyWindowsServiceInfoService(BaseInventoryService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyWindowsServiceInfo(id)


class SurveyTagService(BaseInventoryService):
    ''' User assignable tags per survey '''

    @rbac(rbac_can_read_survey_tag)
    @return_xml
    def rest_GET(self, request, id):
        return self.get(id)

    def get(self, id):
        return self.mgr.getSurveyTag(id)


