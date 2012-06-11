#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import *

from mint.django_rest.rbuilder.reporting import imagereports, \
                                                reportdispatcher, \
                                                reports, \
                                                views

from mint.django_rest.rbuilder.inventory import views as inventoryviews
from mint.django_rest.rbuilder.querysets import views as querysetviews
from mint.django_rest.rbuilder.packages import views as packageviews
from mint.django_rest.rbuilder.changelog import views as changelogviews

handler404 = 'mint.django_rest.handler.handler404'
handler500 = 'mint.django_rest.handler.handler500'

urlpatterns = patterns('',
    # Reporting urls
    url(r'^api/reports/(.*?)/descriptor/?$',
        reportdispatcher.ReportDescriptor()),
    url(r'^api/reports/(.*?)/data/(.*?)/?$',
        reportdispatcher.ReportDispatcher()),
    url(r'^api/reports/(.*?)/?$', views.ReportView()),

    #
    # Inventory urls
    #
    url(r'^api/inventory/?$',
        inventoryviews.InventoryService(),
        name='Inventory'),

    # Log
    url(r'^api/inventory/log/?$',
        inventoryviews.InventoryLogService(),
        name='Log'),

    # System States
    url(r'^api/inventory/system_states/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemStates'),
    url(r'^api/inventory/system_states/(?P<system_state_id>\d+)/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemState'),

    # Zones
    url(r'^api/inventory/zones/?$',
        inventoryviews.InventoryZoneService(),
        name='Zones'),
    url(r'^api/inventory/zones/(?P<zone_id>\d+)/?$',
        inventoryviews.InventoryZoneService(),
        name='Zone'),

    # Management Nodes
    url(r'^api/inventory/management_nodes/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNodes'),
    url(r'^api/inventory/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNode'),
    url(r'^api/inventory/zones/(?P<zone_id>\d+)/management_nodes/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ManagementNodes'),
    url(r'^api/inventory/zones/(?P<zone_id>\d+)/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ManagementNode'),
        
    # Management Interfaces
    url(r'^api/inventory/management_interfaces/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterfaces'),
    url(r'^api/inventory/management_interfaces/(?P<management_interface_id>\d+)/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterface'),
        
    # System types
    url(r'^api/inventory/system_types/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemTypes'),
    url(r'^api/inventory/system_types/(?P<system_type_id>\d+)/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemType'),
    url(r'^api/inventory/system_types/(?P<system_type_id>\d+)/systems/?$',
        inventoryviews.InventorySystemTypeSystemsService(),
        name='SystemTypeSystems'),
       
    # Networks
    url(r'^api/inventory/networks/?$',
        inventoryviews.InventoryNetworkService(),
        name='Networks'),
    url(r'^api/inventory/networks/(?P<network_id>\d+)/?$',
        inventoryviews.InventoryNetworkService(),
        name='Network'),

    # Systems
    # RBL-8919 - accept double slashes to accommodate an rpath-tools bug
    url(r'^api/inventory//?systems/?$',
        inventoryviews.InventorySystemsService(),
        name='Systems'),
    url(r'^api/inventory/inventory_systems/?$',
        inventoryviews.InventoryInventorySystemsService(),
        name='InventorySystems'),
    url(r'^api/inventory/infrastructure_systems/?$',
        inventoryviews.InventoryInfrastructureSystemsService(),
        name='ImageImportMetadataDescriptor'),
    url(r'^api/inventory/image_import_metadata_descriptor/?$',
        inventoryviews.ImageImportMetadataDescriptorService(),
        name='InfrastructureSystems'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/system_log/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLog'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/jobs/(?P<job_id>[a-zA-Z0-9]+)/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJob'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventorySystemJobStatesService(),
        name='SystemJobStateJobs'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/system_events/?$',
        inventoryviews.InventorySystemsSystemEventService(),
        name='SystemsSystemEvent'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/system_log/(?P<format>[a-zA-Z]+)/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/installed_software/?$',
        inventoryviews.InventorySystemsInstalledSoftwareService(),
        name='InstalledSoftware'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/credentials/?$',
        inventoryviews.InventorySystemCredentialsServices(),
        name='SystemCredentials'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/configuration/?$',
        inventoryviews.InventorySystemConfigurationServices(),
        name='SystemConfiguration'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/configuration_descriptor/?$',
        inventoryviews.InventorySystemConfigurationDescriptorServices(),
        name='SystemConfigurationDescriptor'),

    # System Events
    url(r'^api/inventory/system_events/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvents'),
    url(r'^api/inventory/system_events/(?P<system_event_id>\d+)/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvent'),

    # System Tags
    url(r'^api/inventory/systems/(?P<system_id>\d+)/system_tags/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTags'),
    url(r'^api/inventory/systems/(?P<system_id>\d+)/system_tags/(?P<system_tag_id>\d+)/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTag'),

    # Event Types
    url(r'^api/inventory/event_types/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventTypes'),
    url(r'^api/inventory/event_types/(?P<event_type_id>\d+)/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventType'),

    # Users
    url(r'^api/inventory/users/([a-zA-Z0-9]+)/?$',
        inventoryviews.InventoryUsersService(),
        name='Users'),

    # Jobs
    url(r'^api/inventory/jobs/?$',
        inventoryviews.InventoryJobsService(),
        name='Jobs'),
    url(r'^api/inventory/jobs/(?P<job_id>[a-zA-Z0-9]+)/?$',
        inventoryviews.InventoryJobsService(),
        name='Job'),

    # Job States
    url(r'^api/inventory/job_states/?$',
        inventoryviews.InventoryJobStatesService(),
        name='JobStates'),
    url(r'^api/inventory/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/?$',
        inventoryviews.InventoryJobStatesService(),
        name='JobState'),
    url(r'^api/inventory/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventoryJobStatesJobsService(),
        name='JobStateJobs'),

    # Major Versions
    url(r'^api/products/(\w|\-)*/versions/(\w|\.)*/?$',
        inventoryviews.MajorVersionService(),
        name='MajorVersions'),

    # Stages
    url(r'^api/products/(\w|\-)*/versions/(\w|\.)*/stages/(\w)*/?$',
        inventoryviews.StageService(),
        name='Stages'),

    # Projects
    url(r'^api/products/(\w|\-)*/?$',
        inventoryviews.ApplianceService(),
        name='Projects'),

    # Query Sets
    url(r'^api/query_sets/?$',
        querysetviews.QuerySetService(),
        name='QuerySets'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/?$',
        querysetviews.QuerySetService(),
        name='QuerySet'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/all/?$',
        querysetviews.QuerySetAllResultService(),
        name='QuerySetAllResult'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/chosen/?$',
        querysetviews.QuerySetChosenResultService(),
        name='QuerySetChosenResult'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/filtered/?$',
        querysetviews.QuerySetFilteredResultService(),
        name='QuerySetFilteredResult'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/child/?$',
        querysetviews.QuerySetChildResultService(),
        name='QuerySetChildResult'),
    url(r'^api/query_sets/filter_descriptor/?$',
        querysetviews.QuerySetFilterDescriptorService(),
        name='QuerySetFilterDescriptor'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/query_tags/?$',
        querysetviews.QueryTagService(),
        name='QueryTags'),
    url(r'^api/query_sets/(?P<query_set_id>\d+)/query_tags/(?P<query_tag_id>\d+)/?$',
        querysetviews.QueryTagService(),
        name='QueryTag'),

    # Packages
    url(r'^api/packages/?$',
        packageviews.PackageService(),
        name='Packages'),
    url(r'^api/packages/(?P<package_id>\d+)/?$',
        packageviews.PackageService(),
        name='Package'),

    # Change Logs
    url(r'^api/changelogs/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLogs'),
    url(r'^api/changelogs/(?P<change_log_id>\d+)/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLog'),

)


