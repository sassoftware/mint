import base64
import cPickle
import os
import random
from dateutil import tz
from xobj import xobj

from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec

from django.contrib.redirects import models as redirectmodels
from django.db import connection
from django.template import TemplateDoesNotExist

from mint.django_rest import timeutils
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import views
from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.inventory import testsxml
from mint.django_rest.rbuilder.projects import models as projectmodels
from mint.lib import x509
from mint.rest.api import models as restmodels

# from mint.django_rest.rbuilder.rbac.tests import RbacEngine

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class XMLTestCaseStandin(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
    
    def _get(self, url, username=None, password=None, pagination='', *args, **kwargs):
        """
        Handles redirects resulting from rbac requirement that we
        return a query set for resources that are collections.
        The pagination parameter allows us to include an offset and
        limit big enough that our test data will not be truncated.
        """
        # Ugly
        def _parseRedirect(http_redirect):
            redirect_url = http_redirect['Location']
            return redirect_url.split('/api/v1/')[1].strip('/') + pagination

        response = super(XMLTestCaseStandin, self)._get(url, username=username, password=password)
        if str(response.status_code).startswith('3') and response.has_header('Location'):
            new_url = _parseRedirect(response)
            response = XMLTestCaseStandin._get(self, new_url, username=username, password=password)
        return response

class AssimilatorTestCase(XMLTestCaseStandin, test_utils.SmartformMixIn):
    ''' 
    This tests actions as well as the assimilator.  See if we can list the jobs on 
    a system, get the descriptor for spawning that job, and whether we can actually
    start that job.  note: rpath-repeater is mocked, so that will return successful
    job XML even if parameters are insufficient.
    '''

    def setUp(self):
        # make a new system, get ids to use when spawning job
        XMLTestCaseStandin.setUp(self)
        self.system = self.newSystem(name="blinky", description="ghost")
        self.system.management_interface = models.ManagementInterface.objects.get(name='ssh')
        self.mgr.addSystem(self.system)
        self.assimilate = jobmodels.EventType.SYSTEM_ASSIMILATE
        self.event_type = jobmodels.EventType.objects.get(name=self.assimilate)
        self.type_id  = self.event_type.pk
        self.system.save()

        # system needs  a network
        network = models.Network()
        network.dns_name = 'testnetwork.example.com'
        network.system = self.system
        network.save()
        self.system.networks.add(network)
        # system.save not required
        self.system = models.System.objects.get(pk=self.system.pk)
        self.assertTrue(self.mgr.sysMgr.getSystemHasHostInfo(self.system))
        self.setUpSchemaDir()

    def testExpectedActions(self):
        # do we see assimilate as a possible action?
        response = self._get('inventory/systems/%s' % self.system.pk, username="admin",
            password="password")
        obj = xobj.parse(response.content)
        # xobj hack: obj doesn't listify 1 element lists
        # don't break tests if there is only 1 action
        actions = obj.system.actions.action
        if not isinstance(actions, list):
           actions = [actions]
        self.failUnlessEqual([ x.name for x in actions ],
            ['Assimilate system', "system capture"])
        self.failUnlessEqual([ x.description for x in actions ],
            ['Assimilate system', "Capture a system's image"])

    def testFetchActionsDescriptor(self): 
        descriptorType = 'assimilation'
        # can we determine what smartform we need to populate?
        url = "inventory/systems/%s/descriptors/%s" % (self.system.pk, descriptorType)
        response = self._get(url, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.displayName, 'System Assimilation')
        self.failUnlessEqual(obj.descriptor.metadata.descriptions.desc, 'System Assimilation')
        # make sure the same works with parameters
        url = "inventory/systems/%s/descriptors/%s?foo=bar" % (self.system.pk,
            descriptorType)
        response = self._get(url, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.displayName, 'System Assimilation')
        self.failUnlessEqual(obj.descriptor.metadata.descriptions.desc, 'System Assimilation')

    def testSpawnAction(self):
        # can we launch the job>?
        # first make sure SSH managemnet interface credentials are set
        self.assertTrue(self.mgr.sysMgr.getSystemHasHostInfo(self.system))
        response = self._post('inventory/systems/%s/credentials' % \
            self.system.pk,
            data=testsxml.ssh_credentials_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        # now post a barebones job to the systems jobs collection
        url = "inventory/systems/%s/jobs/" % (self.system.pk)
        response = self._post(url, testsxml.system_assimilator_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.content.find("<system_event>") != -1)

class InventoryTestCase(XMLTestCaseStandin):

    def testGetTypes(self):
        response = self._get('inventory/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
        response = self._post('inventory/?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
    def testPostTypes(self):
        response = self._post('inventory/')
        self.assertEquals(response.status_code, 405)
        
    def notestPutTypes(self):
        response = self._put('inventory/')
        self.assertEquals(response.status_code, 405)
        
    def testDeleteTypes(self):
        response = self._delete('inventory/')
        self.assertEquals(response.status_code, 405)

    def testGetTypesNoTrailingSlash(self):
        response = self._get('inventory')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

        response = self._post('inventory?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

class LogTestCase(XMLTestCaseStandin):

    def testGetLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        response = self._get('inventory/log/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/log/', username="testuser", 
            password="password")
        self.assertEquals(response.status_code, 200)

    def testGetLog(self):
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.mgr.addSystem(system)
        system = self.newSystem(name="mgoblue2",
            description="best appliance ever2")
        self.mgr.addSystem(system)
        system = self.newSystem(name="mgoblue3",
            description="best appliance ever3")
        self.mgr.addSystem(system)
        response = self._get('inventory/log/', username="testuser", 
            password="password")
        # Just remove lines with dates in them, it's easier to test for now.
        self.assertXMLEquals(response.content, testsxml.systems_log_xml,
            ignoreNodes = [ 'entry_date' ])

class ZonesTestCase(XMLTestCaseStandin):

    def testGetZones(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        # Create a system, just for kicks
        system = self.newSystem(name="foo", managing_zone=zone)
        system.save()
        response = self._get('inventory/zones/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zones_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date' ])

    def testGetZoneAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveZone()
        response = self._get('inventory/zones/2/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/zones/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetZone(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._get('inventory/zones/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zone_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date' ])
        
    def testAddZoneNodeNull(self):
        
        try:
            self.mgr.addZone(None)
        except:
            assert(False) # should not throw exception
        
    def testAddZone(self):
        zone = self._saveZone()
        new_zone = self.mgr.addZone(zone)
        assert(new_zone is not None)
        
    def testPostZoneAuth(self):
        """
        Ensure we require admin to post zones
        """
        response = self._post('inventory/zones/',
            data= testsxml.zone_post_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._post('inventory/zones/',
            data=testsxml.zone_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPostZone(self):
        zmodels.Zone.objects.all().delete()
        xml = testsxml.zone_post_xml
        response = self._post('inventory/zones/',
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = zmodels.Zone.objects.get(pk=2)
        self.assertXMLEquals(response.content, testsxml.zone_post_response_xml % \
            (zone.created_date.isoformat()))
        
        # test posting a second zone https://issues.rpath.com/browse/RBL-7229
        response = self._post('inventory/zones/',
            data=testsxml.zone_post_2_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zones = zmodels.Zone.objects.all()
        self.assertTrue(len(zones) == 2)
        
    def testPutZoneAuth(self):
        """
        Ensure we require admin to put zones
        """
        zone = zmodels.Zone.objects.get(pk=1)
        response = self._put('inventory/zones/1/', 
            data=testsxml.zone_put_xml % zone.created_date)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('inventory/zones/1/', 
            data=testsxml.zone_put_xml % zone.created_date,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutZoneNotFound(self):
        """
        Ensure we return 404 if we update zone that doesn't exist
        """
        zone = zmodels.Zone.objects.get(pk=1)
        try:
            response = self._put('inventory/zones/1zcvxzvzgvsdzfewrew4t4tga34/', 
                data=testsxml.zone_put_xml % zone.created_date,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))
        
    def testPutZone(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._put('inventory/zones/%d/' % zone.zone_id,
            data=testsxml.zone_put_xml % zone.created_date, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = zmodels.Zone.objects.get(pk=zone.zone_id)
        self.assertTrue(zone.name == "zoneputname")
        self.assertTrue(zone.description == "zoneputdesc")
        
    def testDeleteZoneAuth(self):
        """
        Ensure we require admin to delete zones
        """
        response = self._delete('inventory/zones/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._delete('inventory/zones/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testDeleteZone(self):
        """
        Ensure we can delete zones
        """
        zmodels.Zone.objects.all().delete()
        self._saveZone()
        response = self._delete('inventory/zones/2/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        try:
            zmodels.Zone.objects.get(pk=1)
            self.fail("Lookup should have failed due to deletion")
        except zmodels.Zone.DoesNotExist:
            pass # what we expect
        
class ManagementInterfacesTestCase(XMLTestCaseStandin):

    def testGetManagementInterfaces(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interfaces_xml, ignoreNodes = [ 'created_date', 'modified_by', 'created_by', 'modified_date' ])

    def testGetManagementInterfacesAuth(self):
        """
        Don't require auth or admin
        """
        response = self._get('inventory/management_interfaces/')
        self.assertEquals(response.status_code, 200)
        
        response = self._get('inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementInterface(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('inventory/management_interfaces/%s/' % mi.pk,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interface_xml, ignoreNodes = [ 'created_date', 'modified_by', 'created_by', 'modified_date' ])
        
    def testPutManagementInterfaceAuth(self):
        """
        Ensure we require admin to put
        """
        response = self._put('inventory/management_interfaces/1/', 
            data=testsxml.management_interface_put_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('inventory/management_interfaces/1/', 
            data=testsxml.management_interface_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)

    def testPutManagementInterfaceNotFound(self):
        """
        Ensure we return 404 if we update one that doesn't exist
        """
        try:
            response = self._put('inventory/management_interfaces/1zcvxzvzgvsdzfewrew4t4tga34/', 
                data=testsxml.management_interface_put_xml,
                username="admin", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))
        
    def testPutManagementInterface(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo2", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        self.assertTrue('<name>thisnameshouldnotstick</name>' in testsxml.management_interface_put_xml)
        response = self._put('inventory/management_interfaces/4',
            data=testsxml.management_interface_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        mi = models.ManagementInterface.objects.get(pk=mi.pk)
        # name is read only, should not get changed
        self.assertTrue(mi.name != "thisnameshouldnotstick")
        self.failUnlessEqual(mi.port, 123)
        self.failUnlessEqual(mi.credentials_descriptor, "<foo/>")
        
class SystemTypesTestCase(XMLTestCaseStandin):

    def testGetSystemTypes(self):
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        response = self._get('inventory/system_types/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_types_xml, ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by' ])

    def testGetSystemTypesAuth(self):
        """
        Ensure requires correct auth but is wide open otherwise
        """
        response = self._get('inventory/system_types/',
            username='baduser', password='badpass')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/system_types/')
        self.assertEquals(response.status_code, 200)

        response = self._get('inventory/system_types/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemType(self):
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        response = self._get('inventory/system_types/%s/' % si.pk,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_type_xml, ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date' ])
        
    def testGetSystemTypeSystems(self):
        system = self._saveSystem()
        response = self._get('inventory/system_types/%d/systems/' % \
            system.system_type.system_type_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_type_systems_xml,
            ignoreNodes = [ 'created_date', 'actions',  'created_by', 'modified_by', 'modified_date'])
        
    def testPutSystemTypeAuth(self):
        """
        Ensure we require admin to put
        """
        response = self._put('inventory/system_types/1/', 
            data=testsxml.system_types_put_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('inventory/system_types/1/', 
            data=testsxml.system_types_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def XXXtestPutSystemTypes(self):
        """
        Skipping this test for now, there are problems with PUT support and
        APIReadOnly fields of which name on SystemType is.
        """
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        self.assertTrue('<name>thisnameshouldnotstick</name>' in testsxml.system_types_put_xml)
        response = self._put('inventory/system_types/1',
            data=testsxml.system_types_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        si = models.SystemType.objects.get(pk=si.pk)
        # name is read only, should not get changed
        self.assertTrue(si.name != "thisnameshouldnotstick")
        self.assertTrue(si.infrastructure == True)
        
    def testAddWindowsBuildService(self):
        system = self.mgr.sysMgr.addWindowsBuildService("myname", "mydesc", "1.1.1.1")
        network = self.mgr.sysMgr.extractNetworkToUse(system)
        assert(system.name =="myname")
        assert(system.description == "mydesc")
        assert(system.system_type.name == models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE)
        assert(network.dns_name == "1.1.1.1")
        
    def testGetWindowsBuildServiceNodes(self):
        models.SystemType.objects.all().delete()
        models.SystemType.objects.all().delete()
        st = models.SystemType(name=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE, 
            description=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE_DESC, infrastructure=True,
            creation_descriptor="<foo></foo>")
        st.save()
        system = models.System()
        system.name = 'testsystemname'
        system.description = 'testsystemdescription'
        system.managing_zone = self.localZone
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.system_type = st
        system.save()

        network = models.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()
        
        st2 = models.SystemType(name=models.SystemType.INVENTORY, 
            description=models.SystemType.INVENTORY_DESC, infrastructure=True,
            creation_descriptor="<foo></foo>")
        st2.save()
        
        system2 = models.System()
        system2.name = 'testsystemname2'
        system2.description = 'testsystemdescription2'
        system2.managing_zone = self.localZone
        system2.management_interface = models.ManagementInterface.objects.get(pk=1)
        system2.st = st2
        system2.save()
        
        buildNodes = self.mgr.sysMgr.getWindowsBuildServiceNodes()
        assert(len(buildNodes) == 1)
        assert(buildNodes[0].system_id == system.system_id)
        
    def testGetWindowsBuildServiceNodesEmpty(self):
        models.SystemType.objects.all().delete()
        models.SystemType.objects.all().delete()
        
        buildNodes = self.mgr.sysMgr.getWindowsBuildServiceNodes()
        assert(buildNodes is not None)
        assert(len(buildNodes) == 0)
        
class SystemStatesTestCase(XMLTestCaseStandin):

    def testGetSystemStates(self):
        response = self._get('inventory/system_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_states_xml, 
            ignoreNodes = [ 'created_date' ])

    def testGetSystemState(self):
        response = self._get('inventory/system_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_state_xml, 
            ignoreNodes = [ 'created_date' ])
        
class NetworkTestCase(XMLTestCaseStandin):

    def testGetNetworks(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._get('inventory/networks/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.networks_xml, ignoreNodes = [ 'created_date' ])

    def testGetNetworkAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveSystem()
        response = self._get('inventory/networks/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/networks/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPutNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._put('inventory/networks/1/', 
            data= testsxml.network_put_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('inventory/networks/1/', 
            data=testsxml.network_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutNetworkNotFound(self):
        """
        Ensure we return 404 if we update network that doesn't exist
        """
        try:
            response = self._put('inventory/networks/1zcvxzvzgvsdzfewrew4t4tga34/', 
                data=testsxml.network_put_xml,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))
        
    def testPutNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._put('inventory/networks/2/',
            data=testsxml.network_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        network = models.Network.objects.get(pk=2)
        self.assertTrue(network.dns_name == "new.com")
        self.assertTrue(network.ip_address == "2.2.2.2")
        
    def testDeleteNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._delete('inventory/networks/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._delete('inventory/networks/1/', 
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testDeleteNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        network = models.Network.objects.get(pk=2)
        self.assertTrue(network is not None)
        response = self._delete('inventory/networks/2/', 
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        try:
            network = models.Network.objects.get(pk=1)
            self.assertTrue(False) # should have been deleted
        except models.Network.DoesNotExist:
            pass  #expected

    def testGetNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._get('inventory/networks/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.network_xml, ignoreNodes = [ 'created_date' ])

class ManagementNodesTestCase(XMLTestCaseStandin):

    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        models.ManagementNode.objects.all().delete()

    def testManagementNodeSave(self):
        zone = self._saveZone()
        # make sure state gets set to unmanaged
        management_node = models.ManagementNode(name="mgoblue",
            description="best node ever", zone=zone, managing_zone=zone)
        _eq = self.failUnlessEqual
        _eq(management_node.current_state_id, None)
        management_node.save()
        _eq(management_node.current_state.name, models.SystemState.UNMANAGED)
        
        # make sure we honor the state if set though
        management_node = models.ManagementNode(name="mgoblue", zone=zone,
            description="best node ever",
            current_state=self.mgr.sysMgr.systemState(models.SystemState.DEAD),
            managing_zone=zone)
        management_node.save()
        _eq(management_node.current_state.name, models.SystemState.DEAD)
        
    # -----------------
    def testGetManagementNodes(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_nodes_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                             management_node.current_state.created_date.isoformat(),
                                             management_node.created_date.isoformat()))

    def testPutManagementNodes(self):
        lz = zmodels.Zone.LOCAL_ZONE
        management_node0 = self._saveManagementNode(zoneName=lz)
        self._saveManagementNode(idx=1, zoneName=lz)
        dataTempl = """
<management_nodes>
%s
</management_nodes>"""

        nodeTempl = """<management_node>
<node_jid>%s</node_jid>
<zone_name>%s</zone_name>
</management_node>
"""

        nodeTempl = """<management_node>
<hostname>boo!</hostname>
<node_jid>%(jid)s</node_jid>
<local>%(local)s</local>
<zone><name>%(zoneName)s</name></zone>
<networks><network><ip_address>%(ipAddress)s</ip_address><dns_name>%(ipAddress)s</dns_name><device_name>eth0</device_name></network></networks>
</management_node>
"""


        # Old node in new zone
        # Make sure we don't overwrite the IP address
        nodes = [ dict(jid=management_node0.node_jid, zoneName='new zone 0',
            ipAddress='2.2.2.210', local=False) ]
        # New node in old zone
        nodes.append(dict(jid='node1@host1/node1', zoneName=lz,
            ipAddress='2.2.2.3', local=True))
        # New node in new zone
        nodes.append(dict(jid='node2@host2/node2', zoneName='new zone 2',
            ipAddress='2.2.2.4', local=False))
        # management_node1 is gone

        data = dataTempl % ''.join(nodeTempl % x for x in nodes)
        # First, check that we enforce localhost auth
        response = self._put('inventory/management_nodes',
            headers={'X-rPath-Repeater' : 'does not matter'},
            data=data)
        self.failUnlessEqual(response.status_code, 401)

        # Now a valid PUT
        response = self._put('inventory/management_nodes',
            data=data)
        self.failUnlessEqual(response.status_code, 200)

        obj = xobj.parse(response.content)
        nodes = obj.management_nodes.management_node
        zone0 = zmodels.Zone.objects.get(name='new zone 0')
        zone2 = zmodels.Zone.objects.get(name='new zone 2')
        exp = [(management_node0.node_jid, zone0.zone_id, 'false',
                'test management node', zone0.zone_id,),
            # RBL-7703: this should go away
            ('node01@rbuilder.rpath', management_node0.zone_id, 'true',
                'test management node 01', management_node0.zone_id,),
            ('node1@host1/node1', management_node0.zone_id, 'true',
                'boo!', management_node0.zone_id,),
            ('node2@host2/node2', zone2.zone_id, 'false',
                'boo!', zone2.zone_id,)
        ]
        self.failUnlessEqual(
            [ (str(x.node_jid), int(os.path.basename(x.zone.id)),
                    str(x.local), str(x.name),
                    int(os.path.basename(x.managing_zone.id)))
                for x in nodes ],
            exp)

        node = models.ManagementNode.objects.get(pk=management_node0)
        self.failUnlessEqual(
            [ x.ip_address for x in node.networks.all() ],
            [ '2.2.2.210' ])

        node = models.ManagementNode.objects.get(node_jid='node1@host1/node1')
        self.failUnlessEqual(
            [ x.ip_address for x in node.networks.all() ],
            [ '2.2.2.3' ])

    def testGetManagementNodeAuth(self):
        """
        Ensure requires auth but not admin
        """
        node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/%s/' % node.system_ptr_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/management_nodes/%s/' % node.system_ptr_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNode(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/%s/' % management_node.system_ptr_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_node_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                            management_node.current_state.created_date.isoformat(), 
                                            management_node.created_date.isoformat()))
        
    def testAddManagementNode(self):
        management_node = self._saveManagementNode()
        new_management_node = self.mgr.addManagementNode(management_node)
        assert(new_management_node is not None)
        assert(new_management_node.local)
        type = models.SystemType.objects.get(name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        assert(new_management_node.type == type)
        
    def testPostManagementNodeAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        response = self._post('inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._post('inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
        response = self._post('inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostManagementNode(self):
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        xml = testsxml.management_node_post_xml
        response = self._post('inventory/management_nodes/',
            data=xml, content_type='text/xml', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=3)
        management_node_xml = testsxml.management_node_post_response_xml.replace(
            '<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (management_node.registration_date.isoformat()))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.networks.all()[0].created_date.isoformat(), 
             management_node.current_state.created_date.isoformat(),
             management_node.created_date.isoformat()))
        
    def testGetManagementNodesForZone(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/' % management_node.zone.zone_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_nodes_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                             management_node.current_state.created_date.isoformat(),
                                             management_node.created_date.isoformat()))

    def testGetManagementNodeForZoneAuth(self):
        """
        Ensure quires auth but not admin
        """
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id))
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id),
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNodeForZone(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id),
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_node_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                            management_node.current_state.created_date.isoformat(), 
                                            management_node.created_date.isoformat()))
        
    def testAddManagementNodeForZoneNull(self):
        
        try:
            # create the system
            managementNode = None
            self.mgr.addManagementNodeForZone(None, managementNode)
        except:
            assert(False) # should not throw exception
        
    def testAddManagementNodeForZone(self):
        management_node = self._saveManagementNode()
        new_management_node = self.mgr.addManagementNodeForZone(management_node.zone.zone_id, management_node)
        assert(new_management_node is not None)
        assert(new_management_node.local)
        assert(management_node.type == models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE))
        
    def testAddManagementNodeSave(self):
        management_node = self._saveManagementNode()
        management_node.system_type = models.SystemType.objects.get(
            name = models.SystemType.INVENTORY)
        # now save, which should automatically set management_node
        management_node.save()
        assert(management_node.system_type == models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE))
        
    def testPostManagementNodeForZoneAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostManagementNodeForZone(self):
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        xml = testsxml.management_node_zone_post_xml
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=3)
        management_node_xml = testsxml.management_node_zone_post_response_xml.replace(
            '<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (management_node.registration_date.isoformat()))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.networks.all()[0].created_date.isoformat(), 
             management_node.current_state.created_date.isoformat(),
             management_node.created_date.isoformat()))

class NetworksTestCase(XMLTestCaseStandin):

    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        self.system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.system.save()
        
    def testExtractNetworkToUse(self):
        
        # try a net with no pinned/active nets, but only one net
        network = models.Network(dns_name="foo.com", active=False, pinned=False)
        network.system = self.system
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # Second network showed up, we assume no network
        network2 = models.Network(dns_name = "foo2.com", active=False,
            pinned=False)
        network2.system = self.system
        network2.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net, None)

        # try one with pinned only
        network.pinned = True
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # try one with active only
        network.pinned = False
        network.active = True
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # now add a pinned one in addition to active one to test order
        network3 = models.Network(dns_name="foo3.com", active=False, pinned=True)
        network3.system = self.system
        network3.save()
        self.failUnlessEqual(
            sorted((x.dns_name, x.pinned, x.active)
                for x in self.system.networks.all()),
            [
                ('foo.com', False, True),
                ('foo2.com', False, False),
                ('foo3.com', True, False),
            ])
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.network_id, network3.network_id)

class SystemsTestCase(XMLTestCaseStandin):
    fixtures = ['system_job', 'targets']

    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        self.mock_scheduleSystemRegistrationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mockGetRmakeJob_called = False
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = False
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr.scheduleSystemRegistrationEvent = self.mock_scheduleSystemRegistrationEvent
        self.mgr.sysMgr.scheduleSystemDetectMgmtInterfaceEvent = \
            self.mock_scheduleSystemDetectMgmtInterfaceEvent
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob

    def tearDown(self):
        XMLTestCaseStandin.tearDown(self)

    def mock_scheduleSystemRegistrationEvent(self, system):
        self.mock_scheduleSystemRegistrationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
        
    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def mock_scheduleSystemDetectMgmtInterfaceEvent(self, system):
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = True

    def testSystemPutAuth(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid)

        system = self.newSystem(name="blah")
        system.save()

        system2 = self.newSystem(name="blip")
        system2.save()

        self._newSystemJob(system, eventUuid, 'rmakejob007',
            jobmodels.EventType.SYSTEM_REGISTRATION)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
</system>
"""
        # No event uuid, no auth; this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params)
        self.failUnlessEqual(response.status_code, 401)

        # Bad event uuid; this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid + '-bogus'})
        self.failUnlessEqual(response.status_code, 401)

        # Good uuid, bad system
        response = self._put('inventory/systems/%s' % system2.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid validation, this works
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid },
            username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)

        # user/pass auth, this works
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)

        # uuid valid, bad auth - this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='bogus',
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid bad, goodauth - this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='admin', password='password',
            headers = { 'X-rBuilder-Event-UUID' : eventUuid + '-bogus' })
        self.failUnlessEqual(response.status_code, 401)

    def testSystemMothballAuth(self):
        """
        Ensure admin users can mothball systems https://issues.rpath.com/browse/RBL-7170
        """
        
        # TODO:  This test will fail until https://issues.rpath.com/browse/RBL-7172
        # is fixed, please to do remove it!
        
        models.System.objects.all().delete()
        system = self._saveSystem()
        
        # fail if anon
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml)
        self.failUnlessEqual(response.status_code, 401)
        
        # fail if regular user
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml,
            username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 401)

    def testSystemMothball(self):
        """
        Ensure admin users can mothball systems https://issues.rpath.com/browse/RBL-7170
        """
        models.System.objects.all().delete()
        system = self._saveSystem()
        # work if admin
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.system_id)
        self.assertTrue(system.current_state.name == models.SystemState.MOTHBALLED)
        self.assertTrue(system.current_state.description == models.SystemState.MOTHBALLED_DESC)

    def testBulkSystemAdd(self):
        xmlTempl = """\
  <system>
    <name>%(name)s</name>
    <description>%(name)s</description>
    <networks>
      <network>
        <device_name>eth0</device_name>
        <dns_name>%(dnsName)s</dns_name>
      </network>
    </networks>
    <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
  </system>
"""
        systems = []
        for i in range(10):
            params = dict(name="name %03d" % i,
                description="description %03d" % i,
                dnsName="dns-name-%03d" % i,
                zoneId=self.localZone.zone_id)
            systems.append(xmlTempl % params)
        xml = "<systems>" + ''.join(systems) + "</systems>"
        url = "inventory/systems"
        response = self._post(url, data=xml, username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)


    def testSystemSave(self):
        # make sure state gets set to unmanaged
        system = self.newSystem(name="mgoblue", 
            description="best appliance ever")
        _eq = self.failUnlessEqual
        _eq(system.current_state_id, None)
        system.save()
        _eq(system.current_state.name, models.SystemState.UNMANAGED)
        
        # make sure we honor the state if set though
        system = self.newSystem(name="mgoblue", 
            description="best appliance ever",
            current_state=self.mgr.sysMgr.systemState(models.SystemState.DEAD))
        system.save()
        _eq(system.current_state.name, models.SystemState.DEAD)
        
        # test name fallback to hostname
        system = self.newSystem(hostname="mgoblue", 
            description="best appliance ever")
        self.failUnlessEqual(system.name, '')
        system.save()
        self.failUnlessEqual(system.name, system.hostname)
        
        # test name fallback to blank
        system = self.newSystem(description="best appliance ever")
        self.failUnlessEqual(system.name, '')
        system.save()
        self.failUnlessEqual(system.name, '')
        
        # make sure we honor the name if set though
        system = self.newSystem(name="mgoblue")
        system.save()
        self.failUnlessEqual(system.name, "mgoblue")
        
    def testSystemSaveAgentPort(self):
        # make sure state gets set to unmanaged
        system = self.newSystem(name="mgoblue", 
            description="best appliance ever")
        self.assertTrue(system.agent_port is None)
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.save()
        self.assertTrue(system.agent_port == system.management_interface.port)
        
        system.agent_port = 897
        system.save()
        self.assertTrue(system.agent_port == 897)
        
        system = self.newSystem(name="mgoblue2", 
            description="best appliance ever")
        system.save()
        self.assertTrue(system.agent_port is None)
        
    def testAddSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.UNMANAGED)
        
        # make sure we scheduled our registration event
        assert(self.mock_scheduleSystemDetectMgmtInterfaceEvent_called)
        
    def testAddRegisteredSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            local_uuid='123', generated_uuid='456')
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.REGISTERED)
        
        # make sure we did not schedule registration
        self.failUnlessEqual(self.mock_scheduleSystemRegistrationEvent_called,
            False)
        
        # make sure we scheduled poll event
        assert(self.mock_scheduleSystemPollEvent_called)
        
    def testAddRegisteredManagementNodeSystem(self):
        zone = self._saveZone()
        system_type = models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            system_type=system_type,
            local_uuid='123', generated_uuid='456')
        system.zone = zone
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.REGISTERED)
        
        # make sure we did not schedule registration
        self.failUnlessEqual(self.mock_scheduleSystemRegistrationEvent_called,
            False)
        
        # make sure we did not scheduled poll event since this is a management node and they are managed now
        self.failUnlessEqual(self.mock_scheduleSystemPollEvent_called, False)
        
    def testAddSystemNull(self):
        
        try:
            # create the system
            system = None
            self.mgr.addSystem(system)
        except:
            assert(False) # should not throw exception
            
    def testAddSystemNoNetwork(self):
        """
        Ensure a network is not pinned per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system = self.newSystem(name="foo", description="bar")
        self.mgr.addSystem(system)

    def testPostSystemNoNetwork(self):
        """
        Ensure a network is not pinned per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_no_network_xml
        # Also exercise RBL-8919
        response = self._post('inventory//systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        try:
            models.System.objects.get(pk=3)
        except models.System.DoesNotExist:
            self.assertTrue(False) # should exist

    def testPostSystemNetworkUnpinned(self):
        """
        Unpinned network_address
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_network_unpinned
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "1.2.3.4")
        self.failUnlessEqual(x.system.network_address.pinned, "False")

    def testPostSystemNetworkPinned(self):
        """
        Pinned network_address
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_network_pinned
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, True, ), ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "1.2.3.4")
        self.failUnlessEqual(x.system.network_address.pinned, "True")

    def testPutSystemNetworkUnpinned(self):
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb")
        system.save()
        # No networks initially
        self.failUnlessEqual(list(system.networks.all()), [])

        xml_data = testsxml.system_post_network_unpinned
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

        system = models.System.objects.get(pk=system.pk)

        # Add a bunch of network addresses, none of them pinned
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

        # Add a bunch of network addresses, none of them pinned
        # Pretend the active interface is the same as the one the client
        # specified.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('blah1', '1.2.3.4', True, False, ),
              ('blah2', '10.2.2.2', False, False, ) ])

        # Add a bunch of network addresses, one of them pinned.
        # We should unpin in this case.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=True, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

    def testPutSystemNetworkPinned(self):
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb")
        system.save()
        # No networks initially
        self.failUnlessEqual(list(system.networks.all()), [])

        xml_data = testsxml.system_post_network_pinned
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, True, ), ])

        system = models.System.objects.get(pk=system.pk)

        # Add a bunch of network addresses, none of them pinned
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [
                ('blah1', '10.1.1.1', True, False),
                ('blah2', '10.2.2.2', False, False),
                ('1.2.3.4', None, None, True),
            ])

        # Add a bunch of network addresses, none of them pinned
        # Pretend the active interface is the same as the one the client
        # specified.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [
                ('blah1', '1.2.3.4', True, False),
                ('blah2', '10.2.2.2', False, False),
                ('1.2.3.4', None, None, True),
            ])

        # Add a bunch of network addresses, one of them pinned.
        # We should unpin in this case.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=True, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('blah1', '1.2.3.4', False, True, ),
              ('blah2', '10.2.2.2', True, False, ) ])

    def testPostSystemNetworkPreservePinned(self):
        """
        Pinned network_address
        """
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <networks>
    <network>
      <active>false</active>
      <device_name>eth0</device_name>
      <dns_name>10.1.1.1</dns_name>
      <ip_address>10.1.1.1</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
    <network>
      <active>true</active>
      <device_name>eth1</device_name>
      <dns_name>blah2.example.com</dns_name>
      <ip_address>10.2.2.2</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()

        # Add a bunch of network addresses, one of them pinned.
        # We should preserve the pinned one
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='ignoreme',
            active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2.example.com',
            ip_address='10.2.2.2', netmask='255.255.255.0',
            active=True, pinned=False, device_name='eth0')
        network.save()

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [
                ('blah2.example.com', '10.2.2.2', True, False, ),
                ('10.1.1.1', '10.1.1.1', False, None, ),
                ('blah1', None, None, True, ),
            ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "blah1")
        self.failUnlessEqual(x.system.network_address.pinned, "True")

    def testGetSystems(self):
        system = self._saveSystem()
        response = self._get('inventory/systems/', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.systems_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by' ])
        response = self._get('inventory/systems', username='testuser', password='password')
        self.assertEquals(response.status_code, 403)
        
    def testGetSystemAuth(self):
        """
        Ensure requires auth but not admin
        """
        system = self._saveSystem()
        response = self._get('inventory/systems/%d/' % system.system_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/systems/%d/' % system.system_id,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 403)
        
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testGetSystemDoesntExist(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('inventory/systems/86753021/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 404)

    def testGetSystem(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by', 'time_created', 'time_updated' ])

    def testDeleteSystemDoesNotExist(self):
        # deleting a system that doesn't exist should be a 404, not an error
        models.System.objects.all().delete()
        response = self._delete('inventory/systems/%d/' % 42,
            username="admin", password="password")
        self.assertEquals(response.status_code, 404)

    def testGetSystemWithTarget(self):
        models.System.objects.all().delete()
        targetType = targetmodels.TargetType.objects.get(name='vmware')
        target = targetmodels.Target(target_type=targetType,
            name='testtargetname', description='testtargetdescription',
            state=targetmodels.Target.States.OPERATIONAL,
            zone=self.localZone)
        target.save()
        system = self._saveSystem()
        system.target = target
        system.save()
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_target_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by', 'time_created', 'time_updated' ])
        
    def testPostSystemAuth(self):
        """
        Ensure wide open for rpath-tools usage
        """
        system_xml = testsxml.system_post_xml
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostSystem(self):
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        system_xml = testsxml.system_post_xml_response.replace('<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (system.registration_date.isoformat()))
        self.assertXMLEquals(response.content, system_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'ssl_client_certificate',
                            'time_created', 'time_updated',
                            'registration_date', 'actions', 
                            'created_by', 'modified_by',
                            'created_date', 'modified_date'])

    def testPostSystemThroughManagementNode(self):
        # Send the identity of the management node
        models.System.objects.all().delete()
        self._saveManagementNode()
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
</system>
"""
        zoneName = base64.b64encode(self.localZone.name)
        response = self._post('inventory/systems/',
            data=xmlTempl % params,
            headers={ 'X-rPath-Management-Zone' : zoneName },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

    def testPostSystemDupUuid(self):
        # add the first system
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml_dup
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(system.name, "testsystemname")
        
        # add it with same uuids but with different name to make sure
        # we get back same system with updated prop
        system_xml = testsxml.system_post_xml_dup2
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        this_system = models.System.objects.get(pk=3)
        self.failUnlessEqual(this_system.name, "testsystemnameChanged")

    def testPutSystemManagementInterface(self):
        system = self._saveSystem()

        # Test that a mgmt interface can be changed.
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # Test that a mgmt interface can be added.
        system.management_interface = None
        system.save()
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # Test that mgmt interface can be deleted
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_delete_mgmt_interface_put_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface, None)

    def testSystemCredentials(self):
        system = self._saveSystem()
        response = self._post('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.credentials_resp_xml)

        response = self._get('inventory/systems/%s/credentials' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.credentials_resp_xml)

        response = self._put('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.credentials_put_resp_xml)

        system = models.System.objects.get(pk=system.pk)

        creds = system.credentials
        # Do a simple PUT on systems
        xml = """\
<system>
  <credentials>blahblah</credentials>
</system>
"""
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.credentials, creds)

    def testSystemWmiCredentials(self):
        system = self._saveSystem()
        system.management_interface = models.ManagementInterface.objects.get(name='wmi')
        system.save()
        response = self._post('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_wmi_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.credentials_wmi_resp_xml)

        response = self._get('inventory/systems/%s/credentials' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.credentials_wmi_resp_xml)

        response = self._put('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_wmi_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.credentials_wmi_put_resp_xml)
        
    def testSystemConfiguration(self):
        system = self._saveSystem()
        response = self._post('inventory/systems/%s/configuration' % \
            system.pk,
            data=testsxml.configuration_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.configuration_post_resp_xml)

        response = self._get('inventory/systems/%s/configuration' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.configuration_post_resp_xml)

        response = self._put('inventory/systems/%s/configuration' % \
            system.pk,
            data=testsxml.configuration_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.configuration_put_resp_xml)
        
    def _getSystemConfigurationDescriptor(self, system_id):
        return testsxml.configuration_descriptor_xml
        
    def testSystemConfigurationDescriptor(self):
        ### Disabling this test until the code is in place and working.
        return

        system = self._saveSystem()
        
        self.mgr.sysMgr.getSystemConfigurationDescriptor = self._getSystemConfigurationDescriptor(system.pk)

        response = self._get('inventory/systems/%s/configuration_descriptor' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.configuration_descriptor_xml)

    def testGetSystemLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        models.System.objects.all().delete()
        response = self._post('inventory/systems/',
            data=testsxml.system_post_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        response = self._get('inventory/systems/3/system_log/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/systems/3/system_log/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        response = self._get('inventory/systems/3/system_log/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)
        

    def testGetSystemLog(self):
        models.System.objects.all().delete()
        response = self._post('inventory/systems/', 
            data=testsxml.system_post_xml)
        self.assertEquals(response.status_code, 200)
        response = self._get('inventory/systems/3/system_log/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        content = []
        # Just remove lines with dates in them, it's easier to test for now.
        for line in response.content.split('\n'):
            if 'entry_date' in line or \
               'will be enabled on' in line:
                continue
            else:
                content.append(line)
        self.assertXMLEquals('\n'.join(content), testsxml.system_log_xml)
        
    def testGetSystemHasHostInfo(self):
        system = self.newSystem(name="mgoblue")
        system.save()
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system) == False)
        
        network = models.Network(system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system) == False)
        
        network2 = models.Network(ip_address="1.1.1.1", system=system)
        network2.save()
        system.networks.add(network2)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))
        
        network2.delete()
        network = models.Network(ipv6_address="1.1.1.1", system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))
        
        network.delete()
        network = models.Network(dns_name="foo.bar.com", system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))

    def testDedupByBootUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        bootUuid = 'eventuuid001'
        targetSystemId = 'target-system-id-001'

        # Create 2 systems with differnt target_system_id, just like ec2 would
        # if you asked it to launch 2 instances
        system = self.newSystem(name="blah", target_system_id=targetSystemId)
        system.save()

        system2 = self.newSystem(name="blah2",
            target_system_id=targetSystemId.replace('001', '002'))
        system2.save()

        # Create a job
        cu = connection.cursor()
        now = self.mgr.sysMgr.now()
        cu.execute("""
            INSERT INTO jobs (job_uuid, job_type_id, job_state_id, created_by,
                created, modified)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            [ bootUuid, 1, 1, 1, now, now])
        jobId = cu.lastrowid

        # Pretend that this job launched 2 systems (the way ec2 can do)
        cu.execute("INSERT INTO job_system (job_id, system_id) VALUES (%s, %s)",
            [ jobId, system.pk ])
        cu.execute("INSERT INTO job_system (job_id, system_id) VALUES (%s, %s)",
            [ jobId, system2.pk ])

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            bootUuid=bootUuid, targetSystemId=targetSystemId)

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <boot_uuid>%(bootUuid)s</boot_uuid>
  <target_system_id>%(targetSystemId)s</target_system_id>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.boot_uuid, bootUuid)
        self.failUnlessEqual(model.pk, system.pk)
        self.failUnlessEqual(model.target_system_id, targetSystemId)

    def testLoadFromObjectEventUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.event_uuid, eventUuid)

    def testDedupByEventUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        # Create a system with just a name
        system = self.newSystem(name = 'blippy')
        system.save()
        # Create a job
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        # We should have loaded the old one
        self.failUnlessEqual(system.pk, model.pk)
        self.failUnlessEqual(model.name, 'blippy')
        # Catch the case of synthetic fields not being converted to
        # unicode (xobj types confuse database drivers)
        self.failUnlessEqual(type(model.event_uuid), unicode)

    def testDedupByEventUuidWithRemoval1(self):
        system, systemRemoved = self._testDedupByEventUuidWithRemoval(targetSystemFirst=False)
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                '(copied) Log message from target system',
                'Log message from empty system'
            ])

    def testDedupByEventUuidWithRemoval2(self):
        system, systemRemoved = self._testDedupByEventUuidWithRemoval(targetSystemFirst=True)
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                '(copied) Log message from empty system',
                'Log message from target system',
            ])

    def _newEmptySystem(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        # Create the system, pretending it's registered
        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()
        self.mgr.sysMgr.log_system(system, "Log message from empty system")
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        return system, params

    def _testDedupByEventUuidWithRemoval(self, targetSystemFirst=False):
        eventUuid = 'eventuuid001'

        if not targetSystemFirst:
            system0, params = self._newEmptySystem()

        # Create a target system
        targetSystemId = 'systemid-001'
        targetSystemName = 'target system name 001'
        targetSystemDescription = 'target system description 001'
        targetSystemState = "Obflusterating"
        tgt1 = targetmodels.Target.objects.get(pk=1) # vsphere1
        system1 = self.newSystem(name="bloppy", target=tgt1,
            target_system_id=targetSystemId,
            target_system_name=targetSystemName,
            target_system_description=targetSystemDescription,
            target_system_state=targetSystemState)
        system1.save()
        self.mgr.sysMgr.log_system(system1, "Log message from target system")

        # Create a job
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system1, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        if targetSystemFirst:
            system0, params = self._newEmptySystem()

        params.update(eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)

        # We should have loaded the old one
        self.failUnlessEqual(model.pk, system0.pk)
        self.failUnlessEqual(model.name, 'blippy')
        self.failUnlessEqual(model.event_uuid, eventUuid)

        self.mgr.sysMgr.mergeSystems(model)

        systemToKeep, systemRemoved = sorted([ system0, system1 ],
            key = lambda x: x.pk)
        systemRemovedUrl = systemRemoved.get_absolute_url()
        system = models.System.objects.get(pk=systemToKeep.pk)

        # At this point, properties from system1 should have copied over
        self.failUnlessEqual(system.target.pk, tgt1.pk)
        self.failUnlessEqual(system.target_system_id, targetSystemId)
        self.failUnlessEqual(system.target_system_name, targetSystemName)
        self.failUnlessEqual(system.target_system_description, targetSystemDescription)
        self.failUnlessEqual(system.target_system_state, targetSystemState)
        self.failUnlessEqual(system.local_uuid, params['localUuid'])
        self.failUnlessEqual(system.generated_uuid, params['generatedUuid'])

        # The other system should be gone
        self.failUnlessEqual(list(models.System.objects.filter(
            pk=systemRemoved.pk)),
            [])

        # A redirect should have been created
        redirect = redirectmodels.Redirect.objects.filter(
            new_path=systemToKeep.get_absolute_url(),
            old_path=systemRemovedUrl)
        self.assertEquals(len(redirect), 1)

        return system, systemRemoved

    def testCurrentStateUpdateApi(self):
        # Make sure current state can be updated via the API.  This allows
        # users to mothball systems at any point in time, etc.
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>10</system_state_id>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)
        self.failUnlessEqual(model.current_state.name, "mothballed")

    def testUpdateCurrentState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        jobState = "Completed"
        jobUuid = 'rmakeuuid001'
        statusCode = 291
        statusText = "text 291"
        statusDetail = "detail 291"

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        # Create a job
        eventType = jobmodels.EventType.objects.get(
            name = jobmodels.EventType.SYSTEM_POLL)
        job = jobmodels.Job(job_uuid=jobUuid, job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        # Pass bogus event uuid, we should not update
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid + "bogus", jobUuid=jobUuid + "bogus",
            jobState=jobState, zoneId=self.localZone.zone_id,
            statusCode=statusCode, statusText=statusText,
            statusDetail=statusDetail)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
      <status_code>%(statusCode)s</status_code>
      <status_text>%(statusText)s</status_text>
      <status_detail>%(statusDetail)s</status_detail>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        from mint.django_rest.rbuilder import modellib
        model = models.System.objects.load_from_object(xobjmodel, request=None,
            flags=modellib.Flags(save=False))
        self.failUnlessEqual(model.pk, system.pk)

        # We expect nothing to be updated, since there's no such job
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set jobUuid to be correct
        params['jobUuid'] = jobUuid
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        # We still expect nothing to be updated, since the event_uuid is wrong
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set eventUuid to be correct
        params['eventUuid'] = eventUuid
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)
        self.failUnlessEqual(job.status_code, statusCode)
        self.failUnlessEqual(job.status_text, statusText)
        self.failUnlessEqual(job.status_detail, statusDetail)

        # Make sure that pasting a system job with just the event uuid and job
        # info works (i.e. without the local and generated uuids)
        xmlTempl = """\
<system>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
      <status_code>%(statusCode)s</status_code>
      <status_text>%(statusText)s</status_text>
      <status_detail>%(statusDetail)s</status_detail>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        jobState = 'Failed'
        params['jobState'] = jobState
        statusCode = params['statusCode'] = 432
        statusText = params['statusText'] = "status text 432"
        statusDetail = params['statusDetail'] = "status detail 432"

        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)
        self.failUnlessEqual(job.status_code, statusCode)
        self.failUnlessEqual(job.status_text, statusText)
        self.failUnlessEqual(job.status_detail, statusDetail)

    def testLoadFromObjectHiddenFields(self):
        # Make sure one can't overwrite hidden fields (sslClientKey is hidden)
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        sslClientCert = 'sslClientCert'
        sslClientKey = 'sslClientKey'

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            zoneId=self.localZone.zone_id)

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid,
            ssl_client_certificate=sslClientCert,
            ssl_client_key=sslClientKey)
        system.save()

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <ssl_client_certificate>thou shalt not change me</ssl_client_certificate>
  <ssl_client_key>thou shalt not change me</ssl_client_key>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.ssl_client_certificate, sslClientCert)
        self.failUnlessEqual(model.ssl_client_key, sslClientKey)

    def testBooleanFieldSerialization(self):
        # XML schema sez lowercase true or false for boolean fields
        system = self.newSystem(name = 'blippy')
        system.save()
        network = models.Network(dns_name="foo3.com", ip_address='1.2.3.4',
            active=False, pinned=True, system=system)
        network.save()
        xml = network.to_xml()
        self.failUnlessIn("<active>false</active>", xml)
        self.failUnlessIn("<pinned>true</pinned>", xml)

    def testScheduleImmediatePollAfterRegistration(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        # Create a system with just a name
        system = self.newSystem(name = 'blippy')
        system.save()
        # Create a job
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        response = self._post('inventory/systems', data=xml)
        self.failUnlessEqual(response.status_code, 200)

        # Look up log entries
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                "Unable to create event 'On-demand system synchronization': no networking information",
                "Unable to create event 'System synchronization': no networking information",
            ])

    def testAgentPort(self):
        # RBL-7150
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        agentPort = 12345
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            agentPort=agentPort, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <agent_port>%(agentPort)s</agent_port>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.agent_port, agentPort)
        self.failUnlessIn("<agent_port>%s</agent_port>" % agentPort,
            model.to_xml())

    def testSetSystemState(self):
        # RBL-6795
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        systemState = 'dead'

        system = self.newSystem(name='blah', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            systemState=systemState, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <name>%(systemState)s</name>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.current_state.name, systemState)

    def testPutShouldUpdateExisting(self):
        # Make sure that, if we PUT data to a system, we're updating exactly
        # the one specified in the URL - RBL-7182
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        systemState = 'dead'

        system = self.newSystem(name='blah')
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            systemState=systemState, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <name>%(systemState)s</name>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.local_uuid, localUuid)
        self.failUnlessEqual(system.generated_uuid, generatedUuid)
        self.failUnlessEqual(system.current_state.name, systemState)

    def testSetSystemManagementInterface(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        agentPort = 8675309

        managementInterface = models.Cache.get(models.ManagementInterface,
            name="wmi")
        managementInterfaceId = managementInterface.pk

        system = self.newSystem(name='blah', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        self.failUnlessEqual(system.management_interface_id, None)

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            agentPort=agentPort,
            managementInterfaceId=managementInterfaceId)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <management_interface href="/api/v1/inventory/management_interfaces/%(managementInterfaceId)s"/>
  <agent_port>%(agentPort)s</agent_port>
</system>
""" % params

        """
  <management_interface>
    <name>%(managementInterfaceName)s</name>
  </management_interface>
        """

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.management_interface_id,
            managementInterfaceId)
        self.failUnlessEqual(system.agent_port, agentPort)

    def testGetCredentialsWhenMissing(self):
        system = self.newSystem(name="blah")
        system.save()
        creds = self.mgr.getSystemCredentials(system.pk)
        self.assertXMLEquals(creds.to_xml(),
            '<credentials id="/api/v1/inventory/systems/%s/credentials"/>' %
                system.pk)
        
    def testGetConfigurationWhenMissing(self):
        system = self.newSystem(name="blah")
        system.save()
        config = self.mgr.getSystemConfiguration(system.pk)
        self.assertXMLEquals(config.to_xml(),
            '<configuration id="/api/v1/inventory/systems/%s/configuration"/>' %
                system.pk)

    def testMarkSystemShutdown(self):
        p = dict(local_uuid="abc", generated_uuid="def")
        system = self.newSystem(name="blah", **p)
        system.save()

        p.update(currentState = "non-responsive-shutdown")

        url = 'inventory/systems'
        xml = """
<system>
  <local_uuid>%(local_uuid)s</local_uuid>
  <generated_uuid>%(generated_uuid)s</generated_uuid>
  <current_state><name>%(currentState)s</name></current_state>
</system>
"""
        response = self._post(url, data=xml % p)
        self.failUnlessEqual(response.status_code, 200)

        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.current_state.name,
            p['currentState'])

    def testAddSystemsSameGeneratedUuid(self):
        # RBL-8211 - get rid of unnecessary unique constraint on generated_uuid
        guuid = "some-uuid"
        luuid1 = "localuuid001"
        luuid2 = "localuuid002"
        system1 = self.newSystem(local_uuid=luuid1, generated_uuid=guuid)
        system1.save()
        system2 = self.newSystem(local_uuid=luuid2, generated_uuid=guuid)
        system2.save()

        system1 = models.System.objects.get(local_uuid=luuid1,
            generated_uuid=guuid)
        system2 = models.System.objects.get(local_uuid=luuid2,
            generated_uuid=guuid)
        self.failIf(system1.pk == system2.pk)

class SystemCertificateTestCase(XMLTestCaseStandin):
    def testGenerateSystemCertificates(self):
        system = self.newSystem(local_uuid="localuuid001",
            generated_uuid="generateduuid001")
        system.save()
        self.failUnlessEqual(system.ssl_client_certificate, None)
        self.failUnlessEqual(system.ssl_client_key, None)
        self.mgr.sysMgr.generateSystemCertificates(system)

        clientCert = system.ssl_client_certificate
        clientKey = system.ssl_client_key

        crt = x509.X509(None, None)
        crt.load_from_strings(clientCert, clientKey)
        self.failUnlessEqual(crt.x509.get_subject().as_text(),
            'O=rPath rBuilder, OU=http://rpath.com, CN=local_uuid:localuuid001 generated_uuid:generateduuid001 serial:0')
        # Make sure the cert is signed with the low grade CA
        issuer = 'O=rBuilder Low-Grade Certificate Authority, OU=Created at 2010-09-02 11:18:53-0400'
        # We're using self-signed certs
        issuer = 'O=rPath rBuilder, OU=http://rpath.com, CN=local_uuid:localuuid001 generated_uuid:generateduuid001 serial:0'

        self.failUnlessEqual(crt.x509.get_issuer().as_text(), issuer)
        # Test some of the other functions, while we're at it
        fingerprint = crt.fingerprint
        self.failUnlessEqual(len(fingerprint), 40)

        certHash = crt.hash
        # This always changes, so no point in comparing anything other than
        # length
        self.failUnlessEqual(len(certHash), 8)

        # The issuer hash is always known, since it's our LG CA
        #self.failUnlessEqual(crt.hash_issuer, '6d8bb0a1')
        self.failUnlessEqual(crt.hash_issuer, certHash)

        # Try again, we should not re-generate the cert
        self.mgr.sysMgr.generateSystemCertificates(system)
        self.failUnlessEqual(system.ssl_client_certificate, clientCert)
        self.failUnlessEqual(system.ssl_client_key, clientKey)

class SystemStateTestCase(XMLTestCaseStandin):
    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob
    
    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testSetCurrentState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        jobState = "Completed"

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'

        system = self.newSystem(name='blippy')
        system.save()

        self._newSystemJob(system, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_REGISTRATION)

        params = dict(eventUuid=eventUuid1, jobUuid=jobUuid1, jobState=jobState,
            zoneId=self.localZone.zone_id)

        xmlTempl = """\
<system>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, headers = { 'X-rBuilder-Event-UUID' : eventUuid1 },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        system2 = models.System.objects.get(pk=system.pk)
        # Just because the job completed, it doesn't mean the registration
        # succeeded
        self.failUnlessEqual(system2.current_state.name,
            models.SystemState.UNMANAGED)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')
        self.failUnlessEqual([ x.entry for x in logEntries ],
            [
            ])

        # poll event
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        self._newSystemJob(system, eventUuid2, jobUuid2,
            jobmodels.EventType.SYSTEM_POLL)

        params = dict(eventUuid=eventUuid2, jobUuid=jobUuid2, jobState=jobState,
            zoneId=self.localZone.zone_id)

        xml = xmlTempl % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, headers = { 'X-rBuilder-Event-UUID' : eventUuid1 },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        system2 = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system2.current_state.name,
            models.SystemState.RESPONSIVE)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')
        self.failUnlessEqual([ x.entry for x in logEntries ],
            [
                'System state change: Unmanaged -> Online',
            ])


    def testGetNextSystemState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        jobState = "Completed"

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        eventUuid4 = 'eventuuid004'
        jobUuid4 = 'rmakeuuid004'
        eventUuid5 = 'eventuuid005'
        jobUuid5 = 'rmakeuuid005'
        eventUuid6 = 'eventuuid006'
        jobUuid6 = 'rmakeuuid006'
        eventUuid7 = 'eventuuid007'
        jobUuid7 = 'rmakeuuid007'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        stateCompleted = self.mgr.sysMgr.jobState(jobmodels.JobState.COMPLETED)
        stateFailed = self.mgr.sysMgr.jobState(jobmodels.JobState.FAILED)

        job1 = self._newSystemJob(system, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_REGISTRATION)
        job2 = self._newSystemJob(system, eventUuid2, jobUuid2,
            jobmodels.EventType.SYSTEM_POLL)
        job3 = self._newSystemJob(system, eventUuid3, jobUuid3,
            jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
        job4 = self._newSystemJob(system, eventUuid4, jobUuid4,
            jobmodels.EventType.SYSTEM_APPLY_UPDATE)
        job5 = self._newSystemJob(system, eventUuid5, jobUuid5,
            jobmodels.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE)

        jobRegNoAuth = self._newSystemJob(system, eventUuid6, jobUuid6,
            jobmodels.EventType.SYSTEM_REGISTRATION, statusCode = 401)
        jobPollNoAuth = self._newSystemJob(system, eventUuid7, jobUuid7,
            jobmodels.EventType.SYSTEM_POLL, statusCode = 401)

        UNMANAGED = models.SystemState.UNMANAGED
        UNMANAGED_CREDENTIALS_REQUIRED = models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED
        REGISTERED = models.SystemState.REGISTERED
        RESPONSIVE = models.SystemState.RESPONSIVE
        NONRESPONSIVE = models.SystemState.NONRESPONSIVE
        NONRESPONSIVE_NET = models.SystemState.NONRESPONSIVE_NET
        NONRESPONSIVE_HOST = models.SystemState.NONRESPONSIVE_HOST
        NONRESPONSIVE_SHUTDOWN = models.SystemState.NONRESPONSIVE_SHUTDOWN
        NONRESPONSIVE_SUSPENDED = models.SystemState.NONRESPONSIVE_SUSPENDED
        NONRESPONSIVE_CREDENTIALS = models.SystemState.NONRESPONSIVE_CREDENTIALS
        DEAD = models.SystemState.DEAD
        MOTHBALLED = models.SystemState.MOTHBALLED

        tests = [
            (job1, stateCompleted, UNMANAGED, None),
            (job1, stateCompleted, UNMANAGED_CREDENTIALS_REQUIRED, None),
            (job1, stateCompleted, REGISTERED, None),
            (job1, stateCompleted, RESPONSIVE, None),
            (job1, stateCompleted, NONRESPONSIVE_HOST, None),
            (job1, stateCompleted, NONRESPONSIVE_NET, None),
            (job1, stateCompleted, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateCompleted, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateCompleted, NONRESPONSIVE_CREDENTIALS, None),
            (job1, stateCompleted, NONRESPONSIVE, None),
            (job1, stateCompleted, DEAD, None),
            (job1, stateCompleted, MOTHBALLED, None),

            (job1, stateFailed, UNMANAGED, None),
            (job1, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED, None),
            (job1, stateFailed, REGISTERED, None),
            (job1, stateFailed, RESPONSIVE, None),
            (job1, stateFailed, NONRESPONSIVE_HOST, None),
            (job1, stateFailed, NONRESPONSIVE_NET, None),
            (job1, stateFailed, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateFailed, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateFailed, NONRESPONSIVE_CREDENTIALS, None),
            (job1, stateFailed, NONRESPONSIVE, None),
            (job1, stateFailed, DEAD, None),
            (job1, stateFailed, MOTHBALLED, None),
        ]
        transitionsCompleted = []
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                REGISTERED, RESPONSIVE,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET, NONRESPONSIVE_SHUTDOWN,
                NONRESPONSIVE_SUSPENDED, NONRESPONSIVE,
                NONRESPONSIVE_CREDENTIALS, DEAD, MOTHBALLED]:
            transitionsCompleted.append((oldState, RESPONSIVE))
        transitionsFailed = [
            (REGISTERED, NONRESPONSIVE),
            (RESPONSIVE, NONRESPONSIVE),
        ]
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET,
                NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SUSPENDED,
                NONRESPONSIVE, NONRESPONSIVE_CREDENTIALS, DEAD, MOTHBALLED]:
            transitionsFailed.append((oldState, None))

        for job in [job2, job3, job4, job5]:
            for oldState, newState in transitionsCompleted:
                tests.append((job, stateCompleted, oldState, newState))
            for oldState, newState in transitionsFailed:
                tests.append((job, stateFailed, oldState, newState))

        # Failed auth tests`
        for job in [ jobRegNoAuth, jobPollNoAuth ]:
            tests.append((job, stateFailed, UNMANAGED,
                UNMANAGED_CREDENTIALS_REQUIRED))
            tests.append((job, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED,
                None))
            for oldState in [REGISTERED, RESPONSIVE, NONRESPONSIVE_NET,
                    NONRESPONSIVE_HOST, NONRESPONSIVE_SHUTDOWN,
                    NONRESPONSIVE_SUSPENDED, DEAD]:
                tests.append((job, stateFailed, oldState,
                    NONRESPONSIVE_CREDENTIALS))
            for oldState in [NONRESPONSIVE_CREDENTIALS, MOTHBALLED]:
                tests.append((job, stateFailed, oldState, None))


        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s; %s): %s -> %s (expected: %s)" % (
                (job.job_type.name, jobState.name, job.status_code,
                 oldState, ret, newState))
            self.failUnlessEqual(ret, newState, msg)

        # Time-based tests
        tests = [
            (job2, stateFailed, UNMANAGED, None),
            (job2, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED, None),
            (job2, stateFailed, REGISTERED, NONRESPONSIVE),
            (job2, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job2, stateFailed, NONRESPONSIVE_HOST, DEAD),
            (job2, stateFailed, NONRESPONSIVE_NET, DEAD),
            (job2, stateFailed, NONRESPONSIVE_SHUTDOWN, DEAD),
            (job2, stateFailed, NONRESPONSIVE_SUSPENDED, DEAD),
            (job2, stateFailed, NONRESPONSIVE_CREDENTIALS, DEAD),
            (job2, stateFailed, NONRESPONSIVE, DEAD),
            (job2, stateFailed, DEAD, MOTHBALLED),
            (job2, stateFailed, MOTHBALLED, None),

            (job3, stateFailed, UNMANAGED, None),
            (job3, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED, None),
            (job3, stateFailed, REGISTERED, NONRESPONSIVE),
            (job3, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job3, stateFailed, NONRESPONSIVE_HOST, DEAD),
            (job3, stateFailed, NONRESPONSIVE_NET, DEAD),
            (job3, stateFailed, NONRESPONSIVE_SHUTDOWN, DEAD),
            (job3, stateFailed, NONRESPONSIVE_SUSPENDED, DEAD),
            (job3, stateFailed, NONRESPONSIVE_CREDENTIALS, DEAD),
            (job3, stateFailed, NONRESPONSIVE, DEAD),
            (job3, stateFailed, DEAD, MOTHBALLED),
            (job3, stateFailed, MOTHBALLED, None),
        ]

        self.mgr.cfg.deadStateTimeout = 10
        self.mgr.cfg.mothballedStateTimeout = 10
        stateChange = self.mgr.sysMgr.now() - timeutils.timedelta(days=10)
        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            system.state_change_date = stateChange
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s): %s -> %s (expected: %s)" % (
                (job.job_type.name, jobState.name, oldState, ret, newState))
            self.failUnlessEqual(ret, newState, msg)


class SystemVersionsTestCase(XMLTestCaseStandin):
    fixtures = ['system_job']
    
    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        self.mintConfig = self.mgr.cfg
        from django.conf import settings
        self.mintConfig.dbPath = settings.DATABASES['default']['NAME']
        self.mock_scheduleSystemRegistrationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mock_set_available_updates_called = False
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr.scheduleSystemRegistrationEvent = self.mock_scheduleSystemRegistrationEvent
        rbuildermanager.SystemManager.scheduleSystemApplyUpdateEvent = self.mock_scheduleSystemApplyUpdateEvent
        self.sources = []
        rbuildermanager.VersionManager.set_available_updates = \
            self.mock_set_available_updates
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob

        self.mockGetStagesCalled = False
        self.mockStages = []
        rbuildermanager.VersionManager.getStages = \
            self.mockGetStages

    def mockGetStages(self, *args, **kwargs):
        self.mockGetStagesCalled = True
        return self.mockStages

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def mock_set_available_updates(self, trove, *args, **kwargs):
        self.mock_set_available_updates_called = True

    def mock_scheduleSystemRegistrationEvent(self, system):
        self.mock_scheduleSystemRegistrationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True

    def mock_scheduleSystemApplyUpdateEvent(self, system, sources):
        self.mock_scheduleSystemApplyUpdateEvent_called = True
        self.sources = sources
    mock_scheduleSystemApplyUpdateEvent.exposed = True
 
    def _saveTrove(self):
        version = models.Version()
        version.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1'
        version.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version.ordering = '1234567890.12'
        version.revision = 'change me gently'
        version.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version.save()

        trove = models.Trove()
        trove.name = 'group-clover-appliance'
        trove.version = version
        trove.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        trove.last_available_update_refresh = timeutils.now()
        trove.save()

        version_update = models.Version()
        version_update.fromConaryVersion(versions.ThawVersion(
            '/clover.eng.rpath.com@rpath:clover-1-devel/1234567891.13:1-3-1'))
        version_update.flavor = version.flavor
        version_update.save()

        version_update2 = models.Version()
        version_update2.fromConaryVersion(versions.ThawVersion(
            '/clover.eng.rpath.com@rpath:clover-1-devel/1234567892.14:1-4-1'))
        version_update2.flavor = version.flavor
        version_update2.save()

        trove.available_updates.add(version)
        trove.available_updates.add(version_update)
        trove.available_updates.add(version_update2)
        trove.out_of_date = True
        trove.save()

        version2 = models.Version()
        version2.fromConaryVersion(versions.ThawVersion(
            '/contrib.rpath.org@rpl:devel//2/1234567890.12:23.0.60cvs20080523-1-0.1'))
        version2.flavor = 'desktop is: x86_64'
        version2.save()

        trove2 = models.Trove()
        trove2.name = 'emacs'
        trove2.version = version2
        trove2.flavor = version2.flavor
        trove2.last_available_update_refresh = timeutils.now()
        trove2.save()

        trove2.available_updates.add(version2)
        trove2.save()

        self.trove = trove
        self.trove2 = trove2

    def testRefreshCachedUpdates(self):
        self._saveTrove()
        name = self.trove.name
        label = self.trove.version.label

        version_update3 = models.Version()
        version_update3.fromConaryVersion(versions.ThawVersion(
            '/clover.eng.rpath.com@rpath:clover-1-devel/1234567893.14:1-5-1'))
        version_update3.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version_update3.save()

        def mock_set_available_updates(self, trove, *args, **kwargs):
            trove.available_updates.add(version_update3)

        rbuildermanager.VersionManager.set_available_updates = \
            mock_set_available_updates

        self.mgr.versionMgr.refreshCachedUpdates(name, label)
        update = self.trove.available_updates.all()
        self.assertEquals(4, len(update))
        update = [u.full for u in update]
        self.assertEquals(update,
            ['/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1',
             '/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1',
             '/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1',
             '/clover.eng.rpath.com@rpath:clover-1-devel/1-5-1'])

    def testGetSystemWithVersion(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        response = self._get('inventory/systems/%s/' % system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        expected = (testsxml.system_version_xml % (
                self.trove.last_available_update_refresh.isoformat(),
                self.trove2.last_available_update_refresh.isoformat(),
                system.networks.all()[0].created_date.isoformat(),
                system.created_date.isoformat())).replace(
             'installed_software/', 'installed_software')
        self.assertXMLEquals(response.content, expected,
            ignoreNodes = [ 'actions', 'created_date', 'modified_date', 'created_by', 'modified_by', 
                'last_available_update_refresh' ])

    def testGetInstalledSoftwareRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        url = 'inventory/systems/%s/installed_software/' % system.pk
        response = self._get(url, username="admin", password="password")
        self.assertXMLEquals(response.content,
            testsxml.get_installed_software_xml %(
                self.trove.last_available_update_refresh.isoformat(),
                self.trove2.last_available_update_refresh.isoformat()))

    def XXXtestSetInstalledSoftwareRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        url = 'inventory/systems/%s/installed_software/' % system.pk
        response = self._post(url,
            data=testsxml.installed_software_post_xml)
        self.assertXMLEquals(response.content,
            testsxml.installed_software_response_xml,
            ignoreNodes = ['last_available_update_refresh'])

    def testAvailableUpdatesXml(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        response = self._get('inventory/systems/%s' % system.pk,
            username="admin", password="password")
        self.assertXMLEquals(response.content, 
            testsxml.system_available_updates_xml,
            ignoreNodes=['actions', 'created_date', 'modified_date', 
                'created_by', 'modified_by', 'last_available_update_refresh'])

    def testApplyUpdate(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        # Apply update to 1-3-1
        data = testsxml.system_apply_updates_xml
        response = self._put('inventory/systems/%s/installed_software' 
            % system.pk,
            data=data, username="admin", password="password")
        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(self.sources))
        newGroup = [g for g in self.sources \
            if parseTroveSpec(g).name == 'group-clover-appliance'][0]
        newGroup = parseTroveSpec(newGroup)
        self.assertEquals('group-clover-appliance', newGroup.name)
        version = versions.VersionFromString(newGroup.version)
        self.assertEquals('1-3-1', version.trailingRevision().asString())

    def _mockProductDefinition(self):
        import StringIO
        from rpath_proddef import api1 as proddef
        def fakeLoadFromRepository(slf, client):
            slf.parseStream(StringIO.StringIO(refProductDefintion1))
        self.mock(proddef.ProductDefinition, 'loadFromRepository', fakeLoadFromRepository)

    def testSetInstalledSoftwareSystemRest(self):
        self._mockProductDefinition()
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)

        system.project = projectmodels.Project.objects.get(short_name='chater-foo')
        system.major_version = projectmodels.ProjectVersion.objects.get(
            branch_id=system.project_id, name='1')
        system.stage = projectmodels.Stage.objects.get(
            project_branch=system.major_version, name='Development')
        system.save()

        eventUuid = 'eventuuid007'
        jobUuid = 'rmakejob007'
        self._newSystemJob(system, eventUuid, jobUuid, jobmodels.EventType.SYSTEM_POLL)

        self.failUnlessEqual(
            [ (x.name, (x.version.full, x.version.ordering, x.version.flavor,
                x.version.label, x.version.revision), x.flavor)
                for x in system.installed_software.all() ],
            [
                ('group-clover-appliance',
                    ('/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1',
                     '1234567890.12',
                     '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)',
                    'clover.eng.rpath.com@rpath:clover-1-devel',
                    'change me gently'),
                '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'),
                ('emacs',
                    ('/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1',
                     '1234567890.12',
                     'desktop is: x86_64',
                     'contrib.rpath.org@rpl:2',
                     '23.0.60cvs20080523-1-0.1'),
                    'desktop is: x86_64'),
            ])

        data = testsxml.system_version_put_xml

        self.mockStages.append(restmodels.Stage(
            label='chater-foo.eng.rpath.com@rpath:chater-foo-1-devel',
            name='Development',
            hostname='chater-foo',
            version='1',
            isPromotable=True))

        url = 'inventory/systems/%s/' % system.pk
        response = self._put(url, data=data,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid },
            username="admin", password="password")
            
        # Weak attempt to see if the response is XML
        exp = '<system id="http://testserver/api/v1/inventory/systems/%s">' % system.pk
        self.failUnlessIn(exp, response.content)

        nsystem = models.System.objects.get(system_id=system.pk)
        self.failUnlessEqual(
            [ (x.name, (x.version.full, x.version.ordering, x.version.flavor,
                x.version.label, x.version.revision), x.flavor)
                for x in nsystem.installed_software.all() ],
            [
                ('group-chater-foo-appliance',
                 ('/chater-foo.eng.rpath.com@rpath:chater-foo-1-devel/1-2-1',
                     '1234567890.12',
                     'is: x86',
                     'chater-foo.eng.rpath.com@rpath:chater-foo-1-devel',
                     '1-2-1'),
                 'is: x86'),
                ('vim',
                 ('/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1',
                  '1272410163.98',
                  'desktop is: x86_64',
                  'contrib.rpath.org@rpl:2',
                  '23.0.60cvs20080523-1-0.1'),
                 'desktop is: x86_64'),
                ('info-sfcb',
                 ('/contrib.rpath.org@rpl:2/1-1-1',
                  '1263856871.03',
                  '',
                  'contrib.rpath.org@rpl:2',
                  '1-1-1'),
                  ''),
            ])

        # Try it again
        response = self._put(url, data=data,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.name, "testsystemname")

        response = self._get(url, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_installed_software_version_stage_xml,
            ignoreNodes=['actions', 'created_date', 'modified_date', 'created_by', 'modified_by'],)

class EventTypeTestCase(XMLTestCaseStandin):

    def testGetEventTypes(self):
        response = self._get('inventory/event_types/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_types_xml)

    def testGetEventType(self):
        response = self._get('inventory/event_types/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_type_xml)
        
    def testPutEventTypeAuth(self):
        """
        Ensure we require admin to put event types
        """
        response = self._put('inventory/event_types/1/', 
            data= testsxml.event_type_put_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._put('inventory/event_types/1/', 
            data=testsxml.event_type_put_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutEventType(self):
        jobmodels.EventType.objects.all().delete()
        event_type = jobmodels.EventType(name="foo", description="bar", priority=110)
        event_type.save()
        self.assertTrue(event_type.priority == 110)
        xml = testsxml.event_type_put_xml % dict(event_type_id=event_type.pk)
        response = self._put('inventory/event_types/%s/' % event_type.job_type_id,
            data=xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = jobmodels.EventType.objects.get(pk=event_type.pk)
        self.assertTrue(event_type.priority == 1)
        
    def testPutEventTypeName(self):
        """
        Do not allow changing the event type name https://issues.rpath.com/browse/RBL-7171
        """
        jobmodels.EventType.objects.all().delete()
        event_type = jobmodels.EventType(name=jobmodels.EventType.SYSTEM_POLL, description="bar", priority=110)
        event_type.save()
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_POLL)
        xml = testsxml.event_type_put_name_change_xml % dict(event_type_id=event_type.pk)
        response = self._put('inventory/event_types/%d/' % event_type.pk,
            data=xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = jobmodels.EventType.objects.get(pk=event_type.pk)
        # name should not have changed
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_POLL)

class SystemEventTestCase(XMLTestCaseStandin):
    
    def setUp(self):
        XMLTestCaseStandin.setUp(self)

        # need a system
        network = models.Network(ip_address='1.1.1.1')
        self.system = self.newSystem(name="mgoblue", 
            description="best appliance ever",
            management_interface=models.ManagementInterface.objects.get(name='cim'))
        self.system.save()
        network.system = self.system
        self.system.networks.add(network)
        self.system.save()
        
        # start with no logs/system events
        models.SystemLog.objects.all().delete()
        models.SystemEvent.objects.all().delete()
        
        self.mock_dispatchSystemEvent_called = False
        self.mgr.sysMgr.dispatchSystemEvent = self.mock_dispatchSystemEvent

        self.old_DispatchSystemEvent = rbuildermanager.SystemManager._dispatchSystemEvent

    def tearDown(self):
        rbuildermanager.SystemManager._dispatchSystemEvent = self.old_DispatchSystemEvent
        XMLTestCaseStandin.tearDown(self)

    def mock_dispatchSystemEvent(self, event):
        self.mock_dispatchSystemEvent_called = True
    
    def testGetSystemEventsRest(self):
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        response = self._get('inventory/system_events/',
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_events_xml % \
                (event1.time_created.isoformat(), event1.time_enabled.isoformat(),
                 event2.time_created.isoformat(), event2.time_enabled.isoformat()))

    def testGetSystemEventRestAuth(self):
        """
        Ensure requires auth but not admin
        """
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemEventRest(self):
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))
    
    def testGetSystemEvent(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        new_event = self.mgr.getSystemEvent(event.system_event_id)
        assert(new_event == event)
        
    def testGetSystemEvents(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.mgr.getSystemEvents()
        assert(len(SystemEvents.system_event) == 2)
        
    def testDeleteSystemEvent(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        self.mgr.deleteSystemEvent(event.system_event_id)
        events = models.SystemEvent.objects.all()
        assert(len(events) == 0)
        
    def testCreateSystemEvent(self):
        local_system = self.newSystem(name="mgoblue_local", description="best appliance ever")
        local_system.save()
        network = models.Network(system=local_system)
        network.save()
        local_system.networks.add(network)
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = self.mgr.createSystemEvent(local_system, poll_event)
        assert(event is None)
        assert(self.mock_dispatchSystemEvent_called == False)
                
        network2 = models.Network(system=local_system, ip_address="1.1.1.1")
        network2.save()
        local_system.networks.add(network2)
        event = self.mgr.createSystemEvent(local_system, poll_event)
        assert(event is not None)
        
    def testSaveSystemEvent(self):
        self._saveSystem()
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system, event_type=poll_event)
        event.save()
        # make sure event priority was set even though we didn't pass it in
        assert(event.priority == poll_event.priority)
        
        event2 = models.SystemEvent(system=self.system, event_type=poll_event, priority=1)
        event2.save()
        # make sure we honor priority if set
        assert(event2.priority == 1)
    
    def testScheduleSystemPollEvent(self):
        self.mgr.scheduleSystemPollEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called == False)
        
        # make sure we have our poll event
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=poll_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)
        
    def testScheduleSystemPollNowEvent(self):
        self.mgr.scheduleSystemPollNowEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called)
        
        pn_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=pn_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= timeutils.now())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)
        
    def testScheduleSystemRegistrationEvent(self):
        # registration events are no longer dispatched immediately (RBL-8851)
        self.mgr.scheduleSystemRegistrationEvent(self.system)
        self.failIf(self.mock_dispatchSystemEvent_called)

        registration_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=registration_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= timeutils.now())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)
        
    def testAddSystemEventNull(self):
        
        try:
            self.mgr.addSystemSystemEvent(None, None)
        except:
            assert(False) # should not throw exception
        
    def testAddSystemRegistrationEvent(self):
        # registration events are no longer dispatched immediately (RBL-8851)
        registration_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=registration_event, priority=registration_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        self.failIf(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemConfigNowEvent(self):
        # poll now event should be dispatched now
        config_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_CONFIG_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=config_event, priority=config_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollNowEvent(self):
        # poll now event should be dispatched now
        poll_now_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_now_event, priority=poll_now_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollEvent(self):
        # poll event should not be dispatched now
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_event, priority=poll_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called == False)
        
    def testPostSystemEventAuth(self):
        """
        Ensure requires auth but not admin
        """
        url = 'inventory/systems/%d/system_events/' % self.system.system_id
        system_event_post_xml = testsxml.system_event_post_xml
        response = self._post(url, data=system_event_post_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._post(url,
            data=system_event_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostSystemEvent(self):
        url = 'inventory/systems/%d/system_events/' % self.system.system_id
        system_event_post_xml = testsxml.system_event_post_xml
        response = self._post(url,
            data=system_event_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system_event = models.SystemEvent.objects.get(pk=1)
        system_event_xml = testsxml.system_event_xml % \
            (system_event.time_created.isoformat(),
            system_event.time_enabled.isoformat())
        self.assertXMLEquals(response.content, system_event_xml,
            ignoreNodes=['time_created', 'time_enabled'])
        
    def testIncompatibleEvents(self):
        def mock__dispatchSystemEvent(self, event):
            system = event.system
            job_uuid = str(random.random())
            job = jobmodels.Job(job_uuid=job_uuid, job_token=job_uuid*2,
                job_state=jobmodels.JobState.objects.get(name='Running'),
                job_type=event.event_type)
            job.save()
            systemJob = models.SystemJob(job=job, system=system,
                event_uuid=str(random.random()))
            systemJob.save()

        rbuildermanager.SystemManager._dispatchSystemEvent = mock__dispatchSystemEvent

        url = 'inventory/systems/%d/system_events/' % self.system.system_id
        response = self._post(url,
            data=testsxml.system_event_immediate_poll_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        # Schedule another poll, should fail, can't poll twice at the same
        # time
        response = self._post(url,
            data=testsxml.system_event_immediate_poll_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' in response.content)

        # Clear system events
        [j.delete() for j in self.system.systemjob_set.all()]

        # Schedule an update, should succeed
        response = self._post(url,
            data=testsxml.system_event_immediate_update_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' not in response.content)

        # Schedule a shutdown, should fail
        response = self._post(url,
            data=testsxml.system_event_immediate_shutdown_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' in response.content)
        
        # Clear system events
        [j.delete() for j in self.system.systemjob_set.all()]

        # Schedule a registration, should succeed
        response = self._post(url,
            data=testsxml.system_event_immediate_registration_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' not in response.content)

        # Schedule a poll, should succeed
        response = self._post(url,
            data=testsxml.system_event_immediate_poll_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' not in response.content)

class SystemEventProcessingTestCase(XMLTestCaseStandin):
    
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']
    
    def setUp(self):
        XMLTestCaseStandin.setUp(self)

        self.mintConfig = self.mgr.cfg
        self.mgr.sysMgr.cleanupSystemEvent = self.mock_cleanupSystemEvent
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr.extractNetworkToUse = self.mock_extractNetworkToUse
        self.resetFlags()

    def resetFlags(self):
        self.mock_cleanupSystemEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mock_extractNetworkToUse_called = False

    def mock_cleanupSystemEvent(self, event):
        self.mock_cleanupSystemEvent_called = True
        event.delete()

    def mock_scheduleSystemPollEvent(self, event):
        self.mock_scheduleSystemPollEvent_called = True

    def mock_extractNetworkToUse(self, system):
        self.mock_extractNetworkToUse_called = True
        return None

    def testGetSystemEventsForProcessing(self):

        # set default processing size to 1
        self.mintConfig.systemEventsNumToProcess = 1
                
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        
        # ensure we got our registration event back since it is the highest priority
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION)

        # remove the registration event and ensure we get the on demand poll event next
        event.delete()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_POLL)

        # remove the poll now event and ensure we get the standard poll event next
        event.delete()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)

        # add another poll event with a higher priority but a future time 
        # and make sure we don't get it (because of the future registration time)
        orgPollEvent = event
        new_poll_event = models.SystemEvent(system=orgPollEvent.system, 
            event_type=orgPollEvent.event_type, priority=orgPollEvent.priority + 1,
            time_enabled=orgPollEvent.time_enabled + timeutils.timedelta(1))
        new_poll_event.save()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.system_event_id,
            new_poll_event.system_event_id)
        
    def testGetSystemEventsForProcessingPollCount(self):
        self.mintConfig.systemEventsNumToProcess = 3
        
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 3)
        
    def testProcessSystemEvents(self):
        
        # set default processing size to 1
        self.mintConfig.systemEventsNumToProcess = 1
        
        #remove the registration event so we handle the poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION)
        event.delete()
        
        # make sure next one is poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_POLL)
        self.mgr.sysMgr.processSystemEvents()
        
        # make sure the event was removed and that we have the next poll event 
        # for this system now
        try:
            poll_now_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
            event = models.SystemEvent.objects.get(system_event_id=event.system_event_id,
                event_type=poll_now_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
        local_system = poll_event.system_events.all()[0]
        event = models.SystemEvent.objects.get(system=local_system, event_type=poll_event)
        self.failIf(event is None)
        
    def testProcessSystemEventsNoTrigger(self):
        # make sure registration event doesn't trigger next poll event
        # start with no regular poll events
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        models.SystemEvent.objects.filter(event_type=poll_event).delete()
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        
        # make sure next one is registration now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION)
        self.mgr.sysMgr.processSystemEvents()
        
        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

    def testDispatchSystemEvent(self):
        poll_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL)
        poll_now_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_POLL_IMMEDIATE)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)

        system = self.newSystem(name="hey")
        system.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        self.failUnless(self.mock_cleanupSystemEvent_called)
        self.failUnless(self.mock_scheduleSystemPollEvent_called)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        # sanity check dispatching poll_now event
        self.resetFlags()
        self.mock_scheduleSystemPollEvent_called = False # reset it
        event = models.SystemEvent(system=system, event_type=poll_now_event, priority=poll_now_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        self.failUnless(self.mock_cleanupSystemEvent_called)
        self.failIf(self.mock_scheduleSystemPollEvent_called)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        # sanity check dispatching registration event
        self.resetFlags()
        event = models.SystemEvent(system=system, event_type=act_event, priority=act_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        self.failUnless(self.mock_cleanupSystemEvent_called)
        self.failIf(self.mock_scheduleSystemPollEvent_called)

class SystemEventProcessing2TestCase(XMLTestCaseStandin, test_utils.RepeaterMixIn):
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']

    def setUp(self):
        XMLTestCaseStandin.setUp(self)
        test_utils.RepeaterMixIn.setUpRepeaterClient(self)
        self.system2 = system = self.newSystem(name="hey")
        system.save()
        network2 = models.Network(ip_address="2.2.2.2", active=True)
        network3 = models.Network(ip_address="3.3.3.3", pinned=True)
        system.networks.add(network2)
        system.networks.add(network3)
        system.save()

    def _setupEvent(self, eventType, eventData=None):
        self.system2.agent_port = 12345
        self.system2.save()
        eventType = self.mgr.sysMgr.eventType(eventType)
        # Remove all networks
        for net in self.system2.networks.all():
            net.delete()
        network = models.Network(dns_name = 'superduper.com')
        network.system = self.system2
        network.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=self.system2,
            event_type=eventType, priority=eventType.priority)
        if eventData:
            if isinstance(eventData, basestring):
                event.event_data = eventData
            else:
                event.event_data = cPickle.dumps(eventData)
        event.save()
        return event

    def _mockUuid(self):
        def mockedUuid4():
            return "really-unique-id"
        from mint.lib import uuid
        self.mock(uuid, 'uuid4', mockedUuid4)

    def _dispatchEvent(self, event):
        self._mockUuid()
        self.mgr.sysMgr.dispatchSystemEvent(event)


    def testDispatchSystemEvent(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_POLL)
        self._dispatchEvent(event)

        cimParams = self.mgr.repeaterMgr.repeaterClient.CimParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('poll_cim',
                    (
                        cimParams(
                            host='superduper.com',
                            port=12345,
                            eventUuid='really-unique-id',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork=None,
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=300),
                        resLoc(path='/api/v1/inventory/systems/%s' %
                                self.system2.pk,
                            port=80),
                    ),
                    dict(zone='Local rBuilder'),
                ),
            ])
        system = self.mgr.getSystem(self.system2.system_id)
        jobs = system.jobs.all()
        self.failUnlessEqual([ x.job_uuid for x in jobs ],
            ['uuid000'])

    def testDispatchActivateSystemEvent(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_REGISTRATION)
        self._dispatchEvent(event)

        cimParams = self.mgr.repeaterMgr.repeaterClient.CimParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('register_cim',
                    (
                        cimParams(host='superduper.com',
                            port=12345,
                            eventUuid = 'really-unique-id',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork=None,
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=300),
                        resLoc(path='/api/v1/inventory/systems/4', port=80),
                    ),
                    dict(zone='Local rBuilder'),
                ),
            ])
        system = self.mgr.getSystem(self.system2.system_id)
        jobs = system.jobs.all()
        self.failUnlessEqual([ x.job_uuid for x in jobs ],
            ['uuid000'])
        # XXX find a better way to extract the additional field from the
        # many-to-many table
        self.failUnlessEqual(
            [ x.event_uuid for x in models.SystemJob.objects.filter(system__system_id = system.system_id) ],
            [ 'really-unique-id' ])

    def testDispatchManagementInterfaceEvent(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE)
        self._dispatchEvent(event)

        mgmtIfaceParams = self.mgr.repeaterMgr.repeaterClient.ManagementInterfaceParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('detectMgmtInterface',
                    (
                        mgmtIfaceParams(host='superduper.com',
                            eventUuid = 'really-unique-id',
                            interfacesList=[
                                {
                                    'port': 135,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/2',
                                },
                                {
                                    'port': 5989,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/1',
                                },
                                { 
                                    'port': 22,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/3',
                                }   
                                ]
                        ),
                        resLoc(path='/api/v1/inventory/systems/4', port=80),
                    ),
                    dict(zone='Local rBuilder'),
                ),
            ])
        system = self.mgr.getSystem(self.system2.system_id)
        jobs = system.jobs.all()
        self.failUnlessEqual([ x.job_uuid for x in jobs ],
            ['uuid000'])
        # XXX find a better way to extract the additional field from the
        # many-to-many table
        self.failUnlessEqual(
            [ x.event_uuid for x in models.SystemJob.objects.filter(system__system_id = system.system_id) ],
            [ 'really-unique-id' ])

    def testDispatchPollWmi(self):
        wmiInt = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.WMI)
        self.system2.management_interface = wmiInt
        credDict = dict(username="JeanValjean", password="Javert",
            domain="Paris")
        self.system2.credentials = self.mgr.sysMgr.marshalCredentials(
            credDict)
        event = self._setupEvent(jobmodels.EventType.SYSTEM_POLL)
        self._dispatchEvent(event)

        repClient = self.mgr.repeaterMgr.repeaterClient
        wmiParams = repClient.WmiParams
        resLoc = repClient.ResultsLocation

        wmiDict = credDict.copy()
        wmiDict.update(eventUuid='really-unique-id', host='superduper.com',
            requiredNetwork=None, port=12345)

        self.failUnlessEqual(repClient.getCallList(),
            [
                ('poll_wmi',
                    (
                        wmiParams(**wmiDict),
                        resLoc(path='/api/v1/inventory/systems/4', port=80),
                    ),
                    dict(zone='Local rBuilder'),
                ),
            ])

    def testDispatchUpdateWmi(self):
        wmiInt = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.WMI)
        self.system2.management_interface = wmiInt
        credDict = dict(username="JeanValjean", password="Javert",
            domain="Paris")
        self.system2.credentials = self.mgr.sysMgr.marshalCredentials(
            credDict)
        toInstall = [ "group-foo=/a@b:c/1-2-3", "group-bar=/a@b:c//d@e:f/1-2.1-2.2" ]
        event = self._setupEvent(jobmodels.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE,
            eventData=toInstall)

        self._dispatchEvent(event)

        repClient = self.mgr.repeaterMgr.repeaterClient
        wmiParams = repClient.WmiParams
        resLoc = repClient.ResultsLocation

        wmiDict = credDict.copy()
        wmiDict.update(eventUuid='really-unique-id', host='superduper.com',
            port=12345, requiredNetwork=None)

        self.failUnlessEqual(repClient.getCallList(),
            [
                ('update_wmi',
                    (
                        wmiParams(**wmiDict),
                        resLoc(path='/api/v1/inventory/systems/4', port=80),
                    ),
                    dict(
                        zone='Local rBuilder',
                        sources=[
                            'group-foo=/a@b:c/1-2-3',
                            'group-bar=/a@b:c//d@e:f/1-2.1-2.2',
                        ],),
                ),
            ])

    def testInterfaceDetection(self):
        self._mockUuid()

        eventUuid1 = "eventUuid1"
        jobUuid1 = "jobUuid1"
        eventUuid2 = "eventUuid2"
        jobUuid2 = "jobUuid2"

        CIM = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.CIM)
        WMI = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.WMI)

        systemCim = self.newSystem(name="blah cim",
            management_interface=CIM)
        systemCim.save()
        network = models.Network(dns_name="blah cim", ip_address="1.2.3.4",
            system=systemCim)
        network.save()
        systemWmi = self.newSystem(name="blah wmi",
            management_interface=WMI)
        systemWmi.save()
        network = models.Network(dns_name="blah wmi", ip_address="1.2.3.4",
            system=systemWmi)

        jobCim = self._newSystemJob(systemCim, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
            jobState=jobmodels.JobState.COMPLETED)
        jobWmi = self._newSystemJob(systemWmi, eventUuid2, jobUuid2,
            jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
            jobState=jobmodels.JobState.COMPLETED)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        # Clear out the system events table
        models.SystemEvent.objects.all().delete()
        newState = self.mgr.sysMgr.getNextSystemState(systemCim, jobCim)
        self.failUnlessEqual(newState, None)
        # registration events are no longer dispatched immediately (RBL-)
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [])
        # Dispatch the event now
        self.mgr.sysMgr.processSystemEvents()
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('register_cim',
                    (
                        cimParams(host='1.2.3.4',
                            port=5989,
                            eventUuid='really-unique-id',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork=None,
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=300),
                        resLoc(path='/api/v1/inventory/systems/%s' %
                                systemCim.pk,
                            port=80),
                    ),
                    dict(zone='Local rBuilder'),
                ),
            ])

        # Clean the deck
        self.mgr.repeaterMgr.repeaterClient.reset()

        newState = self.mgr.sysMgr.getNextSystemState(systemWmi, jobWmi)
        self.failUnlessEqual(newState,
            models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED)
        # Being a WMI system, we need credentials
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [])

    def testUpdateCim(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE)
        event.delete()

        url = "inventory/systems/%s/installed_software" % self.system2.pk
        xml = """
<installed_software>
    <trove>
      <name>group-chater-appliance</name>
      <version>
        <full>/chater.eng.rpath.com@rpath:chater-1-devel/1-2-1</full>
        <ordering>1234567890.12</ordering>
        <flavor>is: x86</flavor>
      </version>
      <flavor>is: x86</flavor>
    </trove>
    <trove>
      <name>vim</name>
      <version>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <ordering>1272410163.98</ordering>
        <flavor>desktop is: x86_64</flavor>
      </version>
      <flavor>desktop is: x86_64</flavor>
    </trove>
</installed_software>
"""

        response = self._put(url, data=xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        # We can't mock something past django's handler, so there's no
        # validation that we can do at this point

    def testDispatchConfigurationCim(self):
        cimInt = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.CIM)
        self.system2.management_interface = cimInt
        configDict = dict(a='1', b='2')
        self.system2.configuration = self.mgr.sysMgr.marshalCredentials(
            configDict)

        self.mgr.sysMgr.scheduleSystemConfigurationEvent(self.system2,
            configDict)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        eventUuid = models.SystemJob.objects.all()[0].event_uuid
        self.failUnlessEqual(repClient.getCallList(),
            [
                ('configuration_cim',
                    (
                        cimParams(host='3.3.3.3',
                            port=None,
                            eventUuid=eventUuid,
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork='3.3.3.3',
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=300),
                        resLoc(path='/api/v1/inventory/systems/%s' %
                                self.system2.pk, port=80),
                    ),
                    dict(
                        zone='Local rBuilder',
                        configuration='<configuration><a>1</a><b>2</b></configuration>',
                    ),
                ),
            ])

