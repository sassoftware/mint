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


# Services related to role based access control.

from django.http import HttpResponse, HttpResponseRedirect
from mint.django_rest.deco import return_xml, access, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.rbac import models
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.querysets import models as querymodels

class BaseRbacService(service.BaseService):
    pass

class RbacService(BaseRbacService):
    """
    URLs for discovery purposes
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return models.Rbac()

class RbacPermissionTypesService(BaseRbacService):
    """ 
    Returns the list of permissions configurable for RBAC
    """
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getRbacPermissionTypes()

class RbacPermissionTypeService(BaseRbacService):
    """ 
    Returns the list of permissions configurable for RBAC
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request, permission_type_id):
        return self.get(permission_type_id)

    def get(self, permission_type_id):
        return self.mgr.getRbacPermissionType(permission_type_id)

 
class RbacPermissionsService(BaseRbacService):
    """
    Grants and removes permissions.
    <grants>
        <grant id="http://hostname/api/rbac/permissions/1">
           <permission_id>1</permission_id>
           <role id="http://..."/>
           <queryset id="http://...">
           <permission>write</permission>
        </grant>
        ...
    </grants>
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getRbacPermissions()

    # CREATE
    @access.admin
    @requires('grant', save=False)
    @return_xml
    def rest_POST(self, request, grant):
        return self.mgr.addRbacPermission(grant, request._authUser)


class RbacPermissionService(BaseRbacService):
    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request, permission_id):
        return self.get(permission_id)

    def get(self, permission_id):
        return self.mgr.getRbacPermission(permission_id)

    # UPDATE
    @access.admin
    @requires('grant', save=False)
    @return_xml
    def rest_PUT(self, request, permission_id, grant):
        return self.mgr.updateRbacPermission(permission_id, grant, request._authUser)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, permission_id):
        self.mgr.deleteRbacPermission(permission_id)
        return HttpResponse(status=204)

class RbacQuerySetGrantMatrixService(BaseRbacService):
    '''
    query_set/N/grant_matrix -- a very UI specific
    transmogrification of grants data
    '''

    @access.admin
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getRbacGrantMatrix(query_set_id, request)

class RbacRolesService(BaseRbacService):
    """
    Adds and edits roles.
    <roles>
       <role id="http://hostname/api/rbac/roles/sysadmin">
           <role_id>sysadmin</role_id>
       </role>
    </roles>    
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getRbacRoles()

    # CREATE
    @access.admin
    @return_xml
    @requires('role', save=False)
    def rest_POST(self, request, role):
        return self.mgr.addRbacRole(role, request._authUser)

def can_read_role(view, request, role_id, *args, **kwargs):
    # users are allowed to see their roles, you will notice this
    # doesn't run through RBAC *directly* because we can't use
    # RBAC to RBAC RBAC (actually, it might work, but...)
    user = request._authUser
    if user.is_admin:
        return True
    in_role = view.mgr.isUserInRole(user, role_id)
    if in_role:
        return True
    return False

def can_read_user_roles(view, request, user_id, role_id=None, *args, **kwargs):
    # users can see their roles
    user = request._authUser
    if role_id is None:
        if user.is_admin:
            return True
        if str(user.pk) == str(user_id):
            return True
        return False
    else: 
        return can_read_role(view, request, role_id, *args, **kwargs)

class RbacRoleService(BaseRbacService):
    """
    Adds and edits roles.
    <roles>
       <role id="http://hostname/api/rbac/roles/sysadmin">
           <role_id>sysadmin</role_id>
       </role>
    </roles>    
    """

    # READ
    @rbac(can_read_role)
    @return_xml
    def rest_GET(self, request, role_id):
        return self.get(role_id)

    def get(self, role_id):
        return self.mgr.getRbacRole(role_id)

    # UPDATE
    @access.admin
    @requires('role', save=False)
    @return_xml
    def rest_PUT(self, request, role_id, role):
        return self.mgr.updateRbacRole(role_id, role, request._authUser)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, role_id):
        self.mgr.deleteRbacRole(role_id)
        return HttpResponse(status=204)


class RbacUserRolesService(BaseRbacService):
    """
    Assign roles to a user & list the roles they have.
    <roles>
    ...
    </roles>
    """

    # READ
    @rbac(can_read_user_roles)
    @return_xml
    def rest_GET(self, request, user_id, role_id=None):
        return self.get(user_id, role_id)

    # TODO: this really should be split out into two services
    # functions should not return multiple types of entities
    def get(self, user_id, role_id=None):
        if role_id is not None:
            return self.mgr.getRbacUserRole(user_id, role_id)
        else:
            return self.mgr.getRbacUserRoles(user_id)

    # CREATE -- ADD A RBAC ROLE
    @access.admin
    @requires('role', save=False)
    @return_xml
    def rest_POST(self, request, user_id, role):
        return self.mgr.addRbacUserRole(user_id, role, request._authUser)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, user_id, role_id):
        self.mgr.deleteRbacUserRole(user_id, role_id)
        return HttpResponse(status=204)


class RbacRoleGrantsService(BaseRbacService):
    """
    What grants are available on a role?
    <roles>
    ...
    </roles>
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request, role_id, grant_id=None):
        return self.get(role_id, grant_id)

    def get(self, role_id, grant_id=None):
        if grant_id is not None:
            return self.mgr.getRbacPermission(grant_id)
        else:
            return self.mgr.getRbacPermissionsForRole(role_id)

    # CREATE -- ADD A RBAC ROLE
    # NOTE -- same as RbacRolesService method
    @access.admin
    @requires('grant', save=False)
    @return_xml
    def rest_POST(self, request, role_id, grant):
        return self.mgr.addRbacPermission(grant, request._authUser)

    # DELETE
    # NOTE -- same as RbacRolesService method
    @access.admin
    def rest_DELETE(self, request, role_id, grant_id):
        self.mgr.deleteRbacPermission(grant_id)
        return HttpResponse(status=204)


class RbacRoleUsersService(BaseRbacService):
    """
    What roles have what users?
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request, role_id, user_id=None):
        return self.get(role_id, user_id, request)

    def get(self, role_id, user_id=None, request=None):
        if user_id is None:
            qs = querymodels.QuerySet.objects.get(name='All Users', is_public=True)
            url = "/api/v1/query_sets/%s/all;filter_by=[user_roles.role.pk,EQUAL,%s]%s" % (qs.pk, role_id, request.params)
            return HttpResponseRedirect(url)
        else:
            # obsolete URL no longer linked to since redirect
            url = "/api/v1/users/%s%s" % (user_id, request.params)
            return HttpResponseRedirect(url)

    # CREATE -- ADD A RBAC USER TO A ROLE
    @access.admin
    @requires('user', save=False)
    @return_xml
    def rest_POST(self, request, role_id, user):
        return self.mgr.addRbacUserRole(user.pk, role_id, request._authUser)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, role_id, user_id):
        self.mgr.deleteRbacUserRole(user_id, role_id)
        return HttpResponse(status=204)
