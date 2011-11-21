#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from xobj import xobj

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.users import models
from mint import mint_error, server

from django.db import transaction
import time
import random

exposed = basemanager.exposed

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
        return user

    @exposed
    def getUsers(self):
        Users = models.Users()
        Users.user = models.User.objects.all()
        return Users

    @exposed
    def addUser(self, user, by_user=None):

        # Sanitize user fields
        if not user.display_email:
            user.display_email = ''
        if not user.blurb:
            user.blurb = ''
        if not user.password:
            user.password = ''
        # Create a MintServer object, because that gives us access to
        # the Users class. We won't use registerNewUser, since that
        # performs additional checks that are not necessary (all auth
        # has already been performed)
        s = server.MintServer(self.cfg, allowPrivate=True)
        active = 1
        try:
            s.users.registerNewUser(user.user_name, user.password, user.full_name,
                user.email, user.display_email, user.blurb, active)
        except (mint_error.PermissionDenied, mint_error.InvalidError), e:
            raise self.exceptions.MintException(e)
        dbuser = models.User.objects.get(user_name=user.user_name)
        dbuser.can_create  = user.can_create
        dbuser.created_by  = by_user
        dbuser.modified_by = by_user
        dbuser.is_admin    = user.is_admin
        dbuser.deleted     = False
        dbuser.save()
            
        self.mgr.getOrCreateIdentityRole(user, by_user)
        self.mgr.configureMyQuerysets(dbuser, by_user)
        self.mgr.retagQuerySetsByType('user', by_user)
        return dbuser

    def _setPassword(self, user, password):
        if not password:
            return user
        # We need to flush everything to the db, or else the mint db
        # will be deadlocking on the locked row
        self._commit()
        s = server.MintServer(self.cfg, allowPrivate=True)
        s.auth = self.auth
        s.auth.userId = self.user.user_id
        s.authToken = self.auth.token
        try:
            # casting password to string (from unicode)
            # is necessary to fix bug (mingle 546).
            # DO NOT REMOVE THIS as it will cause a traceback
            # containing the cleartext password
            s.setPassword(user.user_id, str(password))
        finally:
            self._newTransaction()
        return models.User.objects.get(user_name=user.user_name)

    @exposed
    def updateUser(self, user_id, user, by_user=None):

        dbuser = models.User.objects.get(pk=user_id, deleted=False)
        if user.user_name and user.user_name != dbuser.user_name:
            raise self.exceptions.UserCannotChangeNameException()

        # only admins can edit these bits
        if not by_user or not by_user.is_admin:
            user.is_admin   = dbuser.is_admin
            user.can_create = dbuser.can_create
            user.user_name  = dbuser.user_name
            
        if by_user.is_admin and by_user.pk == dbuser.pk:
            # can't de-admin yourself
            user.is_admin = True

        user.modified_by = by_user
        user.modified_date = time.time()
        user.deleted = False
        user.save()
        user = self._setPassword(user, user.password)
        self.mgr.configureMyQuerysets(user, by_user)
        return user

    def _commit(self):
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()

    def _newTransaction(self):
        transaction.enter_transaction_management()
        transaction.managed(True)

    @classmethod
    def _toBool(cls, val):
        if val is None:
            return None
        if not isinstance(val, basestring):
            val = str(val)
        val = val.lower()
        if val in ('true', 'false'):
            return val == 'true'
        if val == '1':
            return True
        return False

    @exposed
    def deleteUser(self, user_id, forUser=None):
        # users are not actually deleted, they are only set to deleted
        # to preserve metadata and relations around them.
        if user_id == str(self.user.user_id):
            raise self.exceptions.UserSelfRemovalException()
        deleting = models.User.objects.filter(pk=user_id, deleted=False)
        if not len(deleting) > 0:
            raise self.exceptions.UserNotFoundException()
        deleting = deleting[0]

        # so that the old user name can be recycled, add a random number
        # on the end 
        oldUserName = deleting.user_name
        deleting.user_name = "%s:%s" % (deleting.user_name, random.randint(0,99999999))
        # if the user name was actually using close to the 127 allowed characters (god, why?)
        # don't worry so much about the random number... a rather unlikely scenario
        excess = 126 - len(deleting.user_name) - 1
        if excess < 0:
            deleting.user_name = deleting.user_name[0:excess]

        deleting.deleted = True
        deleting.save()
        # need to retag because we haven't actually deleted it, otherwise
        # cascade takes care of tag removal for other resources
        self.mgr.retagQuerySetsByType('user', forUser)
        # delete querysets for cleanup reasons, but also so the username
        # can be recycled as My Querysets have the user name in them
        from mint.django_rest.rbuilder.querysets import models as querymodels
        from mint.django_rest.rbuilder.rbac import models as rbacmodels
        querymodels.QuerySet.objects.filter(
            personal_for=deleting
        ).delete()
        rbacmodels.RbacRole.objects.filter(
            name="user:%s" % oldUserName
        ).delete()

    @exposed
    def getSessionInfo(self):
        session = models.Session()
        if self.user:
            session.user = [ self.user ]
        else:
            session.user = [ self._NoUser ]
        return session

    class _UserClass(object):
        _xobj = xobj.XObjMetadata(tag='user')
    _NoUser = _UserClass()

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
