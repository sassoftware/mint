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
# avoid circular reference
#from mint.django_rest.rbuilder.querysets import models as querymodels
from xobj import xobj
from django.core.urlresolvers import reverse

APIReadOnly = modellib.APIReadOnly

class Rbac(modellib.XObjModel):

    # XSL = 'rbac.xsl'

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = 'rbac')

    grants = D(modellib.HrefField('grants'), "permissions granted to roles")
    roles = D(modellib.HrefField('roles'),  "access control roles")

class RbacRoles(modellib.Collection):
    '''
    A collection of RbacRoles
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'roles')
    list_fields = ['role']
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
        tag = 'role',
        attributes = {'id':str},
    )

    summary_view = [ "name", "description" ]
    
    # objects = modellib.RbacRoleManager() # needed because of non-integer PK?
    _xobj_hidden_accessors = set(['rbacuserrole_set', 'tags'])

    role_id = D(models.IntegerField(primary_key=True),
        "the database ID for the role")
    name = D(models.TextField(unique=True, db_column="role_name"), "name of the role")
    description = D(models.TextField(), 'description')
    created_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "creation date")
    modified_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "modification date")
    created_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='created_by')), 'user who created this resource')
    modified_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='modified_by')), 'user who last modified this resource')

class RbacPermissions(modellib.Collection):
    '''
    A collection of RbacPermissions
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'grants')
    list_fields = ['grant']
    grant = []
    objects = modellib.RbacPermissionsManager()
    view_name = 'RbacPermissions'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.grant]

class RbacPermissionTypes(modellib.Collection):
    '''
    A collection of RbacPermissionTypes
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'permissions')
    list_fields = ['permission']
    grant = []
    objects = modellib.RbacPermissionTypesManager()
    view_name = 'RbacPermissionTypes' 

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.permission]

class RbacPermissionType(modellib.XObjIdModel):
    '''
    A permission type that can be granted to an individual user
    and that can be used to gate access control around a resource
    '''
    #   "permission_type_id" %(PRIMARYKEY)s,
    #        "name" TEXT,
    #        "description" TEXT

    XSL = "fixme.xsl" # TODO
    class Meta:
        db_table = 'rbac_permission_type'

    view_name = 'RbacPermissionType' # TODO

    _xobj = xobj.XObjMetadata(
        tag = 'permission'
    )
    summary_view = [ "name", "description" ]

    permission_id = D(models.AutoField(primary_key=True, db_column='permission_type_id'),
        "the database ID for the permission type")
    name         =  D(models.TextField(), 'internal role name/code')
    description  =  D(models.TextField(), 'role description')

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
        tag = 'grant'
    )
    _xobj_hidden_accessors = set(['tags'])

    grant_id = D(models.AutoField(primary_key=True, db_column='permission_id'),
        "the database ID for the permission")
    role         =  D(modellib.ForeignKey(RbacRole, 
        null=False, db_column='role_id', related_name='grants'), 'rbac_role id')
    queryset     =  D(modellib.ForeignKey('querysets.QuerySet', 
        null=False, db_column='queryset_id', related_name='grants'), 'queryset id')
    permission  = D(models.ForeignKey(RbacPermissionType,
        null=False, db_column='permission_type_id', related_name='+'),
        'permission')
    created_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "creation date")
    modified_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "modification date")
    created_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='created_by')), 'user who created this resource')
    modified_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='modified_by')), 'user who last modified this resource')

class RbacUserRoles(modellib.Collection):
    '''
    A collection of RbacUserRoles
    '''

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'user_roles')
    list_fields = ['user_role']
    role = []
    objects = modellib.RbacUserRolesManager()
    view_name = 'RbacUserRoles' # TODO: add view

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.role]

    def serialize(self, request):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        # TODO: add permission info here
        return xobj_model
 
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
        tag = 'user_role'
    )

    rbac_user_role_id = D(models.AutoField(primary_key=True),
        "the database ID for the rbac_user_role")
    role    =  D(modellib.ForeignKey(RbacRole, null=False), 'rbac_role id')
    user    =  D(modellib.ForeignKey(usersmodels.User, null=False, 
        related_name='user_roles'), 'user id')
    created_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "creation date")
    modified_date = D(APIReadOnly(modellib.DateTimeUtcField(auto_now_add=True)),
        "modification date")
    created_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='created_by')), 'user who created this resource')
    modified_by   =  D(APIReadOnly(modellib.ForeignKey(usersmodels.User, null=True, 
        related_name='+', db_column='modified_by')), 'user who last modified this resource')

    def serialize(self, request):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model.id = self.get_absolute_url(request)
        return xobj_model

    def get_absolute_url(self, request, *args, **kwargs):
        return reverse('RbacUserRole', args=[self.user.pk, self.role.pk])
 
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


