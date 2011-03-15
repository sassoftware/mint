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
        self.assertEquals(len(models.QueryTag.objects.all()), 5)
        self.assertEquals(models.QueryTag.objects.all()[4].query_tag,
            "query-tag-Unmanaged systems-5")
        self.assertEquals(len(models.QuerySet.objects.all()), 5)
        self.assertEquals(models.QuerySet.objects.all()[4].name,
            "Unmanaged systems")

class QuerySetFixturedTestCase(XMLTestCase):
    fixtures = ['systems_named_like_3_queryset', 'system_collection']

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

    def testGetFixturedQuerySet(self):
        response = self._get('/api/query_sets/5/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.query_set_fixtured_xml)

    def testGetQuerySetFilteredResult(self):
        response = self._get('/api/query_sets/5/filtered',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '38')

    def testGetQuerySetChosenResult(self):
        response = self._get('/api/query_sets/5/chosen/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '1')

    def testGetQuerySetAllResult(self):
        response = self._get('/api/query_sets/5/all/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '39')

    def testPutQuerySetChosen(self):
        response = self._put('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 2)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 5', u'System name 6'])

        response = self._put('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_put_xml2,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 2)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 7', u'System name 8'])

    def testPostQuerySetChosen(self):
        response = self._post('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 2)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 4', u'System name 7'])

        response = self._post('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_post_xml2,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 3)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 4', u'System name 7',
             u'System name 8'])

    def testDeleteQuerySetChosen(self):
        # Add system 7 to the query set first
        response = self._post('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 2)
        self.assertEquals([s.name for s in systems.system],
            [u'System name 4', u'System name 7'])

        # Now delete system 7 from the query set chosen results
        response = self._delete('/api/query_sets/5/chosen/',
            data=testsxml.systems_chosen_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = self.xobjResponse('/api/query_sets/5/chosen/')
        self.assertEquals(len(systems.system), 0)
        self.assertEquals([s.name for s in systems.system], [])


    def testUpdateQuerySet(self):
        response = self._put('/api/query_sets/5/',
            data=testsxml.query_set_update_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
    
        querySet = models.QuerySet.objects.get(pk=5)
        self.assertEquals(len(querySet.filter_entries.all()), 2)
        self.assertEquals(querySet.filter_entries.all()[1].field,
            'description')
        self.assertEquals(querySet.filter_entries.all()[1].operator,
            'LIKE')
        self.assertEquals(querySet.filter_entries.all()[1].value,
            '3')

    def testDeleteQuerySet(self):
        response = self._delete('/api/query_sets/5/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        
        try:
            querySet = models.QuerySet.objects.get(pk=5)
        except models.QuerySet.DoesNotExist:
            return
        else:
            self.assertTrue(False)

    def testDeleteReadOnlyQuerySet(self):
        response = self._delete('/api/query_sets/1/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)
        fault = xobjModel.fault
        self.assertEquals(fault.message,
            "The All Systems Query Set can not be modified.")

        querySet = models.QuerySet.objects.get(pk=1)
        self.assertEquals(querySet.name,
            "All Systems")

class QuerySetChildFixturedTestCase(XMLTestCase):
    fixtures = ['queryset_children', 'system_collection']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mgr = manager.QuerySetManager()

    def xobjResponse(self, url):
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        return systems


    def testGetQuerySetChildResult(self):
        systems = self.xobjResponse('/api/query_sets/9/child')
        self.assertEquals([s.system_id for s in systems.system],
            [u'210', u'211', u'214', u'215', u'216', u'217', u'212', u'213'])
        systems = self.xobjResponse('/api/query_sets/9/all')
        self.assertEquals([s.system_id for s in systems.system],
            [u'210', u'211', u'214', u'215', u'216', u'217', u'212', u'213'])

        systems = self.xobjResponse('/api/query_sets/12/child')
        self.assertEquals([s.system_id for s in systems.system],
            [u'215', u'216', u'217'])
        systems = self.xobjResponse('/api/query_sets/12/all')
        self.assertEquals([s.system_id for s in systems.system],
            [u'215', u'216', u'217'])

    def testUpdateChildQuery(self):
        response = self._put('/api/query_sets/12/',
            data=testsxml.query_set_child_update_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        querySet = models.QuerySet.objects.get(pk=12)
        self.assertEquals([q.pk for q in querySet.children.all()],
            [6, 10, 11])
        systems = self.xobjResponse('/api/query_sets/12/child')
        self.assertEquals([s.system_id for s in systems.system],
            [u'210', u'211', u'215', u'216', u'217'])
