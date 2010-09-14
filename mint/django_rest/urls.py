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
    url(r'^api/inventory/$', 
        inventoryviews.InventoryService(), 
        name='Inventory'),

    # Log
    url(r'^api/inventory/log/$', 
        inventoryviews.InventoryLogService(),
        name='Log'),

    # System States
    url(r'^api/inventory/systemStates/$', 
        inventoryviews.InventorySystemStateService(), 
        name='SystemStates'),
    url(r'^api/inventory/systemStates/(\d+)/$', 
        inventoryviews.InventorySystemStateService(), 
        name='SystemState'),

    # Zones
    url(r'^api/inventory/zones/$', 
        inventoryviews.InventoryZoneService(), 
        name='Zones'),
    url(r'^api/inventory/zones/(\d+)/$', 
        inventoryviews.InventoryZoneService(), 
        name='Zone'),

    # Management Nodes
    url(r'^api/inventory/zones/(\d+)/managementNodes/$', 
        inventoryviews.InventoryManagementNodeService(), 
        name='ManagementNodes'),
    url(r'^api/inventory/zones/(\d+)/managementNodes/(\d+)/?$', 
        inventoryviews.InventoryManagementNodeService(), 
        name='ManagementNode'),

    # Systems
    url(r'^api/inventory/systems/$', 
        inventoryviews.InventorySystemsService(), 
        name='Systems'),
    url(r'^api/inventory/systems/(\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System'),
    url(r'^api/inventory/systems/(\d+)/systemLog/$', 
        inventoryviews.InventorySystemsSystemLogService(), 
        name='SystemLog'),
    url(r'^api/inventory/systems/(\d+)/jobs/$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs'),
    url(r'^api/inventory/systems/(\d+)/jobs/([a-zA-Z1-9]+)/$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJob'),
    url(r'^api/inventory/systems/(\d+)/systemEvents/$', 
        inventoryviews.InventorySystemsSystemEventService(), 
        name='SystemsSystemEvent'),
    url(r'^api/inventory/systems/(\d+)/systemLog/([a-zA-Z]+)/$', 
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat'),
    url(r'^api/inventory/systems/(\d+)/installedSoftware/$', 
        inventoryviews.InventorySystemsInstalledSoftwareService(), 
        name='InstalledSoftware'),

    # System Events
    url(r'^api/inventory/systemEvents/$', 
        inventoryviews.InventorySystemEventsService(), 
        name='SystemEvents'),
    url(r'^api/inventory/systemEvents/(\d+)/$', 
        inventoryviews.InventorySystemEventsService(), 
        name='SystemEvent'),
    url(r'^api/inventory/eventTypes/$', 
        inventoryviews.InventoryEventTypesService(), 
        name='EventTypes'),
    url(r'^api/inventory/eventTypes/(\d+)/$', 
        inventoryviews.InventoryEventTypesService(), 
        name='EventType'),
    url(r'^api/inventory/users/([a-zA-Z1-9]+)/$',
        inventoryviews.InventoryUsersService(),
        name='Users'),

    # Jobs
    url(r'^api/inventory/jobs/$',
        inventoryviews.InventoryJobsService(),
        name='Jobs'),
    url(r'^api/inventory/jobs/([a-zA-Z1-9]+)/$',
        inventoryviews.InventoryJobsService(),
        name='Job'),

    # Job States
    url(r'^api/inventory/jobStates/$',
        inventoryviews.InventoryJobStatesService(),
        name='JobStates'),
    url(r'^api/inventory/jobStates/([a-zA-Z1-9]+)/$',
        inventoryviews.InventoryJobStatesService(),
        name='JobState'),
    url(r'^api/inventory/jobStates/([a-zA-Z1-9]+)/jobs/$',
        inventoryviews.InventoryJobStatesJobsService(),
        name='JobStateJobs'),
)
