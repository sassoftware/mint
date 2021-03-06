#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.django_rest import timeutils
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.rbac import models 
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.querysets import models as querymodels
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
    def isUserInRole(self, user, role_id):
        role = self._role(role_id)
        mappings = models.RbacUserRole.objects.filter(
            user = user,
            role = role
        ).count()
        return (mappings == 1)

    @exposed
    def getRbacGrantMatrix(self, query_set_id, request):
        # a very UI specific view into grants for a given queryset
        # this will not scale very well but grants per queryset should
        # be quite low.  
        # 
        # this is obviously heinous -- do not repeat
        # principle cause is inverting roles and grants in a way that doesn't
        # jive with the actual model

        qs = querymodels.QuerySet.objects.get(pk=query_set_id)
        dbroles = models.RbacRole.objects.filter(
            is_identity = False
        ) 
        roles_obj = models.RbacRoles()
        roles_obj.role = dbroles

        permissions = dict([ (x, models.RbacPermissionType.objects.get(name=x)) for x in PERMISSION_TYPES ])

        E = modellib.Etree

        # XXX This needs redone. Badly. -- misa
        def mod_serialize(request, *args, **kwargs):
            etreeModel = modellib.XObjIdModel.serialize(roles_obj, request)
            itemCount = E.findBasicChild(etreeModel, 'count')
            etreeModel.attrib.update((x, str(y)) for (x, y) in dict(
                    id = roles_obj.get_absolute_url(request),
                    num_pages = 1,
                    next_page = 0,
                    previous_page = 0,
                    count = len(dbroles),
                    end_index = len(dbroles) - 1,
                    limit = 999999,
                    per_page = len(dbroles),
                    start_index = 0,
            ).items())
            if itemCount is not None:
                etreeModel.attrib.update(count=itemCount)
            for role in etreeModel.iterchildren('role'):
                roleId = role.attrib['id']
                E.Node('matrix_role_id', text=roleId, parent=role)
                actual_role = models.RbacRole.objects.get(
                        pk = E.findBasicChild(role, 'role_id'))
                role.attrib.pop('id')
                for ptype in PERMISSION_TYPES:
                    permission_type = permissions[ptype]
                    ptypename = "%s_permission" % ptype.lower()
                    xperm = permission_type.serialize(request,
                            tag=ptypename)
                    E.Node('matrix_permission_id',
                            parent=xperm,
                            text=xperm.attrib['id'])
                    xperm.attrib.pop('id')
                    grants = models.RbacPermission.objects.filter(
                        queryset = qs,
                        role = actual_role,
                        permission = permission_type
                    )
                    if grants:
                        grant = grants[0]
                        xgrant = grant.serialize(request, tag='grant')
                        for childName in ['modified_by', 'modified_date',
                                'created_by', 'created_date', 'grant_id',
                                'role', 'queryset', 'permissions']:
                            for child in xgrant.findall(childName):
                                xgrant.remove(child)
                        xperm.append(xgrant)
                    role.append(xperm)

                # since this collection is not actually paged, (because
                # it's not relative to the true DB structure, and is a
                # great reason why we shouldn't do this again), avoid
                # XML spam of data we don't need.
                for childName in ['modified_by', 'modified_date',
                        'created_by', 'created_date', 'grants',
                        'users', ]:
                    for child in role.findall(childName):
                        role.remove(child)

            return etreeModel

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
        self.mgr.invalidateQuerySetsByType('role')
        return role    

    @exposed
    def updateRbacRole(self, old_id, role, by_user):
        oldRoleId = role.oldModel.xpath('./role_id/text()')[0]
        old_obj = models.RbacRole.objects.get(pk=oldRoleId)
        role.created_by = old_obj.created_by
        if old_obj.created_date is None:
            raise Exception("ERROR: invalid previous object?")
        role.created_date = old_obj.created_date
        role.modified_date = timeutils.now()
        role.modified_by = by_user
        role.save()
        self.mgr.invalidateQuerySetsByType('role')
        return role

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
        self.mgr.invalidateQuerySetsByType('grant')
        return result

    @exposed
    def updateRbacPermission(self, old_id, permission, by_user):
        oldGrantId = permission.oldModel.xpath('./grant_id/text()')[0]
        old_obj = models.RbacPermission.objects.get(pk=oldGrantId)
        if old_obj.created_date is None:
            raise Exception("ERROR: invalid previous object?")
        permission.created_by    = old_obj.created_by
        permission.created_date  = old_obj.created_date
        permission.modified_date = timeutils.now()
        permission.modified_by   = by_user
        permission.save()
        self.mgr.invalidateQuerySetsByType('grant')
        return permission

    @exposed
    def deleteRbacPermission(self, permission):
        self.mgr.invalidateQuerySetsByType('grant')
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
                # show admin only public querysets + My QS
                # if I happen to have any, though I don't really need them
                results = querymodels.QuerySet.objects.filter(
                    is_public    = True
                ).distinct() | querymodels.QuerySet.objects.filter(
                    personal_for = user
                ).distinct() | querymodels.QuerySet.objects.filter(
                    presentation_type = 'rbac'
                ).distinct()
                querysets_obj = querymodels.FavoriteQuerySets()
                querysets_obj.query_set = results
                return querysets_obj
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

        if not _favorites:
            querysets_obj = querymodels.QuerySets()
        else:
            querysets_obj = querymodels.FavoriteQuerySets()
        querysets_obj.query_set = results
        return querysets_obj

    @exposed
    def favoriteRbacedQuerysets(self, user, querysets, request):
        # return the querysets to show in navigation
        return self.filterRbacQuerysets(user, querysets, request, _favorites=True)

    def __is_admin_like(self, user, request):
        # if the user is an admin, immediately let them by
        if user is None:
            # this occurs when using the RBAC decorator with the access token
            # decorator...higher level rbac code will deny access to unauthenticated
            # users
            return True
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
        granting_sets = querymodels.QuerySet.objects.filter(
            resource_type = resource_type,
            grants__role__rbacuserrole__user = user,
            grants__permission__name = CREATERESOURCE
        )
        personal_sets = [ x for x in granting_sets if x.personal_for == user ]
        # if using "My Query Sets", always create the resource in THAT
        # queryset.  Currently the idea of chosing where to create a resource
        # is not really designed/supported.
        if len(personal_sets) > 0:
            return personal_sets[0]
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
        
        querysets = self.mgr.getQuerySetsForResource(resource)
        if type(querysets) != list:
            querysets = querysets.values_list('pk', flat=True)
        else:
            querysets = [q.pk for q in querysets]

        if len(querysets) == 0:
            return False 

        # write access implies read access.  
        acceptable_permissions = [ permission ]
        if permission == READMEMBERS:
            acceptable_permissions.append(MODMEMBERS)
        if permission == READSET:
            acceptable_permissions.append(MODSETDEF)

        # there is queryset/roles info, so now find the permissions associated
        # with the queryset
        permitted = models.RbacPermission.objects.select_related('rbac_permission_type').filter(
            queryset__pk__in = querysets,
            role__rbacuserrole__user = user,
            permission__name__in = acceptable_permissions
        ).count()

        return (permitted > 0)

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
    def getOrCreateIdentityRole(self, user, byUser):
        # users need to be a in group that contains them
        # similar to Unix user groups in this respect
        # except only create them if we know the user
        # will have "My Querysets"
        role_name = "user:%s" % user.user_name
        role, created = models.RbacRole.objects.get_or_create(
            name = role_name,
            is_identity = True
        )
        if created:
            role.description = "identity role"
            role.created_by = byUser
            role.modified_by = byUser
            role.save()
        user = usermodels.User.objects.get(user_name=user.user_name)
        models.RbacUserRole.objects.get_or_create(
            user=user, 
            role=role
        )
        if created:
            self.mgr.retagQuerySetsByType('role', byUser)
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
    def addIdentityRoleGrants(self, queryset, role, byUser):
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
            perm, created = models.RbacPermission.objects.get_or_create(
                role = role,
                queryset = queryset,
                permission = permission_type
            )
            if created:
                perm.created_by = byUser
                perm.modified_by = byUser
                perm.save()
