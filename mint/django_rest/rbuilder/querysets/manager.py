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

class QuerySetManager(basemanager.BaseManager):

    tagMethodMap = {
        'system' : 'tagSystems',
    }
    resourceCollectionMap = {
        'system' : 'systems',
    }
    tagModelMap = {
        'system' : 'system_tag',
    }

    @exposed
    def getQuerySet(self, querySetId):
        return models.QuerySet.objects.get(pk=querySetId)

    @exposed
    def getQuerySets(self):
        querySets = models.QuerySets()
        querySets.query_set = models.QuerySet.objects.all()
        return querySets

    @exposed
    def addQuerySet(self, querySet):
        if querySet.name == 'All Systems':
            raise errors.AllSystemsQuerySetReadOnly()
        querySet.save()
        self.tagQuerySet(querySet)
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    @exposed
    def updateQuerySet(self, querySet):
        if querySet.name == 'All Systems':
            raise errors.AllSystemsQuerySetReadOnly()
        querySet.save()
        self.tagQuerySet(querySet)
        if querySet.resource_type == 'system' and querySet.isTopLevel():
            self.addToAllQuerySet(querySet)
        return querySet

    def addToAllQuerySet(self, querySet):
        allQuerySet = models.QuerySet.objects.get(name='All Systems')
        allQuerySet.children.add(querySet)
        allQuerySet.save()

    def getQueryTag(self, querySet):
        try:
            queryTag = models.QueryTag.objects.get(query_set=querySet)
        except ObjectDoesNotExist:
            queryTag = 'query-tag-%s-%s' % (querySet.name, querySet.pk)
            queryTag = models.QueryTag(query_set=querySet, query_tag=queryTag)
            queryTag.save()

        return queryTag

    @exposed
    def tagQuerySet(self, querySet):
        resources = self.filterQuerySet(querySet)
        tag = self.getQueryTag(querySet)
        method = getattr(self, self.tagMethodMap[querySet.resource_type])
        inclusionMethod = models.InclusionMethod.objects.get(
            inclusion_method='filtered')
        method(resources, tag, inclusionMethod)

    def tagSystems(self, systems, tag, inclusionMethod):
        for system in systems:
            systemTag, created = models.SystemTag.objects.get_or_create(
                system=system, query_tag=tag, inclusion_method=inclusionMethod)
            systemTag.save()

    def filterQuerySet(self, querySet):
        model = modellib.type_map[querySet.resource_type]
        if not querySet.filter_entries.all():
            resources = EmptyQuerySet(model)
        else:
            resources = model.objects.all()
        for filt in querySet.filter_entries.all():
            resources = modellib.filterDjangoQuerySet(resources, 
                filt.field, filt.operator, filt.value)
        return resources

    def getResourceCollection(self, querySet, resources):
        resourceCollection = modellib.type_map[
            self.resourceCollectionMap[querySet.resource_type]]
        resourceCollection = resourceCollection()
        setattr(resourceCollection, querySet.resource_type, resources)
        resourceCollection._parents = [querySet]
        return resourceCollection

    @exposed
    def getQuerySetAllResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        resourceCollection = self.getResourceCollection(querySet, 
            self._getQuerySetAllResult(querySet))
        resourceCollection.view_name = "QuerySetAllResult"
        return resourceCollection

    def _getQuerySetAllResult(self, querySet):
        filtered = self._getQuerySetFilteredResult(querySet)
        chosen =  self._getQuerySetChosenResult(querySet)
        children = self._getQuerySetChildResult(querySet)
        return filtered | chosen | children

    @exposed
    def getQuerySetChosenResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        resourceCollection = self.getResourceCollection(querySet,
            self._getQuerySetChosenResult(querySet))
        resourceCollection.view_name = "QuerySetChosenResult"
        return resourceCollection

    def _getQuerySetChosenResult(self, querySet):
        queryTag = self.getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.get(
            inclusion_method='chosen')
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
    def getQuerySetFilteredResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        resourceCollection = self.getResourceCollection(querySet,
            self._getQuerySetFilteredResult(querySet))
        resourceCollection.view_name = "Systems"
        resourceCollection._parents = []
        resourceCollection.filter_by = querySet.getFilterBy()
        return resourceCollection

    def _getQuerySetFilteredResult(self, querySet):
        resources = self.filterQuerySet(querySet)
        return resources

    @exposed
    def getQuerySetChildResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        resourceCollection = self.getResourceCollection(querySet,
            self._getQuerySetChildResult(querySet))
        resourceCollection.view_name = "QuerySetChildResult"
        return resourceCollection

    def _getQuerySetChildResult(self, querySet):
        model = modellib.type_map[querySet.resource_type]
        resources = EmptyQuerySet(model)
        for childQuerySet in querySet.children.all():
            childResources = self._getQuerySetAllResult(childQuerySet)
            resources = resources | childResources
        return resources

    @exposed
    def getQuerySetFilterDescriptor(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        model = modellib.type_map[querySet.resource_type]
        filterDescriptor = descriptor.getFilterDescriptor(model)
        filterDescriptor.pk = querySetId
        return filterDescriptor

    @exposed
    def updateQuerySetChosen(self, querySetId, resources):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        queryTag = self.getQueryTag(querySet)
        chosenMethod = models.InclusionMethod.objects.get(
            inclusion_method='chosen')
        resources = getattr(resources, querySet.resource_type)
        tagMethod = getattr(self, self.tagMethodMap[querySet.resource_type])
        tagMethod(resources, queryTag, chosenMethod)
        return self.getQuerySetChosenResult(querySetId)

