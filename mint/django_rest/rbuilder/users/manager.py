#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
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
    
    def cancelUserAccount(self, username):
        user_id = self.getUserId(username)
        self._ensureNoOrphans(user_id)
        self.filterLastAdmin(username)
        
        projectList = models.UserGroupMember.objects.all().filter(user_id=user_id)
        for membership in projectList:
            project_id = productmodels.Projects.objects.get(hostname=membership.hostname).project_id
            pass
            
    def _ensureNoOrphans(self, user_id):
        pass
    
    
class UserGroupsManager(basemanager.BaseManager):
    @exposed
    def getUserGroup(self, user_group_id):
        user_group = models.UserGroup.objects.get(pk=user_group_id)
        return user_group
        
    @exposed
    def getUserGroups(self):
        UserGroups = models.UserGroups()
        UserGroups.user_group = models.UserGroup.objects.all()
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
        
        
class UserUserGroupsManager(basemanager.BaseManager):
    @exposed
    def getUserUserGroups(self, user_id):
        UserGroups = models.UserGroups()
        user_groups = models.User.objects.get(user_id=user_id).user_groups.all()
        UserGroups.user_group = user_groups
        return UserGroups
        
    
# class UserGroupMembersManager(basemanager.BaseManager):
#     @exposed
#     def getUserGroupMembers(self, user_group_id):
#         user_group_members = models.UserGroupMembers.objects.get(pk=user_group_id)
#         return user_group_members
        
class UserGroupMembersManager(basemanager.BaseManager):
    @exposed
    def getUserGroupMembers(self, user_group_id):
        UserGroupMembers = models.UserGroupMembers()
        groups = models.User.user_groups.through.objects.filter(user_group_id=user_group_id)
        UserGroupMembers.user_group_member = groups
        return UserGroupMembers