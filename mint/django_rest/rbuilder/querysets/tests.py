#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

from mint.django_rest.rbuilder.querysets import manager
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.querysets import testsxml

class QuerySetTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mgr = manager.QuerySetManager()

    def testPostQuerySet(self):
        response = self._post('/api/query_sets/',
            data=testsxml.queryset_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        # there's only one unmanaged system initially
        self.assertEquals(len(models.SystemTag.objects.all()), 1)
        self.assertEquals(models.SystemTag.objects.all()[0].system.name,
            "rPath Update Service")
        self.assertEquals(models.SystemTag.objects.all()[0].inclusion_method.inclusion_method,
            "filtered")
        self.assertEquals(len(models.QueryTag.objects.all()), 1)
        self.assertEquals(models.QueryTag.objects.all()[0].query_tag,
            "query-tag-Unmanaged systems-1")
        self.assertEquals(len(models.QuerySet.objects.all()), 1)
        self.assertEquals(models.QuerySet.objects.all()[0].name,
            "Unmanaged systems")


