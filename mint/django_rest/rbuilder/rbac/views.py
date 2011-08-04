#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to role based access control.

#import os
#import time
#
#from django.http import HttpResponse, HttpResponseNotFound
#from django_restapi import resource
#
#from mint.db import database
#from mint import users
from mint.django_rest.deco import return_xml, access #, requires, ACCESS, \
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
           <user id="..."/>
           <rbac_context id="..."/>
           <action>WRITE</action>
        </rbac_permission>
        ...
    </rbac_permissions>
    """

    @access.admin
    @return_xml
    def rest_GET(self, request, permission_id=None):
        # TODO
        return None

    # TODO: rest_PUT
    # TODO: rest_DELETE


class RbacRolesService(BaseRbacService):
    """
    Adds and edits roles.
    <rbac_roles>
       <rbac_role id="http://hostname/api/rbac/roles/sysadmin">
          <description>foo</description>
       </rbac_role>
    </rbac_roles>    
    """

    @access.admin
    @return_xml
    def rest_GET(self, request, role_id=None):
        return self.get(role_id)

    def get(self, role_id=None):
        if role_id is not None:
            return self.mgr.getRbacRole(role_id)
        else:
            return self.mgr.getRbacRoles()

    # TODO: rest_PUT
    # TODO: rest_DELETE

class RbacUserRolesService(BaseRbacService):
   """
   Assign roles to a user.
   <rbac_roles>
   ...
   </rbac_roles>
   """

   @access.admin
   @return_xml
   def rest_GET(slef, request):
       return None

   # TODO: rest_PUT
   # TODO: rest_DELETE
 
class RbacContextsService(BaseRbacService):
    """
    Adds and edits contexts.
    <rbac_contexts>
        <rbac_context id="http://hostname/api/rbac/contexts/datacenter">
           <description>foo</description>
        </rbac_context>
    </rbac_contexts>
    """
   
    @access.admin
    @return_xml
    def rest_GET(self, request, system_state_id=None):
        return None

    # TODO: rest_PUT
    # TODO: rest_DELETE

