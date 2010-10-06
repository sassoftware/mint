import base64
import datetime
import os
import shutil
import tempfile
import time
from dateutil import tz
from xobj import xobj

from conary import versions

from django.db import connection
from django.template import TemplateDoesNotExist
from django.test import TestCase
from django.test.client import Client, MULTIPART_CONTENT

from mint.django_rest import deco
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import manager
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import testsxml
from mint.lib import x509

from testrunner import testcase

class XML(object):
    class OrderedDict(dict):
        def items(self):
            return sorted(dict.items(self))

    @classmethod
    def sortKey(cls, obj):
        return obj.tag

    def __init__(self, orderedChildren=False, ignoreNodes=None):
        self.orderedChildren = orderedChildren
        self.ignoreNodes = set(ignoreNodes or ())

    def normalize(self, node, parent=None):
        """
        This function will:
        * reorder child nodes if so requested
        * ignore some of the nodes
        * strip tail and mixed content
        """
        from lxml import etree
        attrib = self.OrderedDict(node.attrib)
        nsmap = self.OrderedDict(node.nsmap)

        if parent is None:
            nnode = etree.Element(node.tag, nsmap=nsmap, attrib=attrib)
        else:
            nnode = etree.SubElement(parent, node.tag, nsmap=nsmap, attrib=attrib)
        hasChildren = False
        for x in self._iterator(node):
            if x.tag in self.ignoreNodes:
                continue
            self.normalize(x, parent=nnode)
            hasChildren = True
        if not hasChildren:
            # We don't allow for mixed content
            nnode.text = self._strip(node.text)
        return nnode

    def _iterator(self, node):
        if self.orderedChildren:
            return sorted(node, key=self.sortKey)
        return node

    @classmethod
    def _strip(cls, data):
        if data is None:
            return None
        # Convert empty string to None
        return data.strip() or None

    @classmethod
    def nodediff(cls, node1, node2):
        """
        Return False if the nodes are identical, or some random data structure
        that is intended to be helpful otherwise.
        """
        if node1.tag != node2.tag:
            return "Different nodes"
        if node1.attrib != node2.attrib:
            return "Attributes: %s != %s" % (node1.attrib, node2.attrib)
        if node1.nsmap != node2.nsmap:
            return "Namespace maps: %s != %s" % (node1.nsmap, node2.nsmap)
        children1 = [ x for x in node1.getchildren() ]
        children2 = [ x for x in node2.getchildren() ]

        if children1 or children2:
            # Compare text in nodes that have children (mixed content).
            # We shouldn't have mixed content, but we need to be flexible.
            text1 = node1.text
            text2 = node2.text
            if text1 != text2:
                return "Node text: %s != %s" % (text1, text2)
            if len(children1) != len(children2):
                ch1set = set(x.tag for x in children1)
                ch2set = set(x.tag for x in children2)
                return "Child list: Counts %d != %d: A-B: %s; B-A: %s" % (
                    len(children1), len(children2),
                    ch1set - ch2set, ch2set - ch1set)
            for ch1, ch2 in zip(children1, children2):
                nd = cls.nodediff(ch1, ch2)
                if nd:
                    if ch1.tag == ch2.tag:
                        return ("Node %s" % ch1.tag, nd)
                    return ("Nodes %s, %s" % (ch1.tag, ch2.tag), nd)
            return False
        # No children, compare the text
        if node1.text == node2.text:
            return False
        return (node1.text, node2.text)

class XMLTestCase(TestCase, testcase.MockMixIn):

    def setUp(self):
        self.workDir = tempfile.mkdtemp(dir="/tmp", prefix="rbuilder-django-")
        mintCfg = os.path.join(self.workDir, "mint.cfg")
        file(mintCfg, "w")
        from mint import config
        config.RBUILDER_CONFIG = mintCfg
        self.client = Client()
        self.mgr = manager.Manager()
        self.localZone = self.mgr.sysMgr.getLocalZone()
        manager.repeatermgr.repeater_client = None

    def tearDown(self):
        TestCase.tearDown(self)
        self.unmock()

    def failUnlessIn(self, needle, haystack):
        self.failUnless(needle in haystack, "%s not in %s" % (needle,
            haystack))

    def assertXMLEquals(self, first, second, ignoreNodes=None):
        if ignoreNodes is None:
            ignoreNodes = ['time_created', 'time_updated', 'created_date',
                'last_available_update_refresh']
        from lxml import etree
        X = XML(orderedChildren=True, ignoreNodes=ignoreNodes)
        tree0 = X.normalize(etree.fromstring(first.strip()))
        tree1 = X.normalize(etree.fromstring(second.strip()))
        nd = X.nodediff(tree0, tree1)
        if nd:
            data0 = etree.tostring(tree0, pretty_print=True, with_tail=False)
            data1 = etree.tostring(tree1, pretty_print=True, with_tail=False)
            import difflib
            diff = '\n'.join(list(difflib.unified_diff(data1.splitlines(),
                    data0.splitlines()))[2:])
            # Set this to 1 if the diff is too complicated to read
            if 0:
                diff += "\nNode diff: %s" % (nd, )
            self.fail(diff)

    def newSystem(self, **kwargs):
        if 'managing_zone' not in kwargs:
            kwargs['managing_zone'] = self.localZone
        return models.System(**kwargs)

    def _addRequestAuth(self, username=None, password=None, **extra):
        if username:
            type, password = self._authHeader(username, password)
            extra[type] = password

        return extra

    def _get(self, path, data={}, username=None, password=None, follow=False, headers=None):
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.get(path, data, follow, **extra)

    def _post(self, path, data={}, content_type='application/xml',
             username=None, password=None, follow=False, headers=None):
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.post(path, data, content_type, follow, **extra)

    def _put(self, path, data={}, content_type='application/xml',
            username=None, password=None, follow=False, headers=None):
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.put(path, data, content_type, follow, **extra)

    def _delete(self, path, data={}, follow=False, username=None, password=None, headers=None):
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.delete(path, data, follow, **extra)

    def _authHeader(self, username, password):
        authStr = "%s:%s" % (username, password)
        return ("Authorization", "Basic %s" % base64.b64encode(authStr))

    def _saveZone(self):
        zone = models.Zone()
        zone.name = "Local Zone"
        zone.description = "Some local zone"
        zone.save()
        
        return zone

    def _saveSystem(self):
        system = models.System()
        system.name = 'testsystemname'
        system.description = 'testsystemdescription'
        system.local_uuid = 'testsystemlocaluuid'
        system.generated_uuid = 'testsystemgenerateduuid'
        system.ssl_client_certificate = 'testsystemsslclientcertificate'
        system.ssl_client_key = 'testsystemsslclientkey'
        system.ssl_server_certificate = 'testsystemsslservercertificate'
        system.registered = True
        system.current_state = self.mgr.sysMgr.systemState(
            models.SystemState.REGISTERED)
        system.managing_zone = self.localZone
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.save()

        network = models.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system
    
    def _saveManagementNode(self):
        zone = self._saveZone();
        
        management_node = models.ManagementNode()
        management_node.zone = zone
        management_node.managing_zone = zone
        management_node.name = 'test management node'
        management_node.description = 'test management node desc'
        management_node.local_uuid = 'test management node luuid'
        management_node.generated_uuid = 'test management node guuid'
        management_node.ssl_client_certificate = 'test management node client cert'
        management_node.ssl_client_key = 'test management node client key'
        management_node.ssl_server_certificate = 'test management node server cert'
        management_node.registered = True
        management_node.current_state = self.mgr.sysMgr.systemState(
            models.SystemState.REGISTERED)
        management_node.local = True
        management_node.management_node = True
        management_node.management_interface = models.ManagementInterface.objects.get(pk=1)
        management_node.node_jid = "superduperjid2@rbuilder.rpath"
        management_node.save()

        network = models.Network()
        network.ip_address = '2.2.2.2'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = management_node
        network.save()

        return management_node
    
    def _saveSystem2(self):
        system = models.System()
        system.name = 'testsystemname2'
        system.description = 'testsystemdescription2'
        system.local_uuid = 'testsystemlocaluuid2'
        system.generated_uuid = 'testsystemgenerateduuid2'
        system.ssl_client_certificate = 'testsystemsslclientcertificate2'
        system.ssl_client_key = 'testsystemsslclientkey2'
        system.ssl_server_certificate = 'testsystemsslservercertificate2'
        system.registered = True
        system.current_state = self.mgr.sysMgr.systemState(
            models.SystemState.REGISTERED)
        system.managing_zone = self.localZone
        system.save()

        network = models.Network()
        network.ip_address = '2.2.2.2'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork2.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system

    def _newJob(self, system, eventUuid, jobUuid, jobType, jobState=None):
        eventType = self.mgr.sysMgr.eventType(jobType)
        if jobState is None:
            jobState = models.JobState.RUNNING
        jobState = self.mgr.sysMgr.jobState(jobState)
        job = models.Job(job_uuid=jobUuid, event_type=eventType,
            job_state=jobState)
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        return job

    def cleanUp(self):
        shutil.rmtree(self.workDir, ignore_errors=True)

