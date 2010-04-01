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

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    url(r'^api/reports/(.*?)/descriptor/?$', 
        reportdispatcher.ReportDescriptor()),

    url(r'^api/reports/(.*?)/data/(.*?)/?$', 
        reportdispatcher.ReportDispatcher()),

    url(r'^api/reports/(.*?)/?$', views.ReportView()),

    url(r'^api/inventory/$', inventoryviews.InventoryService()),
)
