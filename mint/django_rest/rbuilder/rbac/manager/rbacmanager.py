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
#from mint.django_rest.rbuilder.inventory import errors
#from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.manager import basemanager
#from mint.django_rest.rbuilder.querysets import models as querysetmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
#from mint.rest import errors as mint_rest_errors
from django.db import connection, transaction


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
        if not obj:
            return None
        obj.save()
        return obj

    def _updateThing(self, modelClass, old_id, obj):
        '''generic update method'''
        # FIXME: not convinced this works
        oldObj = modelClass.objects.get(pk=old_id)
        if not oldObj:
            return None
        obj.save()
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
        return self._addThing(models.RbacPermission, permission)

    @exposed
    def updateRbacPermission(self, old_id, permission):
        raise Exception("TODO") # TODO

    @exposed
    def deleteRbacPermission(self, permission):
        return self._deleteThing(models.RbacPermission, self._permission(permission))

    #########################################################
    # RBAC USER_ROLE METHODS
    
    # TODO
    # getRbacUserRole
    # addRbacUserRole
    # updateRbacUserRole
    # deleteRbacUserRole   


