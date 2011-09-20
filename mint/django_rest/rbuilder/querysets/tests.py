#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.querysets import testsxml
#from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.querysets import manager as mgr
from xobj import xobj

# turn off tag cache delay for tests, effectively always
# forcing a retag
mgr.TAG_REFRESH_INTERVAL=-1



class QueryTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

    def _getQs(self, name):
        '''lookup query sets to avoid hardcodes in tests'''
        return models.QuerySet.objects.get(name=name).pk

    def xobjSystems(self, url):
        url = url + ";start_index=0;limit=9999"
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = None
        try:
            systems = xobjModel.systems.system
        except AttributeError:
            return []
        return self.xobjHack(systems)
    
    #def xobjSystem(self, url):
    #    response = self._get(url,
    #        username="admin", password="password")
    #    xobjModel = xobj.parse(response.content)
    #    return xobjModel.system

    def xobjHack(self, result):
        '''get a list from an xobj, even if N=1. Bug/feature in xobj'''
        if type(result) != list:
            return [result]
        return result

class QuerySetTestCase(QueryTestCase):

    fixtures = ['system_collection']

    def setUp(self):
        QueryTestCase.setUp(self)

    def testListQuerySet(self):
        # show that we can list all query sets
        response = self._get('query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        querySets = xobj.parse(response.content)
        length = len(querySets.query_sets.query_set)
        # ok to bump this if we add more QS in the db
        self.assertEqual(length, 10)

    def testGetQuerySet(self):
        # show that we can get the definition of a queryset
        qsid = self._getQs("All Systems")
        response = self._get("query_sets/%s" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        querySet = xobj.parse(response.content)
        self.failUnlessEqual(querySet.query_set.name, 'All Systems')

    def testGetQuerySetAll(self):
        # show that we can get results from a query set
        qsid = self._getQs("All Systems")
        response = self._get("query_sets/%s/all;start_index=0;limit=9999" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = xobj.parse(response.content)
        count = len(systems.systems.system)
        self.failUnlessEqual(count, 201)

        # we will have tagged it by visiting the last pass
        # now hit it again and run down the "tagged" path
        # for code coverage purposes & make sure we get
        # the same result
        mgr.TAG_REFRESH_INTERVAL=9999
        response = self._get("query_sets/%s/all;start_index=0;limit=9999" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        systems = xobj.parse(response.content)
        count = len(systems.systems.system)
        self.failUnlessEqual(count, 201)

        # since we just fetched the queryset, the queryset entry itself
        # should now have an invalidation job on it which we can use
        # have it re-tag on the next pass
        response = self._get("query_sets/%s" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.queryset_with_actions)

        # the tagged date should be set because we ran the queryset 
        # at least once.
        # post the invalidation job to the queryset and verify the tagged
        # date goes back to null
        queryset = models.QuerySet.objects.get(pk=qsid)
        self.assertTrue(queryset.tagged_date is not None)
        response = self._post("query_sets/%s/jobs" % qsid,
            data=testsxml.queryset_invalidate_post_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        queryset = models.QuerySet.objects.get(pk=qsid)
        self.assertEquals(queryset.tagged_date, None)



    # NOTE -- this test did not exist previously, is it
    # supported?

    def testPutQuerySetAndChildSets(self):

        # add a new query set (post)
        # query set, then modify it to add a child set.

        # post a new query set
        response = self._post('query_sets/',
            data=testsxml.queryset_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.status_code, 200)

        # some Django model tweaks so we don't have to fixture
        # the XML.  Notice we don't save here.
        qs1 = models.QuerySet.objects.get(name='New Query Set')
        child1 = self.xobjSystems("query_sets/%s/child/" % qs1.pk)
        all1 = self.xobjSystems("query_sets/%s/all/" % qs1.pk)
        chosen1 = self.xobjSystems("query_sets/%s/chosen/" % qs1.pk)
        filtered1 = self.xobjSystems("query_sets/%s/filtered/" % qs1.pk)
        self.assertEqual(len(child1), 0)
        self.assertEqual(len(all1), 38)
        self.assertEqual(len(chosen1), 0)
        self.assertEqual(len(filtered1), 38)
        
        #qs2 = models.QuerySet.objects.get(name='All Systems')
        #qs1.children.add(qs2)
        #xml = qs1.to_xml()

        # verify the counts are consistent with having a large
        # child set.
        response = self._put("query_sets/%s" % qs1.pk,
            username="admin", password="password", 
            data=testsxml.queryset_put_xml)
        self.assertEquals(response.status_code, 200)

        child2 = self.xobjSystems("query_sets/%s/child/" % qs1.pk)
        self.assertEquals(len(child2), 201)
        all2 = self.xobjSystems("query_sets/%s/all/" % qs1.pk)
        self.assertEquals(len(all2), 201)
        chosen2 = self.xobjSystems("query_sets/%s/chosen/" % qs1.pk)
        self.assertEquals(len(chosen2), 0)
        filtered2 = self.xobjSystems("query_sets/%s/filtered/" % qs1.pk)
        self.assertEquals(len(filtered2), 38)

        # do it again to make sure child tags work
        child2 = self.xobjSystems("query_sets/%s/child/" % qs1.pk)
        self.assertEquals(len(child2), 201)
        all2 = self.xobjSystems("query_sets/%s/all/" % qs1.pk)
        self.assertEquals(len(all2), 201)
        chosen2 = self.xobjSystems("query_sets/%s/chosen/" % qs1.pk)
        self.assertEquals(len(chosen2), 0)
        filtered2 = self.xobjSystems("query_sets/%s/filtered/" % qs1.pk)
        self.assertEquals(len(filtered2), 38)

    def testPostQuerySet(self):
        # show that we can add a new query set
        # get before result
        response = self._get('query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        before_db = list(models.QuerySet.objects.all())
 
        # post a new query set
        response = self._post('query_sets/',
            data=testsxml.queryset_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.status_code, 200)

        # verify the new query set gets added
        response = self._get('query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        after_db = list(models.QuerySet.objects.all())
       
        # ensure we added something 
        self.assertEqual(len(before_db)+1, len(after_db))

        # the query set we added was
        # "systems with a 3 in it" in our set of 10
        # there are 3 matches
        qs = self._getQs("New Query Set")
        response = self._get("query_sets/%s" % qs,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        systems = self.xobjSystems("query_sets/%s/filtered/" % qs)
        self.assertEquals(len(systems), 38)
        systems = self.xobjSystems("query_sets/%s/child/" % qs)
        self.assertEquals(len(systems), 0)
        systems = self.xobjSystems("query_sets/%s/chosen/" % qs)
        self.assertEquals(len(systems), 0)
        systems = self.xobjSystems("query_sets/%s/all/" % qs)
        self.assertEquals(len(systems), 38)

    def testChosenQuerySets(self):
        # get a query set that would not include a
        # system we're trying to add
        qsid = self._getQs('rPath Update Services')
        
        # get a a system to add
        systems = inventorymodels.System.objects.all()
        system = systems[0]
        response = self._get("inventory/systems/%s" % system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system_xml = response.content
        # show that there are no chosen results yet
        systems = self.xobjSystems("query_sets/%s/chosen/" % qsid)
        self.assertEquals(len(systems), 0)

        # post the system to the chosen result of this queryset
        response = self._post("query_sets/%s/chosen/" % qsid,
            username="admin", password="password",
            data=system_xml)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, system_xml)        

        # retrieve the chosen result of this queryset
        # verify that the system is present
        systems = self.xobjSystems("query_sets/%s/chosen/" % qsid)
        self.assertTrue(systems[0].name, system.name)
        self.assertEquals(len(systems), 1)        
        systems = self.xobjSystems("query_sets/%s/all/" % qsid)
        self.assertEquals(len(systems), 1)
        systems = self.xobjSystems("query_sets/%s/filtered/" % qsid)
        self.assertEquals(len(systems), 1)
        systems = self.xobjSystems("query_sets/%s/child/" % qsid)
        self.assertEquals(len(systems), 0)

    def testBaseQuerySets(self):
        # run through various querysets that ship with the app
        # to make sure they don't explode
        qsid = self._getQs('All Projects')
        response = self._get("query_sets/%s/all/" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        qsid = self._getQs('All Users')
        response = self._get("query_sets/%s/all/" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        qsid = self._getQs('All Project Stages')
        response = self._get("query_sets/%s/all/" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        qsid = self._getQs('All Platforms')
        response = self._get("query_sets/%s/all/" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

