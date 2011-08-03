#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# RBAC models

#import datetime
#import sys
#import urllib
#import urlparse
#from dateutil import tz
#
#from conary import versions
#from conary.deps import deps
#
#from django.conf import settings
#from django.db import connection, models
#from django.db.backends import signals
#from mint.django_rest.deco import D
#from mint.django_rest.rbuilder import modellib
#from mint.django_rest.rbuilder import models as rbuildermodels
#from mint.django_rest.rbuilder.projects.models import Project, ProjectVersion, Stage
#from mint.django_rest.rbuilder.users import models as usersmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
#from xobj import xobj
#
#Cache = modellib.Cache
#XObjHidden = modellib.XObjHidden
#APIReadOnly = modellib.APIReadOnly

class RbacRoles(object):
    pass

class RbacRole(object):
    pass

class RbacContexts(object):
    pass

class RbacContext(object):
    pass

class RbacPermissions(object):
    pass

class RbacPermission(object):
    pass

 
#for mod_obj in sys.modules[__name__].__dict__.values():
#    if hasattr(mod_obj, '_xobj'):
#        if mod_obj._xobj.tag:
#            modellib.type_map[mod_obj._xobj.tag] = mod_obj
#for mod_obj in rbuildermodels.__dict__.values():
#    if hasattr(mod_obj, '_meta'):
#        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
#for mod_obj in usersmodels.__dict__.values():
#    if hasattr(mod_obj, '_meta'):
#       modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
