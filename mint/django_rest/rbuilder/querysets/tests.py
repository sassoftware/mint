#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.querysets import testsxml
#from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.querysets import manager as mgr
from xobj import xobj

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

        # favorite queryset view returns what to show in
        # the UI navigation
        response = self._get('favorites/query_sets/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        querySets = xobj.parse(response.content)
        length = len(querySets.favorite_query_sets.query_set)
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
        self.assertXMLEquals(response.content, testsxml.queryset_with_actions,
          ignoreNodes=[
             'filter_entry_id', 'created_date',
             'last_login_date', 'created_by', 'modified_by',
             'tagged_date', 'modified_date', 'is_public', 'is_static',
          ])

        # every queryset should have a "universe" URL that points to the all
        # collection for the given queryset type
        response = self._get("query_sets/%s/universe" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

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

        # verify that asking for 0 results returns 0 results
        # (not this should happen)
        response = self._get("query_sets/%s/all;start_index=0;limit=0" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

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

        # post the queryset AGAIN using the same data
        # to see if we get any duplicate key constraint
        # problems
        response = self._post('query_sets/',
            data=testsxml.queryset_post_xml2,
            username="admin", password="password")
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
       
        # verify the counts are consistent with having a large
        # child set.
        response = self._put("query_sets/%s" % qs1.pk,
            username="admin", password="password", 
            data=testsxml.queryset_put_xml)
        self.assertEquals(response.status_code, 200)

        fetched_qs = models.QuerySet.objects.get(pk=qs1.pk)
        self.assertTrue(fetched_qs.name.find("CHANGED NAME") != -1)
 
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

        # try to add new filter terms on edit
        # without supplying a database ID for them
        # do this TWICE, to make sure we don't get duplicate key errors
        for x in range(0,1):
            response = self._put("query_sets/%s" % qs1.pk,
                username="admin", password="password",
                data=testsxml.queryset_put_xml_different)
            self.assertEquals(response.status_code, 200)

        # removal of child query set
        response = self._delete("query_sets/%s/child" % qs1.pk,
            username="admin", password="password",
            data=testsxml.remove_child_xml)
        self.assertEquals(response.status_code, 200)
        # FIXME: temporarily disabled, call with ignoreNodes including 'actions' ?
        # self.assertXMLEquals(response.content, testsxml.removed_child_xml)

    def testQuerySetWithMissingFilter(self):
        # RCE-1879
        # Create queryset
        response = self._post('query_sets/',
            data=testsxml.queryset_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xobjModel = xobj.parse(response.content)

        qs1 = models.QuerySet.objects.get(
                query_set_id=str(xobjModel.query_set.query_set_id))
        xml = """\
<query_set>
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>name</field>
      <value>jdl</value>
    </filter_entry>
    <filter_entry>
      <field/>
      <operator>EQUAL</operator>
      <value/>
    </filter_entry>
  </filter_entries>
</query_set>
"""
        response = self._put("query_sets/%s" % qs1.pk,
            username="admin", password="password",
            data=xml)
        self.assertEquals(response.status_code, 400)
        xobjModel = xobj.parse(response.content)
        self.assertEquals(xobjModel.fault.message,
                'null value in column "field" violates not-null constraint\nDETAIL:  Failing row contains (21, null, EQUAL, null).\n')

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

        # delete the chosen item
        response = self._delete("query_sets/%s/chosen/" % qsid,
            username="admin", password="password",
            data=system_xml)
        self.assertEquals(response.status_code, 200)
       
        # verify the chosen item is no longer present
        systems = self.xobjSystems("query_sets/%s/chosen/" % qsid)
        # self.assertTrue(systems[0].name, system.name)
        self.assertEquals(len(systems), 0)        
        
        # exercise the very similar "PUT" loop which replaces the chosen
        # collection
        response = self._put("query_sets/%s/chosen/" % qsid,
            username="admin", password="password",
            data=testsxml.system_put_chosen_xml)
        self.assertEquals(response.status_code, 200)
        systems = self.xobjSystems("query_sets/%s/chosen/" % qsid)
        self.assertTrue(systems[0].name, system.name)
        self.assertEquals(len(systems), 1)        

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

    def testGetFilterDescriptor(self):
        # querysets from filter descriptor differ by type of object
        qsid = self._getQs('All Systems')
        response = self._get("query_sets/%s/filter_descriptor/" % qsid,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
                testsxml.queryset_filter_descriptor_xml)

    def testQuerySetUpdateResetsIsStatic(self):
        # RCE-1926
        qsxml = """
<query_set>
  <can_modify>true</can_modify>
  <children/>
  <chosen_members/>
  <config_environments/>
  <description/>
  <filter_entries/>
  <is_top_level>false</is_top_level>
  <name>foobar1</name>
  <resource_type>user</resource_type>
</query_set>
"""
        response = self._post('query_sets/',
            data=qsxml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        childQsId = int(doc.query_set.query_set_id)

        qs = models.QuerySet.objects.get(query_set_id=childQsId)
        self.assertEquals(qs.is_static, True)

        # Add filter_entries
        qsxml = """
<query_set>
  <filter_entries>
    <filter_entry>
      <field>user_name</field>
      <operator>LIKE</operator>
      <value>testuser</value>
    </filter_entry>
  </filter_entries>
</query_set>"""

        response = self._put('query_sets/%s' % qs.query_set_id,
            data=qsxml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        qs = models.QuerySet.objects.get(query_set_id=qs.query_set_id)
        self.assertEquals(qs.filter_entries.count(), 1)
        self.assertEquals(qs.is_static, False)

    def testQuerySetFilteredWrongResource(self):
        # RCE-2070
        qsxml = """
<query_set>
  <name>foobar1</name>
  <resource_type>project_branch_stage</resource_type>
</query_set>
"""
        response = self._post('query_sets/',
            data=qsxml,
            username="admin", password="password")

        doc = xobj.parse(response.content)
        childQsId = int(doc.query_set.query_set_id)

        response = self._get('query_sets/%s/filtered' % childQsId,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.assertEquals(doc.project_branch_stages.full_collection,
                'http://testserver/api/v1/query_sets/%s/filtered' % childQsId)

class ConfigEnvironmentsTestCase(QueryTestCase):

    fixtures = ['system_collection']

    def setUp(self):
        QueryTestCase.setUp(self)

    def testConfigEnvironmentModels(self):
        # show that we can list all query sets

        qs = models.QuerySet.objects.get(pk=1)
        user = usermodels.User.objects.get(pk=1)

        ce = models.ConfigEnvironment(
           name = 'testce',
           created_by = user,
           modified_by = user
           # descriptor = "..."
        )
        ce.save()

        qsce = models.QuerySetConfigEnvironment(
           queryset = qs,
           config_environment = ce,
        )
        qsce.save()

        set1 = models.ConfigEnvironmentSetting(
           config_environment = ce,
           key='http_port',
           value='80'
        )
        set2 = models.ConfigEnvironmentSetting(
           config_environment = ce,
           key='motd',
           value='one does not simply telnet into mordor'
        )
        set1.save()
        set2.save()
         

        # ConfigEnvironmentSetting(...)

        response = self._get("query_sets/%s" % qs.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        
        #querySets = xobj.parse(response.content)
        #length = len(querySets.query_sets.query_set)
        # ok to bump this if we add more QS in the db
        #self.assertEqual(length, 10)