class TargetSystemImportTest(XMLTestCaseStandin):
    fixtures = ['users', 'targets']

    class Driver(object):
        def __init__(self, cloudType, cloudName, userId, instances):
            self.cloudType = cloudType
            self.cloudName = cloudName
            self.instances = instances
            self.userId = userId

        def getAllInstances(self):
            return self.instances

    class TargetInstance(object):
        class _X(object):
            def __init__(self, data):
                self.data = data
            def getText(self):
                return self.data

        def __init__(self, instanceId, instanceName, instanceDescription,
                     dnsName, state):
            self.instanceId = self._X(instanceId)
            self.instanceName = self._X(instanceName)
            self.instanceDescription = self._X(instanceDescription)
            self.state = self._X(state)
            self.dnsName = self._X(dnsName)

    def setUp(self):
        XMLTestCaseStandin.setUp(self)

        TI = self.TargetInstance

        self.vsphere1_001 = TI('vsphere1-001', 'Instance 1', 'Instance desc 1',
                    'dnsName1-001', 'running', )
        self.vsphere1_003 = TI('vsphere1-003', 'Instance 3', 'Instance desc 3',
                    'dnsName1-003', 'shutdown', )
        self.vsphere1_004 = TI('vsphere1-004', 'Instance 4', 'Instance desc 4',
                    'dnsName1-004', 'suspended', )

        self.vsphere2_001 = TI('vsphere2-001', 'Instance 1', 'Instance desc 1',
                    'dnsName2-001', 'running', )
        self.vsphere2_003 = TI('vsphere2-003', 'Instance 3', 'Instance desc 3',
                    'dnsName2-003', 'shutdown', )
        self.vsphere2_004 = TI('vsphere2-004', 'Instance 4', 'Instance desc 4',
                    'dnsName2-004', 'suspended', )

        self.ec2_001 = TI('ec2aws-001', 'Instance 1', 'Instance desc 1',
                    'dnsName1-001', 'running', )
        self.ec2_003 = TI('ec2aws-003', 'Instance 3', 'Instance desc 3',
                    'dnsName1-003', 'shutdown', )
        self.ec2_004 = TI('ec2aws-004', 'Instance 4', 'Instance desc 4',
                    'dnsName1-004', 'suspended', )

        self._targets = [
            ('vmware', 'vsphere1.eng.rpath.com', 'JeanValjean1', [
                self.vsphere1_001,
                self.vsphere1_003,
                self.vsphere1_004,
            ]),
            ('vmware', 'vsphere2.eng.rpath.com', 'JeanValjean2', [
                self.vsphere2_001,
                self.vsphere2_003,
            ]),
            ('vmware', 'vsphere2.eng.rpath.com', 'JeanValjean3', [
                self.vsphere2_001,
                self.vsphere2_004,
            ]),
            ('ec2', 'aws', 'JeanValjean1', [
                self.ec2_001,
                self.ec2_003,
                self.ec2_004,
            ]),
        ]

        self.drivers = []

        for (targetType, targetName, userName, systems) in self._targets:
            self.drivers.append(self.Driver(targetType, targetName, userName,
                systems))
        # Set the db version
        from mint.db import schema
        v = rbuildermodels.DatabaseVersion(
            version=schema.RBUILDER_DB_VERSION.major,
            minor=schema.RBUILDER_DB_VERSION.minor)
        v.save()

        zone = self.localZone

        # Create some dummy systems
        self.tgt1 = targetmodels.Target.objects.get(pk=1) # vsphere1
        self.tgt2 = targetmodels.Target.objects.get(pk=2) # vsphere2
        self.tgt3 = targetmodels.Target.objects.get(pk=3) # ec2
        c1 = targetmodels.TargetCredentials.objects.get(pk=1)
        c2 = targetmodels.TargetCredentials.objects.get(pk=2)
        c3 = targetmodels.TargetCredentials.objects.get(pk=3)
        systems = [
            ('vsphere1-001', 'vsphere1 001', self.tgt1, [c2]),
            ('vsphere1-002', 'vsphere1 002', self.tgt1, [c1, c2]),

            ('vsphere2-001', 'vsphere2 001', self.tgt2, [c1]),
            ('vsphere2-002', 'vsphere2 002', self.tgt2, [c3]),
            ('vsphere2-003', 'vsphere2 003', self.tgt2, []),

            ('ec2aws-001', 'ec2aws 001', self.tgt3, [c1]),
            ('ec2aws-002', 'ec2aws 002', self.tgt3, [c3]),
        ]
        for (systemId, systemName, target, credList) in systems:
            description = systemName + " description"
            sy = models.System(name=systemName, target_system_id=systemId,
                target=target, description=description, managing_zone=zone)
            sy.save()
            nw = models.Network(system=sy, dns_name=systemId)
            nw.save()
            for cred in credList:
                stc = models.SystemTargetCredentials(system=sy, credentials=cred)
                stc.save()
        # Modify the network for one of the systems to look real
        sy = models.System.objects.get(target_system_id='vsphere1-001')
        nw = sy.networks.all()[0]
        nw.dns_name = 'dnsName1-001'
        nw.save()

    def testImportTargetSystems(self):
        self.mgr.sysMgr.importTargetSystems(self.drivers)
        # Make sure these systems have lost their target
        self.failUnlessEqual(models.System.objects.get(
            target_system_id='vsphere1-002').target, None)
        self.failUnlessEqual(models.System.objects.get(
            target_system_id='ec2aws-002').target, None)

        for (targetTypeName, targetName, userName, tsystems) in self._targets:
            targetType = targetmodels.TargetType.objects.get(name=targetTypeName)
            tgt = targetmodels.Target.objects.get(target_type=targetType,
                name=targetName)
            for tsystem in tsystems:
                # Make sure we linked this system to the target
                system = models.System.objects.get(target=tgt,
                    target_system_id=tsystem.instanceId.getText())
                # Make sure we linked it to the user too
                cred_ids = set(x.credentials_id
                    for x in system.target_credentials.all())
                try:
                    tuc = targetmodels.TargetUserCredentials.objects.get(
                        target=tgt, user__user_name = userName)
                except targetmodels.TargetUserCredentials.DoesNotExist:
                    self.fail("System %s not linked to user %s" % (
                        system.target_system_id, userName))
                self.failUnlessIn(
                    tuc.target_credentials_id,
                    cred_ids)
                self.failUnlessEqual([
                    x.dns_name for x in system.networks.all() ],
                    [ tsystem.dnsName.getText() ])

        # Make sure we can re-run
        self.mgr.sysMgr.importTargetSystems(self.drivers)

        # Use the API, make sure the fields come out right
        system = models.System.objects.get(target_system_id='vsphere1-001')
        # Fetch XML
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        xobjmodel = obj.system
        self.failUnlessEqual(xobjmodel.name, 'vsphere1 001')
        self.failUnlessEqual(xobjmodel.target_system_id, 'vsphere1-001')
        self.failUnlessEqual(xobjmodel.target_system_name, 'Instance 1')
        self.failUnlessEqual(xobjmodel.target_system_description,
            'Instance desc 1')
        self.failUnlessEqual(xobjmodel.target_system_state, 'running')
        self.failUnlessEqual(xobjmodel.networks.network.dns_name, 'dnsName1-001')

        # Check system log entries
        system = models.System.objects.get(target_system_id='vsphere2-003')
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                'vsphere2.eng.rpath.com (vmware): using dnsName2-003 as primary contact address',
                'vsphere2.eng.rpath.com (vmware): removing stale network information vsphere2-003 (ip unset)',
            ])
        # Make sure we didn't overwrite the name with the one coming from the
        # target
        self.failUnlessEqual(system.name, "vsphere2 003")

        system = models.System.objects.get(target_system_id='vsphere1-004')
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries[1:] ],
            [
                'vsphere1.eng.rpath.com (vmware): using dnsName1-004 as primary contact address',
                'System added as part of target vsphere1.eng.rpath.com (vmware)',
            ])
        self.failUnless(entries[0].entry.startswith("Event type 'immediate system detect management interface' registered and will be enabled on "))
        # Make sure the zone is set
        self.failUnlessEqual(system.managing_zone.name, 'Local rBuilder')
        # Make sure we did set name, description etc
        self.failUnlessEqual(system.name, system.target_system_name)
        self.failUnlessEqual(system.description, system.target_system_description)

    def testIsManageable(self):
        # First, make sure these two users have the same credentials
        user1 = usersmodels.User.objects.get(user_name='JeanValjean1')
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        user3 = usersmodels.User.objects.get(user_name='JeanValjean3')
        self.failUnlessEqual(
            targetmodels.TargetUserCredentials.objects.get(
                target=self.tgt3, user=user1).target_credentials.pk,
            targetmodels.TargetUserCredentials.objects.get(
                target=self.tgt3, user=user2).target_credentials.pk,
        )

        system = models.System.objects.get(target_system_id='ec2aws-002')
        # Mark the system as being launched by user1
        system.launching_user = user1

        # Owner, so manageable
        self.mgr.user = user1
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), True)
        # same credentials
        self.mgr.user = user2
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), True)
        # Different credentials
        self.mgr.user = user3
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), False)

    def testGetSystemWithTarget(self):
        system = models.System.objects.get(target_system_id='vsphere1-002')
        url = 'inventory/systems/%s' % system.pk
        response = self._get(url, username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_with_target)

    def testAddLaunchedSystem(self):
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
            ssl_client_certificate = "ssl client certificate 001",
            ssl_client_key = "ssl client key 001",
        )
        dnsName = 'dns-name-1'
        system = self.newSystem(**params)
        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)
        for k, v in params.items():
            self.failUnlessEqual(getattr(system, k), v)
        # Make sure we have credentials
        stc = list(system.target_credentials.all())[0]
        self.failUnlessIn(stc.credentials_id,
            [ x.target_credentials_id
                for x in user2.target_user_credentials.all() ])
        self.failUnlessEqual(system.managing_zone.name,
            zmodels.Zone.LOCAL_ZONE)
        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['target_system_name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description,
            params['target_system_description'])

        # Test that it got persisted
        savedsystem = models.System.objects.get(pk=system.pk)

        resp = self._get('inventory/systems/%s' % system.system_id,
            username='admin', password='password')
        self.failUnlessEqual(resp.status_code, 200)
        self.failUnlessIn('<launching_user id="http://testserver/api/v1/users/3">',
            resp.content)

        def repl(item, a, b):
            try:
                return item.replace(a, b)
            except:
                # booleans don't support this operatiion
                return item

        # Another system that specifies a name and description
        params = dict((x, repl(y, '001', '002'))
            for (x, y) in params.items())
        params.update(name="system-name-002",
            description="system-description-002")
        system = self.newSystem(**params)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description, params['description'])

    def testCaptureSystem(self):
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
            ssl_client_certificate = "ssl client certificate 001",
            ssl_client_key = "ssl client key 001",
        )
        dnsName = 'dns-name-1'
        system = self.newSystem(**params)
        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        stage = projectmodels.Stage.objects.filter(project__name='chater-foo',
            name='Development')[0]
        params = dict(stage=stage, imageName="foo image")
        self.mgr.captureSystem(system, params)

