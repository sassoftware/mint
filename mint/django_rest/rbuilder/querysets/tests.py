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

from xobj import xobj

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
        self.assertEquals(len(models.QueryTag.objects.all()), 2)
        self.assertEquals(models.QueryTag.objects.all()[1].query_tag,
            "query-tag-Unmanaged systems-2")
        self.assertEquals(len(models.QuerySet.objects.all()), 2)
        self.assertEquals(models.QuerySet.objects.all()[1].name,
            "Unmanaged systems")

class QuerySetFixturedTestCase(XMLTestCase):
    fixtures = ['systems-named-like-3-queryset', 'system_collection']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mgr = manager.QuerySetManager()

    def testGetQuerySets(self):
        response = self._get('/api/query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.query_sets_xml)

    def testGetQuerySet(self):
        response = self._get('/api/query_sets/2/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.query_set_xml)

    def testGetQuerySetFilteredResult(self):
        response = self._get('/api/query_sets/2/filtered',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '38')

    def testGetQuerySetChosenResult(self):
        response = self._get('/api/query_sets/2/chosen/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '1')

    def testGetQuerySetAllResult(self):
        response = self._get('/api/query_sets/2/all/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '39')

    def testPostQuerySetChosen(self):
        pass

    def testPostQuerySetFiltered(self):
        pass
