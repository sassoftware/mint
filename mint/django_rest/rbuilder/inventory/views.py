#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from django.http import HttpResponse, HttpResponseNotFound
from django_restapi import resource

from mint.django_rest.deco import requires, return_xml, access, \
    HttpAuthenticationRequired, getHeaderValue, xObjRequires
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS

class RestDbPassthrough(resource.Resource):
    pass

class StageProxyService(service.BaseAuthService):
    
    @staticmethod
    def getStageAndSetGroup(request, stage_id):
        stage = projectsmodels.Stage.objects.get(pk=stage_id)
        hostname = stage.project.short_name # aka project's short_name
        label = stage.label
        href = 'http://' + request.get_host().strip('/') + '/api/products/%s/repos/search?type=group&label=%s'
        stage.groups = projectsmodels.Group(href=href % (hostname, label))
        return stage
    
    @staticmethod
    def getStagesAndSetGroup(request, version=None):
        Stages = projectsmodels.Stages()
        
        if version:
            project_branch_stages = projectsmodels.Stage.objects.all().filter(name=version)
        else:
            project_branch_stages = projectsmodels.Stage.objects.all()
        # project_branch_stages = projectsmodels.Stage.objects.all()
        stages_collection = []
        
        for stage in project_branch_stages:
            stages_collection.append(StageProxyService.getStageAndSetGroup(request, stage.stage_id))
        Stages.project_branch_stage = stages_collection
        return Stages


class MajorVersionService(service.BaseAuthService):

    def get(self, request, short_name, version):
        """
        XXX defunct for now
        """
        modifiers = ['platform', 'platform_version', 'definition', 'image_type_definitions',
                     'image_definitions', 'images', 'source_group']
        project = projectsmodels.Project.objects.get(short_name=short_name)
        project_version = projectsmodels.ProjectVersion.objects.get(project=project)
        for m in modifiers:
            url = r'%(host)s/api/products/%(short_name)s/versions/%(version)s/%(modifier)s/'\
                    % dict(host= 'http://' + request.get_host(), short_name=short_name, version=version, modifier=m)
            setattr(project_version, m, url)
        return project_version


class ApplianceService(RestDbPassthrough):
    def get(self, project):
        return None

class BaseInventoryService(service.BaseAuthService):    
    def _check_uuid_auth(self, request, kwargs):
        headerName = 'X-rBuilder-Event-UUID'
        eventUuid = getHeaderValue(request, headerName)
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
    def rest_GET(self, request, system_state_id=None):
        return self.get(system_state_id)
    
    def get(self, system_state_id=None):
        if system_state_id:
            return self.mgr.getSystemState(system_state_id)
        else:
            return self.mgr.getSystemStates()
    
class InventoryZoneService(BaseInventoryService):
    
    @access.authenticated
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
    
class InventoryManagementNodeService(BaseInventoryService):
    
    @access.authenticated
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

    @access.localhost
    @requires('management_nodes')
    @return_xml
    def rest_PUT(self, request, management_nodes):
        self.mgr.synchronizeZones(management_nodes)
        return self.mgr.getManagementNodes()

class InventoryManagementInterfaceService(BaseInventoryService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, management_interface_id=None):
        return self.get(management_interface_id)
    
    def get(self, management_interface_id=None):
        if management_interface_id:
            return self.mgr.getManagementInterface(management_interface_id)
        else:
            return self.mgr.getManagementInterfaces()
        
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
    
class InventorySystemTypeService(BaseInventoryService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, system_type_id=None):
        return self.get(system_type_id)
    
    def get(self, system_type_id=None):
        if system_type_id:
            return self.mgr.getSystemType(system_type_id)
        else:
            return self.mgr.getSystemTypes()
        
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
    
class InventoryZoneManagementNodeService(BaseInventoryService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request, zone_id, management_node_id=None):
        return self.get(zone_id, management_node_id)
    
    def get(self, zone_id, management_node_id=None):
        if management_node_id:
            return self.mgr.getManagementNodeForZone(zone_id, management_node_id)
        else:
            return self.mgr.getManagementNodesForZone(zone_id)
        
    # FIXME: consider removing support
    @access.admin
    @requires('management_node')
    @return_xml
    def rest_POST(self, request, zone_id, management_node):
        managementNode = self.mgr.addManagementNodeForZone(zone_id,
            management_node)
        return managementNode

class InventoryNetworkService(BaseInventoryService):
    
    @access.authenticated
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

    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getSystems()

    # this must remain public for rpath-tools
    @access.anonymous
    @requires(['system', 'systems'])
    @return_xml
    def rest_POST(self, request, system=None, systems=None):
        if system is not None:
            system = self.mgr.addSystem(system, generateCertificates=True)
            return system
        systems = self.mgr.addSystems(systems.system)
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
        response = HttpResponse(status=200, content=self.get())
        response['Content-Type'] = 'text/xml'
        return response

    def get(self):
        return self.mgr.getImageImportMetadataDescriptor()


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
        
class InventorySystemsSystemService(BaseInventoryService):

    @return_xml
    @rbac(READMEMBERS)
    def rest_GET(self, request, system_id):
        return self.get(system_id)

    def get(self, system_id):
        return self.mgr.getSystem(system_id)

    # FIXME -- come back, tricky -- rbac if no event_uuid ???
    @access.event_uuid
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
        self.mgr.updateSystem(system)
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
    def rest_GET(self, request, system_event_id=None):
        return self.get(system_event_id)
        
    def get(self, system_event_id=None):
        if system_event_id:
            return self.mgr.getSystemEvent(system_event_id)
        else:
            return self.mgr.getSystemEvents()

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
        return self.mgr.addSystemConfiguration(system_id, configDict)

    @rbac(rbac_can_write_system_id)
    @return_xml
    @requires('configuration')
    def rest_POST(self, request, system_id, configuration):
        configDict = {}
        for k, v in configuration.__dict__.items():
            if not k.startswith('_'):
                configDict[k] = v
        return self.mgr.addSystemConfiguration(system_id, configDict)

    def get(self, system_id):
        return self.mgr.getSystemConfiguration(system_id)
    
class InventorySystemConfigurationDescriptorServices(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @access.admin
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
    def rest_GET(self, request, event_type_id=None):
        return self.get(event_type_id)
        
    def get(self, event_type_id=None):
        if event_type_id:
            return self.mgr.getEventType(event_type_id)
        else:
            return self.mgr.getEventTypes()
        
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
    @xObjRequires('job')
    @return_xml
    def rest_POST(self, request, system_id, job):
        '''request starting a job on this system'''
        system = self.mgr.getSystem(system_id)
        return self.mgr.scheduleJobAction(
            system, job
        )

class InventorySystemJobDescriptorService(BaseInventoryService):

    @rbac(rbac_can_read_system_id)
    @return_xml
    def rest_GET(self, request, system_id, job_type):
        '''
        Get a smartform descriptor for starting a action on
        InventorySystemJobsService.  An action is not *quite* a job.
        It's a request to start a job.
        '''
        content = self.get(system_id, job_type, request.GET.copy())
        response = HttpResponse(status=200, content=content)
        response['Content-Type'] = 'text/xml'
        return response

    def get(self, system_id, job_type, parameters):
        return self.mgr.getDescriptorForSystemAction(
            system_id, job_type, parameters
        )

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
    def rest_GET(self, request, system_id, system_tag_id=None):
        return self.get(system_id, system_tag_id)

    def get(self, system_id, system_tag_id):
        if system_tag_id:
            return self.mgr.getSystemTag(system_id, system_tag_id)
        else:
            return self.mgr.getSystemTags(system_id)

