#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.rbac import models 
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.querysets import models as querymodels
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from mint.django_rest.rbuilder.errors import PermissionDenied
from copy import deepcopy

exposed = basemanager.exposed

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
# ability to create a resource -- also specifies what queryset
# to add the resource as a chosen member to
CREATERESOURCE = 'CreateResource'

PERMISSION_TYPES = [ 
    READSET, 
    MODSETDEF, 
    CREATERESOURCE, 
    READMEMBERS, 
    MODMEMBERS,
]

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
    def getRbacGrantMatrix(self, query_set_id, request):
        # a very UI specific view into grants for a given queryset
        # this will not scale very well but grants per queryset should
        # be quite low
        qs = querymodels.QuerySet.objects.get(pk=query_set_id)
        dbroles = models.RbacRole.objects.filter(
            is_identity = False
        ) 
        roles_obj = models.RbacRoles()
        roles_obj.role = dbroles
                    
        permissions = dict([ (x, models.RbacPermissionType.objects.get(name=x)) for x in PERMISSION_TYPES ])

        def mod_serialize(request, *args, **kwargs):
            xobj_model = modellib.XObjIdModel.serialize(roles_obj, request)
            # xobj gets confused with one element entries
            if type(xobj_model.role) != list:
               xobj_model.role = [ xobj_model.role ] 
            xobj_model.id = xobj_model.id.replace("/rbac/roles","/query_sets/%s/grant_matrix" % qs.pk)
            xobj_model.num_pages = 1
            xobj_model.next_page = 0
            xobj_model.previous_page = 0
            xobj_model.count = len(xobj_model.role)
            xobj_model.end_index = len(xobj_model.role) - 1
            xobj_model.limit = 999999 
            xobj_model.per_page = xobj_model.count
            xobj_model.id = roles_obj.get_absolute_url(request)
            xobj_model.start_index = 0
            for role in xobj_model.role:
                actual_role = models.RbacRole.objects.get(pk = role.role_id)
                tweaked_grants = []
                for ptype in PERMISSION_TYPES:
                    xperm = None
                    permission_type = permissions[ptype]
                    ptypename = "%s_permission" % ptype.lower()
                    try:
                        grant = models.RbacPermission.objects.get(
                            queryset = qs,
                            role = actual_role,
                            permission = permission_type
                        )
                        permission_type._xobj = deepcopy(permission_type._xobj)
                        xperm = modellib.XObjIdModel.serialize(permission_type, request)
                        permission_type._xobj.tag = ptypename
                        xperm.set = 'true'
                    except models.RbacPermission.DoesNotExist:
                        # important: should NOT be saved
                        grant = models.RbacPermission(
                            queryset = qs,
                            role = actual_role,
                            permission = permission_type
                        )
                        permission_type._xobj = deepcopy(permission_type._xobj)
                        xperm = modellib.XObjIdModel.serialize(permission_type, request)
                        permission_type._xobj.tag = ptypename
                        xperm.set = 'false'
                    setattr(role, "%s_permission" % ptypename, xperm)

            return xobj_model

        roles_obj.serialize = mod_serialize
        return roles_obj

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
        users = usermodels.Users()
        rbac_user_roles = models.RbacUserRole.objects.all()
        rbac_user_roles = models.RbacUserRole.objects.filter(
            role = role
        ).order_by('user')
        user_results = usermodels.User.objects.filter(
            user_roles__in = rbac_user_roles
        )
        users.user = user_results
        return users
 
    @exposed
    def addRbacPermission(self, permission, by_user):
        try:
            # if already exists, it's ok, do nothing. 
            # want a better way to handle this generically in
            # modellib later, as way to define this in the model
            previous = models.RbacPermission.objects.get(
                role = permission.role,
                queryset = permission.queryset,
                permission = permission.permission
            )
            return previous
        except ObjectDoesNotExist:
            pass

        if permission.queryset.resource_type in [ 'grant', 'role' ]:
            raise PermissionDenied(msg="RBAC configuration rights cannot be delegated")

        # enforce restrictions on who can modify querysets -- this will
        # be upgraded later when we support rbac grant delegation
        if permission.permission.name == MODSETDEF:
            if not permission.queryset.is_static:
               raise PermissionDenied(msg="Modify Set Definition cannot be granted on dynamic querysets")

        if permission.permission.name == CREATERESOURCE:
            # there can be only one CreateResource per resource type
            try:
                previous = models.RbacPermission.objects.get(
                    role = permission.role,
                    queryset__resource_type = permission.queryset.resource_type,
                    permission = permission.permission
                )
                error_args = (permission.queryset.resource_type, previous.role.name, previous.queryset.name)
                raise PermissionDenied(msg="Create Resource for queryset type (%s) can only be granted once per role (%s), already exists for queryset: %s" % error_args)
            except ObjectDoesNotExist:
                pass

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
        return self._orId(value, usermodels.User)

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
    def filterRbacQuerysets(self, user, querysets_obj, request=None, _favorites=False):
        '''
        Modify a querysets collection to contain only the querysets
        the user is allowed to see, leaving the others hidden.
        Applies only to querysets collections themselves, member filtering is
        done in the querysets module.  Querysets are collected in collections
        NOT querysets.
        '''
        orig_results = querysets_obj.query_set
        if request is not None and request._is_admin or user.is_admin:
            if not _favorites:
                # show all querysets
                return querysets_obj
            else:
                # show admin only non-personal querysets
                results = querymodels.QuerySet.objects.filter(
                    personal_for__isnull = True
                )
        results = orig_results.filter(
            is_public = True,
        ).distinct() 
        if not _favorites:
            # always show things I have ReadSet on, as well as sets marked
            # public
            results = results | orig_results.filter(
                grants__role__rbacuserrole__user = user, 
                grants__permission__name__in = [ READSET, MODSETDEF ]
            ).distinct()
        else:
            # show public sets but do not show things I have permissions
            # on unless that is marked personal_for me (My Querysets)
            #
            # if I can read Foo, it will appear in the set browser but
            # not in 'favorites' ... to be extended later when things
            # are actually bookmarkable
            results = results | orig_results.filter(
                grants__role__rbacuserrole__user = user,
                grants__permission__name__in = [ READSET, MODSETDEF ],
                personal_for = user
            ).distinct()

        querysets_obj = querymodels.QuerySets()
        querysets_obj.query_set = results
        return querysets_obj

    @exposed
    def favoriteRbacedQuerysets(self, user, querysets, request):
        # return the querysets to show in navigation
        return self.filterRbacQuerysets(user, querysets, request, _favorites=True)

    def __is_admin_like(self, user, request):
        # if the user is an admin, immediately let them by
        if request is not None and request._is_admin:
            return True
        if user.is_admin:
            return True
        return False

    @exposed
    def resourceHomeQuerySet(self, user, resource_type):
        '''
        When creating a resource, what querysets should I auto-add the resource to
        as a chosen member?  The resource_type is a queryset resource
        type, not a model, database,  or tag name.
        '''
        #tags__query_set__grants__role__rbacuserrole__user = for_user,
        #tags__query_set__grants__permission__name__in = [ READMEMBERS, MODMEMBERS ]
        granting_sets = querymodels.QuerySet.objects.filter(
            resource_type = resource_type,
            grants__role__rbacuserrole__user = user,
            grants__permission__name = CREATERESOURCE
        )
        if len(granting_sets) == 0:
            return None
        # the grant code shouldn't allow x>1 but we shouldn't choke either
        # just add it to the first
        return granting_sets[0]
 
    @exposed
    def userHasRbacCreatePermission(self, user, resource_type, request=None):
        '''
        Checks to see if a user can create a new resource of a given type.
        Some resources may have CREATERESOURCE grants
        (because they act as pointers to chosen querysets) and still further
        restrict access... thus CREATERESOURCE may be used by object types
        that do NOT call this function.
        '''  
        if self.__is_admin_like(user, request):
            return True
        home = self.resourceHomeQuerySet(user, resource_type)
        if home is None:
            return False
        return True

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

        if permission == CREATERESOURCE:
            raise Exception("Internal error: use userHasRbacCreatePermission instead")

        if self.__is_admin_like(user, request):
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
     
    ##################################################################
    # Support for the "My Querysets" feature of allowing
    # users to automatically have access to what they create and
    # having a createable place to put resources set up with
    # the user account

    @exposed
    def getOrCreateIdentityRole(self, user):
        # users need to be a in group that contains them
        # similar to Unix user groups in this respect
        # except only create them if we know the user
        # will have "My Querysets"
        if not user.can_create:
            raise Exception('internal error: user creation rights not set')
        role_name = "user:%s" % user.user_name
        role = models.RbacRole.objects.get_or_create(
            name = role_name,
            is_identity = True
        )[0]
        role.description = "identity role for user"
        role.save()
        user = usermodels.User.objects.get(user_name=user.user_name)
        models.RbacUserRole.objects.get_or_create(
            user=user, 
            role=role
        )
        return role

    @exposed
    def removeIdentityRole(self, user):
        # user can no longer create anything, so remove
        # the role, and by sql cascade effects, delete
        # the grants. It is ok if it's already missing
        role_name = "user:%s" % user.user_name
        roles = models.RbacRole.objects.filter(
            name = role_name,
            is_identity = True
        )
        for role in roles:
            role.delete()
        # grants will be deleted by cascade

    @exposed
    def addIdentityRoleGrants(self, queryset, role):
        # for a my queryset, add permissions so that it's fully usable --
        # a user can create and can see/edit what they own
        if queryset.personal_for is None:
            raise Exception("internal error: not a 'My' Queryset")
        if role.is_identity is None:
            raise Exception("internal error: not an identity role")
        createresource = models.RbacPermissionType.objects.get(name=CREATERESOURCE)
        modmembers = models.RbacPermissionType.objects.get(name=MODMEMBERS)
        readset = models.RbacPermissionType.objects.get(name=READSET)
        for permission_type in [ createresource, modmembers, readset ]: 
            models.RbacPermission.objects.get_or_create(
                role = role,
                queryset = queryset,
                permission = permission_type
            )[0]
  

