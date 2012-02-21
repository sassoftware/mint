#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
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