class CollectionTest(XMLTestCaseStandin):
    fixtures = ['system_collection']

    def xobjResponse(self, url):
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        return systems

    def testGetDefaultCollection(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        self.assertXMLEquals(response.content, testsxml.systems_collection_xml,
            ignoreNodes=['actions', 'created_date', 'modified_date', 'created_by', 'modified_by' ])
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '201')
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
        self.assertEquals(systems.num_pages, '21')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=10;limit=10'))
        self.assertEquals(systems.previous_page, '')
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testGetNextPage(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.next_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '201')
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '10')
        self.assertEquals(systems.end_index, '19')
        self.assertEquals(systems.num_pages, '21')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=20;limit=10'))
        self.assertTrue(systems.previous_page.endswith(
            '/api/v1/query_sets/5/all;start_index=0;limit=10'))
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testGetPreviousPage(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.next_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.previous_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.count, '201')
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
        self.assertEquals(systems.num_pages, '21')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=10;limit=10'))
        self.assertEquals(systems.previous_page, '')
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testOrderBy(self):
        systems = self.xobjResponse('/api/v1/inventory/systems;order_by=name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            ['10', '100', '101', '102', '103', '104', '105', '106', '107', '108'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=name')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=name')
        self.assertEquals(systems.order_by, 'name')
        systems = self.xobjResponse('/api/v1/inventory/systems;order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            ['rPath Update Servic', '99', '98', '97', '96', '95', '94', '93', '92', '91'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name')
        self.assertEquals(systems.order_by, '-name')

    def testFilterBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,LIKE,3]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'3', u'13', u'23', u'30', u'31', u'32', u'33', u'34', u'35', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'rPath Update Servic', u'4', u'5', u'6', u'7', u'8', u'9', u'10', u'11', u'12'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,NOT_LIKE,3]')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'4', u'5', u'6', u'7', u'8', u'9', u'10', u'11', u'12', u'14'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals(systems.filter_by,
            '[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')

    def testOrderAndFilterBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,LIKE,3];order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53', u'43', u'39', u'38', u'37', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53', u'43', u'39', u'38', u'37', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')

    def testLimit(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;limit=5')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'rPath Update Servic', u'3', u'4', u'5', u'6'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=5')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=5;limit=5')
        self.assertEquals(systems.limit, '5')

    def testOrderAndFilterAndLimitBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;limit=5;filter_by=[name,LIKE,3];order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=5;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=5;limit=5;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.limit,
            '5')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')

    def testFilterByBoolean(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[local_uuid,IS_NULL,True]')
        # System 50 and the Update Service are the only one set up with a null
        # local_uuid in the fixture
        self.assertEquals([x.system_id for x in systems.system],
            [u'2', u'50'])

refProductDefintion1 = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-2.0.xsd" xmlns:xsi=
"http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd rpd-2.0.xsd" version="2.0">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>Awesome</productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>Awesome Version</productVersionDescription>
  <conaryRepositoryHostname>product.example.com</conaryRepositoryHostname>
  <conaryNamespace>exm</conaryNamespace>
  <imageGroup>group-awesome-dist</imageGroup>
  <baseFlavor>is: x86 x86_64</baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths/>
</productDefinition>
"""

class AntiRecursiveSaving(XMLTestCaseStandin):
    '''
    Generalized xobj test.  Make sure that when saving an object with child members, 
    in this case a system & a management interface, and we go to EDIT
    that system, we can't CREATE a new, non-existant management interface OR
    rename an existing management interface.   This, if present, would
    allow for priveledge escalation.
    '''
    def setUp(self):
        # make a new system
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="blinky", description="ghost")
        self.system.management_interface = models.ManagementInterface.objects.get(name='ssh')
        self.mgr.addSystem(self.system)

    def testCannotModifySubObjects(self):
        # make sure that fields in foreign key relationships, when saved,
        # do not allow editing the object represented by the FK.
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        xml = response.content
        self.assertEquals(response.status_code, 200)
        xml2 = xml.replace("Secure Shell (SSH)", "Special Hacker Interface (SHI)")
        response = self._put("inventory/systems/%s" % self.system.pk,
            data=xml2, username='admin', password='password')
        # this raised a 400 because one of the objects we tried to save
        # did not exist, bad input.
        self.assertEquals(response.status_code, 400)
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.content.find("Hacker Interface") == -1)

    def testCannotCreateNewSubObjects(self):
        # make sure we do not allow creating new sub objects on a put.
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        xml = response.content
        xml2 = xml.replace("management_interfaces/3", "management_interfaces/9999")
        xml2 = xml2.replace("Secure Shell (SSH)", "Special Hacker Interface (SHI)")
        response = self._put("inventory/systems/%s" % self.system.pk,
            data=xml2, username='admin', password='password')
        self.assertTrue(response.status_code, 200)
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.content.find("Hacker Interface") == -1)
        self.assertTrue(response.content.find("management_interfaces/4") == -1)

    def testPostShouldNotInjectNewSubObjects(self):
        # make sure we do not allow saving new sub objects on a post...
        response = self._post("inventory/systems",
            username='admin', password='password',
            data=testsxml.system_post_forge_object)
        # sub object didn't exist, so causes a 400, bad input
        self.assertEquals(response.status_code, 400)
        interfaces = list(models.ManagementInterface.objects.all())
        self.assertEquals(len(interfaces), 3, 'no interfaces added')

class DescriptorTestCase(XMLTestCase, test_utils.RepeaterMixIn):
    def setUp(self):
        XMLTestCase.setUp(self)
        self.setUpRepeaterClient()

    def testGetImageMetadataImportDescriptor(self):
        response = self._get("inventory/image_import_metadata_descriptor",
            username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        fields = obj.descriptor.dataFields.field
        # These are coming from test_utils, not from the real descriptor
        self.failUnlessEqual(
            [x.name for x in fields],
            ['metadata.owner', 'metadata.admin'])
