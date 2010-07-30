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
    url(r'^api/inventory/$', inventoryviews.InventoryService()),
    url(r'^api/inventory/log/$', inventoryviews.InventoryLogsService()),
    url(r'^api/inventory/systems/$', inventoryviews.InventorySystemsService()),
    url(r'^api/inventory/systems/(\d+)/$', inventoryviews.InventorySystemsService()),
    url(r'^api/inventory/systems/(\d+)/systemLog/$', inventoryviews.InventorySystemsSystemLogService()),
    url(r'^api/inventory/systems/(\d+)/systemLog/([a-zA-Z]+)/$', inventoryviews.InventorySystemsSystemLogService()),
)
