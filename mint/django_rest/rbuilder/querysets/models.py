#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys
from django.db import models

from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import errors
from mint.django_rest.rbuilder.jobs import models as jobmodels

from xobj import xobj

APIReadOnly = modellib.APIReadOnly
XObjHidden = modellib.XObjHidden

OPERATOR_CHOICES = [(k, v) for k, v in modellib.filterTermMap.items()]

class Universe(modellib.XObjIdModel):
    '''Reference to the absolute all of a Given Type parent of any queryset'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = "universe")
    view_name = "QuerySetUniverseResult"

class AllMembers(modellib.XObjIdModel):
    '''Query set results matched regardless of match type (below)'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "all_members")
    view_name = "QuerySetAllResult"

class ChosenMembers(modellib.XObjIdModel):
    '''Query set results based on resources explicitly added to the QS'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "chosen_members")
    view_name = "QuerySetChosenResult"

class FilteredMembers(modellib.XObjIdModel):
    '''Query set results based on given match criteria'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "filtered_members")
    view_name = "QuerySetFilteredResult"

class ChildMembers(modellib.XObjIdModel):
    '''Query set results that are selected because of a child query set'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "child_members")
    view_name = "QuerySetChildResult"

class GrantMatrix(modellib.XObjIdModel):
    '''Permissions on queryset arranged in a UI-friendly way'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "grant_matrix")
    view_name = "QuerySetGrantMatrix"

class QuerySets(modellib.Collection):
    '''A list of all query sets in the rBuilder'''
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "query_sets")
    list_fields = ["query_set"]
    query_set = []

class FilterDescriptor(modellib.XObjIdModel):

    # this is a stub for serialization of a URL only, 
    # see the other FilterDescriptor in descriptors.py 

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "filter_descriptor")

    id = models.AutoField(primary_key=True)
    view_name = "QuerySetFilterDescriptor"

class CollectionId(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='collection')
                

