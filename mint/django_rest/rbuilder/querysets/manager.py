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
        model = modellib.type_map[querySet.resource_type]
        objects = model.objects.all()
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
            objects = objects.filter(~Q(**qFilter))

        for filt in filters:
            objects = objects.filter(**filt)

        tag = self.getQueryTag(querySet)
        method = getattr(self, self.tagMethodMap[querySet.resource_type])
        inclusionMethod = models.InclusionMethod.objects.get(
            inclusion_method='filtered')
        method(objects, tag, inclusionMethod)

    def tagSystems(self, systems, tag, inclusionMethod):
        for system in systems:
            systemTag, created = models.SystemTag.objects.get_or_create(
                system=system, query_tag=tag, inclusion_method=inclusionMethod)
            systemTag.save()
