import base64
import cPickle
import os
import random
from xobj import xobj
from lxml import etree

from smartform import descriptor

from django.contrib.redirects import models as redirectmodels
from django.db import connection, transaction
from django.template import TemplateDoesNotExist

from mint.django_rest import timeutils
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.inventory import testsxml
from mint.lib import x509

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class BasicTests(XMLTestCase):
    """XML Parsing and such"""
    def testEmptyStringsInXmlNodes(self):
        s = "<root><a/><b></b></root>"
        doc = modellib.Etree.fromstring(s)
        self.assertEquals(modellib.Etree.findBasicChild(doc, 'a'), '')
        self.assertEquals(modellib.Etree.findBasicChild(doc, 'b'), '')
        self.assertEquals(modellib.Etree.findBasicChild(doc, 'c'), None)
        self.assertEquals(
                modellib.Etree.findBasicChild(doc, 'c', default=1), 1)


class AuthTests(XMLTestCase):
    def testAuthRCE1341(self):
        password = "password with 'weird :chars"
        response = self._get('inventory/log/', username="test-rce1341",
            password=password)
        self.assertEquals(response.status_code, 200)

        # Now pretend it's an external user
        from mint.django_rest.rbuilder.users import models as usermodels
        u = usermodels.User.objects.get(user_name='test-rce1341')
        u.update(passwd=None)

        # Capture the requested password
        class MockAuthClient(object):
            def __init__(slf):
                slf.args = []
            def checkPassword(slf, username, password):
                slf.args.append((username, password))
                return True
        authClient = MockAuthClient()
        from mint.lib import auth_client
        self.mock(auth_client, 'getClient', lambda *args: authClient)

        response = self._get('inventory/log/', username="test-rce1341",
            password=password)
        self.assertEquals(response.status_code, 200)

        self.assertEquals(authClient.args, [('test-rce1341', password)])


class InventoryTestCase(XMLTestCase):

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

class LogTestCase(XMLTestCase):

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
        # unsure of what correct log XML should actually be
        #self.assertXMLEquals(response.content, testsxml.systems_log_xml,
        #    ignoreNodes = [ 'entry_date' ])

class ZonesTestCase(XMLTestCase):

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
            ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date', ])

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
        self.assertEquals(response.status_code, 403)

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
        self.assertEquals(response.status_code, 403)

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
        self.assertEquals(response.status_code, 403)

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


class SystemTypesTestCase(XMLTestCase):

    def testGetSystemTypes(self):
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        response = self._get('inventory/system_types/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_types_xml, ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by', ])

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
            testsxml.system_type_xml, ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date', ])

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
        self.assertEquals(response.status_code, 403)

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


class SystemStatesTestCase(XMLTestCase):

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

class NetworkTestCase(XMLTestCase):

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
        self.assertEquals(response.status_code, 403)

    def testPutNetworkLocalIp(self):
        """
        Ensure Network models are not saved if pointing to link-local IPs.
        """
        models.System.objects.all().delete()
        self._saveSystem()
        old_count = models.Network.objects.count()
        self._put('inventory/networks/1/',
                  data=testsxml.network_put_xml_opt_ip_addr % "169.254.4.4",
                  username="admin", password="password")
        self.assertEquals(old_count, models.Network.objects.count())

        self._put('inventory/networks/1/',
                  data=testsxml.network_put_xml_opt_ip_addr % "4.4.4.4",
                  username="admin", password="password")
        self.assertEquals(old_count + 1, models.Network.objects.count())

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
        self.assertEquals(response.status_code, 403)

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
        self.failUnlessEqual(response.status_code, 403)

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
        self.assertEquals(response.status_code, 403)

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
        self.assertEquals(response.status_code, 403)

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

class NetworksTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
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

