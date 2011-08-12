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
#from mint.django_rest.rbuilder.inventory import models
#from mint.django_rest.rbuilder.projects import models as projectsmodels

class BaseRbacService(service.BaseService):
    pass
 
class RbacPermissionsService(BaseRbacService):
    """
    Grants and removes permissions.
    <rbac_permissions>
        <rbac_permission id="http://hostname/api/rbac/permissions/1">
           <permission_id>1</permission_id>
           <rbac_role id="http://..."/>
           <queryset id="http://...">
           <action>write</action>
        </rbac_permission>
        ...
    </rbac_permissions>
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request, permission_id=None):
        return self.get(permission_id)

    def get(self, permission_id=None):
        if permission_id is not None:
            return self.mgr.getRbacPermission(permission_id)
        else:
            return self.mgr.getRbacPermissions()

    # CREATE
    @access.admin
    @requires('rbac_permission')
    @return_xml
    def rest_POST(self, request, rbac_permission):
        return self.mgr.addRbacPermission(rbac_permission)

    # UPDATE
    @access.admin
    @requires('rbac_permission')
    @return_xml
    def rest_PUT(self, request, permission_id, rbac_permission):
        return self.mgr.updateRbacPermission(permission_id, rbac_permission)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, permission_id):
        self.mgr.deleteRbacPermission(permission_id)
        return HttpResponse(status=204)


class RbacRolesService(BaseRbacService):
    """
    Adds and edits roles.
    <rbac_roles>
       <rbac_role id="http://hostname/api/rbac/roles/sysadmin">
           <role_id>sysadmin</role_id>
       </rbac_role>
    </rbac_roles>    
    """

    # READ
    @access.admin
    @return_xml
    def rest_GET(self, request, role_id=None):
        return self.get(role_id)

    def get(self, role_id=None):
        if role_id is not None:
            return self.mgr.getRbacRole(role_id)
        else:
            return self.mgr.getRbacRoles()

    # CREATE
    @access.admin
    @return_xml
    @requires('rbac_role')
    def rest_POST(self, request, rbac_role):
        return self.mgr.addRbacRole(rbac_role)

    # UPDATE
    @access.admin
    @requires('rbac_role', save=False)
    @return_xml
    def rest_PUT(self, request, role_id, rbac_role):
        return self.mgr.updateRbacRole(role_id, rbac_role)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, role_id):
        self.mgr.deleteRbacRole(role_id)
        return HttpResponse(status=204)

class RbacUserRolesService(BaseRbacService):
    """
    Assign roles to a user & list the roles they have.
    <rbac_roles>
    ...
    </rbac_roles>
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
    @requires('rbac_role')
    @return_xml
    def rest_POST(self, request, user_id, rbac_role):
        return self.mgr.addRbacUserRole(user_id, rbac_role)

    # DELETE
    @access.admin
    def rest_DELETE(self, request, user_id, role_id):
        self.mgr.deleteRbacUserRole(user_id, role_id)
        return HttpResponse(status=204)

