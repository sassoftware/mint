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

    def _updateSingleColumnThing(self, modelClass, old_id, obj, field):
        '''update a table where the only value is a primary key'''
        #oldObj = modelClass.objects.get(pk=old_id)
        #if not oldObj:
        #    return None
        #print oldObj.__dict__
        #value = getattr(obj, field)
        #print "FIELD=%s" % field
        #print "NEW VALUE=%s" % value
        #setattr(oldObj, field, value)
        #print oldObj.__dict__
        #oldObj.save(force_update=True)
        # modelClass.objects.raw('UPDATE % FROM '?
        # return oldObj
        return None

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
        
    def _role(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacRole)

    @exposed
    def getRbacRoles(self):
        #roles = models.RbacRoles()
        #roles.rbac_role = models.RbacRole.objects.all()
        #return roles
        return self._getThings(models.RbacRoles, models.RbacRole, 'rbac_role')

    @exposed
    def getRbacRole(self, role):
        return self._role(role)
   
    @exposed
    def addRbacRole(self, role):
        return self._addThing(models.RbacRole, role)

    @exposed
    def updateRbacRole(self, old_id, role):
        return self._updateSingleColumnThing(models.RbacRole, old_id, role, 'role_id')

    @exposed
    def deleteRbacRole(self, role):
        return self._deleteThing(models.RbacRole, role) 


