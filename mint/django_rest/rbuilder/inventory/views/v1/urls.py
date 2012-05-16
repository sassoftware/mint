#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.inventory.views.v1 import views as inventoryviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    # Discoverability
    URL(r'/?$', 
        inventoryviews.InventoryService(), 
        name='Inventory'),

    # Log
    URL(r'/log/?$',
        inventoryviews.InventoryLogService(),
        name='Log'),

    # System States
    URL(r'/system_states/?$',
        inventoryviews.InventorySystemStatesService(),
        name='SystemStates'),
    URL(r'/system_states/(?P<system_state_id>\d+)/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemState'),

    # Zones
    URL(r'/zones/?$',
        inventoryviews.InventoryZonesService(),
        name='Zones'),
    URL(r'/zones/(?P<zone_id>\d+)/?$',
        inventoryviews.InventoryZoneService(),
        name='Zone'),

    # Management Nodes
    URL(r'/management_nodes/?$',
        inventoryviews.InventoryManagementNodesService(),
        name='ManagementNodes',
        model='inventory.ManagementNodes'),
    URL(r'/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNode',
        model='inventory.ManagementNode'),
    URL(r'/zones/(?P<zone_id>\d+)/management_nodes/?$',
        inventoryviews.InventoryZoneManagementNodesService(),
        name='ZoneManagementNodes',
        model='inventory.ZoneManagementNodes'),
    URL(r'/zones/(?P<zone_id>\d+)/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ZoneManagementNode',
        model='inventory.ZoneManagementNode'),
        
    # Management Interfaces
    URL(r'/management_interfaces/?$',
        inventoryviews.InventoryManagementInterfacesService(),
        name='ManagementInterfaces',
        model='inventory.ManagementInterfaces'),
    URL(r'/management_interfaces/(?P<management_interface_id>\d+)/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterface',
        model='inventory.ManagementInterface'),
        
    # System types
    URL(r'/system_types/?$',
        inventoryviews.InventorySystemTypesService(),
        name='SystemTypes',
        model='inventory.SystemTypes'),
    URL(r'/system_types/(?P<system_type_id>\d+)/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemType',
        model='inventory.SystemType'),
    URL(r'/system_types/(?P<system_type_id>\d+)/systems/?$',
        inventoryviews.InventorySystemTypeSystemsService(),
        name='SystemTypeSystems',
        model='inventory.Systems'),
       
    # Networks
    URL(r'/networks/?$',
        inventoryviews.InventoryNetworksService(),
        name='Networks',
        model='inventory.Networks'),
    URL(r'/networks/(?P<network_id>\d+)/?$',
        inventoryviews.InventoryNetworkService(),
        name='Network',
        model='inventory.Network'),

    # Systems
    # RBL-8919 - accept double slashes to accommodate an rpath-tools bug
    URL(r'/systems/?$',
        inventoryviews.InventorySystemsService(),
        name='Systems',
        model='inventory.Systems'),
    URL(r'/inventory_systems/?$',
        inventoryviews.InventoryInventorySystemsService(),
        name='InventorySystems',
        model='inventory.Systems'),
    URL(r'/infrastructure_systems/?$',
        inventoryviews.InventoryInfrastructureSystemsService(),
        name='ImageImportMetadataDescriptor',
        model='inventory.Systems'),
    URL(r'/image_import_metadata_descriptor/?$',
        inventoryviews.ImageImportMetadataDescriptorService(),
        name='InfrastructureSystems'),
    URL(r'/systems/(?P<system_id>\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System',
        model='inventory.System'),
    URL(r'/systems/(?P<system_id>\d+)/system_log/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLog',
        model='inventory.SystemLog'),
    URL(r'/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs',
        model='inventory.SystemJobs'),
    URL(r'/systems/(?P<system_id>\d+)/descriptors/(?P<descriptor_type>[_A-Za-z]+)/?$',
        inventoryviews.InventorySystemJobDescriptorService(),
        name='SystemJobDescriptors'),
    URL(r'/systems/(?P<system_id>\d+)/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventorySystemJobStatesService(),
        name='SystemJobStateJobs',
        model='inventory.SystemJobs'),
    URL(r'/systems/(?P<system_id>\d+)/system_events/?$',
        inventoryviews.InventorySystemsSystemEventService(),
        name='SystemsSystemEvent',
        model='inventory.SystemEvents'),
    URL(r'/systems/(?P<system_id>\d+)/system_log/(?P<format>[a-zA-Z]+)/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat',
        model='inventory.SystemLog'),
    URL(r'/systems/(?P<system_id>\d+)/installed_software/?$',
        inventoryviews.InventorySystemsInstalledSoftwareService(),
        name='InstalledSoftware',
        model='inventory.InstalledSoftware'),
    URL(r'/systems/(?P<system_id>\d+)/credentials/?$',
        inventoryviews.InventorySystemCredentialsServices(),
        name='SystemCredentials',
        model='inventory.Credentials'),
    URL(r'/systems/(?P<system_id>\d+)/configuration/?$',
        inventoryviews.InventorySystemConfigurationServices(),
        name='SystemConfiguration',
        model='inventory.Configuration'),
    URL(r'/systems/(?P<system_id>\d+)/configuration_descriptor/?$',
        inventoryviews.InventorySystemConfigurationDescriptorServices(),
        name='SystemConfigurationDescriptor',
        model='inventory.ConfigurationDescriptor'),

    # System Events
    URL(r'/system_events/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvents',
        model='inventory.SystemEvents'),
    URL(r'/system_events/(?P<system_event_id>\d+)/?$',
        inventoryviews.InventorySystemEventService(),
        name='SystemEvent',
        model='inventory.SystemEvent'),

    # System Tags
    URL(r'/systems/(?P<system_id>\d+)/system_tags/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTags'),
    URL(r'/systems/(?P<system_id>\d+)/system_tags/(?P<system_tag_id>\d+)/?$',
        inventoryviews.InventorySystemTagService(),
        name='SystemTag'),

    # Event Types
    URL(r'/event_types/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventTypes',
        model='inventory.EventTypes'),
    URL(r'/event_types/(?P<event_type_id>\d+)/?$',
        inventoryviews.InventoryEventTypeService(),
        name='EventType',
        model='inventory.EventType'),

    # Surveys & System Discovery
    URL(r'/systems/(?P<system_id>\d+)/surveys/?$',
        inventoryviews.SurveysService(),
        name='Surveys',
        model='inventory.Surveys'),
    URL(r'/management_nodes/(?P<system_id>\d+)/surveys/?$',
        inventoryviews.SurveysService(),
        name='SurveysForManagementNode',
        model='inventory.Surveys'),
    URL(r'/surveys/(?P<uuid>[-a-zA-Z0-9]+)/?$',
        inventoryviews.SurveyService(),
        name='Survey',
        model='inventory.Survey'),
    URL(r'/survey_tags/(?P<id>\d+)/?$',
        inventoryviews.SurveyTagService(),
        name='SurveyTag',
        model='inventory.SurveyTag'),
    URL(r'/survey_rpm_packages/(?P<id>\d+)/?$',
        inventoryviews.SurveyRpmPackageService(),
        name='SurveyRpmPackage',
        model='inventory.RpmPackage'),
    URL(r'/survey_conary_packages/(?P<id>\d+)/?$',
        inventoryviews.SurveyConaryPackageService(),
        name='SurveyConaryPackage',
        model='inventory.ConaryPackage'),
    URL(r'/survey_windows_packages/(?P<id>\d+)/?$',
        inventoryviews.SurveyWindowsPackageService(),
        name='SurveyWindowsPackage',
        model='inventory.WindowsPackage'),
    URL(r'/survey_windows_patches/(?P<id>\d+)/?$',
        inventoryviews.SurveyWindowsPatchService(),
        name='SurveyWindowsPatch',
        model='inventory.WindowsPatch'),


    URL(r'/survey_services/(?P<id>\d+)/?$',
        inventoryviews.SurveyServiceService(),
        name='SurveyService',
        model='inventory.Service'),
    URL(r'/survey_windows_services/(?P<id>\d+)/?$',
        inventoryviews.SurveyWindowsServiceService(),
        name='SurveyWindowsService',
        model='inventory.WindowsService'),

    URL(r'/surveys/(?P<uuid1>[-a-zA-Z0-9]+)/diffs/(?P<uuid2>[-a-zA-Z0-9]+)/?$',
        inventoryviews.SurveyDiffService(),
        name='SurveyDiff',
        model='inventory.SurveyDiff'),
    URL(r'/rpm_package_info/(?P<id>\d+)/?',
        inventoryviews.SurveyRpmPackageInfoService(),
        name='SurveyRpmPackageInfo',
        model='inventory.SurveyRpmPackageInfo'),
    URL(r'/conary_package_info/(?P<id>\d+)/?',
        inventoryviews.SurveyConaryPackageInfoService(),
        name='SurveyConaryPackageInfo',
        model='inventory.SurveyConaryPackageInfo'),
    URL(r'/windows_package_info/(?P<id>\d+)/?',
        inventoryviews.SurveyWindowsPackageInfoService(),
        name='SurveyWindowsPackageInfo',
        model='inventory.SurveyWindowsPackageInfo'),
    URL(r'/windows_patch_info/(?P<id>\d+)/?',
        inventoryviews.SurveyWindowsPatchInfoService(),
        name='SurveyWindowsPatchInfo',
        model='inventory.SurveyWindowsPatchInfo'),

    URL(r'/service_info/(?P<id>\d+)/?',
        inventoryviews.SurveyServiceInfoService(),
        name='SurveyServiceInfo',
        model='inventory.SurveyServiceInfo'),
    URL(r'/windows_service_info/(?P<id>\d+)/?',
        inventoryviews.SurveyWindowsServiceInfoService(),
        name='SurveyWindowsServiceInfo',
        model='inventory.SurveyWindowsServiceInfo'),
    
)