class InventoryTestCase(XMLTestCase):

    def testGetTypes(self):
        response = self._get('/api/inventory/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
        response = self._post('/api/inventory/?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
    def testPostTypes(self):
        response = self._post('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def notestPutTypes(self):
        response = self._put('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def testDeleteTypes(self):
        response = self._delete('/api/inventory/')
        self.assertEquals(response.status_code, 405)
       

class LogTestCase(XMLTestCase):

    def testGetLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        response = self._get('/api/inventory/log/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/log/', username="testuser", 
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
        response = self._get('/api/inventory/log/', username="testuser", 
            password="password")
        # Just remove lines with dates in them, it's easier to test for now.
        self.assertXMLEquals(response.content, testsxml.systems_log_xml,
            ignoreNodes = [ 'entry_date' ])

class ZonesTestCase(XMLTestCase):

    def testGetZones(self):
        models.Zone.objects.all().delete()
        zone = self._saveZone()
        # Create a system, just for kicks
        system = self.newSystem(name="foo", managing_zone=zone)
        system.save()
        response = self._get('/api/inventory/zones/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zones_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date' ])

    def testGetZoneAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveZone()
        response = self._get('/api/inventory/zones/2/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/zones/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetZone(self):
        models.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._get('/api/inventory/zones/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zone_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date' ])
        
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
        response = self._post('/api/inventory/zones/',
            data= testsxml.zone_post_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._post('/api/inventory/zones/',
            data=testsxml.zone_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPostZone(self):
        models.Zone.objects.all().delete()
        xml = testsxml.zone_post_xml
        response = self._post('/api/inventory/zones/',
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = models.Zone.objects.get(pk=1)
        self.assertXMLEquals(response.content, testsxml.zone_post_response_xml % \
            (zone.created_date.isoformat()))
        
        # test posting a second zone https://issues.rpath.com/browse/RBL-7229
        response = self._post('/api/inventory/zones/',
            data=testsxml.zone_post_2_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zones = models.Zone.objects.all()
        self.assertTrue(len(zones) == 2)
        
    def testPutZoneAuth(self):
        """
        Ensure we require admin to put zones
        """
        zone = models.Zone.objects.get(pk=1)
        response = self._put('/api/inventory/zones/1/', 
            data=testsxml.zone_put_xml % zone.created_date)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('/api/inventory/zones/1/', 
            data=testsxml.zone_put_xml % zone.created_date,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutZoneNotFound(self):
        """
        Ensure we return 404 if we update zone that doesn't exist
        """
        zone = models.Zone.objects.get(pk=1)
        try:
            response = self._put('/api/inventory/zones/1zcvxzvzgvsdzfewrew4t4tga34/', 
                data=testsxml.zone_put_xml % zone.created_date,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))
        
    def testPutZone(self):
        models.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._put('/api/inventory/zones/%d/' % zone.zone_id,
            data=testsxml.zone_put_xml % zone.created_date, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = models.Zone.objects.get(pk=1)
        self.assertTrue(zone.name == "zoneputname")
        self.assertTrue(zone.description == "zoneputdesc")
        
    def testDeleteZoneAuth(self):
        """
        Ensure we require admin to delete zones
        """
        response = self._delete('/api/inventory/zones/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._delete('/api/inventory/zones/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testDeleteZone(self):
        """
        Ensure we can delete zones
        """
        models.Zone.objects.all().delete()
        self._saveZone()
        response = self._delete('/api/inventory/zones/1/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        try:
            models.Zone.objects.get(pk=1)
            self.fail("Lookup should have failed due to deletion")
        except models.Zone.DoesNotExist:
            pass # what we expect
        
class ManagementInterfacesTestCase(XMLTestCase):

    def testGetManagementInterfaces(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('/api/inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interfaces_xml, ignoreNodes = [ 'created_date' ])

    def testGetManagementInterfacesAuth(self):
        """
        Ensure requires auth but not admin
        """
        response = self._get('/api/inventory/management_interfaces/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementInterface(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('/api/inventory/management_interfaces/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interface_xml, ignoreNodes = [ 'created_date' ])
        
    def testPutManagementInterfaceAuth(self):
        """
        Ensure we require admin to put
        """
        response = self._put('/api/inventory/management_interfaces/1/', 
            data=testsxml.management_interface_put_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('/api/inventory/management_interfaces/1/', 
            data=testsxml.management_interface_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutManagementInterfaceNotFound(self):
        """
        Ensure we return 404 if we update one that doesn't exist
        """
        try:
            response = self._put('/api/inventory/management_interfaces/1zcvxzvzgvsdzfewrew4t4tga34/', 
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
        response = self._put('/api/inventory/management_interfaces/1',
            data=testsxml.management_interface_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        mi = models.ManagementInterface.objects.get(pk=mi.pk)
        # name is read only, should not get changed
        self.assertTrue(mi.name != "thisnameshouldnotstick")
        self.assertTrue(mi.port == 123)
        
class SystemStatesTestCase(XMLTestCase):

    def testGetSystemStates(self):
        response = self._get('/api/inventory/system_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_states_xml, 
            ignoreNodes = [ 'created_date' ])

    def testGetSystemState(self):
        response = self._get('/api/inventory/system_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_state_xml, 
            ignoreNodes = [ 'created_date' ])
        
class NetworkTestCase(XMLTestCase):

    def testGetNetworks(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._get('/api/inventory/networks/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.networks_xml, ignoreNodes = [ 'created_date' ])

    def testGetNetworkAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveSystem()
        response = self._get('/api/inventory/networks/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/networks/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPutNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._put('/api/inventory/networks/1/', 
            data= testsxml.network_put_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._put('/api/inventory/networks/1/', 
            data=testsxml.network_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutNetworkNotFound(self):
        """
        Ensure we return 404 if we update network that doesn't exist
        """
        try:
            response = self._put('/api/inventory/networks/1zcvxzvzgvsdzfewrew4t4tga34/', 
                data=testsxml.network_put_xml,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))
        
    def testPutNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._put('/api/inventory/networks/1/',
            data=testsxml.network_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        network = models.Network.objects.get(pk=1)
        self.assertTrue(network.dns_name == "new.com")
        self.assertTrue(network.ip_address == "2.2.2.2")
        
    def testDeleteNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._delete('/api/inventory/networks/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._delete('/api/inventory/networks/1/', 
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testDeleteNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        network = models.Network.objects.get(pk=1)
        self.assertTrue(network is not None)
        response = self._delete('/api/inventory/networks/1/', 
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
        response = self._get('/api/inventory/networks/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.network_xml, ignoreNodes = [ 'created_date' ])

class ManagementNodesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        models.ManagementNode.objects.all().delete()

    def testManagementNodeSave(self):
        zone = self._saveZone()
        # make sure state gets set to unmanaged
        management_node = models.ManagementNode(name="mgoblue",
            description="best node ever", zone=zone, managing_zone=zone)
        _eq = self.failUnlessEqual
        _eq(management_node.current_state_id, None)
        management_node.save()
        assert(management_node.management_node)
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
        response = self._get('/api/inventory/management_nodes/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_nodes_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                             management_node.current_state.created_date.isoformat(),
                                             management_node.created_date.isoformat()))

    def testGetManagementNodeAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveManagementNode()
        response = self._get('/api/inventory/management_nodes/1/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/management_nodes/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNode(self):
        management_node = self._saveManagementNode()
        response = self._get('/api/inventory/management_nodes/1/',
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
        assert(new_management_node.management_node)
        
    def testPostManagementNodeAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        response = self._post('/api/inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._post('/api/inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
        response = self._post('/api/inventory/management_nodes/', 
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostManagementNode(self):
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        xml = testsxml.management_node_post_xml
        response = self._post('/api/inventory/management_nodes/', 
            data=xml, content_type='text/xml', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=1)
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
        response = self._get('/api/inventory/zones/%d/management_nodes/' % management_node.zone.zone_id,
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
        response = self._get('/api/inventory/zones/%d/management_nodes/1/' % management_node.zone.zone_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/zones/%d/management_nodes/1/' % management_node.zone.zone_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNodeForZone(self):
        management_node = self._saveManagementNode()
        response = self._get('/api/inventory/zones/%d/management_nodes/1/' % management_node.zone.zone_id,
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
        assert(new_management_node.management_node)
        
    def testAddManagementNodeSave(self):
        management_node = self._saveManagementNode()
        management_node.management_node = False
        assert(management_node.management_node == False)
        # now save, which should automatically set management_node
        management_node.save()
        assert(management_node.management_node)
        
    def testPostManagementNodeForZoneAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        response = self._post('/api/inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._post('/api/inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
        response = self._post('/api/inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostManagementNodeForZone(self):
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        xml = testsxml.management_node_zone_post_xml
        response = self._post('/api/inventory/zones/%d/management_nodes/' % zone.zone_id, 
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=1)
        management_node_xml = testsxml.management_node_zone_post_response_xml.replace(
            '<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (management_node.registration_date.isoformat()))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.networks.all()[0].created_date.isoformat(), 
             management_node.current_state.created_date.isoformat(),
             management_node.created_date.isoformat()))

class NetworksTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.system.save()
        
    def testExtractNetworkToUse(self):
        
        # try a net with no required/active nets, but only one net
        network = models.Network(dns_name="foo.com", active=False, required=False)
        network.system = self.system
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # Second network showed up, we assume no network
        network2 = models.Network(dns_name = "foo2.com", active=False,
            required=False)
        network2.system = self.system
        network2.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        self.failUnlessEqual(net, None)

        # try one with required only
        network.required = True
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # try one with active only
        network.required = False
        network.active = True
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # now add a required one in addition to active one to test order
        network3 = models.Network(dns_name="foo3.com", active=False, required=True)
        network3.system = self.system
        network3.save()
        self.failUnlessEqual(
            sorted((x.dns_name, x.required, x.active)
                for x in self.system.networks.all()),
            [
                ('foo.com', False, True),
                ('foo2.com', False, False),
                ('foo3.com', True, False),
            ])
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        self.failUnlessEqual(net.network_id, network3.network_id)

class SystemsTestCase(XMLTestCase):
    fixtures = ['system_job', 'targets']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mock_scheduleSystemRegistrationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mockGetRmakeJob_called = False
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = False
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr.scheduleSystemRegistrationEvent = self.mock_scheduleSystemRegistrationEvent
        self.mgr.sysMgr.scheduleSystemDetectMgmtInterfaceEvent = \
            self.mock_scheduleSystemDetectMgmtInterfaceEvent
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def tearDown(self):
        XMLTestCase.tearDown(self)

    def mock_scheduleSystemRegistrationEvent(self, system):
        self.mock_scheduleSystemRegistrationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
        
    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def mock_scheduleSystemDetectMgmtInterfaceEvent(self, system):
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = True

    def testBenchmarkQueryCount(self):
        # Clean up
        models.System.objects.all().delete()
        count = 50
        zone = self.localZone
        flv = 'is:x86'
        ver0 = models.Version(full='/localhost@rpath:linux/1-1-1',
            ordering='1234567890.12', flavor=flv)
        ver0.save()
        ver01 = models.Version(full='/localhost@rpath:linux/1-2-1',
            ordering='1234567890.13', flavor=flv)
        ver01.save()
        trv0 = models.Trove(name='group-foo', version=ver0, flavor=flv)
        trv0.save()
        trv0.available_updates.add(ver01)

        eventTypeCount = len(models.EventType.EVENT_TYPES)
        for i in range(count):
            ver = models.Version(full='/localhost@rpath:linux/2-1-%d' % i,
                ordering=str(1234567891.12 + 10 * i), flavor=flv)
            ver.save()
            ver1 = models.Version(full='/localhost@rpath:linux/2-2-%d' % i,
                ordering=str(1234567891.22 + 10 * i), flavor=flv)
            ver1.save()
            trv = models.Trove(name='group-foo', version=ver, flavor=flv)
            trv.save()
            trv.available_updates.add(ver1)

            system = self.newSystem(
                local_uuid = "local-uuid-%03d" % i,
                generated_uuid = "generated-uuid-%03d" % i,
                name = "name-%03d" % i,
                description = "description-%03d" % i,
                managing_zone = zone,
            )
            system.save()
            system.installed_software.add(trv0)
            system.installed_software.add(trv)
            network = models.Network(
                dns_name = "dns-name-%3d" % i,
                system = system)
            network.save()

            eventUuid = "event-uuid-%03d" % i
            jobUuid = "rmake-job-%03d" % i
            eventTypeName = models.EventType.EVENT_TYPES[i % eventTypeCount][0]
            self._newJob(system, eventUuid, jobUuid, eventTypeName)

        class Request(object):
            def build_absolute_uri(slf, href=None):
                return "blah%s" % href
        request = Request()
        from django.db import settings
        settings.DEBUG = True

        try:
            connection.queries = []
            t0 = time.time()
            systems = self.mgr.getSystems(request)
            t1 = time.time()
            print "Systems generated: %d: %.2fs" % (len(systems.system), t1 - t0)

            f = deco.return_xml(lambda *args, **kwargs: systems)
            f(None, request)
            t2 = time.time()
            print "return_xml decorator: %.2fs" % (t2 - t1)

            qcount = len(connection.queries)
            self.failUnlessEqual(len(systems.system), count)
            if qcount > count:
                f = file("/tmp/queries", "w")
                for x in connection.queries:
                    f.write("%s\n" % x['sql'])
                    f.write("\n\n")
                f.close()
            self.failUnless(qcount < count,
                "Expected fewer than %s queries; got %s" % (count, qcount))
        finally:
            connection.queries = []
            settings.DEBUG = False

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

        self._newJob(system, eventUuid, 'rmakejob007',
            models.EventType.SYSTEM_REGISTRATION)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
</system>
"""
        # No event uuid, no auth; this fails
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params)
        self.failUnlessEqual(response.status_code, 401)

        # Bad event uuid; this fails
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid + '-bogus'})
        self.failUnlessEqual(response.status_code, 401)

        # Good uuid, bad system
        response = self._put('/api/inventory/systems/%s' % system2.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid validation, this works
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 200)

        # user/pass auth, this works
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)

        # uuid valid, bad auth - this fails
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='bogus',
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid bad, goodauth - this fails
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='password',
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
        response = self._put('/api/inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml)
        self.failUnlessEqual(response.status_code, 401)
        
        # fail if regular user
        response = self._put('/api/inventory/systems/%d/' % system.system_id,
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
        response = self._put('/api/inventory/systems/%d/' % system.system_id,
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
    <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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
        url = "/api/inventory/systems"
        response = self._post(url, data=xml)
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
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            management_node=True,
            local_uuid='123', generated_uuid='456')
        system.zone = zone
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.REGISTERED)
        
        # make sure we did not schedule registration
        self.failUnlessEqual(self.mock_scheduleSystemRegistrationEvent_called,
            False)
        
        # make sure we did not scheduled poll event since this is a management node
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
        Ensure a network is not required per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system = self.newSystem(name="foo", description="bar")
        self.mgr.addSystem(system)
        
    def testPostSystemNoNetwork(self):
        """
        Ensure a network is not required per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_no_network_xml
        response = self._post('/api/inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        try:
            models.System.objects.get(pk=1)
        except models.System.DoesNotExist:
            self.assertTrue(False) # should exist
        
    def testGetSystems(self):
        system = self._saveSystem()
        response = self._get('/api/inventory/systems/', username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.systems_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date' ])

    def testGetSystemAuth(self):
        """
        Ensure requires auth but not admin
        """
        system = self._saveSystem()
        response = self._get('/api/inventory/systems/%d/' % system.system_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/systems/%d/' % system.system_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testGetSystemDoesntExist(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('/api/inventory/systems/86753021/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 404)

    def testGetSystem(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('/api/inventory/systems/%d/' % system.system_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'time_created', 'time_updated' ])

    def testGetSystemWithTarget(self):
        models.System.objects.all().delete()
        target = rbuildermodels.Targets(pk=1, targettype='testtargettype',
            targetname='testtargetname')
        target.save()
        system = self._saveSystem()
        system.target = target
        system.save()
        response = self._get('/api/inventory/systems/%d/' % system.system_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_target_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'time_created', 'time_updated' ])
        
    def testPostSystemAuth(self):
        """
        Ensure wide open for rpath-tools usage
        """
        system_xml = testsxml.system_post_xml
        response = self._post('/api/inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        
    def testPostSystem(self):
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml
        response = self._post('/api/inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=1)
        system_xml = testsxml.system_post_xml_response.replace('<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (system.registration_date.isoformat()))
        self.assertXMLEquals(response.content, system_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'ssl_client_certificate',
                            'time_created', 'time_updated'])
        # Unfortunately, we can't mock modules since we don't control Django's
        # class loading. So we ignore the cert in the previous step and we
        # test it with xobj (it is different every time)
        obj = xobj.parse(response.content)
        xobjmodel = obj.system
        self.failUnless(xobjmodel.ssl_client_certificate.startswith(
            '-----BEGIN CERTIFICATE-----'),
            repr(xobjmodel.ssl_client_certificate))

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
        response = self._post('/api/inventory/systems/',
            data=xmlTempl % params,
            headers={ 'X-rPath-Management-Zone' : zoneName })
        self.failUnlessEqual(response.status_code, 200)

    def testPostSystemDupUuid(self):
        # add the first system
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml_dup
        response = self._post('/api/inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=1)
        self.failUnlessEqual(system.name, "testsystemname")
        
        # add it with same uuids but with different name to make sure
        # we get back same system with updated prop
        system_xml = testsxml.system_post_xml_dup2
        response = self._post('/api/inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        this_system = models.System.objects.get(pk=1)
        self.failUnlessEqual(this_system.name, "testsystemnameChanged")

    def testPutSystemManagementInterface(self):
        system = self._saveSystem()

        # Test that a mgmt interface can be changed.
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # Test that a mgmt interface can be added.
        system.management_interface = None
        system.save()
        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml, 
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # DISABLED TEST, no support for this
        # Test that mgmt interface can be deleted
        # response = self._put('/api/inventory/systems/%s' % system.pk,
            # data=testsxml.system_delete_mgmt_interface_put_xml, 
            # username="admin", password="password")
        # self.assertEquals(response.status_code, 200)
        # system = models.System.objects.get(pk=system.pk)
        # self.assertEquals(system.management_interface, None)

    def testGetSystemLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        models.System.objects.all().delete()
        response = self._post('/api/inventory/systems/',
            data=testsxml.system_post_xml)
        self.assertEquals(response.status_code, 200)
        
        response = self._get('/api/inventory/systems/1/system_log/')
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/systems/1/system_log/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        

    def testGetSystemLog(self):
        models.System.objects.all().delete()
        response = self._post('/api/inventory/systems/', 
            data=testsxml.system_post_xml)
        self.assertEquals(response.status_code, 200)
        response = self._get('/api/inventory/systems/1/system_log/',
            username="testuser", password="password")
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
        cu.execute("INSERT INTO jobs (job_uuid) VALUES (%s)",
            [ bootUuid ])
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        # Create a system with just a name
        system = self.newSystem(name = 'blippy')
        system.save()
        # Create a job
        eventType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        job = models.Job(job_uuid = 'rmakeuuid001', event_type=eventType,
            job_state=self.mgr.sysMgr.jobState(models.JobState.RUNNING))
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
        tgt1 = rbuildermodels.Targets.objects.get(pk=1) # vsphere1
        system1 = self.newSystem(name="bloppy", target=tgt1,
            target_system_id=targetSystemId,
            target_system_name=targetSystemName,
            target_system_description=targetSystemDescription,
            target_system_state=targetSystemState)
        system1.save()
        self.mgr.sysMgr.log_system(system1, "Log message from target system")

        # Create a job
        eventType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        job = models.Job(job_uuid = 'rmakeuuid001', event_type=eventType,
            job_state=self.mgr.sysMgr.jobState(models.JobState.RUNNING))
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        # Create a job
        eventType = models.EventType.objects.get(
            name = models.EventType.SYSTEM_POLL)
        job = models.Job(job_uuid=jobUuid, event_type=eventType,
            job_state=self.mgr.sysMgr.jobState(models.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        # Pass bogus event uuid, we should not update
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid + "bogus", jobUuid=jobUuid + "bogus",
            jobState=jobState, zoneId=self.localZone.zone_id)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        # We expect nothing to be updated, since there's no such job
        job = models.Job.objects.get(pk=job.pk)
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
        job = models.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set eventUuid to be correct
        params['eventUuid'] = eventUuid
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = models.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)

        # Make sure that pasting a system job with just the event uuid and job
        # info works (i.e. without the local and generated uuids)
        xmlTempl = """\
<system>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
"""
        jobState = 'Failed'
        params['jobState'] = jobState

        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = models.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)

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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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
            active=False, required=True, system=system)
        network.save()
        xml = network.to_xml()
        self.failUnlessIn("<active>false</active>", xml)
        self.failUnlessIn("<required>true</required>", xml)

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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        # Create a system with just a name
        system = self.newSystem(name = 'blippy')
        system.save()
        # Create a job
        eventType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        job = models.Job(job_uuid = 'rmakeuuid001', event_type=eventType,
            job_state=self.mgr.sysMgr.jobState(models.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        response = self._post('/api/inventory/systems', data=xml)
        self.failUnlessEqual(response.status_code, 200)

        # Look up log entries
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                "Unable to register event 'on-demand polling event': no networking information",
                "Unable to register event 'standard polling event': no networking information",
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xml, username="testuser", password="password")
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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xml, username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.local_uuid, localUuid)
        self.failUnlessEqual(system.generated_uuid, generatedUuid)
        self.failUnlessEqual(system.current_state.name, systemState)

class SystemCertificateTestCase(XMLTestCase):
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

class SystemStateTestCase(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
        models.Job.getRmakeJob = self.mockGetRmakeJob
    
    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testSetCurrentState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        jobState = "Completed"

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        self._newJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION)

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
  <managing_zone href="http://testserver/api/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params

        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xml, headers = { 'X-rBuilder-Event-UUID' : eventUuid1 })
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
        self._newJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_POLL)

        params = dict(eventUuid=eventUuid2, jobUuid=jobUuid2, jobState=jobState,
            zoneId=self.localZone.zone_id)

        xml = xmlTempl % params

        response = self._put('/api/inventory/systems/%s' % system.pk,
            data=xml, headers = { 'X-rBuilder-Event-UUID' : eventUuid1 })
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

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        stateCompleted = self.mgr.sysMgr.jobState(models.JobState.COMPLETED)
        stateFailed = self.mgr.sysMgr.jobState(models.JobState.FAILED)

        job1 = self._newJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION)
        job2 = self._newJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_POLL)
        job3 = self._newJob(system, eventUuid3, jobUuid3,
            models.EventType.SYSTEM_POLL_IMMEDIATE)

        UNMANAGED = models.SystemState.UNMANAGED
        REGISTERED = models.SystemState.REGISTERED
        RESPONSIVE = models.SystemState.RESPONSIVE
        NONRESPONSIVE = models.SystemState.NONRESPONSIVE
        NONRESPONSIVE_NET = models.SystemState.NONRESPONSIVE_NET
        NONRESPONSIVE_HOST = models.SystemState.NONRESPONSIVE_HOST
        NONRESPONSIVE_SHUTDOWN = models.SystemState.NONRESPONSIVE_SHUTDOWN
        NONRESPONSIVE_SUSPENDED = models.SystemState.NONRESPONSIVE_SUSPENDED
        DEAD = models.SystemState.DEAD
        MOTHBALLED = models.SystemState.MOTHBALLED

        tests = [
            (job1, stateCompleted, UNMANAGED, None),
            (job1, stateCompleted, REGISTERED, None),
            (job1, stateCompleted, RESPONSIVE, None),
            (job1, stateCompleted, NONRESPONSIVE_HOST, None),
            (job1, stateCompleted, NONRESPONSIVE_NET, None),
            (job1, stateCompleted, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateCompleted, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateCompleted, NONRESPONSIVE, None),
            (job1, stateCompleted, DEAD, None),
            (job1, stateCompleted, MOTHBALLED, None),

            (job1, stateFailed, UNMANAGED, None),
            (job1, stateFailed, REGISTERED, None),
            (job1, stateFailed, RESPONSIVE, None),
            (job1, stateFailed, NONRESPONSIVE_HOST, None),
            (job1, stateFailed, NONRESPONSIVE_NET, None),
            (job1, stateFailed, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateFailed, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateFailed, NONRESPONSIVE, None),
            (job1, stateFailed, DEAD, None),
            (job1, stateFailed, MOTHBALLED, None),

            (job2, stateCompleted, UNMANAGED, RESPONSIVE),
            (job2, stateCompleted, REGISTERED, RESPONSIVE),
            (job2, stateCompleted, RESPONSIVE, RESPONSIVE),
            (job2, stateCompleted, NONRESPONSIVE_HOST, RESPONSIVE),
            (job2, stateCompleted, NONRESPONSIVE_NET, RESPONSIVE),
            (job2, stateCompleted, NONRESPONSIVE_SHUTDOWN, RESPONSIVE),
            (job2, stateCompleted, NONRESPONSIVE_SUSPENDED, RESPONSIVE),
            (job2, stateCompleted, NONRESPONSIVE, RESPONSIVE),
            (job2, stateCompleted, DEAD, RESPONSIVE),
            (job2, stateCompleted, MOTHBALLED, RESPONSIVE),

            (job2, stateFailed, UNMANAGED, None),
            (job2, stateFailed, REGISTERED, NONRESPONSIVE),
            (job2, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job2, stateFailed, NONRESPONSIVE_HOST, None),
            (job2, stateFailed, NONRESPONSIVE_NET, None),
            (job2, stateFailed, NONRESPONSIVE_SHUTDOWN, None),
            (job2, stateFailed, NONRESPONSIVE_SUSPENDED, None),
            (job2, stateFailed, NONRESPONSIVE, None),
            (job2, stateFailed, DEAD, None),
            (job2, stateFailed, MOTHBALLED, None),

            (job3, stateCompleted, UNMANAGED, RESPONSIVE),
            (job3, stateCompleted, REGISTERED, RESPONSIVE),
            (job3, stateCompleted, RESPONSIVE, RESPONSIVE),
            (job3, stateCompleted, NONRESPONSIVE_HOST, RESPONSIVE),
            (job3, stateCompleted, NONRESPONSIVE_NET, RESPONSIVE),
            (job3, stateCompleted, NONRESPONSIVE_SHUTDOWN, RESPONSIVE),
            (job3, stateCompleted, NONRESPONSIVE_SUSPENDED, RESPONSIVE),
            (job3, stateCompleted, NONRESPONSIVE, RESPONSIVE),
            (job3, stateCompleted, DEAD, RESPONSIVE),
            (job3, stateCompleted, MOTHBALLED, RESPONSIVE),

            (job3, stateFailed, UNMANAGED, None),
            (job3, stateFailed, REGISTERED, NONRESPONSIVE),
            (job3, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job3, stateFailed, NONRESPONSIVE_HOST, None),
            (job3, stateFailed, NONRESPONSIVE_NET, None),
            (job3, stateFailed, NONRESPONSIVE_SHUTDOWN, None),
            (job3, stateFailed, NONRESPONSIVE_SUSPENDED, None),
            (job3, stateFailed, NONRESPONSIVE, None),
            (job3, stateFailed, DEAD, None),
            (job3, stateFailed, MOTHBALLED, None),
        ]
        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s): %s -> %s (expected: %s)" % (
                (job.event_type.name, jobState.name, oldState, ret, newState))
            self.failUnlessEqual(ret, newState, msg)

        # Time-based tests
        tests = [
            (job2, stateFailed, UNMANAGED, None),
            (job2, stateFailed, REGISTERED, NONRESPONSIVE),
            (job2, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job2, stateFailed, NONRESPONSIVE_HOST, DEAD),
            (job2, stateFailed, NONRESPONSIVE_NET, DEAD),
            (job2, stateFailed, NONRESPONSIVE_SHUTDOWN, DEAD),
            (job2, stateFailed, NONRESPONSIVE_SUSPENDED, DEAD),
            (job2, stateFailed, NONRESPONSIVE, DEAD),
            (job2, stateFailed, DEAD, MOTHBALLED),
            (job2, stateFailed, MOTHBALLED, None),

            (job3, stateFailed, UNMANAGED, None),
            (job3, stateFailed, REGISTERED, NONRESPONSIVE),
            (job3, stateFailed, RESPONSIVE, NONRESPONSIVE),
            (job3, stateFailed, NONRESPONSIVE_HOST, DEAD),
            (job3, stateFailed, NONRESPONSIVE_NET, DEAD),
            (job3, stateFailed, NONRESPONSIVE_SHUTDOWN, DEAD),
            (job3, stateFailed, NONRESPONSIVE_SUSPENDED, DEAD),
            (job3, stateFailed, NONRESPONSIVE, DEAD),
            (job3, stateFailed, DEAD, MOTHBALLED),
            (job3, stateFailed, MOTHBALLED, None),
        ]

        self.mgr.cfg.deadStateTimeout = 10
        self.mgr.cfg.mothballedStateTimeout = 10
        stateChange = self.mgr.sysMgr.now() - datetime.timedelta(days=10)
        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            system.state_change_date = stateChange
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s): %s -> %s (expected: %s)" % (
                (job.event_type.name, jobState.name, oldState, ret, newState))
            self.failUnlessEqual(ret, newState, msg)

class SystemVersionsTestCase(XMLTestCase):
    fixtures = ['system_job']
    
    def setUp(self):
        XMLTestCase.setUp(self)
        self.mintConfig = self.mgr.cfg
        from django.conf import settings
        self.mintConfig.dbPath = settings.DATABASE_NAME
        self.mock_scheduleSystemRegistrationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mock_set_available_updates_called = False
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr.scheduleSystemRegistrationEvent = self.mock_scheduleSystemRegistrationEvent
        manager.versionmgr.VersionManager.set_available_updates = \
            self.mock_set_available_updates
        models.Job.getRmakeJob = self.mockGetRmakeJob
        
    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def mock_set_available_updates(self, trove, *args, **kwargs):
        self.mock_set_available_updates_called = True

    def mock_scheduleSystemRegistrationEvent(self, system):
        self.mock_scheduleSystemRegistrationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
 
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
        trove.last_available_update_refresh = \
            datetime.datetime.now(tz.tzutc())
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

        trove.available_updates.add(version_update)
        trove.available_updates.add(version_update2)
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
        trove2.last_available_update_refresh = \
            datetime.datetime.now(tz.tzutc())
        trove2.save()

        self.trove = trove
        self.trove2 = trove2

    def testGetSystemWithVersion(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        response = self._get('/api/inventory/systems/%s/' % system.pk,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_version_xml % \
            (self.trove.last_available_update_refresh.isoformat(),
             self.trove2.last_available_update_refresh.isoformat(),
             system.networks.all()[0].created_date.isoformat(),
             system.created_date.isoformat()),
            ignoreNodes = [ 'created_date' ])

    def testGetInstalledSoftwareRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        url = '/api/inventory/systems/%s/installed_software/' % system.pk
        response = self._get(url, username="testuser", password="password")
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

        url = '/api/inventory/systems/%s/installed_software/' % system.pk
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

        response = self._get('/api/inventory/systems/%s' % system.pk,
            username="testuser", password="password")
        self.assertXMLEquals(response.content, 
            testsxml.system_available_updates_xml,
            ignoreNodes=['created_date', 'last_available_update_refresh'])

    def testSetInstalledSoftwareSystemRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        eventUuid = 'eventuuid007'
        jobUuid = 'rmakejob007'
        self._newJob(system, eventUuid, jobUuid, models.EventType.SYSTEM_POLL)

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

        url = '/api/inventory/systems/%s/' % system.pk
        response = self._put(url, data=data,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        # Weak attempt to see if the response is XML
        exp = '<system id="http://testserver/api/inventory/systems/%s">' % system.pk
        self.failUnless(exp in response.content)

        nsystem = models.System.objects.get(system_id=system.pk)
        self.failUnlessEqual(
            [ (x.name, (x.version.full, x.version.ordering, x.version.flavor,
                x.version.label, x.version.revision), x.flavor)
                for x in nsystem.installed_software.all() ],
            [
                ('group-chater-appliance',
                 ('/chater.eng.rpath.com@rpath:chater-1-devel/1-2-1',
                     '1234567890.12',
                     'is: x86',
                     'chater.eng.rpath.com@rpath:chater-1-devel',
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
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 200)

        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.name, "testsystemname")

class EventTypeTestCase(XMLTestCase):

    def testGetEventTypes(self):
        response = self._get('/api/inventory/event_types/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_types_xml)

    def testGetEventType(self):
        response = self._get('/api/inventory/event_types/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_type_xml)
        
    def testPutEventTypeAuth(self):
        """
        Ensure we require admin to put event types
        """
        response = self._put('/api/inventory/event_types/1/', 
            data= testsxml.event_type_put_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)
        
        response = self._put('/api/inventory/event_types/1/', 
            data=testsxml.event_type_put_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testPutEventType(self):
        models.EventType.objects.all().delete()
        event_type = models.EventType(name="foo", description="bar", priority=110)
        event_type.save()
        self.assertTrue(event_type.priority == 110)
        response = self._put('/api/inventory/event_types/1/', 
            data=testsxml.event_type_put_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = models.EventType.objects.get(pk=1)
        self.assertTrue(event_type.priority == 1)
        
    def testPutEventTypeName(self):
        """
        Do not allow changing the event type name https://issues.rpath.com/browse/RBL-7171
        """
        models.EventType.objects.all().delete()
        event_type = models.EventType(name=models.EventType.SYSTEM_POLL, description="bar", priority=110)
        event_type.save()
        self.failUnlessEqual(event_type.name, models.EventType.SYSTEM_POLL)
        response = self._put('/api/inventory/event_types/%d/' % event_type.pk,
            data=testsxml.event_type_put_name_change_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = models.EventType.objects.get(pk=event_type.pk)
        # name should not have changed
        self.failUnlessEqual(event_type.name, models.EventType.SYSTEM_POLL)

class SystemEventTestCase(XMLTestCase):
    
    def setUp(self):
        XMLTestCase.setUp(self)

        # need a system
        network = models.Network(ip_address='1.1.1.1')
        self.system = self.newSystem(name="mgoblue", description="best appliance ever")
        self.system.save()
        network.system = self.system
        self.system.networks.add(network)
        self.system.save()
        
        # start with no logs/system events
        models.SystemLog.objects.all().delete()
        models.SystemEvent.objects.all().delete()
        
        self.mock_dispatchSystemEvent_called = False
        self.mgr.sysMgr.dispatchSystemEvent = self.mock_dispatchSystemEvent

    def mock_dispatchSystemEvent(self, event):
        self.mock_dispatchSystemEvent_called = True
    
    def testGetSystemEventsRest(self):
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        act_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        response = self._get('/api/inventory/system_events/',
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
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self._get('/api/inventory/system_events/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 401)
        
        response = self._get('/api/inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemEventRest(self):
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self._get('/api/inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))
    
    def testGetSystemEvent(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        new_event = self.mgr.getSystemEvent(event.system_event_id)
        assert(new_event == event)
        
    def testGetSystemEvents(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        act_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.mgr.getSystemEvents()
        assert(len(SystemEvents.system_event) == 2)
        
    def testDeleteSystemEvent(self):
        # add an event
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
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
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
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
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
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
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=poll_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)
        
    def testScheduleSystemPollNowEvent(self):
        self.mgr.scheduleSystemPollNowEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called)
        
        pn_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=pn_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.now(tz.tzutc()))
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)
        
    def testScheduleSystemRegistrationEvent(self):
        self.mgr.scheduleSystemRegistrationEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called)
        
        registration_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=registration_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.now(tz.tzutc()))
        
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
        # registration event should be dispatched now
        registration_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=registration_event, priority=registration_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollNowEvent(self):
        # poll now event should be dispatched now
        poll_now_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_now_event, priority=poll_now_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollEvent(self):
        # poll event should not be dispatched now
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_event, priority=poll_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called == False)
        
    def testPostSystemEventAuth(self):
        """
        Ensure requires auth but not admin
        """
        url = '/api/inventory/systems/%d/system_events/' % self.system.system_id
        system_event_post_xml = testsxml.system_event_post_xml
        response = self._post(url, data=system_event_post_xml)
        self.assertEquals(response.status_code, 401)
        
        response = self._post(url,
            data=system_event_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testPostSystemEvent(self):
        url = '/api/inventory/systems/%d/system_events/' % self.system.system_id
        system_event_post_xml = testsxml.system_event_post_xml
        response = self._post(url,
            data=system_event_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        system_event = models.SystemEvent.objects.get(pk=1)
        system_event_xml = testsxml.system_event_xml % \
            (system_event.time_created.isoformat(),
            system_event.time_enabled.isoformat())
        self.assertXMLEquals(response.content, system_event_xml,
            ignoreNodes='time_created')
        
class SystemEventProcessingTestCase(XMLTestCase):
    
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']
    
    def setUp(self):
        XMLTestCase.setUp(self)

        self.mintConfig = self.mgr.cfg
        self.mgr.sysMgr.cleanupSystemEvent = self.mock_cleanupSystemEvent
        self.mgr.sysMgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.sysMgr._extractNetworkToUse = self.mock_extractNetworkToUse
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
            models.EventType.SYSTEM_REGISTRATION)

        # remove the registration event and ensure we get the on demand poll event next
        event.delete()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_POLL_IMMEDIATE)

        # remove the poll now event and ensure we get the standard poll event next
        event.delete()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_POLL)

        # add another poll event with a higher priority but a future time 
        # and make sure we don't get it (because of the future registration time)
        orgPollEvent = event
        new_poll_event = models.SystemEvent(system=orgPollEvent.system, 
            event_type=orgPollEvent.event_type, priority=orgPollEvent.priority + 1,
            time_enabled=orgPollEvent.time_enabled + datetime.timedelta(1))
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
            models.EventType.SYSTEM_REGISTRATION)
        event.delete()
        
        # make sure next one is poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_POLL_IMMEDIATE)
        self.mgr.sysMgr.processSystemEvents()
        
        # make sure the event was removed and that we have the next poll event 
        # for this system now
        try:
            poll_now_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
            event = models.SystemEvent.objects.get(system_event_id=event.system_event_id,
                event_type=poll_now_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        local_system = poll_event.system_events.all()[0]
        event = models.SystemEvent.objects.get(system=local_system, event_type=poll_event)
        self.failIf(event is None)
        
    def testProcessSystemEventsNoTrigger(self):
        # make sure registration event doesn't trigger next poll event
        # start with no regular poll events
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
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
            models.EventType.SYSTEM_REGISTRATION)
        self.mgr.sysMgr.processSystemEvents()
        
        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

    def testDispatchSystemEvent(self):
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        poll_now_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
        act_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)

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

class SystemEventProcessing2TestCase(XMLTestCase):
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']

    def setUp(self):
        XMLTestCase.setUp(self)

        class RepeaterClient(object):
            methodsCalled = []

            class CimParams(object):
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
                def __eq__(self, other):
                    return self.__dict__ == other.__dict__
                def __repr__(self):
                    return repr(self.__dict__)

            class ResultsLocation(object):
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
                def __eq__(self, other):
                    return self.__dict__ == other.__dict__
                def __repr__(self):
                    return repr(self.__dict__)

            def register(slf, *args, **kwargs):
                return slf._action('register', *args, **kwargs)

            def poll(slf, *args, **kwargs):
                return slf._action('poll', *args, **kwargs)

            def _action(slf, method, *args, **kwargs):
                count = len(slf.methodsCalled)
                slf.methodsCalled.append((method, args, kwargs))
                return "uuid%03d" % count, object()

        class RepeaterMgr(object):
            repeaterClient = RepeaterClient()

        self.mgr.repeaterMgr = RepeaterMgr()
        self.system2 = system = self.newSystem(name="hey")
        system.save()
        network2 = models.Network(ip_address="2.2.2.2", active=True)
        network3 = models.Network(ip_address="3.3.3.3", required=True)
        system.networks.add(network2)
        system.networks.add(network3)
        system.save()

    def testDispatchSystemEvent(self):
        poll_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_POLL)
        self.system2.agent_port = 12345
        self.system2.save()

        # sanity check dispatching poll event
        event = models.SystemEvent(system=self.system2,
            event_type=poll_event, priority=poll_event.priority)
        event.save()
        def mockedUuid4():
            return "really-unique-id"
        from mint.lib import uuid
        origUuid4 = uuid.uuid4
        try:
            uuid.uuid4 = mockedUuid4
            self.mgr.sysMgr.dispatchSystemEvent(event)
        finally:
            uuid.uuid4 = origUuid4

        cimParams = self.mgr.repeaterMgr.repeaterClient.CimParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.methodsCalled,
            [
                ('poll',
                    (
                        cimParams(
                            host='3.3.3.3',
                            port=12345,
                            eventUuid='really-unique-id',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            targetName=None,
                            targetType=None,
                            instanceId=None),
                        resLoc(path='/api/inventory/systems/%s' %
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
        self.system2.agent_port = 12345
        self.system2.save()
        act_event = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_REGISTRATION)
        # Remove all networks
        for net in self.system2.networks.all():
            net.delete()
        network = models.Network(dns_name = 'superduper.com')
        network.system = self.system2
        network.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=self.system2,
            event_type=act_event, priority=act_event.priority)
        event.save()
        def mockedUuid4():
            return "really-unique-id"
        from mint.lib import uuid
        origUuid4 = uuid.uuid4
        try:
            uuid.uuid4 = mockedUuid4
            self.mgr.sysMgr.dispatchSystemEvent(event)
        finally:
            uuid.uuid4 = origUuid4

        cimParams = self.mgr.repeaterMgr.repeaterClient.CimParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.methodsCalled,
            [
                ('register',
                    (
                        cimParams(host='superduper.com',
                            port=12345,
                            eventUuid = 'really-unique-id',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            targetName=None,
                            targetType=None,
                            instanceId=None),
                        resLoc(path='/api/inventory/systems/4', port=80),
                    ),
                    dict(requiredNetwork=None, zone='Local rBuilder'),
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

class TargetSystemImportTest(XMLTestCase):
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
        XMLTestCase.setUp(self)

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
        self.tgt1 = rbuildermodels.Targets.objects.get(pk=1) # vsphere1
        self.tgt2 = rbuildermodels.Targets.objects.get(pk=2) # vsphere2
        self.tgt3 = rbuildermodels.Targets.objects.get(pk=3) # ec2
        c1 = rbuildermodels.TargetCredentials.objects.get(pk=1)
        c2 = rbuildermodels.TargetCredentials.objects.get(pk=2)
        c3 = rbuildermodels.TargetCredentials.objects.get(pk=3)
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

        for (targetType, targetName, userName, tsystems) in self._targets:
            tgt = rbuildermodels.Targets.objects.get(targettype=targetType,
                targetname=targetName)
            for tsystem in tsystems:
                # Make sure we linked this system to the target
                system = models.System.objects.get(target=tgt,
                    target_system_id=tsystem.instanceId.getText())
                # Make sure we linked it to the user too
                cred_ids = set(x.credentials_id
                    for x in system.target_credentials.all())
                try:
                    tuc = rbuildermodels.TargetUserCredentials.objects.get(
                        targetid=tgt, userid__username = userName)
                except rbuildermodels.TargetUserCredentials.DoesNotExist:
                    self.fail("System %s not linked to user %s" % (
                        system.target_system_id, userName))
                self.failUnlessIn(
                    tuc.targetcredentialsid.targetcredentialsid,
                    cred_ids)
                self.failUnlessEqual([
                    x.dns_name for x in system.networks.all() ],
                    [ tsystem.dnsName.getText() ])

        # Make sure we can re-run
        self.mgr.sysMgr.importTargetSystems(self.drivers)

        # Use the API, make sure the fields come out right
        system = models.System.objects.get(target_system_id='vsphere1-001')
        # Fetch XML
        response = self._get('/api/inventory/systems/%d/' % system.system_id,
            username="testuser", password="password")
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
        self.failUnless(entries[0].entry.startswith("Event type 'system registration' registered and will be enabled on "))
        # Make sure the zone is set
        self.failUnlessEqual(system.managing_zone.name, 'Local rBuilder')
        # Make sure we did set name, description etc
        self.failUnlessEqual(system.name, system.target_system_name)
        self.failUnlessEqual(system.description, system.target_system_description)

    def testIsManageable(self):
        # First, make sure these two users have the same credentials
        user1 = rbuildermodels.Users.objects.get(username='JeanValjean1')
        user2 = rbuildermodels.Users.objects.get(username='JeanValjean2')
        user3 = rbuildermodels.Users.objects.get(username='JeanValjean3')
        self.failUnlessEqual(
            rbuildermodels.TargetUserCredentials.objects.get(
                targetid=self.tgt3, userid=user1).targetcredentialsid.pk,
            rbuildermodels.TargetUserCredentials.objects.get(
                targetid=self.tgt3, userid=user2).targetcredentialsid.pk,
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
        url = '/api/inventory/systems/%s' % system.pk
        response = self._get(url, username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_with_target,
            ignoreNodes=['created_date'])

    def testAddLaunchedSystem(self):
        user2 = rbuildermodels.Users.objects.get(username='JeanValjean2')
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
            targetName=self.tgt2.targetname,
            targetType=self.tgt2.targettype)
        for k, v in params.items():
            self.failUnlessEqual(getattr(system, k), v)
        # Make sure we have credentials
        stc = list(system.target_credentials.all())[0]
        self.failUnlessIn(stc.credentials_id,
            [ x.targetcredentialsid.targetcredentialsid
                for x in user2.targetusercredentials_set.all() ])
        self.failUnlessEqual(system.managing_zone.name,
            models.Zone.LOCAL_ZONE)
        self.failUnlessEqual(system.name, params['target_system_name'])
        self.failUnlessEqual(system.description,
            params['target_system_description'])

class JobsTestCase(XMLTestCase):

    def _mock(self):
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def setUp(self):
        XMLTestCase.setUp(self)
        self._mock()

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        system = self._saveSystem()

        job1 = self._newJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION)
        job2 = self._newJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_POLL)
        job3 = self._newJob(system, eventUuid3, jobUuid3,
            models.EventType.SYSTEM_POLL_IMMEDIATE)

        self.system = system

    def testGetJobs(self):
        response = self._get('/api/inventory/jobs/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_xml)
    
    def testGetJobStates(self):
        response = self._get('/api/inventory/job_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_states_xml)

    def testGetJob(self):
        response = self._get('/api/inventory/jobs/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_xml)

    def testGetJobState(self):
        response = self._get('/api/inventory/job_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_state_xml)

    def testGetSystemJobs(self):
        response = self._get('/api/inventory/systems/%s/jobs/' % \
            self.system.pk)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.systems_jobs_xml)

