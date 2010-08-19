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

    # Inventory urls
    url(r'^api/inventory/$', 
        inventoryviews.InventoryService(), 
        name='Inventory'),
    url(r'^api/inventory/log/$', 
        inventoryviews.InventoryLogService(),
        name='Log'),
    url(r'^api/inventory/managementNodes/$', 
        inventoryviews.InventoryManagementNodeService(), 
        name='ManagementNodes'),
    url(r'^api/inventory/managementNodes/(\d+)/$', 
        inventoryviews.InventoryManagementNodeService(), 
        name='ManagementNode'),
    url(r'^api/inventory/systems/$', 
        inventoryviews.InventorySystemsService(), 
        name='Systems'),
    url(r'^api/inventory/systems/(\d+)/$', 
        inventoryviews.InventorySystemsService(), 
        name='System'),
    url(r'^api/inventory/systems/(\d+)/systemLog/$', 
        inventoryviews.InventorySystemsSystemLogService(), 
        name='SystemLog'),
    url(r'^api/inventory/systems/(\d+)/systemEvent/$', 
        inventoryviews.InventorySystemsSystemEventService(), 
        name='SystemEvent'),
    url(r'^api/inventory/systems/(\d+)/systemLog/([a-zA-Z]+)/$', 
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat'),
    url(r'^api/inventory/systemEvents/$', 
        inventoryviews.InventorySystemsEventService(), 
        name='SystemEvents'),
    url(r'^api/inventory/systemEvents/(\d+)/$', 
        inventoryviews.InventorySystemsEventService(), 
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
    url(r'^api/inventory/jobs/([a-zA-Z1-9]+)/$',
        inventoryviews.InventoryJobsService(),
        name='Jobs'),
    url(r'^api/inventory/systems/(\d+)/jobs/$',
        inventoryviews.InventoryJobsService(),
        name='Jobs'),
    url(r'^api/inventory/systems/(\d+)/jobs/([a-zA-Z1-9]+)/$',
        inventoryviews.InventoryJobsService(),
        name='Jobs'),
)
