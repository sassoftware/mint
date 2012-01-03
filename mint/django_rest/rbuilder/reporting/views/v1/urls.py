#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import url, patterns
from mint.django_rest.rbuilder.reporting.views.v1 import reportdispatcher
from mint.django_rest.rbuilder.reporting.views.v1 import views
from mint.django_rest import urls
URL = urls.URLRegistry.URL

urlpatterns = ( 
   # belongs in the one view module, really
   URL(r'(.*?)/descriptor/?$', reportdispatcher.ReportDescriptor()),
   URL(r'(.*?)/data/(.*?)/?$', reportdispatcher.ReportDispatcher()),
   URL(r'(.*?)/?$',            views.ReportView())
)