class SystemsTestCase(XMLTestCase):
    fixtures = ['system_job', 'targetusers', 'targets']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mockGetRmakeJob_called = False
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob

    def tearDown(self):
        XMLTestCase.tearDown(self)

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

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
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

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

    def testAddSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.UNMANAGED)

    def testAddRegisteredSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            local_uuid='123', generated_uuid='456')
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.RESPONSIVE)

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
            models.SystemState.RESPONSIVE)

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
        response = self._post('inventory/systems/', data=system_xml)
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
        self.failUnlessEqual(x.system.network_address.pinned.lower(), "false")

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
        self.failUnlessEqual(x.system.network_address.pinned.lower(), "true")

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

    def testPostNewSystemNetworkPinned(self):
        xmlTempl = """\
<system>
  <name>%(name)s</name>
  <network_address>
    <address>%(ipAddr)s</address>
    <pinned>true</pinned>
  </network_address>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>"""
        params = dict(name='test1', zoneId=self.localZone.zone_id,
            ipAddr='1.1.1.1')
        response = self._post('inventory/systems/',
            data=xmlTempl % params, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        systemId = doc.system.system_id
        system = models.System.objects.get(system_id=systemId)
        self.assertEquals(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.order_by('dns_name') ],
            [ (params['ipAddr'], None, None, True), ])


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
                for x in system.networks.order_by('dns_name') ],
            [
                ('10.1.1.1', '10.1.1.1', False, None, ),
                ('blah1', None, False, True, ),
                ('blah2.example.com', '10.2.2.2', True, False, ),
            ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "blah1")
        self.failUnlessEqual(x.system.network_address.pinned.lower(), "true")

    def testGetSystems(self):
        system = self._saveSystem()
        response = self._get('inventory/systems/', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.systems_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by' ])
        response = self._get('inventory/systems', username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

    def testPostSystemNetworkDuplicateAddress(self):
        """
        RCE-985

        2 entries in network:
        IP_ADDRESS  DNS_NAME
        -----------+--------
        (null)      10.1.1.1
        10.1.1.1    ...
        we should update the second and delete the first, not the other way
        around.
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
      <active>true</active>
      <device_name>eth0</device_name>
      <dns_name>dhcp1.example.com</dns_name>
      <ip_address>10.1.1.1</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()
        models.Network.objects.create(system=system,
            dns_name='10.1.1.1', active=True, pinned=False)
        nw = models.Network.objects.create(system=system,
            ip_address='10.1.1.1', dns_name='dhcp1.example.com',
            active=True, pinned=False)

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)

        system = models.System.objects.get(system_id=system.system_id)
        self.assertEquals([
            (x.network_id, x.ip_address) for x in system.networks.all() ],
            [(nw.network_id, '10.1.1.1')])

    def testPostSystemNetworkAddressChange(self):
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
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()
        network = models.Network(system=system, ip_address='1.2.3.4',
            dns_name='blah1', active=True, pinned=False)
        network.save()

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)

        system = models.System.objects.get(system_id=system.system_id)
        self.assertEquals([ x.ip_address for x in system.networks.all() ],
            ['10.1.1.1'])

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

    def testPostSystemBadNetwork(self):
        """Ensure network address validation is done pre-save"""
        system_xml = testsxml.system_post_xml_bad_network
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 400)
        self.assertTrue(response.content.find('<fault>') != -1)

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
            ignoreNodes = [ 'created_date',
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
        self.assertXMLEquals(response.content, testsxml.system_log_xml,
                ignoreNodes=['entry_date'])

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
        import time
        now = time.time()
        cu.execute("""
            INSERT INTO jobs (job_uuid, job_type_id, job_state_id, created_by,
                created, modified)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING job_id""",
            [ bootUuid, 1, 1, 1, now, now])
        jobId = cu.fetchone()[0]

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
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.boot_uuid, bootUuid)
        self.failUnlessEqual(model.pk, system.pk)
        self.failUnlessEqual(model.target_system_id, targetSystemId)

        # FIXME: this used to look at surveys to confirm deduplication but
        # surveys were deleted
        system = self.mgr.addSystem(model)

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
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.event_uuid, eventUuid)

    def _setupDedupEventUuid(self):
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
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        return system, xml

    def testDedupByEventUuid(self):
        system, xml = self._setupDedupEventUuid()
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
        # We should have loaded the old one
        self.failUnlessEqual(system.pk, model.pk)
        self.failUnlessEqual(model.name, 'blippy')
        # Catch the case of synthetic fields not being converted to
        # unicode (xobj types confuse database drivers)
        self.failUnlessEqual(type(model.event_uuid), str)

        system = self.mgr.addSystem(model)

    def testDedupByEventUuidWithRemoval1(self):
        system, systemRemoved = self._testDedupByEventUuidWithRemoval(targetSystemFirst=False)
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                '(copied) Log message from target system',
                'Log message from empty system'
            ])

    def testDedupByEventUuidPUT(self):
        system, xml = self._setupDedupEventUuid()
        url = 'inventory/systems/%s' % system.system_id
        headers = { 'X-rBuilder-Event-UUID' :
            system.systemjob_set.all()[0].event_uuid }
        response = self._put(url, data=xml, headers=headers)
        self.assertEquals(response.status_code, 200)

        system = system.__class__.objects.get(system_id=system.system_id)

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
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
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

        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)

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
            name = jobmodels.EventType.SYSTEM_UPDATE)
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
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None,
            flags=modellib.Flags(save=False))
        self.failUnlessEqual(model.pk, system.pk)

        # We expect nothing to be updated, since there's no such job
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set jobUuid to be correct
        params['jobUuid'] = jobUuid
        xml = xmlTempl % params
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        # We still expect nothing to be updated, since the event_uuid is wrong
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set eventUuid to be correct
        params['eventUuid'] = eventUuid
        xml = xmlTempl % params
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
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
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
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
            generated_uuid=generatedUuid)
        system.save()

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        etreeModel = etree.fromstring(xml)
        model = models.System.objects.load_from_object(etreeModel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)

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

    def testIncompleteRegistration(self):
        # Mingle #1733
        generatedUuid = 'JeanValjean'
        params = dict(localUuid='', generatedUuid=generatedUuid,
                zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        resp = self._post('inventory/systems', data=xml)
        self.failUnlessEqual(resp.status_code, 200)
        data = xobj.parse(resp.content)
        systemId = data.system.system_id
        system = models.System.objects.get(system_id=systemId)
        actual = [ x.entry for x in models.SystemLogEntry.objects.filter(system_log__system__system_id = system.system_id) ]
        desired = [
              u'System added to inventory',
              u'Incomplete registration: missing local_uuid. Possible cause: dmidecode malfunctioning',
        ]
        self.failUnlessEqual(actual,desired)


class SystemStateTestCase(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
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
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

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
            models.SystemState.RESPONSIVE)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')

        system2 = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system2.current_state.name,
            models.SystemState.RESPONSIVE)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')
        # don't care so much
        #self.failUnlessEqual([ x.entry for x in logEntries ],
        #    [
        #        'System state change: Unmanaged -> Online',
        #    ])


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
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        jobRegNoAuth = self._newSystemJob(system, eventUuid6, jobUuid6,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE, statusCode = 401)

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

        tests = [
            (job1, stateCompleted, UNMANAGED, RESPONSIVE),
            (job1, stateCompleted, UNMANAGED_CREDENTIALS_REQUIRED, RESPONSIVE),
            (job1, stateCompleted, REGISTERED, None),
            (job1, stateCompleted, RESPONSIVE, None),
            (job1, stateCompleted, NONRESPONSIVE_HOST, None),
            (job1, stateCompleted, NONRESPONSIVE_NET, None),
            (job1, stateCompleted, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateCompleted, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateCompleted, NONRESPONSIVE_CREDENTIALS, None),
            (job1, stateCompleted, NONRESPONSIVE, None),
            (job1, stateCompleted, DEAD, None),

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
        ]
        transitionsCompleted = []
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                REGISTERED, RESPONSIVE,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET, NONRESPONSIVE_SHUTDOWN,
                NONRESPONSIVE_SUSPENDED, NONRESPONSIVE,
                NONRESPONSIVE_CREDENTIALS, DEAD]:
            transitionsCompleted.append((oldState, RESPONSIVE))
        transitionsFailed = [
            (REGISTERED, NONRESPONSIVE),
            (RESPONSIVE, NONRESPONSIVE),
        ]
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET,
                NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SUSPENDED,
                NONRESPONSIVE, NONRESPONSIVE_CREDENTIALS, DEAD]:
            transitionsFailed.append((oldState, None))

        # Failed auth tests`
        for job in [ jobRegNoAuth ]:
            tests.append((job, stateFailed, UNMANAGED,
                UNMANAGED_CREDENTIALS_REQUIRED))
            tests.append((job, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED,
                None))
            for oldState in [REGISTERED, RESPONSIVE, NONRESPONSIVE_NET,
                    NONRESPONSIVE_HOST, NONRESPONSIVE_SHUTDOWN,
                    NONRESPONSIVE_SUSPENDED, DEAD]:
                tests.append((job, stateFailed, oldState,
                    NONRESPONSIVE_CREDENTIALS))
            for oldState in [NONRESPONSIVE_CREDENTIALS]:
                tests.append((job, stateFailed, oldState, None))


        # these tests are no longer applicable because they test the internals
        # of a particular function versus the desired result of the changes
        # in the objects.  Disabling them since intent could not be discerned.
        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s; %s): %s -> %s (expected: %s)" % (
                (job.job_type.name, jobState.name, job.status_code,
                 oldState, ret, newState))

class EventTypeTestCase(XMLTestCase):

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
        self.assertEquals(response.status_code, 403)

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
        event_type = jobmodels.EventType(name=jobmodels.EventType.SYSTEM_UPDATE, description="bar", priority=110)
        event_type.save()
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_UPDATE)
        xml = testsxml.event_type_put_name_change_xml % dict(event_type_id=event_type.pk)
        response = self._put('inventory/event_types/%d/' % event_type.pk,
            data=xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = jobmodels.EventType.objects.get(pk=event_type.pk)
        # name should not have changed
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_UPDATE)

class SystemEventTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

        # need a system
        network = models.Network(ip_address='1.1.1.1')
        self.system = self.newSystem(name="mgoblue",
            description="best appliance ever")
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
        XMLTestCase.tearDown(self)

    def mock_dispatchSystemEvent(self, event):
        self.mock_dispatchSystemEvent_called = True

    # test needs update
    #
    #def testGetSystemEventsRest(self):
    #    act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
    #    event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
    #    event2.save()
    #    response = self._get('inventory/system_events/',
    #       username="testuser", password="password")
    #    self.assertEquals(response.status_code, 200)
    #    self.assertXMLEquals(response.content,
    #        testsxml.system_events_xml % \
    #             (event2.time_created.isoformat(), event2.time_enabled.isoformat()))

    def testGetSystemEventRestAuth(self):
        """
        Ensure requires auth but not admin
        """
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemEventRest(self):
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))

    def testGetSystemEvent(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        new_event = self.mgr.getSystemEvent(event.system_event_id)
        assert(new_event == event)

    def testGetSystemEvents(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        event1 = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.mgr.getSystemEvents()
        assert(len(SystemEvents.system_event) == 2)

    def testDeleteSystemEvent(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
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
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = self.mgr.createSystemEvent(local_system, update_event)
        assert(event is None)
        assert(self.mock_dispatchSystemEvent_called == False)

        network2 = models.Network(system=local_system, ip_address="1.1.1.1")
        network2.save()
        local_system.networks.add(network2)
        event = self.mgr.createSystemEvent(local_system, update_event)
        assert(event is not None)

    def testSaveSystemEvent(self):
        self._saveSystem()
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system, event_type=update_event)
        event.save()
        # make sure event priority was set even though we didn't pass it in
        assert(event.priority == update_event.priority)

        event2 = models.SystemEvent(system=self.system, event_type=update_event, priority=1)
        event2.save()
        # make sure we honor priority if set
        assert(event2.priority == 1)

    def testAddSystemEventNull(self):

        try:
            self.mgr.addSystemSystemEvent(None, None)
        except:
            assert(False) # should not throw exception

    def testAddSystemRegistrationEvent(self):
        # registration events are no longer dispatched immediately (RBL-8851)
        registration_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system,
            event_type=registration_event, priority=registration_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)


    # temporarily disabled -- needs to send an old school job not a new one?

    #def testPostSystemEventAuth(self):
    #    """
    #    Ensure requires auth but not admin
    #    """
    #    url = 'inventory/systems/%d/system_events/' % self.system.system_id
    #    system_event_post_xml = testsxml.system_event_post_xml
    #    response = self._post(url, data=system_event_post_xml)
    #    self.assertEquals(response.status_code, 401)
    #
    #    response = self._post(url,
    #        data=system_event_post_xml,
    #        username="admin", password="password")
    #    self.assertEquals(response.status_code, 200)

    #def testPostSystemEvent(self):
    #    url = 'inventory/systems/%d/system_events/' % self.system.system_id
    #    system_event_post_xml = testsxml.system_event_post_xml
    #    response = self._post(url,
    #        data=system_event_post_xml,
    #        username="admin", password="password")
    #    self.assertEquals(response.status_code, 200)
    #    system_event = models.SystemEvent.objects.get(pk=1)
    #    # TODO: looser checking of XML returns


class SystemEventProcessingTestCase(XMLTestCase):

    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']

    def setUp(self):
        XMLTestCase.setUp(self)

        self.mintConfig = self.mgr.cfg
        self.mock(self.mgr.sysMgr, 'extractNetworkToUse',
            self.mock_extractNetworkToUse)
        self.resetFlags()

    def resetFlags(self):
        self.mock_extractNetworkToUse_called = False

    def mock_extractNetworkToUse(self, system):
        self.mock_extractNetworkToUse_called = True
        return None

    def testProcessSystemEvents(self):

        # set default processing size to 1
        self.mintConfig.systemEventsNumToProcess = 1

        #remove the registration event so we handle the poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        event.delete()

    def testProcessSystemEventsNoTrigger(self):
        # make sure registration event doesn't trigger next poll event
        # start with no regular poll events
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        models.SystemEvent.objects.filter(event_type=update_event).delete()
        try:
            models.SystemEvent.objects.get(event_type=update_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

        # make sure next one is registration now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        self.mgr.sysMgr.processSystemEvents()

        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=update_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

    def testDispatchSystemEvent(self):
        self.resetFlags()
        self.failIf(self.mock_extractNetworkToUse_called)

        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        system = self.newSystem(name="hey")
        system.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=system,event_type=update_event, priority=update_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        transaction.commit()

        self.failUnlessEqual(event.system_event_id, None)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        self.failUnlessEqual(event.system_event_id, None)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        # sanity check dispatching registration event
        self.resetFlags()
        event = models.SystemEvent(system=system, event_type=act_event, priority=act_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        transaction.commit()

        self.failUnlessEqual(event.system_event_id, None)


class TargetSystemImportTest(XMLTestCase, test_utils.RepeaterMixIn):
    fixtures = ['targetusers', 'targets']

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
        test_utils.RepeaterMixIn.setUpRepeaterClient(self)

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
        jobs = self.mgr.sysMgr.importTargetSystems()
        self.failUnlessEqual(
            [ [ y.target.name for y in x.target_jobs.all() ] for x in jobs ],
            [
                ['vsphere2.eng.rpath.com'],
                ['vsphere1.eng.rpath.com'],
                ['vsphere2.eng.rpath.com'],
                ['aws'],
            ])

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.listInstances'] * 4)
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=jobs[-1].job_uuid))
        self.mgr.repeaterMgr.repeaterClient.reset()


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
        )
        dnsName = 'dns-name-1'
        ipAddress = '1.2.3.4'
        system = self.newSystem(**params)

        system.boot_uuid = bootUuid = str(self.uuid4())
        # To mimic the workflow from target, we initially add the target
        # system with no networking info
        system = self.mgr.addLaunchedSystem(system,
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

        # Make sure we've saved the boot uuid
        cu = connection.cursor()
        cu.execute("""
            SELECT j.job_uuid
              FROM job_system AS js
              JOIN inventory_system AS invsys USING (system_id)
              JOIN jobs AS j ON (js.job_id=j.job_id)
             WHERE invsys.system_id = %s""", [ system.system_id ])
        self.failUnlessEqual([ x[0] for x in cu ],
            [ bootUuid, ])

        # Mingle #1962: don't add the same network entry multiple times
        # Add networks, to pretend the system registered while we were
        # waiting for the target to report its ip address.
        models.Network.objects.filter(system=savedsystem).delete()
        models.Network.objects.create(system=savedsystem,
            dns_name=dnsName, ip_address=ipAddress, device_name='eth0',
            active=True)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)
        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address) for x in system.networks.all() ],
            [ (dnsName, ipAddress) ])

        def repl(item, a, b):
            try:
                return item.replace(a, b)
            except:
                # booleans don't support this operatiion
                return item

        # Make sure we have an entry in target_system
        tsys = targetmodels.TargetSystem.objects.get(target=system.target,
            target_internal_id=system.target_system_id)
        self.failUnlessEqual(tsys.name, system.name)

        # Another system, no description
        params = dict((x, repl(y, '001', '003'))
            for (x, y) in params.items())
        params['target_system_description'] = None

        system = self.newSystem(**params)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['target_system_name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description, params['target_system_description'])
        tsys = targetmodels.TargetSystem.objects.get(target=system.target,
            target_internal_id=system.target_system_id)
        self.failUnlessEqual(tsys.name, system.name)
        self.failUnlessEqual(tsys.description, '')

        # Another system that specifies a name and description
        params = dict((x, repl(y, '003', '002'))
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

    def testAddLaunchedSystem2(self):
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
            created_by = user2,
        )
        system = self.newSystem(**params)

        system.boot_uuid = bootUuid = str(self.uuid4())

        system = self.mgr.addLaunchedSystem(system,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type,
            )
        for k, v in params.items():
            self.failUnlessEqual(getattr(system, k), v)

        savedsystem = models.System.objects.get(pk=system.pk)

        # System registers and passes a boot uuid
        params = dict(localUuid=str(self.uuid4()),
            generatedUuid=str(self.uuid4()),
            ipAddress='10.10.10.10',
            bootUuid=bootUuid)

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <boot_uuid>%(bootUuid)s</boot_uuid>
  <hostname>bluetorch.example.com</hostname>
  <networks>
    <network>
      <ip_address>%(ipAddress)s</ip_address>
      <dns_name>%(ipAddress)s</dns_name>
    </network>
  </networks>
</system>
""" % params
        url = "inventory/systems"
        response = self._post(url, data=xml)
        self.assertEquals(response.status_code, 200)


class CollectionTest(XMLTestCase):
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
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
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
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '10')
        self.assertEquals(systems.end_index, '19')
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
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
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

    def testFilterBy2(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=LIKE(name,3)')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'3', u'13', u'23', u'30', u'31', u'32', u'33', u'34', u'35', u'36'])

    def testFilterByIn(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=IN(system_id,1, 3 , 5)')
        self.assertEquals([x.system_id for x in systems.system],
            ['3', '5'])

    def testFilterByAndIn(self):
        # RCE-1158
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=AND(IS_NULL(local_uuid,false),IN(system_id,1, 3 , 5))')
        self.assertEquals([x.system_id for x in systems.system],
            ['3', '5'])

    def testFilterByIsNull(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=IS_NULL(local_uuid,true)')
        self.assertEquals([x.system_id for x in systems.system],
            ['2', '50'])

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

class ModuleHooksTest(XMLTestCase):
    """
    Added here, so we don't add modulehooks as a django app. Surprisingly,
    it seems to work, minus the testsuite being run.
    """
    def testGetModuleHooks(self):
        moduleHooksDir = self.mintCfg.moduleHooksDir
        os.makedirs(self.mintCfg.moduleHooksDir)
        # Some extensions
        for i in range(5):
            file(os.path.join(moduleHooksDir, 'file-%d.swf' % i), "w")
        # Some dummy files
        for i in range(3):
            file(os.path.join(moduleHooksDir, 'file-%d.blah' % i), "w")

        response = self._get("module_hooks",
            username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(int(obj.module_hooks.count), 5)
        self.failUnlessEqual(
            sorted(x.url for x in obj.module_hooks.module_hook),
                [
                    'hooks/file-0.swf',
                    'hooks/file-1.swf',
                    'hooks/file-2.swf',
                    'hooks/file-3.swf',
                    'hooks/file-4.swf',
                ])
