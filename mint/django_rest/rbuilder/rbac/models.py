#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# RBAC models

#import datetime
import sys
#import urllib
#import urlparse
#from dateutil import tz
#
#from conary import versions
#from conary.deps import deps
#
#from django.conf import settings
from django.db import models # connection
#from django.db.backends import signals
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
#from mint.django_rest.rbuilder import models as rbuildermodels
#from mint.django_rest.rbuilder.projects.models import Project, ProjectVersion, Stage
#from mint.django_rest.rbuilder.users import models as usersmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
from xobj import xobj
#
#Cache = modellib.Cache
#XObjHidden = modellib.XObjHidden
#APIReadOnly = modellib.APIReadOnly

class RbacRoles(modellib.XObjModel):
    '''
    A collection of RbacRoles
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'rbac_roles')
    list_fields = ['rbac_role']
    role = []
    objects = modellib.RbacRolesManager() # TODO: add django manager
    view_name = 'RbacRoles' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.role]

class RbacRole(modellib.XObjIdModel):
    '''
    An RbacRole represents a role a user has that is used to determine a RbacPermission
    on an RbacContext.  Example roles could be "syadmin", "developer", or "it_architect"
    '''

    # XSL = "fixme.xsl" # TODO

    class Meta:
        db_table = 'rbac_role'

    view_name = 'RbacRole' # TODO

    _xobj = xobj.XObjMetadata(
        tag = 'rbac_role',
        attributes = {'id':str},
    )

    # objects = modellib.RbacManager() # NEEDED?

    role_id = D(models.TextField(primary_key=True),
        "the database ID for the role")

class RbacContexts(object):
    # TODO
    pass

class RbacContext(object):
    # TODO
    pass

class RbacPermissions(object):
    # TODO
    pass

class RbacPermission(object):
    # TODO
    pass

 
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
#for mod_obj in rbuildermodels.__dict__.values():
#    if hasattr(mod_obj, '_meta'):
#        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
#for mod_obj in usersmodels.__dict__.values():
#    if hasattr(mod_obj, '_meta'):
#       modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
