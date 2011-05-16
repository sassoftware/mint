#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml


class UsersService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request, user_id=None):
        return self.get(user_id)
    
    def get(self, user_id=None):
        if user_id:
            return self.mgr.getUser(user_id)
        else:
            return self.mgr.getUsers()
    
    @requires('user')
    @return_xml
    def rest_POST(self, request, user):
        return self.mgr.addUser(user)
    
    @requires('user')
    @return_xml
    def rest_PUT(self, request, user_id, user):
        return self.mgr.updateUser(user_id, user)

    def rest_DELETE(self, request, user_id):
        self.mgr.deleteUser(user_id)
       
        
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
    
    def rest_DELETE(self, request, user_group_id):
        self.mgr.deleteUserGroup(user_group_id)


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