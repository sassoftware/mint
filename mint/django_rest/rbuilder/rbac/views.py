#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to role based access control.

#import os
#import time
#
from django.http import HttpResponse #, HttpResponseNotFound
#from django_restapi import resource
#
#from mint.db import database
#from mint import users
from mint.django_rest.deco import return_xml, access, requires #, ACCESS, \
#    HttpAuthenticationRequired, getHeaderValue, xObjRequires
#from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.rbac import models
#from mint.django_rest.rbuilder.projects import models as projectsmodels

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
    @access.admin
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
    @access.admin
    @return_xml
    def rest_GET(self, request, user_id, role_id=None):
        return self.get(user_id, role_id)

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
        return self.get(role_id, user_id)

    def get(self, role_id, user_id=None):
        if user_id is not None:
            return self.mgr.getUser(user_id)
        else:
            return self.mgr.getRbacUsersForRole(role_id)

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

