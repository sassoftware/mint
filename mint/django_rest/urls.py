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
    url(r'^api/inventory/system_states/(\d+)/?$', 
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
    url(r'^api/inventory/management_nodes/(\d+)/?$', 
        inventoryviews.InventoryManagementNodeService(), 
        name='ManagementNode'),
    url(r'^api/inventory/zones/(\d+)/management_nodes/?$', 
        inventoryviews.InventoryZoneManagementNodeService(), 
        name='ManagementNodes'),
    url(r'^api/inventory/zones/(\d+)/management_nodes/(\d+)/?$', 
        inventoryviews.InventoryZoneManagementNodeService(), 
        name='ManagementNode'),
        
    # Networks
    url(r'^api/inventory/networks/?$', 
        inventoryviews.InventoryNetworkService(), 
        name='Networks'),
    url(r'^api/inventory/networks/(?P<network_id>\d+)/?$', 
        inventoryviews.InventoryNetworkService(), 
        name='Network'),

    # Systems
    url(r'^api/inventory/systems/?$', 
        inventoryviews.InventorySystemsService(), 
        name='Systems'),
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

    # System Events
    url(r'^api/inventory/system_events/?$', 
        inventoryviews.InventorySystemEventsService(), 
        name='SystemEvents'),
    url(r'^api/inventory/system_events/(?P<system_event_id>\d+)/?$', 
        inventoryviews.InventorySystemEventsService(), 
        name='SystemEvent'),

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
)
