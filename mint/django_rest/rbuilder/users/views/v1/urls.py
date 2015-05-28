#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.users.views.v1 import views
from mint.django_rest.rbuilder.rbac.views.v1 import views as rbacviews
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
    URL(r'^/(?P<user_id>\d+)/roles/?$',
        rbacviews.RbacUserRolesService(),
        name='UserRoles',
        model='rbac.RbacUserRoles'),
    URL(r'^/(?P<user_id>\d+)/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRole',
        model='rbac.RbacUserRole'),

)
