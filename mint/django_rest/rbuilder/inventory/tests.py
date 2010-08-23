import collections
import datetime
import os
import shutil
import tempfile
from dateutil import tz

from conary import versions
from django.test import TestCase
from django.test.client import Client

from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import manager
from mint.django_rest.rbuilder.inventory import models

from mint.django_rest.rbuilder.inventory import testsxml

class XMLTestCase(TestCase):
    def assertXMLEquals(self, first, second, ignoreNodes=None):
        from lxml import etree
        tree0 = self._removeTail(etree.fromstring(first.strip()))
        tree1 = self._removeTail(etree.fromstring(second.strip()))
        if not self._nodecmp(tree0, tree1, ignoreNodes=ignoreNodes):
            data0 = etree.tostring(tree0, pretty_print=True, with_tail=False)
            data1 = etree.tostring(tree1, pretty_print=True, with_tail=False)
            import difflib
            diff = '\n'.join(list(difflib.unified_diff(data0.splitlines(),
                    data1.splitlines()))[2:])
            self.fail(diff)

    @classmethod
    def _removeTail(self, node):
        stack = collections.deque([ node ])
        while stack:
            n = stack.pop()
            n.tail = None
            children = n.getchildren()
            if children:
                # We don't accept mixed content
                n.text = None
            stack.extend(n.getchildren())
        return node

    @classmethod
    def _strip(cls, data):
        if data is None:
            return None
        # Convert empty string to None
        return data.strip() or None

    @classmethod
    def _sortChildren(self, child1, child2):
        if child1.tag < child2.tag:
            return -1
        elif child1.tag == child2.tag:
            return 0
        else:
            return 1

    @classmethod
    def _nodecmp(cls, node1, node2, ignoreNodes=None):
        if node1.attrib != node2.attrib:
            return False
        if node1.nsmap != node2.nsmap:
            return False
        ignoreNodes = set(ignoreNodes or [])
        children1 = [ x for x in node1.getchildren()
            if x.tag not in ignoreNodes ]
        children2 = [ x for x in node2.getchildren()
            if x.tag not in ignoreNodes ]
        # For the purpose of these tests, we don't care about ordering,
        # so sort all the children before comparing.
        children1.sort(cmp=cls._sortChildren)
        children2.sort(cmp=cls._sortChildren)

        if children1 or children2:
            # Compare text in nodes that have children (mixed content).
            # We shouldn't have mixed content, but we need to be flexible.
            if cls._strip(node1.text) != cls._strip(node2.text):
                return False
            if len(children1) != len(children2):
                return False
            for ch1, ch2 in zip(children1, children2):
                if not cls._nodecmp(ch1, ch2, ignoreNodes=ignoreNodes):
                    return False
            return True
        # No children, compare the text
        return node1.text == node2.text
    
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
        system.activated = True
        system.current_state = 'activated'
        system.save()

        network = models.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.public_dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system
    
    def _saveManagementNode(self):
        management_node = models.ManagementNode()
        management_node.name = 'test management node'
        management_node.description = 'test management node desc'
        management_node.local_uuid = 'test management node luuid'
        management_node.generated_uuid = 'test management node guuid'
        management_node.ssl_client_certificate = 'test management node client cert'
        management_node.ssl_client_key = 'test management node client key'
        management_node.ssl_server_certificate = 'test management node server cert'
        management_node.activated = True
        management_node.current_state = 'activated'
        management_node.local = True
        management_node.is_management_node = True
        management_node.save()

        network = models.Network()
        network.ip_address = '2.2.2.2'
        network.device_name = 'eth0'
        network.public_dns_name = 'testnetwork.example.com'
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
        system.activated = True
        system.current_state = 'activated'
        system.save()

        network = models.Network()
        network.ip_address = '2.2.2.2'
        network.device_name = 'eth0'
        network.public_dns_name = 'testnetwork2.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system

    def setUp(self):
        self.workDir = tempfile.mkdtemp(dir="/tmp", prefix="rbuilder-django-")
        mintCfg = os.path.join(self.workDir, "mint.cfg")
        file(mintCfg, "w")
        from mint import config
        config.RBUILDER_CONFIG = mintCfg
        self.client = Client()
        self.mgr = manager.Manager()

    def cleanUp(self):
        shutil.rmtree(self.workDir, ignore_errors=True)

