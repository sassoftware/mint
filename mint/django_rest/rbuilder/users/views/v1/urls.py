#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.users.views.v1 import views
from mint.django_rest.rbuilder.notices.views.v1 import views as noticesviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    URL(r'^/?$',
        views.UsersService(),
        name='Users',
        model='users.Users'),
    URL(r'^/(?P<user_id>\d+)/?$',
        views.UserService(),
        name='User',
        model='users.User'),
    URL(r'^/(?P<user_id>\d+)/notices/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices'),

)


