#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.users import models
from mint import mint_error, server

exposed = basemanager.exposed

from django.db import connection

class UserExceptions(object):
    class BaseException(errors.RbuilderError):
        pass
    class UserNotFoundException(BaseException):
        "The specified user does not exist"
        status = 404
    class UserCannotChangeNameException(BaseException):
        "The user's login name cannot be changed"
        status = 403
    class AdminRequiredException(BaseException):
        "Only administrators are allowed to edit other users"
        status = 403
    class UserSelfRemovalException(BaseException):
        "Users are not allowed to remove themselves"
        status = 403
    class MintException(BaseException):
        def __init__(self, exc):
            self.msg = exc.msg
            self.status = exc.status
            self.kwargs = dict()

class UsersManager(basemanager.BaseManager):
    exceptions = UserExceptions

    @exposed
    def getUser(self, user_id):
        user = models.User.objects.get(pk=user_id)
        user.set_is_admin()
        return user

    @exposed
    def getUsers(self):
        Users = models.Users()
        Users.user = models.User.objects.all()
        for user in Users.user:
            user.set_is_admin()
        return Users

    @exposed
    def addUser(self, user):
        # Sanitize user fields
        if not user.display_email:
            user.display_email = ''
        if not user.blurb:
            user.blurb = ''
        # Create a MintServer object, because that gives us access to
        # the Users class. We won't use registerNewUser, since that
        # performs additional checks that are not necessary (all auth
        # has already been performed)
        s = server.MintServer(self.cfg, allowPrivate=True)
        active = True
        try:
            s.users.registerNewUser(user.user_name, user.password, user.full_name,
                user.email, user.display_email, user.blurb, active)
        except (mint_error.PermissionDenied, mint_error.InvalidError), e:
            raise self.exceptions.MintException(e)
        return models.User.objects.get(user_name=user.user_name)

    def _setPassword(self, user, password):
        if not password:
            return user
        s = server.MintServer(self.cfg, allowPrivate=True)
        s.setPassword(user.user_id, password)
        return models.User.objects.get(user_name=user.user_name)

    @exposed
    def updateUser(self, user_id, user):
        if not self._auth.admin:
            if user_id != str(self.user.user_id):
                # Non-admin users can only edit themselves
                raise self.exceptions.AdminRequiredException()
        dbusers = models.User.objects.filter(pk=user_id)
        if not dbusers:
            raise self.exceptions.UserNotFoundException()
        dbuser = dbusers[0]
        if user.user_name and user.user_name != dbuser.user_name:
            raise self.exceptions.UserCannotChangeNameException()
        # Copy all fields the user may have chosen to change
        models.User.objects.copyFields(dbuser, user)
        dbuser.save()
        dbuser = self._setPassword(dbuser, user.password)
        return dbuser

    @exposed
    def deleteUser(self, user_id):
        if user_id == str(self.user.user_id):
            raise self.exceptions.UserSelfRemovalException()
        cu = connection.cursor()
        ret = cu.execute("DELETE FROM users WHERE userid = %s", [ user_id ])
        if not ret.rowcount:
            raise self.exceptions.UserNotFoundException()

    # def cancelUserAccount(self, username):
    #     user_id = self.getUserId(username)
    #     self._ensureNoOrphans(user_id)
    #     self.filterLastAdmin(username)
    #     
    #     projectList = models.UserGroupMember.objects.all().filter(user_id=user_id)
    #     for membership in projectList:
    #         project_id = productmodels.Projects.objects.get(hostname=membership.hostname).project_id
    #         pass
            
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
