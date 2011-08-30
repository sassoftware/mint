#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access
from django.http import HttpResponse
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS

def rbac_can_read_user(view, request, user_id, *args, **kwargs):
    obj = view.mgr.getUser(user_id)
    user = request._authUser
    if obj.pk == user.pk:
        # you can always read yourself
        return True 
    return view.mgr.userHasRbacPermission(user, obj, READMEMBERS)

def rbac_can_write_user(view, request, user_id, *args, **kwargs):
    obj = view.mgr.getUser(user_id)
    user = request._authUser
    if obj.pk == user.pk:
        # you can always update yourself
        # TODO: but you can't delete yourself unless admin
        return True
    return view.mgr.userHasRbacPermission(user, obj, MODMEMBERS)

class UsersService(service.BaseService):
    
    # manual rbac
    @access.authenticated
    @return_xml
    def rest_GET(self, request, user_id=None):
        if user_id is not None:
             if rbac_can_read_user(self, request, user_id):
                 return self.get(user_id)
             raise PermissionDenied()
        else:
             # non-priveledged users should use a queryset
             # they have access to in order to obtain all results
             if request._is_admin:
                 return self.get()
             # TODO: redirect to queryset
             raise PermissionDenied()

    def get(self, user_id=None):
        if user_id:
            return self.mgr.getUser(user_id)
        else:
            return self.mgr.getUsers()

    # Has to be public, so one can create an account before logging in
    @access.anonymous
    @requires('user')
    @return_xml
    def rest_POST(self, request, user):
        if not user.password:
            return HttpResponse(status=400)
        if not user.user_name:
            return HttpResponse(status=400)
        return self.mgr.addUser(user)

    @rbac(rbac_can_write_user)
    @requires('user')
    @return_xml
    def rest_PUT(self, request, user_id, user):
        oldUser = self.mgr.getUser(user_id)
        if oldUser.pk != user.pk:
            raise PermissionDenied()
        return self.mgr.updateUser(user_id, user)

    @access.admin
    def rest_DELETE(self, request, user_id):
        self.mgr.deleteUser(user_id)
        return HttpResponse(status=204)

class UserGroupsService(service.BaseService):

    @access.admin # FIXME: correct?
    @return_xml
    def rest_GET(self, request, user_group_id=None):
        return self.get(user_group_id)
    
    def get(self, user_group_id=None):
        if user_group_id:
            return self.mgr.getUserGroup(user_group_id)
        else:
            return self.mgr.getUserGroups()
    
    # user groups are only exposed in rBuilder for the purpose
    # of defining the admin user, so only the admin user
    # should be able to create user groups
    @access.admin 
    @requires('user_group')       
    @return_xml
    def rest_POST(self, request, user_group):
        return self.mgr.addUserGroup(user_group)
    
    @access.admin
    @requires('user_group')
    @return_xml
    def rest_PUT(self, request, user_group_id, user_group):
        return self.mgr.updateUserGroup(user_group_id, user_group)

    @access.admin
    def rest_DELETE(self, request, user_group_id):
        self.mgr.deleteUserGroup(user_group_id)
        return HttpResponse(status=204)


class UserUserGroupsService(service.BaseService):
    
    @rbac(rbac_can_read_user)
    @return_xml
    def rest_GET(self, request, user_id):
        return self.mgr.getUserUserGroups(user_id)


class UserGroupMembersService(service.BaseService):
    
    @access.admin
    @return_xml
    def rest_GET(self, request, user_group_id):
        return self.get(user_group_id)

    def get(self, user_group_id):
        return self.mgr.getUserGroupMembers(user_group_id)

class SessionService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getSessionInfo()