class InventoryTestCase(XMLTestCase):

    def testGetTypes(self):
        response = self.client.get('/api/inventory/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
        response = self.client.post('/api/inventory/?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)
        
    def testPostTypes(self):
        response = self.client.post('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def notestPutTypes(self):
        response = self.client.put('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def testDeleteTypes(self):
        response = self.client.delete('/api/inventory/')
        self.assertEquals(response.status_code, 405)
       

class LogTestCase(XMLTestCase):

    def testGetLog(self):
        system = models.System(name="mgoblue", 
            description="best appliance ever", activated=False)
        new_system = self.mgr.addSystem(system)
        system = models.System(name="mgoblue2", 
            description="best appliance ever2", activated=False)
        new_system = self.mgr.addSystem(system)
        system = models.System(name="mgoblue3", 
            description="best appliance ever3", activated=False)
        new_system = self.mgr.addSystem(system)
        response = self.client.get('/api/inventory/log/')
        # Just remove lines with dates in them, it's easier to test for now.
        content = []
        for line in response.content.split('\n'):
            if 'entryDate' in line or \
               'poll event' in line or \
               'activation event' in line:
                continue
            else:
                content.append(line)
        self.assertXMLEquals('\n'.join(content), testsxml.systems_log_xml)
        
class ZonesTestCase(XMLTestCase):

    def testGetZones(self):
        zone = self._saveZone()
        response = self.client.get('/api/inventory/zones/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.zones_xml % (zone.created_date.isoformat()))

    def testGetZone(self):
        zone = self._saveZone()
        response = self.client.get('/api/inventory/zones/2/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.zone_xml % (zone.created_date.isoformat()))
        
    def testAddZoneNodeNull(self):
        
        try:
            self.mgr.addZone(None)
        except:
            assert(False) # should not throw exception
        
    def testAddZone(self):
        zone = self._saveZone()
        new_zone = self.mgr.addZone(zone)
        assert(new_zone is not None)
        
    def testPostZone(self):
        xml = testsxml.zone_post_xml
        response = self.client.post('/api/inventory/zones/', 
            data=xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        zone = models.Zone.objects.get(pk=1)
        self.assertXMLEquals(response.content, testsxml.zone_post_response_xml % \
            (zone.created_date.isoformat() + '+00:00'))

class ManagementNodesTestCase(XMLTestCase):

    def testManagementNodeSave(self):
        # make sure state gets set to unmanaged
        management_node = models.ManagementNode(name="mgoblue", 
            description="best node ever")
        assert(management_node.current_state != models.System.UNMANAGED)
        management_node.save()
        assert(management_node.is_management_node)
        assert(management_node.current_state == models.System.UNMANAGED)
        
        # make sure we honor the state if set though
        management_node = models.ManagementNode(name="mgoblue", 
            description="best node ever", current_state=models.System.DEAD)
        management_node.save()
        assert(management_node.current_state == models.System.DEAD)
        
    def testGetManagementNodes(self):
        management_node = self._saveManagementNode()
        response = self.client.get('/api/inventory/managementNodes/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_nodes_xml % (management_node.created_date.isoformat()))

    def testGetManagementNode(self):
        management_node = self._saveManagementNode()
        management_node.save();
        response = self.client.get('/api/inventory/managementNodes/2/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.management_node_xml % (management_node.created_date.isoformat()))
        
    def testAddManagementNodeNull(self):
        
        try:
            # create the system
            managementNode = None
            self.mgr.addManagementNode(managementNode)
        except:
            assert(False) # should not throw exception
        
    def testAddManagementNode(self):
        management_node = self._saveManagementNode()
        new_management_node = self.mgr.addManagementNode(management_node)
        assert(new_management_node is not None)
        assert(new_management_node.local)
        assert(new_management_node.is_management_node)
        
    def testAddManagementNodeSave(self):
        management_node = self._saveManagementNode()
        management_node.is_management_node = False
        assert(management_node.is_management_node == False)
        # now save, which should automatically set is_management_node
        management_node.save()
        assert(management_node.is_management_node)
        
    def testPostManagementNode(self):
        xml = testsxml.management_node_post_xml
        response = self.client.post('/api/inventory/managementNodes/', 
            data=xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=2)
        management_node_xml = testsxml.management_node_xml.replace(
            '<activationDate/>',
            '<activationDate>%s</activationDate>' % \
            (management_node.activation_date.isoformat() + '+00:00'))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.created_date.isoformat() + '+00:00'))

class NetworksTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        self.system = models.System(name="mgoblue", description="best appliance ever")
        self.system.save()
        
    def testExtractNetworkToUse(self):
        
        # try a net with no required/active nets
        network = models.Network(public_dns_name="foo.com", active=False, required=False)
        network.system = self.system
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        assert(net is None)
        
        # try one with required only
        network.required = True
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        assert(net is not None)
        
        # try one with active only
        network.required = False
        network.active = True
        network.save()
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        assert(net is not None)
        
        # now add a required one in addition to active one to test order
        network2 = models.Network(public_dns_name="foo2.com", active=False, required=True)
        network2.system = self.system
        network2.save()
        assert(len(self.system.networks.all()) == 2)
        assert(self.system.networks.all()[0].required == False)
        assert(self.system.networks.all()[1].required == True)
        net = self.mgr.sysMgr._extractNetworkToUse(self.system)
        assert(net.network_id == network2.network_id)

class SystemsTestCase(XMLTestCase):
    fixtures = ['system_job']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mock_scheduleSystemActivationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.scheduleSystemActivationEvent = self.mock_scheduleSystemActivationEvent
        
    def mock_scheduleSystemActivationEvent(self, system):
        self.mock_scheduleSystemActivationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
        
    def testAddSystemNull(self):
        
        try:
            # create the system
            system = None
            self.mgr.addSystem(system)
        except:
            assert(False) # should not throw exception
            
    def testSystemSave(self):
        # make sure state gets set to unmanaged
        system = models.System(name="mgoblue", 
            description="best appliance ever")
        assert(system.current_state != models.System.UNMANAGED)
        system.save()
        assert(system.current_state == models.System.UNMANAGED)
        
        # make sure we honor the state if set though
        system = models.System(name="mgoblue", 
            description="best appliance ever", current_state=models.System.DEAD)
        system.save()
        assert(system.current_state == models.System.DEAD)
        
    def testAddSystem(self):
        # create the system
        system = models.System(name="mgoblue", 
            description="best appliance ever", activated=False)
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        assert(new_system.current_state == models.System.UNMANAGED)
        
        # make sure we scheduled our activation event
        assert(self.mock_scheduleSystemActivationEvent_called)
        
    def testAddActivatedSystem(self):
        # create the system
        system = models.System(name="mgoblue", description="best appliance ever", activated=True)
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        assert(new_system.current_state == models.System.ACTIVATED)
        
        # make sure we did not schedule activation
        assert(self.mock_scheduleSystemActivationEvent_called == False)
        
        # make sure we scheduled poll event
        assert(self.mock_scheduleSystemPollEvent_called)
        
    def testAddActivatedManagementNodeSystem(self):
        # create the system
        system = models.System(name="mgoblue", description="best appliance ever", activated=True)
        system.is_management_node = True
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        assert(new_system.current_state == models.System.ACTIVATED)
        
        # make sure we did not schedule activation
        assert(self.mock_scheduleSystemActivationEvent_called == False)
        
        # make sure we did not scheduled poll event since this is a management node
        assert(self.mock_scheduleSystemPollEvent_called == False)
        
    def testGetSystems(self):
        system = self._saveSystem()
        response = self.client.get('/api/inventory/systems/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.systems_xml % (system.created_date.isoformat()))

    def testGetSystem(self):
        system = self._saveSystem()
        response = self.client.get('/api/inventory/systems/2/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_xml % (system.created_date.isoformat()))

    def testGetSystemWithTarget(self):
        target = rbuildermodels.Targets(pk=1, targettype='testtargettype',
            targetname='testtargetname')
        target.save()
        system = self._saveSystem()
        system.target = target
        system.save()
        response = self.client.get('/api/inventory/systems/2/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_target_xml % \
            system.created_date.isoformat())

    def XXXtestPutSystems(self):
        """
        Disable this test for now, puts don't seem to work with django 1.1
        """
        systems_xml = testsxml.systems_put_xml % ('', '')
        response = self.client.put('/api/inventory/systems/', 
            data=systems_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        systems = models.System.objects.all()
        assert(len(systems) == 3)
        
    def testPostSystem(self):
        system_xml = testsxml.system_post_xml
        response = self.client.post('/api/inventory/systems/', 
            data=system_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=2)
        system_xml = testsxml.system_xml.replace('<activationDate/>',
            '<activationDate>%s</activationDate>' % \
            (system.activation_date.isoformat() + '+00:00'))
        self.assertXMLEquals(response.content, system_xml % \
            (system.created_date.isoformat() + '+00:00'))
        
    def testPostSystemDupUuid(self):
        # add the first system
        system_xml = testsxml.system_post_xml_dup
        response = self.client.post('/api/inventory/systems/', 
            data=system_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=2)
        self.failUnlessEqual(system.current_state, "activated")
        
        # add it with same uuids but with different current state to make sure
        # we get back same system with update prop
        system_xml = testsxml.system_post_xml_dup2
        response = self.client.post('/api/inventory/systems/', 
            data=system_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        this_system = models.System.objects.get(pk=2)
        self.failUnlessEqual(system.current_state, "dead")

    def testGetSystemLog(self):
        response = self.client.post('/api/inventory/systems/', 
            data=testsxml.system_post_xml, content_type='text/xml')
        response = self.client.get('/api/inventory/systems/2/')
        response = self.client.get('/api/inventory/systems/2/systemLog/')
        self.assertEquals(response.status_code, 200)
        content = []
        # Just remove lines with dates in them, it's easier to test for now.
        for line in response.content.split('\n'):
            if 'entryDate' in line or \
               'poll event' in line:
                continue
            else:
                content.append(line)
        self.assertXMLEquals('\n'.join(content), testsxml.system_log_xml)
        
    def testGetSystemHasHostInfo(self):
        system = models.System(name="mgoblue")
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
        network = models.Network(public_dns_name="foo.bar.com", system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))

class SystemVersionsTestCase(XMLTestCase):
    fixtures = ['system_job']
    
    def setUp(self):
        XMLTestCase.setUp(self)
        self.mintConfig = self.mgr.cfg
        from django.conf import settings
        self.mintConfig.dbPath = settings.DATABASE_NAME
        self.mock_scheduleSystemActivationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.mgr.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.mgr.scheduleSystemActivationEvent = self.mock_scheduleSystemActivationEvent
        
    def mock_scheduleSystemActivationEvent(self, system):
        self.mock_scheduleSystemActivationEvent_called = True
        
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
        trove.save()

        version_update = models.Version()
        version_update.fromConaryVersion(versions.ThawVersion(
            '/clover.eng.rpath.com@rpath:clover-1-devel/1234567890.13:1-3-1'))
        version_update.flavor = version.flavor
        version_update.save()

        version_update2 = models.Version()
        version_update2.fromConaryVersion(versions.ThawVersion(
            '/clover.eng.rpath.com@rpath:clover-1-devel/1234567890.14:1-4-1'))
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
        trove2.save()

        self.trove = trove
        self.trove2 = trove2

    def testGetSystemWithVersion(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        response = self.client.get('/api/inventory/systems/%s/' % system.pk)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_version_xml % \
            (self.trove.last_available_update_refresh.isoformat(),
             self.trove2.last_available_update_refresh.isoformat(),
             system.created_date.isoformat()))

    def testGetInstalledSoftwareRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()
        url = '/api/inventory/systems/%s/installedSoftware/' % system.pk
        response = self.client.get(url)
        self.assertXMLEquals(response.content,
            testsxml.installed_software_xml %(
                self.trove.last_available_update_refresh.isoformat(),
                self.trove2.last_available_update_refresh.isoformat()))

    def testSetInstalledSoftwareRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        url = '/api/inventory/systems/%s/installedSoftware/' % system.pk
        response = self.client.post(url,
            data=testsxml.installed_software_post_xml,
            content_type="application/xml")
        self.assertXMLEquals(response.content,
            testsxml.installed_software_response_xml,
            ignoreNodes = ['lastAvailableUpdateRefresh'])

    def testSetInstalledSoftwareSystemRest(self):
        system = self._saveSystem()
        self._saveTrove()
        system.installed_software.add(self.trove)
        system.installed_software.add(self.trove2)
        system.save()

        data = testsxml.system_version_put_xml

        url = '/api/inventory/systems/%s/' % system.pk
        response = self.client.put(url,
            data=data,
            content_type="application/xml")
        self.assertXMLEquals(response.content,
            testsxml.system_version_put_response_xml,
            ignoreNodes = ['lastAvailableUpdateRefresh'])

class EventTypeTestCase(XMLTestCase):

    def testGetEventTypes(self):
        response = self.client.get('/api/inventory/eventTypes/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_types_xml)

    def testGetEventType(self):
        response = self.client.get('/api/inventory/eventTypes/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_type_xml)

class SystemEventTestCase(XMLTestCase):
    
    def setUp(self):
        XMLTestCase.setUp(self)

        # need a system
        network = models.Network(ip_address='1.1.1.1')
        self.system = models.System(name="mgoblue", description="best appliance ever")
        self.system.save()
        network.system = self.system
        self.system.networks.add(network)
        self.system.save()
        
        # start with no logs/system events
        models.SystemLog.objects.all().delete()
        models.SystemEvent.objects.all().delete()
        
        self.mock_dispatchSystemEvent_called = False
        self.mgr.dispatchSystemEvent = self.mock_dispatchSystemEvent

    def mock_dispatchSystemEvent(self, event):
        self.mock_dispatchSystemEvent_called = True
    
    def testGetSystemEventsRest(self):
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        act_event = models.EventType.objects.get(name=models.EventType.SYSTEM_ACTIVATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        response = self.client.get('/api/inventory/systemEvents/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_events_xml % \
                (event1.time_created.isoformat(), event1.time_enabled.isoformat(),
                 event2.time_created.isoformat(), event2.time_enabled.isoformat()))

    def testGetSystemEventRest(self):
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self.client.get('/api/inventory/systemEvents/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))
    
    def testGetSystemEvent(self):
        # add an event
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        new_event = self.mgr.getSystemEvent(event.system_event_id)
        assert(new_event == event)
        
    def testGetSystemEvents(self):
        # add an event
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        act_event = models.EventType.objects.get(name=models.EventType.SYSTEM_ACTIVATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.mgr.getSystemEvents()
        assert(len(SystemEvents.systemEvent) == 2)
        
    def testDeleteSystemEvent(self):
        # add an event
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        self.mgr.deleteSystemEvent(event.system_event_id)
        events = models.SystemEvent.objects.all()
        assert(len(events) == 0)
        
    def testCreateSystemEvent(self):
        local_system = models.System(name="mgoblue_local", description="best appliance ever")
        local_system.save()
        network = models.Network(system=local_system)
        network.save()
        local_system.networks.add(network)
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
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
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
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
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=poll_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testScheduleSystemPollNowEvent(self):
        self.mgr.scheduleSystemPollNowEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called)
        
        pn_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL_IMMEDIATE)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=pn_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.utcnow())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testScheduleSystemActivationEvent(self):
        self.mgr.scheduleSystemActivationEvent(self.system)
        assert(self.mock_dispatchSystemEvent_called)
        
        activation_event = models.EventType.objects.get(name=models.EventType.SYSTEM_ACTIVATION)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=activation_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.utcnow())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testAddSystemEventNull(self):
        
        try:
            self.mgr.addSystemSystemEvent(None, None)
        except:
            assert(False) # should not throw exception
        
    def testAddSystemActivationEvent(self):
        # activation event should be dispatched now
        activation_event = models.EventType.objects.get(name=models.EventType.SYSTEM_ACTIVATION)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=activation_event, priority=activation_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollNowEvent(self):
        # poll now event should be dispatched now
        poll_now_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_now_event, priority=poll_now_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called)
        
    def testAddSystemPollEvent(self):
        # poll event should not be dispatched now
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        systemEvent = models.SystemEvent(system=self.system, 
            event_type=poll_event, priority=poll_event.priority,
            time_enabled=datetime.datetime.now(tz.tzutc()))
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)
        assert(self.mock_dispatchSystemEvent_called == False)
        
    def testPostSystemEvent(self):
        url = '/api/inventory/systems/%d/systemEvents/' % self.system.system_id
        system_event_post_xml = testsxml.system_event_post_xml
        response = self.client.post(url,
            data=system_event_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        system_event = models.SystemEvent.objects.get(pk=1)
        system_event_xml = testsxml.system_event_xml % \
            (system_event.time_created.isoformat() + '+00:00',
            system_event.time_enabled.isoformat() + '+00:00')
        self.assertXMLEquals(response.content, system_event_xml)
        
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

        self.mock_scheduleSystemPollEvent_called = True

    def mock_extractNetworkToUse(self, system):
        self.mock_extractNetworkToUse_called = True
        return None

    def testGetSystemEventsForProcessing(self):
        
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        
        # ensure we got our activation event back since it is the highest priority
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_ACTIVATION)

        # remove the activation event and ensure we get the on demand poll event next
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
        # and make sure we don't get it (because of the future activation time)
        orgPollEvent = event
        enabled_time = datetime.datetime.now() + datetime.timedelta(1) # now + 1 day
        new_poll_event = models.SystemEvent(system=orgPollEvent.system, 
            event_type=orgPollEvent.event_type, priority=orgPollEvent.priority + 1,
            time_enabled=enabled_time)
        new_poll_event.save()
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.system_event_id,
            new_poll_event.system_event_id)
        
    def testGetSystemEventsForProcessingPollCount(self):
        self.mintConfig.systemPollCount = 3
        
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        self.failUnlessEqual(len(events), 3)
        
    def testProcessSystemEvents(self):
        
        #remove the activation event so we handle the poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_ACTIVATION)
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
            models.SystemEvent.objects.get(system_event_id=event.system_event_id)
        except models.SystemEvent.DoesNotExist:
            pass
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        local_system = poll_event.system_events.all()[0]
        event = models.SystemEvent.objects.get(system=local_system, event_type=poll_event)
        self.failIf(event is not None)
        
    def testProcessSystemEventsNoTrigger(self):
        # make sure activation event doesn't trigger next poll event
        # start with no regular poll events
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        models.SystemEvent.objects.filter(event_type=poll_event).delete()
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        
        # make sure next one is activation now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            models.EventType.SYSTEM_ACTIVATION)
        self.mgr.sysMgr.processSystemEvents()
        
        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        
    def testDispatchSystemEvent(self):
        poll_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL)
        poll_now_event = models.EventType.objects.get(name=models.EventType.SYSTEM_POLL_IMMEDIATE)
        act_event = models.EventType.objects.get(name=models.EventType.SYSTEM_ACTIVATION)
        
        system = models.System(name="hey")
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

        # sanity check dispatching activation event
        self.resetFlags()
        event = models.SystemEvent(system=system, event_type=act_event, priority=act_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        self.failUnless(self.mock_cleanupSystemEvent_called)
        self.failIf(self.mock_scheduleSystemPollEvent_called)
