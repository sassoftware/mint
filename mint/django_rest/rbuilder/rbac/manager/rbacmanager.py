#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

#import cPickle
import logging
#import sys
#import datetime
#import random
#import time
#import traceback
#from dateutil import tz
#from xobj import xobj

#from django.db import connection
#from django.conf import settings
#from django.contrib.redirects import models as redirectmodels
#from django.contrib.sites import models as sitemodels
#from django.core.exceptions import ObjectDoesNotExist

#from mint.lib import uuid, x509
#from mint.lib import data as mintdata
from mint.django_rest.rbuilder.rbac import models 
#from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.users import models as usersmodels
#from mint.django_rest.rbuilder.inventory import errors
#from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.manager import basemanager
#from mint.django_rest.rbuilder.querysets import models as querysetmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
#from mint.rest import errors as mint_rest_errors
from django.db import connection, transaction
import exceptions

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class RbacManager(basemanager.BaseManager):

    def _getThings(self, modelClass, containedClass, collection_field):
        '''generic collection loader'''
        things = modelClass()
        setattr(things, collection_field, containedClass.objects.all())
        return things

    def _addThing(self, modelClass, obj):
        '''generic creation method'''
        # it's already saved, crazy @requires stuff.
        #obj.save()
        return obj

    def _updateThing(self, modelClass, old_id, obj):
        '''generic update method'''
        # it's already saved, crazy @requires stuff.
        #obj.save(force_update=True)
        return obj

    def _updateSingleColumnThing(self, modelClass, old_id, obj, field, table):
        '''update a table where the only value is a primary key'''
        oldObj = modelClass.objects.get(pk=old_id)
        if not oldObj:
            return None
        # django doesn't like primary key updates
        # so this is somewhat low level
        newValue = getattr(obj, field)
        oldValue = getattr(oldObj, field)
        cursor = connection.cursor()
        pattern = 'UPDATE ' + table + ' SET ' + field + '=' + '%s WHERE ' + field + '=%s' 
        cursor.execute(pattern, [newValue, oldValue])
        transaction.commit_unless_managed()
        return modelClass.objects.get(pk=newValue)

    def _deleteThing(self, modelClass, obj):
        '''generic delete method'''
        if not obj:
            return None
        obj.delete()
        return obj
    
    def _orId(self, value, modelClass):
        '''prevent duplicate get requests'''
        if type(value) != modelClass:
            return modelClass.objects.get(pk=value)
        return value
    
    #########################################################
    # RBAC ROLE METHODS
    # handled a bit nonstandard due to the string PK
    # and need to override the Django manager
    
    def _role(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacRole)

    @exposed
    def getRbacRoles(self):
        return self._getThings(models.RbacRoles, 
            models.RbacRole, 'rbac_role')

    @exposed
    def getRbacRole(self, role):
        return self._role(role)
   
    @exposed
    def addRbacRole(self, role):
        return self._addThing(models.RbacRole, role)

    @exposed
    def updateRbacRole(self, old_id, role):
        return self._updateSingleColumnThing(models.RbacRole, old_id, 
            role, 'role_id', 'rbac_role')

    @exposed
    def deleteRbacRole(self, role):
        return self._deleteThing(models.RbacRole, self._role(role)) 

    #########################################################
    # RBAC CONTEXT METHODS
    # handled a bit nonstandard due to the string PK
    # and need to override the Django manager

    def _context(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacContext)

    @exposed
    def getRbacContexts(self):
        return self._getThings(models.RbacContexts,
            models.RbacContext, 'rbac_context')

    @exposed
    def getRbacContext(self, context):
        return self._context(context)

    @exposed
    def addRbacContext(self, context):
        return self._addThing(models.RbacContext, context)

    @exposed
    def updateRbacContext(self, old_id, context):
        return self._updateSingleColumnThing(models.RbacContext, old_id,
            context, 'context_id', 'rbac_context')

    @exposed
    def deleteRbacContext(self, context):
        return self._deleteThing(models.RbacContext, self._context(context)) 

    #########################################################
    # RBAC PERMISSION METHODS
    # these do NOT override the manager so are coded differently than above
    
    def _permission(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacPermission)

    @exposed
    def getRbacPermissions(self):
        return self._getThings(models.RbacPermissions,
            models.RbacPermission, 'rbac_permission')

    @exposed
    def getRbacPermission(self, permission):
        return self._permission(permission)

    @exposed
    def addRbacPermission(self, permission):
        permission.save()
        return permission

    @exposed
    def updateRbacPermission(self, old_id, permission):
        permission.save()
        return permission

    @exposed
    def deleteRbacPermission(self, permission):
        return self._deleteThing(models.RbacPermission, self._permission(permission))

    #########################################################

    def _user(self, value):
        '''cast input as a user'''
        return self._orId(value, usersmodels.User)

    #########################################################
    # RBAC USER_ROLE METHODS
    # note -- this may grow to support external user/role
    # mappings later.  This database implementation is only
    # one possible method of storage.
    
    @exposed
    def getRbacUserRoles(self, user_id):
        '''Get all the roles the user is assigned to.'''
        # TODO: allow passing in user or user id
        user = self._user(user_id)
        mapping = models.RbacUserRole.objects.filter(user=user)
        collection = models.RbacRoles()
        collection.rbac_role = [ x.role for x in mapping ]
        return collection 

    @exposed
    def getRbacUserRole(self, user_id, role_id):
        '''See if this user has a certain role.'''
        # TODO: allow passing in user or user id
        user = self._user(user_id)
        role = self._role(role_id)
        mapping = models.RbacUserRole.objects.get(user=user, role=role)
        return mapping.role

    @exposed
    def userHasRbacPermissionTo(self, user_id, context_id, action_id):
        '''
        Can User X Do Action Y On Resoures with Context Z?
        This function is not surfaced directly via REST but is the core
        of how we'll implement RBAC protection on resources.  Permissions
        are simple at the moment, but later some permissions may imply
        others.
        '''
        # TODO -- add to tests
        user = self._user(user_id)
        context = self._context(context_id)
        # TODO -- implement
        # this is the primary function to see if a user is
        # allowed to do something, ex:
        # userHasRbacPermission(sysadmin, 
        raise exceptions.NotImplementedError

    @exposed
    def addRbacUserRole(self, user_id, role_id):
        '''Results in the user having this rbac role'''
        user = self._user(user_id)
        role = self._role(role_id)
        try:
            mapping = models.RbacUserRole.objects.get(user=user, role=role)
            # mapping already exists, nothing to do
        except models.RbacUserRole.DoesNotExist:
            # no role assignment found, create it
            models.RbacUserRole(user=user, role=role).save()
        return role

    # why no update function?
    # update role doesn't make sense here -- just update
    # the actual role.

    @exposed
    def deleteRbacUserRole(self, user_id, role_id):
        '''Results in the user no longer having this role'''
        user = self._user(user_id)
        role = self._role(role_id)
        role = models.RbacRole.objects.get(role=role)
        mapping = models.RbacUserRole.objects.get(user=user, role=role)
        mapping.delete()
        # we're deleting the mapping, not the role
        # so it doesn't make sense to return the role
        # as what we've deleted.
        return mapping


