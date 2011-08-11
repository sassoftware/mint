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
from mint.django_rest.rbuilder.inventory import models as inventorymodels
#from mint.django_rest.rbuilder.querysets import models as querysetmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
#from mint.rest import errors as mint_rest_errors
from django.db import connection, transaction
import exceptions

log = logging.getLogger(__name__)
exposed = basemanager.exposed

# resource types that we can manipulate RBAC context on:
RESOURCE_TYPE_SYSTEM   = 'system'
RESOURCE_TYPE_PLATFORM = 'platform'
RESOURCE_TYPE_IMAGE    = 'image'

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
    def userHasRbacPermission(self, user=None, context=None, action=None):
        '''
        Can User X Do Action Y On Resoures with Context Z?
        This function is not surfaced directly via REST but is the core
        of how we'll implement RBAC protection on resources.  Permissions
        are simple at the moment, but later some permissions may imply
        others.
        '''
        user = self._user(user)
      
        # if the user is an admin, immediately let them by
        if user.is_admin:
            return True
 
        # get the resource's context -- if none, do not allow access
        found_context = None
        try: 
            found_context = self._context(context)
        except models.RbacContext.DoesNotExist:
            return False

        role_maps = models.RbacUserRole.objects.filter(user=user)
        user_role_ids = [ x.role.pk for x in role_maps ]

        # if the user has no roles on this context, fail immediately
        if len(user_role_ids) == 0:
            return False

        # write access implies read access.  When we have more granular
        # permissions this will have to go.
        acceptable_permitted_actions = [ action ]
        if action == 'read':
            acceptable_permitted_actions.append('write')

        # there is context/roles info, so now find the permissions associated
        # with the context
        resource_permissions = models.RbacPermission.objects.filter(
            rbac_context = found_context,
        ).extra(
            where=['role_id=%s'], params=user_role_ids
        )

        # permit user if they have one of the actions we want...
        # Django seems to displike duplicate extra queries, so...
        for x in resource_permissions:
             if x.action in acceptable_permitted_actions:
                 return True
        return False

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
        mapping = models.RbacUserRole.objects.get(user=user, role=role)
        mapping.delete()
        # we're deleting the mapping, not the role
        # so it doesn't make sense to return the role
        # as what we've deleted.
        return mapping
    
    #########################################################
    # RBAC RESOURCE<->CONTEXT METHODS
    # set a context on a resource, uncontext a resource, etc
    # ex, system256 is "datacenter", system101 is "lab", etc.
    
    def _getManagerByType(self, resource_type):
        '''Get the django manager for a resource'''
        if resource_type == RESOURCE_TYPE_SYSTEM:
            return inventorymodels.System.objects
        #elif resource_type == RESOURCE_TYPE_PLATFORM:
        #    pass
        #elif resource_Type == RESOURCE_TYPE_IMAGE:
        #    pass
        else:
            raise exceptions.NotImplementedError(
                "rbac not yet supported on this resource")

    @exposed
    def getResourceRbacContext(self, resource_type, resource_id):
        mgr = self._getManagerByType(resource_type)
        obj = mgr.get(pk=resource_id)
        return obj.rbac_context

    @exposed
    def setResourceRbacContext(self, resource_type, resource_id, rbac_context):
        mgr = self._getManagerByType(resource_type)
        obj = mgr.get(pk=resource_id)
        obj.rbac_context = rbac_context
        obj.save()
        return obj

    @exposed
    def deleteResourceRbacContext(self, resource_type, resource_id):
        mgr = self._getManagerByType(resource_type)
        obj = mgr.get(pk=resource_id)
        obj.rbac_context = None
        obj.save()
        return obj

