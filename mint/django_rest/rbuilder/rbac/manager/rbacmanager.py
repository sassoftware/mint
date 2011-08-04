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

    def _role(self, value):
        if type(value) != models.RbacRole:
           return models.RbacRole.objects.get(pk=value)
        return value

    @exposed
    def getRbacRoles(self):
        roles = models.RbacRoles()
        roles.role = models.RbacRoles.objects.all()
        return roles

    @exposed
    def getRbacRole(self, role):
        return self._role(role)
    