class QuerySet(modellib.XObjIdModel):
    '''An individual queryset, ex: "All Systems"'''

    objects = modellib.SaveableManyToManyManager()
    _xobj = xobj.XObjMetadata(
                tag = "query_set")
    _xobj_explicit_accessors = set([])
    _m2m_safe_to_create = [ 'filter_entries' ]

    query_set_id = D(models.AutoField(primary_key=True),
        "The database id for the query set")
    name = D(models.TextField(unique=True),
        "Query set name")
    description = D(models.TextField(null=True),
        "Query set description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "Date the query set was created")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "Date the query set was modified")
    tagged_date = D(modellib.DateTimeUtcField(auto_now_add=False),
        "Date the query set was last tagged")
    children = D(models.ManyToManyField("self", symmetrical=False),
        "Query sets that are children of this query set")
    filter_entries = D(models.ManyToManyField("FilterEntry"),
        "Defined filter entries for this query set")
    resource_type = D(models.TextField(),
        "Name of the resource this query set operates on")
    presentation_type = D(models.TextField(),
        "A classification for client to use when displaying the objects.  For example, stages can be on projects, branches, platforms, etc.")
    can_modify = D(models.BooleanField(default=True),
        "Whether this query set can be deleted through the API.")
    actions = D(modellib.SyntheticField(jobmodels.Actions), 'Available actions on this query set')
    # public querysets are querysets like "All Systems" and do not require rbac ReadSet permissions
    # to be visible, but will be empty unless ReadMember(ship) is conveyed on some of their contents.
    is_public = APIReadOnly(models.BooleanField(default=False))
    is_static = APIReadOnly(models.BooleanField(default=False))
    created_by = APIReadOnly(modellib.ForeignKey('users.User', related_name='+', null=True, db_column='created_by'))
    modified_by = APIReadOnly(modellib.ForeignKey('users.User', related_name='+', null=True, db_column='modified_by'))
    personal_for = APIReadOnly(modellib.ForeignKey('users.User', related_name='+', db_column='personal_for', null=True))

    load_fields = [name]

    # the name of the most important key (default) in the filter descriptor
    _queryset_search_key_map = {
        'system'               : 'System name' ,
        'user'                 : 'User name'   ,
        'project'              : 'Project name',
        'project_branch_stage' : 'Project name',
        'grant'                : 'Grant name'  ,
        'role'                 : 'Role name'   ,
        'target'               : 'Target name' , 
    }

    def searchKey(self):
        '''The name of the most important item in the filter descriptor'''
        return self._queryset_search_key_map[self.resource_type]

    def computeSyntheticFields(self, sender, **kwargs):
        ''' Compute non-database fields.'''
        self._computeActions()

    def _computeActions(self):
        '''What actions are available on the system?'''

        self.actions = jobmodels.Actions()
        self.actions.action = []
         
        if self.tagged_date is not None:
            # refreshes the queryset next time it is accessed
            # regardless of resource tag (cache) age
            invalidate = jobmodels.EventType.makeAction(
                jobmodels.EventType.QUERYSET_INVALIDATE
            )
            self.actions.action.append(invalidate)

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)

        am = AllMembers()
        am._parents = [self]
        xobjModel.all_members = am.serialize(request)
        cm = ChosenMembers()
        cm._parents = [self]
        xobjModel.chosen_members = cm.serialize(request)
        fm = FilteredMembers()
        fm._parents = [self]
        xobjModel.filtered_members = fm.serialize(request)
        childM = ChildMembers()
        childM._parents = [self]
        xobjModel.child_members = childM.serialize(request)
        universe = Universe()
        universe._parents = [self]
        xobjModel.universe = universe.serialize(request)
        grant_matrix = GrantMatrix()
        grant_matrix._parents = [self]
        xobjModel.grant_matrix = grant_matrix.serialize(request)

        fd = FilterDescriptor(id=self.query_set_id)
        xobjModel.filter_descriptor = fd.serialize(request)

        xobjModel.is_top_level = self.isTopLevel()

        return xobjModel

    def getFilterBy(self):
        filterBy = []
        for filterEntry in self.filter_entries.all():
            filterStr = '[%s,%s,%s]' % (filterEntry.field, filterEntry.operator,
                filterEntry.value)
            filterBy.append(filterStr)
        return ','.join(filterBy)

    def isTopLevel(self):
        parents = self.__class__.children.through.objects.filter(to_queryset=self)
        if parents:
            return False
        else: 
            return True

    def save(self, *args, **kwargs):
        """
        Validate that the query set does not have any circular relationships in
        it's children before saving it.  E.g., a query set can not be a child
        of one of it's children.
        """
        # If we don't have a query_set_id (pk), then we've never even been saved
        # and Django prevents us from using the Many to Many manager on
        # children.  Skip validating children in this case.
        if self.query_set_id is not None:
            self._validateChildren()
        return modellib.XObjIdModel.save(self, *args, **kwargs)

    def _validateChildren(self, validatedChildren=[]):
        """
        Validate the query set does not have any circular relationships in
        it's children.
        """
        # Save the current query set as validated
        validatedChildren.append(self)

        children = self.children.all()

        # A query set can not be in it's own children
        if self in children:
            raise errors.InvalidChildQuerySet(parent=self.name,
                child=self.name)

        # A query set can not be a child of any of it's children
        for childQuerySet in children:
            grandChildren = childQuerySet.children.all()
            if self in grandChildren:
                raise errors.InvalidChildQuerySet(parent=childQuerySet.name,
                    child=self.name)

            # Recurse, validating each child
            childQuerySet._validateChildren(validatedChildren)

    def parents(self):
        '''querysets that directly include this queryset'''
        results = QuerySet.objects.filter(
            children = self
        )
        return results
 
    def ancestors(self):
        '''querysets that directly or indirectly include this queryset'''
        return self._ancestors([], 0) 

    def _ancestors(self, results, depth):
        self._depth = depth
        my_parents = self.parents()
        results.extend(my_parents)
        for parent in my_parents:
            results.extend(parent._ancestors(results, depth-1))
        return results

