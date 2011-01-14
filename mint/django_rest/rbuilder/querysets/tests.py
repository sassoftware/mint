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
        self.assertEquals(len(models.QueryTag.objects.all()), 4)
        self.assertEquals(models.QueryTag.objects.all()[3].query_tag,
            "query-tag-Unmanaged systems-4")
        self.assertEquals(len(models.QuerySet.objects.all()), 4)
        self.assertEquals(models.QuerySet.objects.all()[3].name,
            "Unmanaged systems")

class QuerySetFixturedTestCase(XMLTestCase):
    fixtures = ['systems-named-like-3-queryset', 'system_collection']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mgr = manager.QuerySetManager()

    def xobjResponse(self, url):
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        return systems

    def testGetQuerySets(self):
        response = self._get('/api/query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.query_sets_xml)

    def testGetQuerySet(self):
        response = self._get('/api/query_sets/4/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.query_set_xml)

    def testGetQuerySetFilteredResult(self):
        response = self._get('/api/query_sets/4/filtered',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '38')

    def testGetQuerySetChosenResult(self):
        response = self._get('/api/query_sets/4/chosen/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '1')

    def testGetQuerySetAllResult(self):
        response = self._get('/api/query_sets/4/all/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '39')

    def testPutQuerySetChosen(self):
        response = self._put('/api/query_sets/4/chosen/',
            data=testsxml.systems_chosen_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/4/chosen/')
        self.assertEquals(len(systems.system), 3)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 4', u'System name 5', u'System name 6'])

        response = self._put('/api/query_sets/4/chosen/',
            data=testsxml.systems_chosen_put_xml2,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/4/chosen/')
        self.assertEquals(len(systems.system), 5)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 4', u'System name 5', u'System name 6',
             u'System name 7', u'System name 8'])

    def testUpdateQuerySet(self):
        response = self._put('/api/query_sets/4/',
            data=testsxml.query_set_update_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
    
        querySet = models.QuerySet.objects.get(pk=4)
        self.assertEquals(len(querySet.filter_entries.all()), 2)
        self.assertEquals(querySet.filter_entries.all()[1].field,
            'description')
        self.assertEquals(querySet.filter_entries.all()[1].operator,
            'LIKE')
        self.assertEquals(querySet.filter_entries.all()[1].value,
            '3')
