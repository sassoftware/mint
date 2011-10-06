#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint.django_rest.rbuilder.rbac import models 
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.querysets import models as querymodels
from django.db import connection, transaction
from datetime import datetime

log = logging.getLogger(__name__)
exposed = basemanager.exposed

# resource types that we can manipulate RBAC context on:
RESOURCE_TYPE_SYSTEM   = 'system'
RESOURCE_TYPE_PLATFORM = 'platform'
RESOURCE_TYPE_IMAGE    = 'image'

# the following constants are used to lookup RbacPermissionTypes
# in the database and are not to be used directly.
#
# ability to view items inside a queryset
READMEMBERS = 'ReadMembers'  
# ability to edit items in a queryset
MODMEMBERS = 'ModMembers'  
# ability to see a queryset, but not execute it
READSET = 'ReadSet' 
# ability to modify/delete a query set
MODSETDEF = 'ModSetDef' 

class RbacManager(basemanager.BaseManager):

    def _getThings(self, modelClass, containedClass, collection_field, order_by=None):
        '''generic collection loader'''
        things = modelClass()
        all = containedClass.objects
        if order_by:
            all = all.order_by(*order_by)
        all = all.all()
        setattr(things, collection_field, all)
        return things

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
    # RBAC PERMISSION TYPE METHODS
    # read only!
    
    def _permission_type(self, value):
       return self._orId(value, models.RbacPermissionType)

    @exposed
    def getRbacPermissionTypes(self):
        return self._getThings(models.RbacPermissionTypes,
            models.RbacPermissionType, 'permission', order_by=['permission_id'])

    @exposed
    def getRbacPermissionType(self, permission_type):
        return self._permission_type(permission_type)

    #########################################################
    # RBAC ROLE METHODS
    
    def _role(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacRole)

    @exposed
    def getRbacRoles(self):
        return self._getThings(models.RbacRoles, 
            models.RbacRole, 'role', order_by=['role_id'])

    @exposed
    def getRbacRole(self, role):
        return self._role(role)
   
    @exposed
    def addRbacRole(self, role, by_user):
        role.created_by = by_user
        role.modified_by = by_user
        role.save()
        role = models.RbacRole.objects.get(name=role.name)
        self.mgr.invalidateQuerySetByName('All Roles')
        return role

    @exposed
    def updateRbacRole(self, old_id, role, by_user):
        old_obj = models.RbacRole.objects.get(pk=role.oldModel.role_id)
        role.created_by = old_obj.created_by
        if old_obj.created_date is None:
            raise Exception("ERROR: invalid previous object?")
        role.created_date = old_obj.created_date
        role.modified_date = datetime.now()
        role.modified_by = by_user
        role.save()
        self.mgr.invalidateQuerySetByName('All Roles')
        return role

    @exposed
    def deleteRbacRole(self, role):
        self.mgr.invalidateQuerySetByName('All Roles')
        return self._deleteThing(models.RbacRole, self._role(role)) 

    #########################################################
    # RBAC PERMISSION METHODS
    # these do NOT override the manager so are coded differently than above
    
    def _permission(self, value):
        '''cast input as a role'''
        return self._orId(value, models.RbacPermission)

    @exposed
    def getRbacPermissions(self):
        return self._getThings(models.RbacPermissions,
            models.RbacPermission, 'grant',  
            order_by=['queryset', 'role', 'permission']
        )

    @exposed
    def getRbacPermission(self, permission):
        return self._permission(permission)

    @exposed
    def getRbacPermissionsForRole(self, role):
        role = self._role(role)
        grants = models.RbacPermissions()
        all = models.RbacPermission.objects.filter(
            role = role
        ).order_by('queryset', 'role', 'permission')
        grants.grant = all
        return grants

    @exposed
    def getRbacUsersForRole(self, role):
        role = self._role(role)
        users = usersmodels.Users()
        rbac_user_roles = models.RbacUserRole.objects.all()
        rbac_user_roles = models.RbacUserRole.objects.filter(
            role = role
        ).order_by('user')
        user_results = usersmodels.User.objects.filter(
            user_roles__in = rbac_user_roles
        )
        users.user = user_results
        return users
 
    @exposed
    def addRbacPermission(self, permission, by_user):
        permission.created_by  = by_user
        permission.modified_by = by_user
        permission.save()
        result = models.RbacPermission.objects.get(
            role = permission.role,
            queryset = permission.queryset,
            permission = permission.permission
        )
        self.mgr.invalidateQuerySetByName('All Grants')
        return result

    @exposed
    def updateRbacPermission(self, old_id, permission, by_user):
        # BOOKMARK
        old_obj = models.RbacPermission.objects.get(pk=permission.oldModel.grant_id)
        if old_obj.created_date is None:
            raise Exception("ERROR: invalid previous object?")
        permission.created_by    = old_obj.created_by
        permission.created_date  = old_obj.created_date
        permission.modified_date = datetime.now()
        permission.modified_by   = by_user
        permission.save()
        self.mgr.invalidateQuerySetByName('All Grants')
        return permission

    @exposed
    def deleteRbacPermission(self, permission):
        self.mgr.invalidateQuerySetByName('All Grants')
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
        user = self._user(user_id)
        mapping = models.RbacUserRole.objects.filter(user=user).order_by(
            'user__user_name', 'role__role_id',
        )
        collection = models.RbacRoles()
        collection.role = [ x.role for x in mapping ]
        return collection 

    @exposed
    def getRbacUserRole(self, user_id, role_id):
        '''See if this user has a certain role.'''
        user = self._user(user_id)
        role = self._role(role_id)
        mapping = models.RbacUserRole.objects.get(user=user, role=role)
        return mapping.role

    def _queryset(self, queryset_or_id):
        if type(queryset_or_id) == int:
            return querymodels.objects.get(pk=queryset_or_id)
        return queryset_or_id

    @exposed
    def filterRbacQuerysets(self, user, querysets_obj, request=None):
        '''
        Modify a querysets collection to contain only the querysets
        the user is allowed to see, leaving the others hidden.
        '''
        if request is not None and request._is_admin:
            return querysets_obj
        if getattr(user, '_is_admin', False):
            return querysets_obj
        querysets = querysets_obj.query_set

        roles = models.RbacUserRole.objects.select_related().filter(
            user = user
        )
        my_roles = [ x.role for x in roles ] 
        perms = models.RbacPermission.objects.select_related().filter(
           role__in = my_roles,
        )

        results = []
        for p in perms:
            if p.queryset not in results:
                results.append(p.queryset)
        querysets_obj.query_set = results
        return querysets_obj

    @exposed
    def userHasRbacPermission(self, user, resource, permission, 
        request=None):
        '''
        Can User X Do Action Y On Resource?

        This function is not surfaced directly via REST but is the core
        of how we implement RBAC protection on resources.  Permissions
        are simple at the moment, but some imply others.   Query set
        tags must exist to find the queryset relationships.

        Whether the user is anonymous or admin can come in through multiple routes,
        depending on usage.  
        '''


        # if the user is an admin, immediately let them by
        if request is not None and request._is_admin:
            return True
        # some of the tests use this path, but the main app doesn't
        # TODO: modify tests so they act like everything else
        if getattr(user, '_is_admin', False):
            return True
        # this will trigger on DB users even if request is not passed in
        # so we could probably eliminate the request check
        # TODO: make it happen
        if user.getIsAdmin():
            return True
        
        # input permission is a permission name, upconvert to PermissionType object
        permission = models.RbacPermissionType.objects.get(name=permission)

        querysets = self.mgr.getQuerySetsForResource(resource)
        user = self._user(user)
        if len(querysets) == 0:
            return False 
        role_maps = models.RbacUserRole.objects.filter(user=user)
        role_ids = [ x.role.pk for x in role_maps ]
        all_roles = [ x.role for x in role_maps ]

        # if the user has no roles on this queryset, fail immediately
        if len(role_ids) == 0:
            return False

        # write access implies read access.  
        acceptable_permitted_permissions = [ permission ]
        if permission.name == READMEMBERS:
            modmembers = models.RbacPermissionType.objects.get(name=MODMEMBERS)
            acceptable_permitted_permissions.append(modmembers)
        if permission.name == READSET:
            modsetdef = models.RbacPermissionType.objects.get(name=MODSETDEF)
            acceptable_permitted_permissions.append(modsetdef)
        acceptable_permitted_permissions = [ x.name for x in acceptable_permitted_permissions ]

        # there is queryset/roles info, so now find the permissions associated
        # with the queryset
        resource_permissions = models.RbacPermission.objects.select_related('rbac_permission_type').filter(
            queryset__in = querysets,
            role__in = all_roles
        )

        # permit user if they have one of the permissions we want...
        # Django seems to displike duplicate extra queries, so...
        for x in resource_permissions: # aka grants
             if x.permission.name in acceptable_permitted_permissions:
                 return True
        return False

    @exposed
    def addRbacUserRole(self, user_id, role_id, by_user):
        '''Results in the user having this rbac role'''
        user = self._user(user_id)
        role = self._role(role_id)
        try:
            mapping = models.RbacUserRole.objects.get(user=user, role=role)  # pyflakes=ignore
            # mapping already exists, nothing to do
        except models.RbacUserRole.DoesNotExist:
            # no role assignment found, create it
            models.RbacUserRole(
                user=user, 
                role=role, 
                created_by=by_user, 
                modified_by=by_user
            ).save()
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
    

