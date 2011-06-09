#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access

from django.http import HttpResponse

class UsersService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request, user_id=None):
        return self.get(user_id)
    
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
        # if user.is_admin:
        #     # CHANGEME -- find appropriate exception to place here
        #     raise Exception('only admins can create admin users')
        return self.mgr.addUser(user)
    
    @requires('user')
    @return_xml
    def rest_PUT(self, request, user_id, user):
        # if user.is_admin:
        #     pass
        return self.mgr.updateUser(user_id, user)

    @access.admin
    def rest_DELETE(self, request, user_id):
        self.mgr.deleteUser(user_id)
        return HttpResponse(status=204)

class UserGroupsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, user_group_id=None):
        return self.get(user_group_id)
    
    def get(self, user_group_id=None):
        if user_group_id:
            return self.mgr.getUserGroup(user_group_id)
        else:
            return self.mgr.getUserGroups()
    
    
    @requires('user_group')       
    @return_xml
    def rest_POST(self, request, user_group):
        return self.mgr.addUserGroup(user_group)
    
    @requires('user_group')
    @return_xml
    def rest_PUT(self, request, user_group_id, user_group):
        return self.mgr.updateUserGroup(user_group_id, user_group)

    @access.admin
    def rest_DELETE(self, request, user_group_id):
        self.mgr.deleteUserGroup(user_group_id)
        return HttpResponse(status=204)


class UserUserGroupsService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request, user_id):
        return self.mgr.getUserUserGroups(user_id)


class UserGroupMembersService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request, user_group_id):
        return self.get(user_group_id)

    def get(self, user_group_id):
        return self.mgr.getUserGroupMembers(user_group_id)
