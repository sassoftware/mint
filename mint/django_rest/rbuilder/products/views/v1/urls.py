#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.products.views.v1 import views
from mint.django_rest import urls
URL = urls.URLRegistry.URL

urlpatterns = patterns('products.views.v1',

    URL(r'/(?P<short_name>(\w|\-)*)/versions/(?P<version>(\w|\.)*)/?$',
        views.MajorVersionService(),
        name='MajorVersions'),

)


