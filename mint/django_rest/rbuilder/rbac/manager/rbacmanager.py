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

# allowable permission types
# *member =
#    read and write to members of a queryset
# *queryset = 
#    ability to see queryset at all or modify it

RMEMBER = 'rmember'  
WMEMBER = 'wmember'  
RQUERYSET = 'rqueryset' 
WQUERYSET = 'wqueryset' 

class RbacManager(basemanager.BaseManager):

    def _getThings(self, modelClass, containedClass, collection_field, order_by=None):
        '''generic collection loader'''
        things = modelClass()
        all = containedClass.objects.all()
        if order_by:
            all = all.order_by(*order_by)
        setattr(things, collection_field, containedClass.objects.all())
        return things

    def _addThing(self, modelClass, obj):
        '''generic creation method'''
        # it's already saved, crazy @requires stuff.
        #obj.save()
        return obj

    def _updateThing(self, modelClass, old_id, obj):
        '''generic update method'''
        # it's already saved, via crazy @requires stuff, but we'll save again
        # to make sure the date is correct.
        obj.modified_date = datetime.now()
        obj.save()
        return obj

    def _updatePrimaryKey(self, modelClass, old_id, obj, field, table):
        '''update a table and change the primary key'''
        oldObj = modelClass.objects.get(pk=old_id)
        if not oldObj:
            return None
        # django doesn't like primary key updates
        # so this is somewhat low level
        newValue = getattr(obj, field)
        oldValue = getattr(oldObj, field)
        cursor = connection.cursor()
        pattern = 'UPDATE ' + table + ' SET ' + field + '=%s WHERE ' + field + '=%s' 
        cursor.execute(pattern, [newValue, oldValue])
        transaction.commit_unless_managed()
        obj = modelClass.objects.get(pk=newValue)
        obj.modified_date = datetime.now()
        obj.save()
        return obj


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
            models.RbacRole, 'role', order_by=['role_id'])

    @exposed
    def getRbacRole(self, role):
        return self._role(role)
   
    @exposed
    def addRbacRole(self, role):
        return self._addThing(models.RbacRole, role)

    @exposed
    def updateRbacRole(self, old_id, role):
        return self._updatePrimaryKey(models.RbacRole, old_id, 
            role, 'role_id', 'rbac_role')

    @exposed
    def deleteRbacRole(self, role):
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
            order_by=['queryset_id', 'role_id', 'action']
        )

    @exposed
    def getRbacPermission(self, permission):
        return self._permission(permission)

    @exposed
    def addRbacPermission(self, permission):
        permission.save()
        return permission

    @exposed
    def updateRbacPermission(self, old_id, permission):
        permission.modified_date = datetime.now()
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
        allowed_permissions = [ 'rmember', 'wmember', 'rqueryset', 'wqueryset' ]
        perms = models.RbacPermission.objects.select_related().filter(
           role__in = my_roles,
           permission__in    = allowed_permissions
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
        user_is_admin = str(getattr(user, 'is_admin', 'false'))
        if user_is_admin == 'true':
            return True
        querysets = self.mgr.getQuerySetsForResource(resource)
        user = self._user(user)
        if len(querysets) == 0:
            return False 
        role_maps = models.RbacUserRole.objects.filter(user=user)
        role_ids = [ x.role.pk for x in role_maps ]

        # if the user has no roles on this queryset, fail immediately
        if len(role_ids) == 0:
            return False

        # write access implies read access.  
        acceptable_permitted_permissions = [ permission ]
        if permission == RMEMBER:
            acceptable_permitted_permissions.extend([WMEMBER])
        if permission == RQUERYSET:
            acceptable_permitted_permissions.extend([WQUERYSET])

        # there is queryset/roles info, so now find the permissions associated
        # with the queryset
        resource_permissions = models.RbacPermission.objects.filter(
            queryset__in = querysets
        ).extra(
            where=['role_id=%s'], params=role_ids
        )

        # permit user if they have one of the permissions we want...
        # Django seems to displike duplicate extra queries, so...
        for x in resource_permissions:
             if x.permission in acceptable_permitted_permissions:
                 return True
        return False

    @exposed
    def addRbacUserRole(self, user_id, role_id):
        '''Results in the user having this rbac role'''
        user = self._user(user_id)
        role = self._role(role_id)
        try:
            mapping = models.RbacUserRole.objects.get(user=user, role=role)  # pyflakes=ignore
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
    

