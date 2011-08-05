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
from mint.django_rest.rbuilder.users import models as usersmodels
#from mint.django_rest.rbuilder.jobs import models as jobmodels
from xobj import xobj
#
#Cache = modellib.Cache
#XObjHidden = modellib.XObjHidden
#APIReadOnly = modellib.APIReadOnly

class RbacRoles(modellib.Collection):
    '''
    A collection of RbacRoles
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'rbac_roles')
    list_fields = ['rbac_role']
    rbac_role = []
    objects = modellib.RbacRolesManager() # TODO: add django manager
    view_name = 'RbacRoles' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.rbac_role]

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
    objects = modellib.RbacRoleManager() # needed because of non-integer PK
    _xobj_hidden_accessors = set(['rbacuserrole_set','rbacpermission_set'])

    role_id = D(models.TextField(primary_key=True),
        "the database ID for the role")

class RbacContexts(modellib.Collection):
    '''
    A collection of RbacContexts
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'rbac_contexts')
    list_fields = ['rbac_context']
    rbac_context = []
    objects = modellib.RbacContextsManager() 
    view_name = 'RbacContexts' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.rbac_context]

class RbacContext(modellib.XObjIdModel):
    '''
    An RbacContext is a label assigned to resources that has security permissions
    associated with it.  An example context might be "lab", "datacenter", "tradingfloor",
    etc.  A resource can only have one context.  A resource having no context means
    it is write access to admins only, but viewable to everyone.
    '''
    # XSL = "fixme.xsl" # TODO
    class Meta:
        db_table = 'rbac_context'

    view_name = 'RbacContext' # TODO

    objects = modellib.RbacContextManager() # needed because of non-integer PK
    _xobj = xobj.XObjMetadata(
        tag = 'rbac_context',
        attributes = {'id':str},
    )
    _xobj_hidden_accessors = set(['rbacpermission_set'])

    context_id = D(models.TextField(primary_key=True),
        "the database ID for the context")


class RbacPermissions(modellib.Collection):
    '''
    A collection of RbacPermissions
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'rbac_permissions')
    list_fields = ['rbac_permission']
    rbac_permission = []
    objects = modellib.RbacPermissionsManager()
    view_name = 'RbacPermissions' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.rbac_permission]

class RbacPermission(modellib.XObjIdModel):
    '''
    An RBAC permission maps the combination of a RbacContext, a RbacRole,
    and an action.  For example, on systems tagged "datacenter" a user
    with the "sysadmin" role can "write".
    '''
    # XSL = "fixme.xsl" # TODO
    class Meta:
        db_table = 'rbac_permission'

    view_name = 'RbacPermission' # TODO

    _xobj = xobj.XObjMetadata(
        tag = 'rbac_permission'
    )

    permission_id = D(models.AutoField(primary_key=True),
        "the database ID for the context")
    rbac_role    =  D(modellib.ForeignKey(RbacRole, null=False, db_column='role_id'), 'rbac_role id')
    rbac_context =  D(modellib.ForeignKey(RbacContext, null=False, db_column='context_id'), 'rbac_context id')
    action  = D(models.TextField(), 'allowed capability name')

class RbacUserRoles(modellib.Collection):
    '''
    A collection of RbacUserRoles
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'rbac_user_roles')
    list_fields = ['rbac_user_role']
    rbac_user_role = []
    objects = modellib.RbacUserRolesManager()
    view_name = 'RbacUserRoles' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.rbac_user_role]

class RbacUserRole(modellib.XObjIdModel):
    '''
    Keeps track of what rBuilder users have as RbacRoles.
    This may be used when NOT using a live directory for role mappings, i.e. standalone
    or via a sync script.
    '''
    # XSL = "fixme.xsl" # TODO
    class Meta:
        db_table = 'rbac_user_role'

    view_name = 'RbacUserRole' # TODO

    _xobj = xobj.XObjMetadata(
        tag = 'rbac_user_role'
    )

    rbac_user_role_id = D(models.AutoField(primary_key=True),
        "the database ID for the rbac_user_role")
    role    =  D(modellib.ForeignKey(RbacRole, null=False), 'rbac_role id')
    user    =  D(modellib.ForeignKey(usersmodels.User, null=False), 'user id')

 
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