class FilterEntry(modellib.XObjIdModel):

    class Meta:
        unique_together = ('field', 'operator', 'value')

    _xobj = xobj.XObjMetadata(
                tag = "filter_entry")

    filter_entry_id = models.AutoField(primary_key=True)
    field = D(models.TextField(),
        "Field this filter operates on.  '.' in field names indicate resource relationships")
    operator = D(models.TextField(choices=OPERATOR_CHOICES),
        "Operator for this filter")
    value = D(models.TextField(null=True),
        "Value for this filter")

    load_fields = [field, operator, value]

class InclusionMethod(modellib.XObjIdModel):
    '''
    Explains how the system came to be in the query set.  This is probably
    not needed and could be removed for a performance boost.  [MPD]
    '''
    _xobj = xobj.XObjMetadata(
                tag = 'inclusion_method')
    _xobj_explicit_accessors = set([])

    METHOD_CHOICES = [
        ('chosen', 'Chosen'),
        ('filtered', 'Filtered'),
    ]

    inclusion_method_id = models.AutoField(primary_key=True)
    name = models.TextField(choices=METHOD_CHOICES)

    load_fields = [name]

class SystemTag(modellib.XObjIdModel):
    '''
    Indicates what systems were matched by a query set
    '''

    class Meta:
        unique_together = (("system", "query_set", "inclusion_method"),)

    _xobj = xobj.XObjMetadata(
                tag = 'system_tag')

    system_tag_id = models.AutoField(primary_key=True)
    system = XObjHidden(modellib.ForeignKey('inventory.System',
        related_name="tags"))
    query_set = XObjHidden(modellib.ForeignKey(QuerySet, related_name="system_tags",
        text_field="name"))
    inclusion_method = XObjHidden(modellib.ForeignKey(InclusionMethod,
        related_name="system_tags"))

    load_fields = [system, query_set, inclusion_method]

    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.system, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel

class TargetTag(modellib.XObjIdModel):
    '''
    Indicates what targets were matched by a query set
    '''

    class Meta:
        unique_together = (("target", "query_set", "inclusion_method"),)

    _xobj = xobj.XObjMetadata(
                tag = 'target_tag')

    target_tag_id = models.AutoField(primary_key=True)
    target = XObjHidden(modellib.ForeignKey('targets.Target',
        related_name="tags"))
    query_set = XObjHidden(modellib.ForeignKey(QuerySet, related_name="target_tags",
        text_field="name"))
    inclusion_method = XObjHidden(modellib.ForeignKey(InclusionMethod,
        related_name="target_tags"))

    load_fields = [target, query_set, inclusion_method]

    # TODO: believe these aren't really serialized anywhere anymore, ok
    # to strike URL/serialize methods for all of these?

    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.target, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel

# TODO: reduce duplication here, add a common tag base class or factory?
class RoleTag(modellib.XObjIdModel):
    '''
    Indicates what roles were matched by a query set
    '''

    class Meta:
        unique_together = (("role", "query_set", "inclusion_method"),)

    _xobj = xobj.XObjMetadata(
                tag = 'role_tag')

    role_tag_id = models.AutoField(primary_key=True)
    role = XObjHidden(modellib.ForeignKey(rbacmodels.RbacRole,
        related_name="tags"))
    query_set = XObjHidden(modellib.ForeignKey(QuerySet, related_name="role_tags",
        text_field="name"))
    inclusion_method = XObjHidden(modellib.ForeignKey(InclusionMethod,
        related_name="role_tags"))

    load_fields = [role, query_set, inclusion_method]

    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.system, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel         
         
