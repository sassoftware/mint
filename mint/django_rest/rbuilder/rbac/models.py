#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# RBAC models

import sys
from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from xobj import xobj

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
    # objects = modellib.RbacRoleManager() # needed because of non-integer PK?
    _xobj_hidden_accessors = set(['rbacuserrole_set','rbacpermission_set'])

    role_id = D(models.TextField(primary_key=True),
        "the database ID for the role")

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
    rbac_role    =  D(modellib.ForeignKey(RbacRole, 
        null=False, db_column='role_id'), 'rbac_role id')
    queryset     =  D(modellib.ForeignKey(querymodels.QuerySet, 
        null=False, db_column='queryset_id'), 'queryset id')
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