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

# TODO: this code passes around ids way too much and should be passing
# around objects to reduce SQL usage

USE_TAGS_IN_QUERY=True

class QuerySetManager(basemanager.BaseManager):

    tagMethodMap = {
        'system' : 'tagSystems',
        'user' : 'tagUsers',
        'project' : 'tagProjects',
        'project_branch_stage' : 'tagStages'
    }
    resourceCollectionMap = {
        'system' : 'systems',
        'user' : 'users',
        'project' : 'projects',
        'project_branch_stage' : 'stages'
    }
    tagModelMap = {
        'system' : 'system_tag',
        'user' : 'user_tag',
        'project_branch_stage' : 'stage_tag',
        'project' : 'project_tag'
    }


    @exposed
    def getQuerySet(self, querySetId):
        return models.QuerySet.objects.select_related().get(pk=querySetId)

    @exposed
    def getQuerySets(self):
        querySets = models.QuerySets()
        querySets.query_set = models.QuerySet.objects.select_related().all()
        return querySets

    @exposed
    def addQuerySet(self, querySet):
        querySet.save()
        self.tagQuerySet(querySet)
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    @exposed
    def updateQuerySet(self, querySet):
        if not querySet.can_modify:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)
        querySet.save()
        self.tagQuerySet(querySet)
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    @exposed
    def deleteQuerySet(self, querySet):
        if querySet.can_modify: 
            querySet.delete()
        else:
            raise errors.QuerySetReadOnly(querySetName=querySet.name)

    def addToAllQuerySet(self, querySet):
        allQuerySet = models.QuerySet.objects.select_related().get(name='All Systems')
        allQuerySet.children.add(querySet)
        allQuerySet.save()

    def _getQueryTag(self, querySet):
        try:
            queryTag = models.QueryTag.objects.select_related().get(query_set=querySet)
        except ObjectDoesNotExist:
            querySetName = querySet.name.replace(' ', '_')
            queryTagName = 'query-tag-%s-%s' % (querySetName, querySet.pk)
            queryTag = models.QueryTag(query_set=querySet, name=queryTagName)
            queryTag.save()

        return queryTag

    @exposed
    def tagQuerySet(self, querySet):
        resources = self.filterQuerySet(querySet)
        tag = self._getQueryTag(querySet)
        method = getattr(self, self.tagMethodMap[querySet.resource_type])
        inclusionMethod = models.InclusionMethod.objects.select_related().get(
            name='filtered')
        method(resources, tag, inclusionMethod)

    def tagSystems(self, systems, tag, inclusionMethod):
        for system in systems:
            systemTag, created = models.SystemTag.objects.select_related().get_or_create(
                system=system, query_tag=tag, inclusion_method=inclusionMethod)
            systemTag.save()

    def _classByName(self, kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)            
        return m

    # BOOKMARK!!!
    def filterQuerySet(self, querySet, use_tags=False):
        model = modellib.type_map[querySet.resource_type]
 
        resources = None
        if not use_tags:
            if not querySet.filter_entries.select_related().all():
                resources = EmptyQuerySet(model)
            else:
                resources = model.objects.select_related().all()
            # TODO remove duplciate use of new query set
            for filt in querySet.filter_entries.select_related().all():
                resources = modellib.filterDjangoQuerySet(resources, 
                    filt.field, filt.operator, filt.value)
            return resources
        else:
            # EXPERIMENTAL PATH -- do not filter, but instead
            # use tags to find what is matched by the query set
            # this should probably be it's own method
            query_tag = models.QueryTag.objects.select_related().get(query_set=querySet)
            resources = model.objects.select_related().filter(
                  tags__query_tag__query_tag_id = query_tag.pk
            ).all()
            return resources

    def getResourceCollection(self, querySet, resources):
        resourceCollection = modellib.type_map[
            self.resourceCollectionMap[querySet.resource_type]]
        resourceCollection = resourceCollection()
        setattr(resourceCollection, querySet.resource_type, resources)
        resourceCollection._parents = [querySet]
        return resourceCollection

    @exposed
    def getQuerySetAllResult(self, querySetId, use_tags=False):
        # definition of the query set
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        # contents...
        qsAllResult = self._getQuerySetAllResult(querySet, use_tags=use_tags)
        resourceCollection = self.getResourceCollection(querySet, qsAllResult)
        resourceCollection.view_name = "QuerySetAllResult"
        return resourceCollection

    def _getQuerySetAllResult(self, querySet, use_tags=False):
        filtered = self._getQuerySetFilteredResult(querySet, use_tags=use_tags)
        if not use_tags:
            # use_tags currently doesn't have any meaning to the following:
            chosen =  self._getQuerySetChosenResult(querySet, use_tags=use_tags)
            children = self._getQuerySetChildResult(querySet, use_tags=use_tags)
            return filtered | chosen | children
        else:
            # filtered will include both chosen+filtered in this case
            children = self._getQuerySetChildResult(querySet, use_tags=use_tags)
            return children | filtered

    @exposed
    def getQuerySetChosenResult(self, querySetId, use_tags=False):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        result_data = self._getQuerySetChosenResult(querySet, use_tags=use_tags)
        resourceCollection = self.getResourceCollection(querySet, result_data)
        resourceCollection.view_name = "QuerySetChosenResult"
        return resourceCollection

    def _getQuerySetChosenResult(self, querySet, use_tags=False):
        queryTag = self._getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.select_related().get(
            name='chosen')
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        taggedModels = tagModel.objects.filter(query_tag=queryTag,
            inclusion_method=chosenMethod)
        resourceModel = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(resourceModel)
        for taggedModel in taggedModels:
            r = getattr(taggedModel, querySet.resource_type)
            r = resourceModel.objects.filter(pk=r.pk)
            resources = resources | r
        return resources

    @exposed
    def getQuerySetFilteredResult(self, querySetId, use_tags=False):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        resultData = self._getQuerySetFilteredResult(querySet, use_tags=use_tags)
        resourceCollection = self.getResourceCollection(querySet, resultData)
        resourceCollection.view_name = "Systems"
        resourceCollection._parents = []
        resourceCollection.filter_by = querySet.getFilterBy()
        return resourceCollection

    def _getQuerySetFilteredResult(self, querySet, use_tags=False):
        return self.filterQuerySet(querySet, use_tags=use_tags)

    @exposed
    def getQuerySetChildResult(self, querySetId, use_tags=False):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        result_data = self._getQuerySetChildResult(querySet, use_tags=use_tags)
        resourceCollection = self.getResourceCollection(querySet, result_data)
        resourceCollection.view_name = "QuerySetChildResult"
        return resourceCollection

    def _getQuerySetChildResult(self, querySet, use_tags=False):
        model = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(model)
        for childQuerySet in querySet.children.select_related().all():
            childResources = self._getQuerySetAllResult(childQuerySet, use_tags=use_tags)
            resources = resources | childResources
        return resources

    @exposed
    def getQuerySetFilterDescriptor(self, querySetId):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        model = modellib.type_map[querySet.resource_type]
        filterDescriptor = descriptor.getFilterDescriptor(model)
        filterDescriptor.pk = querySetId
        return filterDescriptor

    @exposed
    def updateQuerySetChosen(self, querySetId, resource):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        queryTag = self._getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.select_related().get(
            name='chosen')
        tagMethod = getattr(self, self.tagMethodMap[querySet.resource_type])
        tagMethod([resource], queryTag, chosenMethod)
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def addQuerySetChosen(self, querySetId, resources):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        queryTag = self._getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.select_related().get(
            name='chosen')
        resources_out = getattr(resources, querySet.resource_type)

        # Delete all previously tagged resources
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        tagModels = tagModel.objects.select_related().filter(query_tag=queryTag,
            inclusion_method=chosenMethod)
        tagModels.delete()

        # Tag new resources
        tagMethod = getattr(self, self.tagMethodMap[querySet.resource_type])
        tagMethod(resources_out, queryTag, chosenMethod)

        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def deleteQuerySetChosen(self, querySetId, resource):
        querySet = models.QuerySet.objects.select_related().get(pk=querySetId)
        queryTag = self._getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.select_related().get(
            name='chosen')
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        resourceArg = {querySet.resource_type:resource}
        tagModels = tagModel.objects.filter(query_tag=queryTag, 
            inclusion_method=chosenMethod, **resourceArg)
        tagModels.delete()
        return self.getQuerySetChosenResult(querySetId)

    @exposed
    def getQueryTags(self, query_set_id):
        queryTags = models.QueryTags()
        queryTags.query_tag = \
            models.QueryTag.objects.select_related().filter(query_set__pk=query_set_id)
        return queryTags

    @exposed
    def getQueryTag(self, query_set_id, query_tag_id):
        queryTag = models.QueryTag.objects.select_related().get(pk=query_tag_id)
        return queryTag