# TODO: reduce duplication here, add a common tag base class or factory?
class PermissionTag(modellib.XObjIdModel):
    '''
    Indicates what roles were matched by a query set
    '''

    class Meta:
        unique_together = (("permission", "query_set", "inclusion_method"),)

    _xobj = xobj.XObjMetadata(
                tag = 'grant_tag')

    # NOTE: we call permissions "GRANTS" in the XML api, though these
    # tags will largely be hidden here, and we can call fields by their
    # internal names, knowing this data need not be surfaced.
    permission_tag_id = models.AutoField(primary_key=True)
    permission = XObjHidden(modellib.ForeignKey(rbacmodels.RbacPermission,
        related_name="tags"))
    query_set = XObjHidden(modellib.ForeignKey(QuerySet, related_name="permission_tags",
        text_field="name"))
    inclusion_method = XObjHidden(modellib.ForeignKey(InclusionMethod,
        related_name="permission_tags"))

    load_fields = [permission, query_set, inclusion_method]

    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.system, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)

    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel

class UserTag(modellib.XObjIdModel):
    '''Indicates what users were matched by a query set'''

    class Meta:
        unique_together = (('user', 'query_set', 'inclusion_method'),)

    _xobj = xobj.XObjMetadata(tag='user_tag')
    
    user_tag_id = models.AutoField(primary_key=True)
    user = modellib.ForeignKey(usersmodels.User, related_name='tags')
    query_set = XObjHidden(
        modellib.ForeignKey(QuerySet, related_name='user_tags', text_field='name')
    )
    # TODO -- also don't share inclusion_method
    inclusion_method = XObjHidden(
        modellib.SerializedForeignKey(InclusionMethod, related_name='user_tags')
    )    

    load_fields = [user, query_set, inclusion_method]
    
    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.user, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)
        
    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel
    
class ProjectTag(modellib.XObjIdModel):
    '''Indicates what projects were matched by a query set'''

    class Meta:
        unique_together = (('project', 'query_set', 'inclusion_method'),)
    
    _xobj = xobj.XObjMetadata(tag='project_tag')
    
    project_tag_id = models.AutoField(primary_key=True)
    project = modellib.ForeignKey(projectsmodels.Project, related_name='tags')
    query_set = XObjHidden(
        modellib.ForeignKey(QuerySet, related_name='project_tags', text_field='name')
    )
    # TODO -- also don't share inclusion_method
    inclusion_method = XObjHidden(
       modellib.SerializedForeignKey(InclusionMethod, related_name='project_tags')
    )    

    load_fields = [project, query_set, inclusion_method]
    
    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.project, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)
        
    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel
    
class StageTag(modellib.XObjIdModel):
    '''Indicates which stages were matched by a query set'''
 
    class Meta:
        unique_together = (('stage', 'query_set', 'inclusion_method'),)
    
    _xobj = xobj.XObjMetadata(tag='stage_tag')
    
    stage_tag_id = models.AutoField(primary_key=True)
    stage = modellib.ForeignKey(projectsmodels.Stage, related_name='tags')
    query_set = XObjHidden(
        modellib.ForeignKey(QuerySet, related_name='stage_tags', text_field='name')
    )
    # TODO -- also don't share inclusion_method
    inclusion_method = XObjHidden(
        modellib.SerializedForeignKey(InclusionMethod, related_name='stage_tags')
    )    

    load_fields = [stage, query_set, inclusion_method]
    # Queryset resource_type is 'project_branch_stage' but the field here is
    # just called 'stage', so a special override is needed.
    tagged_field = 'stage'
    
    def get_absolute_url(self, *args, **kwargs):
        self._parents = [self.stage, self]
        return modellib.XObjIdModel.get_absolute_url(self, *args, **kwargs)
        
    def serialize(self, request=None, values=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        querySetHref = self.query_set.get_absolute_url(request)
        xobjModel.query_set = modellib.XObjHrefModel(querySetHref)
        return xobjModel

# register xobj metadata
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
