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
from mint.django_rest.rbuilder.rbac.views.v1 import views
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    URL(r'^/?$',
        views.RbacService(),
        name='Rbac',
        model='rbac.Rbac'),
    URL(r'^/grants/?$',
        views.RbacPermissionsService(),
        name='RbacPermissions',
        model='rbac.RbacPermissions'),
    URL(r'^/grants/(?P<permission_id>\d+)?$',
        views.RbacPermissionService(),
        name='RbacPermission',
        model='rbac.RbacPermission'),
    URL(r'^/roles/?$',
        views.RbacRolesService(),
        name='RbacRoles',
        model='rbac.RbacRoles'),
    URL(r'^/roles/(?P<role_id>\d+)?$',
        views.RbacRoleService(),
        name='RbacRole',
        model='rbac.RbacRole'),
    URL(r'^/(?P<user_id>\d+)/roles/?$',
        views.RbacUserRolesService(),
        name='RbacUserRoles',
        model='rbac.RbacUserRoles'),
    URL(r'^/roles/(?P<role_id>\d+)/grants/?$',
        views.RbacRoleGrantsService(),
        name='RbacRoleGrants',
        model='rbac.RbacPermissions'),
    URL(r'^/roles/(?P<role_id>\d+)/users/?$',
        views.RbacRoleUsersService(),
        name='RbacRoleUser',
        model='users.Users'),
    URL(r'^/permissions/?$',
        views.RbacPermissionTypesService(),
        name='RbacPermissionTypes',
        model='rbac.RbacPermissionTypes'),
    URL(r'^/permissions/(?P<permission_type_id>\d+)?$',
        views.RbacPermissionTypeService(),
        name='RbacPermissionType',
        model='rbac.RbacPermissionType'),


)
