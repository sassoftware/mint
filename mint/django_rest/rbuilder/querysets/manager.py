#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
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
        querySet.save()
        self.tagQuerySet(querySet)
        return querySet

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
        resources = model.objects.all()
        filters = []
        qFilters = []
        for filt in querySet.filter_entries.all():
            # Replace all '.' with '__', to handle fields that span
            # relationships
            field = filt.field.replace('.', '__')
            operator = modellib.filterTermMap[filt.operator]

            k = '%s__%s' % (field, operator)
            if operator.startswith('NOT_'):
                qFilters.append({k:filt.value})
            else:
                filters.append({k:filt.value})

        for qFilter in qFilters:
            resources = resources.filter(~Q(**qFilter))

        for filt in filters:
            resources = resources.filter(**filt)

        return resources

    def getResourceCollection(self, querySet, resources):
        resourceCollection = modellib.type_map[
            self.resourceCollectionMap[querySet.resource_type]]
        resourceCollection = resourceCollection()
        setattr(resourceCollection, querySet.resource_type, resources)
        return resourceCollection

    @exposed
    def getQuerySetAllResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        return self.getResourceCollection(querySet,
            list(self._getQuerySetChosenResult(querySet)) + \
            list(self._getQuerySetFilteredResult(querySet)))

    @exposed
    def getQuerySetChosenResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        return self.getResourceCollection(querySet,
            self._getQuerySetChosenResult(querySet))

    def _getQuerySetChosenResult(self, querySet):
        queryTag = models.QueryTag.objects.get(query_set=querySet)
        chosenMethod = models.InclusionMethod.objects.get(
            inclusion_method='chosen')
        tagModel = modellib.type_map[self.tagModelMap[querySet.resource_type]]
        taggedModels = tagModel.objects.filter(query_tag=queryTag,
            inclusion_method=chosenMethod)
        resources = [getattr(r, querySet.resource_type) \
            for r in taggedModels]
        return resources

    @exposed
    def getQuerySetFilteredResult(self, querySetId):
        querySet = models.QuerySet.objects.get(pk=querySetId)
        return self.getResourceCollection(querySet,
            self._getQuerySetFilteredResult(querySet))

    def _getQuerySetFilteredResult(self, querySet):
        resources = self.filterQuerySet(querySet)
        return resources
