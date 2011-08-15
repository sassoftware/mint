#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.core.exceptions import ObjectDoesNotExist

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.querysets import descriptor
from mint.django_rest.rbuilder.querysets import errors
from mint.django_rest.rbuilder.querysets import models

from datetime import datetime

# retag if a new query is made and the results are greater
# than this many seconds old
TAG_REFRESH_INTERVAL=60

# TODO: this code passes around ids way too much and should be passing
# around objects to reduce SQL usage

class QuerySetManager(basemanager.BaseManager):

    # TODO: make this more pluggable/OO so these maps aren't needed
    tagMethodMap = {
        'system'               : '_tagSystems',
        'user'                 : None, # '_tagUsers',     # FIXME: implement
        'project'              : None, # '_tagProjects',  # FIXME: implement
        'project_branch_stage' : None  #'_tagStages'     # FIXME: implement
    }
    resourceCollectionMap = {
        'system'               : 'systems',
        'user'                 : 'users',
        'project'              : 'projects',
        'project_branch_stage' : 'stages'
    }
    tagModelMap = {
        'system'               : 'system_tag',
        'user'                 : 'user_tag',
        'project_branch_stage' : 'stage_tag',
        'project'              : 'project_tag'
    }

    def __init__(self, mgr):
        basemanager.BaseManager.__init__(self, mgr)

        # query tag inclusion objects (see usage below)
        self.__filtered_method = None
        self.__chosen_method = None

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
        return models.QuerySet.objects.select_related(depth=1).get(pk=querySetId)

    @exposed
    def getQuerySets(self):
        '''return all query set objects'''
        querySets = models.QuerySets()
        querySets.query_set = models.QuerySet.objects.select_related(depth=1).all()
        return querySets

    @exposed
    def addQuerySet(self, querySet):
        '''create a new query set'''
        querySet.save()
        # we don't have to tag anything because if it's not tagged tags always run
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    @exposed
    def updateQuerySet(self, querySet):
        '''edit a query set'''
        if not querySet.can_modify:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)
        querySet.save()
        # we don't have to tag anything because if it's not tagged tags always run
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    @exposed
    def deleteQuerySet(self, querySet):
        '''remove a query set unless it's one that shipped w/ rBuilder'''
        if querySet.can_modify: 
            querySet.delete()
        else:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)

    def addToAllQuerySet(self, querySet):
        '''
        The "all" (systems) queryset is auto-maintained to 
        include all system querysets
        '''
        allQuerySet = models.QuerySet.objects.get(
            name='All Systems'
        )
        allQuerySet.children.add(querySet)
        allQuerySet.save()

    def _getQueryTag(self, querySet):
        '''
        TODO: eliminate query tags as a middle layer, we don't need them, 
        resource tags are enough'''
        try:
            queryTag = models.QueryTag.objects.get(
                query_set=querySet
            )
        except ObjectDoesNotExist:
            querySetName = querySet.name.replace(' ', '_')
            queryTagName = 'query-tag-%s-%s' % (querySetName, querySet.pk)
            queryTag = models.QueryTag(query_set=querySet, name=queryTagName)
            queryTag.save()

        return queryTag

    def _tagMethod(self, querySet):
        '''
        Get the routine to tag a query set
        TODO: make this pluggable and eliminate the map.
        '''
        method_name = self.tagMethodMap[querySet.resource_type]
        if method_name is None:
            return None
        return getattr(self, method_name)

    def _tagSingleQuerySetFiltered(self, querySet):
        '''tag a single query set, non recursively'''
        # get the results the filtered items would have matched
        resources = self.filterQuerySet(querySet, use_tags=False)
        tag = self._getQueryTag(querySet)
        method = self._tagMethod(querySet)
        if method is None:
            # query set doesn't support tagging yet
            return
        method(resources, tag, self._filteredMethod())
        querySet.tagged_date = datetime.now()
        querySet.save()

    # no need to do this, as adding systems to a chosen
    # set already does this, this would be a no-op, right?
    # 
    #def _tagQuerySetChosen(self, querySet):
    #    '''tag resources explicitly added to query set'''
    #    resources = self._getQuerySetChosenResult(querySet, use_tags=False)
    #    tag = self._getQueryTag(querySet)
    #    method = getattr(self, self.tagMethodMap[querySet.resource_type])
    #    inclusionMethod = models.InclusionMethod.objects.select_related().get(
    #        name='chosen')
    #    method(resources, tag, inclusionMethod)

    def _tagSystems(self, systems, tag, inclusionMethod):
        '''
        store that a given query tag matched the system 
        for caching purposes
        '''
        # TODO: make this pluggable so we don't neeed model 
        # specific methods

        if inclusionMethod.name != 'chosen':
            # membership in the chosen set is stored ONLY 
            # through resource tags so we do not delete stale 
            # entries here, however filtered matches
            # need to be recalculated
            old_tags = models.SystemTag.objects.filter(
                query_tag=tag, 
                inclusion_method=inclusionMethod
            ).delete()

        for system in systems:
            # create a tag for each system
            systemTag, created = models.SystemTag.objects.get_or_create(
                system=system, 
                query_tag=tag, 
                inclusion_method=inclusionMethod
            )
            systemTag.save()

    def _classByName(self, kls):
        '''helper method to load modules'''
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)            
        return m

    def filterQuerySet(self, querySet, use_tags=True):
        '''Return resources matching specific filter criteria'''
        model = modellib.type_map[querySet.resource_type]

        # make sure we've implemented tags for these objects
        # should be able to remove this code once Edge-p1 is 
        # complete
        method = self._tagMethod(querySet)
        if method is None:
            use_tags = False
 
        resources = None
        if not use_tags:
            if not querySet.filter_entries.all():
                resources = EmptyQuerySet(model)
            else:
                resources = model.objects.select_related().all()
            # TODO remove duplciate use of new query set
            for filt in querySet.filter_entries.select_related().all():
                resources = modellib.filterDjangoQuerySet(resources, 
                    filt.field, filt.operator, filt.value)
            return resources.distinct()
        else:
            # use tags to find what is matched by the query set
            # this should probably be it's own method
            query_tag = models.QueryTag.objects.get(
                query_set=querySet
            )
            resources = model.objects.select_related().filter(
                #tags__query_tag__query_tag_id = query_tag.pk,
                tags__query_tag__query_tag_id = query_tag.pk,
                tags__inclusion_method = self._filteredMethod()
            ).distinct().all()
            return resources

    def _getResourceCollection(self, querySet, resources):
        '''
        Given a queryset and a list of matched resources, 
        construct and return a collection object.'''
        resourceCollection = modellib.type_map[
            self.resourceCollectionMap[querySet.resource_type]]
        resourceCollection = resourceCollection()
        setattr(resourceCollection, querySet.resource_type, resources)
        resourceCollection._parents = [querySet]
        return resourceCollection

    @exposed
    def getQuerySetAllResult(self, querySetId, use_tags=True):
        '''
        The results for a queryset are typically the 'all' result.  It is
        also possible to be more fine grained and only see matches
        due to filters, chosen (explicitly added) or child (recursive) matches,
        though 'all' includes, well, all of those.
        '''
        querySet = self._querySet(querySetId)
        qsAllResult = self._getQuerySetAllResult(querySet, use_tags=use_tags)
        resourceCollection = self._getResourceCollection(querySet, qsAllResult)
        resourceCollection.view_name = "QuerySetAllResult"
        return resourceCollection

    def _getQuerySetAllResult(self, querySet, use_tags=True):
        '''
        The result for a queryset is the merger of it's filtered, chosen,
        and child query sets
        '''
        filtered = self._getQuerySetFilteredResult(querySet, use_tags=use_tags)
        chosen   = self._getQuerySetChosenResult(querySet)
        children = self._getQuerySetChildResult(querySet)
        return filtered | chosen | children

    @exposed
    def getQuerySetChosenResult(self, querySetId): #, use_tags=False):
        '''
        For a given query set, return only the chosen matches, aka resources
        explicitly placed in the queryset
        TODO: allow passing in the queryset or the ID
        '''
        querySet = self._querySet(querySetId)
        result_data = self._getQuerySetChosenResult(querySet) #, use_tags=use_tags)
        resourceCollection = self._getResourceCollection(querySet, result_data)
        resourceCollection.view_name = "QuerySetChosenResult"
        return resourceCollection

    def _getQuerySetChosenResult(self, querySet): 
        queryTag = self._getQueryTag(querySet)
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        taggedModels = tagModel.objects.filter(query_tag=queryTag,
            inclusion_method=self._chosenMethod())
        resourceModel = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(resourceModel)
        for taggedModel in taggedModels:
            r = getattr(taggedModel, querySet.resource_type)
            r = resourceModel.objects.filter(pk=r.pk).distinct()
            resources = resources | r
        return resources

    @exposed
    def getQuerySetFilteredResult(self, querySetId, use_tags=True, nocache=False):
        '''
        For a given queryset, return only the portion of it's matches
        that correspond to "smart match" style comparison checks.
        '''
        querySet = self._querySet(querySetId)
        resultData = self._getQuerySetFilteredResult(querySet, use_tags=use_tags)
        resourceCollection = self._getResourceCollection(querySet, resultData)
        resourceCollection.view_name = "Systems"
        resourceCollection._parents = []
        resourceCollection.filter_by = querySet.getFilterBy()
        return resourceCollection

    def _areResourceTagsStale(self, querySet):
         '''
         Does the query set need to be retagged?
         '''
         if querySet.tagged_date is None:
             # never been tagged before
             return True
         else:
             then  = querySet.tagged_date.replace(tzinfo=None)
             delta = datetime.now() - then
             return (delta.seconds > TAG_REFRESH_INTERVAL)

    def _getQuerySetFilteredResult(self, querySet, use_tags=False, nocache=False):

        # if we requested to use tags and the queryset is stale,
        # retag the queryset before using it

        # TODO: plumb nocache up?

        if nocache or self._areResourceTagsStale(querySet):
            self._tagSingleQuerySetFiltered(querySet)

        return self.filterQuerySet(querySet, use_tags=use_tags)

    @exposed
    def getQuerySetChildResult(self, querySetId, use_tags=True):
        ''' 
        Return the portion of queryset match data that comes from child
        querysets, regardless of whether those child matches are themselves
        'chosen', 'filtered', or 'child' matches.
        '''
        # NOTE: child query set ALWAYS uses tags, because you can't choose
        # to use tags or not at UI visible level, (there may be a nocache
        # flag instead).
        # TODO: provide a nice wrapper to get these by ID
        querySet = self._querySet(querySetId)
        result_data = self._getQuerySetChildResult(querySet, use_tags=True)
        resourceCollection = self._getResourceCollection(querySet, result_data)
        resourceCollection.view_name = "QuerySetChildResult"
        return resourceCollection

    def _getQuerySetChildResult(self, querySet, use_tags=True):
        '''
        Determine child results...
        TODO: uniqueness detection/removal
        '''
        children = self._getAllChildQuerySets(querySet, results=[])
        model = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(model)
        #for childQuerySet in querySet.children.select_related().all():
        #    childResources = self._getQuerySetAllResult(
        #        childQuerySet, 
        #        use_tags=use_tags
        #    )
        #    resources = resources | childResources
        for qs in children:
             filtered = self._getQuerySetFilteredResult(
                 qs, use_tags=use_tags
             ).distinct()
             chosen = self._getQuerySetChosenResult(
                 qs
             ).distinct()
             resources = resources | filtered | chosen
        resources = resources.distinct()

        # all the child resources in this query set must be assigned to each
        # of their parents -- BOOKMARK

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
        filterDescriptor = descriptor.getFilterDescriptor(model)
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
        queryTag = self._getQueryTag(querySet)
        # we do not update the queryset tag date here because it could
        # still be stale with respect to child or filtered results
        tagMethod = self._tagMethod(querySet)
        tagMethod([resource], queryTag, self._chosenMethod())
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def addQuerySetChosen(self, querySetId, resources):
        '''
        Add a list of matched systems to a chosen query set result list.
        Deletes all previous matches.
        '''
        querySet = self._querySet(querySetId)
        queryTag = self._getQueryTag(querySet)
        resources_out = getattr(resources, querySet.resource_type)

        # Delete all previously tagged resources
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        tagModel.objects.filter(
            query_tag=queryTag,
            inclusion_method=self._chosenMethod(),
        ).delete()

        # Tag new resources
        tagMethod = self._tagMethod(querySet)
        tagMethod(resources_out, queryTag, self._chosenMethod())

        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def deleteQuerySetChosen(self, querySetId, resource):
        '''
        Remove a resource from a queryset chosen result.
        '''
        querySet = self._querySet(querySetId)
        queryTag = self._getQueryTag(querySet)
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        resourceArg = {querySet.resource_type:resource}
        tagModels = tagModel.objects.filter(query_tag=queryTag, 
            inclusion_method=self._chosenMethod(), **resourceArg)
        tagModels.delete()
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def getQueryTags(self, query_set_id):
        '''
        Return the querytags associated with a queryset.
        TODO: These seem to basically be 1:1 with them and we can probably smite them.
        '''
        queryTags = models.QueryTags()
        queryTags.query_tag = models.QueryTag.objects.filter(
            query_set__pk=query_set_id
        )
        return queryTags

    @exposed
    def getQueryTag(self, query_set_id, query_tag_id):
        '''
        I think we can remove this.  See getQueryTags.
        '''
        queryTag = models.QueryTag.objects.get(
            pk=query_tag_id
        )
        return queryTag


