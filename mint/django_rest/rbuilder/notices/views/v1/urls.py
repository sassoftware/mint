#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.notices.views.v1 import views
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    URL(r'^/users/(?P<user_id>\d+)/?$',
        views.UserNoticesService(),
        name='UserNotices2'),

)


