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

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.users import models

exposed = basemanager.exposed


class UsersManager(basemanager.BaseManager):
    @exposed
    def getUser(self, user_id):
        user = models.User.objects.get(pk=user_id)
        return user

    @exposed
    def getUsers(self):
        Users = models.Users()
        Users.user = models.User.objects.all()
        return Users
    
    @exposed
    def addUser(self, user):
        user.save()
        return user
    
    @exposed
    def updateUser(self, user_id, user):
        user.save()
        return user
        
    @exposed
    def deleteUser(self, user_id):
        user = models.User.objects.get(pk=user_id)
        user.delete()
    
    
class UserGroupsManager(basemanager.BaseManager):
    @exposed
    def getUserGroup(self, user_group_id):
        user_group = models.UserGroup.objects.get(pk=user_group_id)
        return user_group
        
    @exposed
    def getUserGroups(self):
        UserGroups = models.UserGroups()
        UserGroups.group = models.UserGroup.objects.all()
        return UserGroups
    
    @exposed
    def addUserGroups(self, user_group):
        user_group.save()
        return user_group
        
    @exposed
    def updateUserGroups(self, user_group):
        user_group.save()
        return user_group
        
    @exposed
    def deleteUserGroup(self, user_group_id):
        user_group = models.UserGroup.objects.get(pk=user_group_id)
        user_group.delete()
        
class UserGroupMembersManager(basemanager.BaseManager):
    @exposed
    def getUserGroupMembers(self, user_group_id):
        user_group_members = models.UserGroupMembers.objects.get(pk=user_group_id)
        return user_group_members