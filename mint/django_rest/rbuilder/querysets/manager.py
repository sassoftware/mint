#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction
from datetime import datetime

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.querysets import descriptor
from mint.django_rest.rbuilder.querysets import errors
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.projects import models as projectmodels
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import READMEMBERS, MODMEMBERS

# retag if a new query is made and the results are greater
# than this many seconds old
TAG_REFRESH_INTERVAL=60

# TODO: this code passes around ids way too much and should be passing
# around objects to reduce SQL usage

class QuerySetManager(basemanager.BaseManager):

    # TODO: make this more pluggable/OO so these maps aren't needed
    # there are some inconsistencies between queryset DB and XML tags

    # queryset tag method for each queryset resource type
    tagMethodMap = {
        'system'               : '_tagSystems',
        'user'                 : '_tagUsers',
        'project'              : '_tagProjects',
        'project_branch_stage' : '_tagStages',
        'grant'                : '_tagGrants',
        'role'                 : '_tagRoles',
        'target'               : '_tagTargets',
    }
    # container for each queryset resource type
    resourceCollectionMap = {
        'system'               : 'systems',
        'user'                 : 'users',
        'project'              : 'projects',
        'project_branch_stage' : 'stages',
        'grant'                : 'grants',
        'role'                 : 'roles',
        'target'               : 'targets',
    }
    universeMap = {
        'system'               : 'All Systems',
        'user'                 : 'All Users',
        'project'              : 'All Projects',
        'project_branch_stage' : 'All Project Stages',
        'grant'                : 'All Grants',
        'role'                 : 'All Roles',
        'target'               : 'All Targets',
    }
    # tag finder method per queryset resource type
    tagLookupMap = {
        'system'               : '_lookupTaggedSystems',
        'user'                 : '_lookupTaggedUsers', 
        'project'              : '_lookupTaggedProjects',
        'project_branch_stage' : '_lookupTaggedStages',
        'grant'                : '_lookupTaggedGrants',
        'role'                 : '_lookupTaggedRoles',
        'target'               : '_lookupTaggedTargets',
    }
    # Django tag model for each queryset resource type
    tagModelMap = {
        'system'               : 'system_tag',
        'user'                 : 'user_tag',
        'project_branch_stage' : 'stage_tag',
        'project'              : 'project_tag',
        'target'               : 'target_tag',
    }

    def __init__(self, mgr):
        basemanager.BaseManager.__init__(self, mgr)

        # query tag inclusion objects (see usage below)
        self.__filtered_method = None
        self.__chosen_method = None
        self.__transitive_method = None

    def _querySet(self, query_set_or_id):
        '''
        Get a query set by ID or silently accept an object.
        '''
        if type(query_set_or_id) != models.QuerySet:
            qs = models.QuerySet.objects.select_related(depth=1).get(
                pk=query_set_or_id
            )
            return qs
        else:
            return query_set_or_id

    def _lookupMethod(self, key):
         '''
         Get an inclusion method and try to avoid repeated lookups.
         TODO: use cache module on constant table.
         '''
         storage = "__%s_method" % key
         if getattr(self, storage, None) is None:
             setattr(self, storage, models.InclusionMethod.objects.get(
                 name=key
             ))
         return getattr(self, storage)

    def _filteredMethod(self):
         return self._lookupMethod('filtered')

    def _chosenMethod(self):
         return self._lookupMethod('chosen')

    def _transitiveMethod(self):
         return self._lookupMethod('transitive')

    @exposed
    def getQuerySet(self, querySetId):
        '''look up a query set object'''
        return models.QuerySet.objects.get(pk=querySetId)

    @exposed
    def getQuerySetUniverseSet(self, query_set_id):
        ''' 
        For a given queryset, eg. Systems XYZ, return
        the universe queryset, ex: All Systems
        '''
        qs = self.getQuerySet(query_set_id)
        return models.QuerySet.objects.get(
            name=self.universeMap.get(qs.resource_type)
        )

    @exposed
    def getQuerySets(self):
        '''return all query set objects'''
        querySets = models.QuerySets()
        querySets.query_set = models.QuerySet.objects.all()
        return querySets

    @exposed
    def addQuerySet(self, querySet):
        '''create a new query set'''
        # this is probably a duplicate save because of how xobj
        # is used.
        querySet.save()
        return querySet

    @exposed
    def invalidateQuerySetByName(self, name):
        ''' 
        to be called after adding an object such that a regular request
        to the queryset that does NOT want to bother with queryset invalidation
        jobs can get reasonably results... only use for querysets of small size
        as we have a tag/cache timeout and that should be fine for larger querysets
        '''
        qs = models.QuerySet.objects.get(name=name)
        qs.tagged_date = None
        qs.save()

    @exposed
    def retagQuerySetsByType(self, type):
        '''
        Invalidates all querysets of a given type and then recomputes their data.
        This is needed on addition of some resource types when security context of all
        tags must be applied atomically.   The result is the next request to the queryset
        can operate from tags and attempts to access the resource directly by ID
        will work regardless of RBAC queryset granting access and whether the queryset
        was requested or not -- otherwise application of security rules is latent until
        the next time the queryset members are accessed.  This avoids that.
        '''
        all_sets = models.QuerySet.objects.filter(resource_type=type)
        for qs in all_sets:
            qs.tagged_date = None
            qs.save()
            self.getQuerySetAllResult(qs, use_tags=False)
        

    @exposed
    def updateQuerySet(self, querySet):
        '''edit a query set'''
        if not querySet.can_modify:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)

        # in case the filter terms changed, evaluate queryset and
        # all parents so they can contain accurate membership.  Transitive
        # tags must be applied on each so RBAC will be up to date
        # this will probably be slow, but likely infrequent.

        to_update = querySet.ancestors()
        to_update.append(querySet)
        for qs in to_update:
            qsAllResult = self._getQuerySetAllResult(qs)
            self._tagSingleQuerySetTransitive(qs, qsAllResult)
            self._updateQuerySetTaggedDate(qs)

        querySet.tagged_date = None
        querySet.save()
        return querySet

    @exposed
    def deleteQuerySet(self, querySet):
        '''remove a query set unless it's one that shipped w/ rBuilder'''
        if querySet.can_modify: 
            querySet.delete()
        else:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)

    def _tagMethod(self, querySet):
        '''
        Get the routine to tag a query set
        TODO: make this pluggable and eliminate the map.
        '''
        method_name = self.tagMethodMap[querySet.resource_type]
        return getattr(self, method_name)

    def _searchMethod(self, querySet):
        '''
        Get the tag lookup method for the querySet
        '''
        method_name = self.tagLookupMap[querySet.resource_type]
        return getattr(self, method_name)

    def _tagSingleQuerySetFiltered(self, querySet):
        '''tag a single query set, non recursively'''
        # get the results the filtered items would have matched
        resources = self.filterQuerySet(querySet)
        method = self._tagMethod(querySet)
        method(resources, querySet, self._filteredMethod())

    def _tagSingleQuerySetTransitive(self, querySet, resources):
        method = self._tagMethod(querySet)
        method(resources, querySet, self._transitiveMethod())

    def _tagGeneric(self, resources, queryset, inclusionMethod, tagClass, tagTable, idColumn):
        '''
        store that a given query tag matched the system 
        for caching purposes
        '''
        # TODO: make this pluggable so we don't neeed model 
        # specific methods

        if len(resources) == 0:
            return

        if inclusionMethod.name != 'chosen':
            old_tags = tagClass.objects.filter(
                query_set=queryset,
                inclusion_method=inclusionMethod
            ).delete()

        query = "INSERT INTO %s" % tagTable 
        query = query + " (%s, query_set_id, inclusion_method_id)" % idColumn
        query = query + " VALUES (%s, %s, %s)"
        insertParams = [(resource.pk, queryset.pk, inclusionMethod.pk) for \
            resource in resources]
        cursor = connection.cursor()
        cursor.executemany(query, insertParams)
        transaction.commit_unless_managed()

    def _tagSystems(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.SystemTag,
           tagTable='querysets_systemtag',
           idColumn='system_id')

    def _tagTargets(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.TargetTag,
           tagTable='querysets_targettag',
           idColumn='target_id')

    def _tagUsers(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.UserTag,
           tagTable='querysets_usertag',
           idColumn='user_id')

    def _tagProjects(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.ProjectTag,
           tagTable='querysets_projecttag',
           idColumn='project_id')

    def _tagStages(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.StageTag,
           tagTable='querysets_stagetag',
           idColumn='stage_id')

    def _tagRoles(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.RoleTag,
           tagTable='querysets_roletag',
           idColumn='role_id')

    def _tagGrants(self, resources, tag, inclusionMethod):
        self._tagGeneric(resources, tag, inclusionMethod,
           tagClass=models.PermissionTag,
           tagTable='querysets_permissiontag',
           idColumn='permission_id')

    def _classByName(self, kls):
        '''helper method to load modules'''
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)            
        return m

    def filterQuerySet(self, querySet):
        '''Return resources matching specific filter criteria'''
        model = modellib.type_map[querySet.resource_type]

        # make sure we've implemented tags for these objects
        # should be able to remove this code once Edge-p1 is 
        # complete
 
        resources = None
        retval = None
        if not querySet.filter_entries.all():
            resources = EmptyQuerySet(model)
        else:
            resources = model.objects.select_related().all()
        for filt in querySet.filter_entries.select_related().all():
            resources = modellib.filterDjangoQuerySet(resources, 
                filt.field, filt.operator, filt.value)
        retval = resources.distinct()

        self._updateTransitiveTags(querySet, resources)

        return retval

    def _getResourceCollection(self, querySet, resources, for_user=None):
        '''
        Given a queryset and a list of matched resources, 
        construct and return a collection object.'''
        resourceCollection = modellib.type_map[
            self.resourceCollectionMap[querySet.resource_type]]
        resourceCollection = resourceCollection()
                
        if for_user is None:
            # this happens when relabelling or when the user already has READMEMBER on the set.
            pass
        # FIXME: accomodate for some sqlite/modellib stupidity, let's fix in modellib
        elif for_user.is_admin and str(for_user.is_admin).lower() != 'false': 
            # admin users can see everything in the set
            pass
        else:
            # return all things that would be matched that I already have permissions on
           
            resources = resources.filter(
                tags__query_set__grants__role__rbacuserrole__user = for_user,
                tags__query_set__grants__permission__name__in = [ READMEMBERS, MODMEMBERS ] 
            )
              
            # user hack, should always be able to see yourself in All Users
            if querySet.resource_type == 'user' and querySet.is_public and querySet.name == 'All Users':
                resources = resources | usermodels.User.objects.filter(
                    pk = for_user.pk
                ).distinct()
        
        setattr(resourceCollection, querySet.resource_type, resources)
        resourceCollection._parents = [querySet]
        return resourceCollection

    @exposed
    def getQuerySetAllResult(self, querySetId, use_tags=True, for_user=None):
        '''
        The results for a queryset are typically the 'all' result.  It is
        also possible to be more fine grained and only see matches
        due to filters, chosen (explicitly added) or child (recursive) matches,
        though 'all' includes, well, all of those.
        '''
        # TODO: if the query is still fresh, just go directly to transitive tags
        # and don't descend below at all.
        querySet = self._querySet(querySetId)
        stale = self._areResourceTagsStale(querySet)
        lookupFn = self._searchMethod(querySet)
        if stale or not use_tags:
            # if use_tags is true, attempt to use tags *WHERE* possible in
            # subquerysets, asking each if they are stale or not.  If stale
            # automatically retag resouces that match
            qsAllResult = self._getQuerySetAllResult(querySet)
            # the individual match tag types will NOT be here, so let's tag
            # TRANSITIVELY instead, even though we're not a kid.  (Transitive!=Child)
            self._tagSingleQuerySetTransitive(querySet, qsAllResult)
            self._updateQuerySetTaggedDate(querySet)
        else:
            qsAllResult = self._getQuerySetAllResultFast(querySet, lookupFn)

        resourceCollection = self._getResourceCollection(querySet, qsAllResult, for_user=for_user)
        resourceCollection.view_name = "QuerySetAllResult"
        return resourceCollection

    def _updateQuerySetTaggedDate(self, querySet):
        querySet.tagged_date = datetime.now()
        querySet.save()
 
    def _getQuerySetAllResult(self, querySet):
        '''
        The result for a queryset is the merger of it's filtered, chosen,
        and child query sets
        '''
       
        lookupFn = self._searchMethod(querySet)
        results = self._getQuerySetFilteredResult(querySet).distinct() | \
            self._getQuerySetChosenResult(querySet, lookupFn).distinct() | \
            self._getQuerySetChildResult(querySet).distinct()
        return results

    def _getQuerySetAllResultFast(self, querySet, lookupFn):
        return self._getQuerySetResultFast(querySet, lookupFn, [
            self._filteredMethod().pk,
            self._chosenMethod().pk,
            self._transitiveMethod().pk,
        ])

    def _getQuerySetChildResultFast(self, querySet, lookupFn):
        return self._getQuerySetResultFast(querySet, lookupFn, [
            self._transitiveMethod().pk,
        ])

    def _getQuerySetFilteredResultFast(self, querySet, lookupFn):
        return self._getQuerySetResultFast(querySet, lookupFn, [
            self._filteredMethod().pk,
        ])

    def _getQuerySetChosenResult(self, querySet, lookupFn):
        lookupFn = self._searchMethod(querySet)
        results = self._getQuerySetChosenResultFast(querySet, lookupFn)
        self._updateTransitiveTags(querySet, results)
        return results

    def _getQuerySetChosenResultFast(self, querySet, lookupFn):
        return self._getQuerySetResultFast(querySet, lookupFn, [
            self._chosenMethod().pk,
        ])

    def _getQuerySetResultFast(self, querySet, lookupFn, methods):
        return lookupFn(querySet, methods)

    def _lookupTaggedSystems(self, querySet, methods):
        return inventorymodels.System.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('system_id')
    
    def _lookupTaggedTargets(self, querySet, methods):
        return targetmodels.Target.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('target_id')

    def _lookupTaggedUsers(self, querySet, methods):
        # TODO: eliminate duplication here
        return usermodels.User.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('user_id')

    def _lookupTaggedProjects(self, querySet, methods):
        # TODO: eliminate duplication here
        return projectmodels.Project.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('project_id')

    def _lookupTaggedStages(self, querySet, methods):
        # TODO: eliminate duplication here
        return projectmodels.Stage.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('stage_id')

    def _lookupTaggedRoles(self, querySet, methods):
        # TODO: eliminate duplication here
        return rbacmodels.RbacRole.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('role_id')

    def _lookupTaggedGrants(self, querySet, methods):
        # TODO: eliminate duplication here
        return rbacmodels.RbacPermission.objects.filter(
            tags__query_set=querySet,
            tags__inclusion_method__inclusion_method_id__in=methods
        ).distinct().order_by('grant_id')

    @exposed
    def getQuerySetsForResource(self, resource):
        '''
        If the resource is a querySet, just return it.
        If it's a item in a QuerySet, return the QuerySets
        that match it.  This is key to rBac and requires
        resource tags to have been applied.   
        ''' 

        if type(resource) == models.QuerySet:
            return [ resource ]           
  
        # TODO -- make this more generic / compress
        tags = []
        if type(resource) == usermodels.User:
            tags = models.QuerySet.objects.select_related().filter(
                user_tags__user = resource
            )
        elif type(resource) == projectmodels.Stage:
            tags = models.QuerySet.objects.select_related().filter(
                stage_tags__stage = resource
            )
        elif type(resource) == projectmodels.Project:
            tags = models.QuerySet.objects.select_related().filter(
                project_tags__project = resource
            )
        elif type(resource) == inventorymodels.System:
            tags = models.QuerySet.objects.select_related().filter(
                system_tags__system = resource
            )
        else:
            raise Exception("resource is not searchable by queryset tags")

        return tags

    @exposed
    def getQuerySetChosenResult(self, querySetId, for_user=None):
        '''
        For a given query set, return only the chosen matches, aka resources
        explicitly placed in the queryset
        '''
        querySet = self._querySet(querySetId)
        lookupFn = self._searchMethod(querySet)
        result_data = None
        result_data = self._getQuerySetChosenResultFast(querySet, lookupFn)
        resourceCollection = self._getResourceCollection(querySet, result_data, for_user=for_user)
        resourceCollection.view_name = "QuerySetChosenResult"
        return resourceCollection

    @exposed
    def getQuerySetFilteredResult(self, querySetId, use_tags=True, nocache=False, for_user=None):
        '''
        For a given queryset, return only the portion of it's matches
        that correspond to "smart match" style comparison checks.
        '''
        # NOTE: the speedy version can only be used for 'all' queries.
        # because we only have one type of tagged_date
        querySet = self._querySet(querySetId)
        stale = self._areResourceTagsStale(querySet)
        resultData = self._getQuerySetFilteredResult(querySet)
        resourceCollection = self._getResourceCollection(querySet, resultData, for_user=for_user)
        resourceCollection.view_name = "Systems"
        resourceCollection._parents = []
        resourceCollection.filter_by = querySet.getFilterBy()
        return resourceCollection

    def _areResourceTagsStale(self, querySet):
         '''
         Does the query set need to be retagged?
         '''
         # hack -- restlib has transaction issues with calling Django land
         # so temporarily assume "All Targets" is always invalid.  This really
         # doesn't do any damage (not enough to ever be slow) and can be removed
         # once targets are fully Djangofied
         if querySet.resource_type == 'target':
             return True

         if querySet.tagged_date is None:
             # never been tagged before
             return True
         else:
             then  = querySet.tagged_date.replace(tzinfo=None)
             delta = datetime.now() - then
             return (delta.seconds > TAG_REFRESH_INTERVAL)

    def _getQuerySetFilteredResult(self, querySet):

        # if queryset is stale, retag, then just go down the tag
        # path
        lookupFn = self._searchMethod(querySet)
        if self._areResourceTagsStale(querySet):
            self._tagSingleQuerySetFiltered(querySet)
        return self._getQuerySetFilteredResultFast(querySet, lookupFn)

    def _updateTransitiveTags(self, querySet, results):
        '''
        When we get results back for a query set, we'll
        tag each element, but we also need to populate this up
        the chain for child sets so child set lookup can utilize tags.

        '''
        parents = getattr(querySet, '_parents', [])
        for p in parents:
            tagMethod = self._tagMethod(p)
            tagMethod(results, querySet, self._transitiveMethod())

    @exposed
    def getQuerySetChildResult(self, querySetId, use_tags=True, for_user=None):
        ''' 
        Return the portion of queryset match data that comes from child
        querysets, regardless of whether those child matches are themselves
        'chosen', 'filtered', or 'child' matches.
        '''
        querySet = self._querySet(querySetId)
        stale = self._areResourceTagsStale(querySet)
        lookupFn = self._searchMethod(querySet)
        result_data = self._getQuerySetChildResult(querySet)
        resourceCollection = self._getResourceCollection(querySet, result_data, for_user=for_user)
        resourceCollection.view_name = "QuerySetChildResult"
        return resourceCollection

    def _getQuerySetChildResult(self, querySet):
        '''
        Determine child results...
        TODO: uniqueness detection/removal
        '''
        children = self._getAllChildQuerySets(querySet, results=[])
        model = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(model)
        lookupFn = self._searchMethod(querySet)
        for qs in children:
             # this won't use the tags for the child but will re-run
             # the kids and update transitive tags
             filtered = self._getQuerySetFilteredResult(
                 qs
             ).distinct()
             chosen = self._getQuerySetChosenResult(
                 qs, lookupFn
             ).distinct()
             resources = resources | filtered | chosen
        resources = resources.distinct()
        # this could be slow if we update on every access, and is complicated by the fact
        # that chosen ONLY works through tags.   So only update transitive tags when
        # the tags are already stale
        #if self._areResourceTagsStale(querySet):
        self._updateTransitiveTags(querySet, resources)
        return resources

    def _getAllChildQuerySets(self, querySet, results=None):
        '''
        Return all query sets below this one
        '''
        if results is None:
            results = []
        kids = querySet.children.all()
        results.extend(kids)
        if not hasattr(querySet, '_parents'):
            querySet._parents = []
        for k in kids:
            # annotate this queryset as having it's parent
            # so we can update transitive tags later
            if not hasattr(k, '_parents'):
                k._parents = []
            k._parents.extend(querySet._parents)
            k._parents.append(querySet)
            self._getAllChildQuerySets(k, results)
        return results

    @exposed
    def getQuerySetFilterDescriptor(self, querySetId):
        '''
        Return the smartform that describes how this queryset can
        be configured (or IS configured???)
        '''
        querySet = self._querySet(querySetId)
        model = modellib.type_map[querySet.resource_type]
        filterDescriptor = descriptor.getFilterDescriptor(model, querySet)
        filterDescriptor.pk = querySetId
        return filterDescriptor

    @exposed
    def updateQuerySetChosen(self, querySetId, resource):
        '''
        Add a resource explicitly to the query set match results.
        It must be of the same collection type, querysets are not
        heterogeneous.
        '''

        querySet = self._querySet(querySetId)
        # we do not update the queryset tag date here because it could
        # still be stale with respect to child or filtered results
        tagMethod = self._tagMethod(querySet)
        # if we support tagging this resource type yet
        # then tag it, otherwise, basically no-op.

        t1 = resource._xobj.tag
        t2 = querySet.resource_type
        if t1 != t2:
            raise Exception("attempting to add an object of the wrong type (%s vs %s)" % (t1, t2))

        if tagMethod is not None:
            tagMethod([resource], querySet, self._chosenMethod())
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def addQuerySetChosen(self, querySetId, resources):
        '''
        Add a list of matched systems to a chosen query set result list.
        Deletes all previous matches.
        '''
        # TODO: update transitive items
        querySet = self._querySet(querySetId)
        resources_out = getattr(resources, querySet.resource_type)

        if len(resources_out) > 0:
            t1 = resources_out[0]._xobj.tag
            t2 = querySet.resource_type
            if t1 != t2:
                raise Exception("attempting to add an object of the wrong type (%s vs %s)" % (t1, t2))

        # Delete all previously tagged resources
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        tagModel.objects.filter(
            query_set=querySet,
            inclusion_method=self._chosenMethod(),
        ).delete()

        # Tag new resources
        tagMethod = self._tagMethod(querySet)
        tagMethod(resources_out, querySet, self._chosenMethod())

        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def deleteQuerySetChosen(self, querySetId, resource):
        '''
        Remove a resource from a queryset chosen result.
        '''
        # TODO: if for this querySet I'm marked chosen but NOT filtered
        # set the tagged_date back to NULL so it will be retagged next time
        querySet = self._querySet(querySetId)
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        taggedField = getattr(tagModel, 'tagged_field', querySet.resource_type)
        resourceArg = {taggedField:resource}
        tagModels = tagModel.objects.filter(query_set=querySet,
            inclusion_method=self._chosenMethod(), **resourceArg)
        tagModels.delete()
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def scheduleQuerySetJobAction(self, querySet, job):
        '''
        An action is a bare job submission that is a request to start
        a real job.   (However, querysets don't really have jobs).

        Job coming in will be xobj only,
        containing job_type, descriptor, and descriptor_data.  

        Normally, we'd use that data to schedule a completely different job, 
        which will be more complete.  However, there really aren't any 
        background jobs on a queryset, so things just run immediately
        for now.  (We may want an object agnostic job dispatch engine in
        rbuilder at some point, right now it's inventory specific).
        '''

        # get integer job type even if not a django model
        # (because the job isn't fully formed)
        jt = job.job_type.id
        if str(jt).find("/") != -1:
            jt = int(jt.split("/")[-1])

        # lookup job name for ID in database
        event_type = jobmodels.EventType.objects.get(job_type_id=jt)
        job_name   = event_type.name

        if job_name == jobmodels.EventType.QUERYSET_INVALIDATE:
            querySet.tagged_date = None
            querySet.save()
        else:
            raise Exception("action dispatch not yet supported on job type: %s" % jt)

        return None

