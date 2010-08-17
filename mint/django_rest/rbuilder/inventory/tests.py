import collections
import datetime
from dateutil import tz
from django.test import TestCase
from django.test.client import Client

from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import systemdbmgr
from mint.django_rest.rbuilder.inventory import models

from mint.django_rest.rbuilder.inventory import testsxml

class XMLTestCase(TestCase):
    def assertXMLEquals(self, first, second):
        from lxml import etree
        tree0 = self._removeTail(etree.fromstring(first.strip()))
        tree1 = self._removeTail(etree.fromstring(second.strip()))
        if not self._nodecmp(tree0, tree1):
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
    def _nodecmp(cls, node1, node2):
        if node1.attrib != node2.attrib:
            return False
        if node1.nsmap != node2.nsmap:
            return False
        children1 = node1.getchildren()
        children2 = node2.getchildren()

        if children1 or children2:
            # Compare text in nodes that have children (mixed content).
            # We shouldn't have mixed content, but we need to be flexible.
            if cls._strip(node1.text) != cls._strip(node2.text):
                return False
            if len(children1) != len(children2):
                return False
            for ch1, ch2 in zip(children1, children2):
                if not cls._nodecmp(ch1, ch2):
                    return False
            return True
        # No children, compare the text
        return node1.text == node2.text

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

class InventoryTestCase(XMLTestCase):
          
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.client = Client()

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

    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()

    def testGetLog(self):
        system = models.System(name="mgoblue", 
            description="best appliance ever", activated=False)
        new_system = self.system_manager.addSystem(system)
        system = models.System(name="mgoblue2", 
            description="best appliance ever2", activated=False)
        new_system = self.system_manager.addSystem(system)
        system = models.System(name="mgoblue3", 
            description="best appliance ever3", activated=False)
        new_system = self.system_manager.addSystem(system)
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
        self.assertXMLEquals('\n'.join(content), testsxml.systems_log)


class SystemsTestCase(XMLTestCase):
    fixtures = ['system_job']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        self.mintConfig = self.system_manager.cfg
        self.mock_scheduleSystemActivationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.system_manager.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.system_manager.scheduleSystemActivationEvent = self.mock_scheduleSystemActivationEvent
        
    def mock_scheduleSystemActivationEvent(self, system):
        self.mock_scheduleSystemActivationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
        
    def testAddSystemNull(self):
        
        try:
            # create the system
            system = None
            self.system_manager.addSystem(system)
        except:
            assert(False) # should not throw exception
        
    def testAddSystem(self):
        # create the system
        system = models.System(name="mgoblue", 
            description="best appliance ever", activated=False)
        new_system = self.system_manager.addSystem(system)
        assert(new_system is not None)
        assert(new_system.current_state == models.System.UNMANAGED)
        
        # make sure we scheduled our activation event
        assert(self.mock_scheduleSystemActivationEvent_called)
        
    def testAddActivatedSystem(self):
        # create the system
        system = models.System(name="mgoblue", description="best appliance ever", activated=True)
        new_system = self.system_manager.addSystem(system)
        assert(new_system is not None)
        assert(new_system.current_state == models.System.ACTIVATED)
        
        # make sure we did not schedule activation
        assert(self.mock_scheduleSystemActivationEvent_called == False)
        
        # make sure we scheduled poll event
        assert(self.mock_scheduleSystemPollEvent_called)
        
    def testGetSystems(self):
        system = self._saveSystem()
        response = self.client.get('/api/inventory/systems/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.systems_xml % (system.created_date.isoformat()))

    def testGetSystem(self):
        system = self._saveSystem()
        response = self.client.get('/api/inventory/systems/1/')
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
        response = self.client.get('/api/inventory/systems/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_target_xml % \
            system.created_date.isoformat())

    def testPutSystems(self):
        systems_xml = testsxml.systems_put_xml % ('', '')
        response = self.client.put('/api/inventory/systems/', 
            data=systems_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        systems = models.System.objects.all()
        assert(len(systems) == 2)
        
    def testPostSystem(self):
        system_xml = testsxml.system_post_xml
        response = self.client.post('/api/inventory/systems/', 
            data=system_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=1)
        system_xml = testsxml.system_xml.replace('<activationDate/>',
            '<activationDate>%s</activationDate>' % \
            (system.activation_date.isoformat() + '+00:00'))
        self.assertXMLEquals(response.content, system_xml % \
            (system.created_date.isoformat() + '+00:00'))

    def testGetSystemLog(self):
        system_xml = testsxml.system_xml % ('')
        response = self.client.post('/api/inventory/systems/', 
            data=system_xml, content_type='text/xml')
        response = self.client.get('/api/inventory/systems/1/')
        response = self.client.get('/api/inventory/systems/1/systemLog/')
        self.assertEquals(response.status_code, 200)
        content = []
        # Just remove lines with dates in them, it's easier to test for now.
        for line in response.content.split('\n'):
            if 'entryDate' in line or \
               'poll event' in line:
                continue
            else:
                content.append(line)
        self.assertXMLEquals('\n'.join(content), testsxml.system_log)
        
    def testGetSystemHasHostInfo(self):
        system = models.System(name="mgoblue")
        system.save()
        assert(self.system_manager.getSystemHasHostInfo(system) == False)
        
        network = models.Network(system=system)
        network.save()
        system.networks.add(network)
        assert(self.system_manager.getSystemHasHostInfo(system) == False)
        
        network2 = models.Network(ip_address="1.1.1.1", system=system)
        network2.save()
        system.networks.add(network2)
        assert(self.system_manager.getSystemHasHostInfo(system))
        
        network2.delete()
        network = models.Network(ipv6_address="1.1.1.1", system=system)
        network.save()
        system.networks.add(network)
        assert(self.system_manager.getSystemHasHostInfo(system))
        
        network.delete()
        network = models.Network(public_dns_name="foo.bar.com", system=system)
        network.save()
        system.networks.add(network)
        assert(self.system_manager.getSystemHasHostInfo(system))

class SystemVersionsTestCase(XMLTestCase):
    fixtures = ['system_job']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        self.mintConfig = self.system_manager.cfg
        self.mock_scheduleSystemActivationEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.system_manager.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
        self.system_manager.scheduleSystemActivationEvent = self.mock_scheduleSystemActivationEvent
        
    def mock_scheduleSystemActivationEvent(self, system):
        self.mock_scheduleSystemActivationEvent_called = True
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True
 
    def _saveTrove(self):
        version = models.Version()
        version.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1'
        version.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version.ordering = '1272410162.98'
        version.revision = '1-2-1'
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
        version_update.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1'
        version_update.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version_update.ordering = '1272410162.98'
        version_update.revision = '1-3-1'
        version_update.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version_update.save()

        version_update2 = models.Version()
        version_update2.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1'
        version_update2.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version_update2.ordering = '1272410162.98'
        version_update2.revision = '1-4-1'
        version_update2.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version_update2.save()

        trove.available_updates.add(version_update)
        trove.available_updates.add(version_update2)
        trove.save()

        version2 = models.Version()
        version2.full = '/contrib.rpath.org@rpl:2/23.0.60cvs20080523-1-0.1'
        version2.label = 'contrib.rpath.org@rpl:2'
        version2.ordering = '1272410163.98'
        version2.flavor = 'desktop is: x86_64'
        version2.revision = '23.0.60cvs20080523-1-0.1'
        version2.save()

        trove2 = models.Trove()
        trove2.name = 'emacs'
        trove2.flavor = 'desktop is: x86_64'
        trove2.version = version2
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

class SystemEventTestCase(XMLTestCase):
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        
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
            
    def tearDown(self):
        pass
    
    def testGetSystemEventsRest(self):
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        act_event = models.SystemEventType.objects.get(name=models.SystemEventType.ACTIVATION)
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
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        response = self.client.get('/api/inventory/systemEvents/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))
    
    def testGetSystemEvent(self):
        # add an event
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        new_event = self.system_manager.getSystemEvent(event.system_event_id)
        assert(new_event == event)
        
    def testGetSystemEvents(self):
        # add an event
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        act_event = models.SystemEventType.objects.get(name=models.SystemEventType.ACTIVATION)
        event1 = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.system_manager.getSystemEvents()
        assert(len(SystemEvents.systemEvent) == 2)
        
    def testDeleteSystemEvent(self):
        # add an event
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = models.SystemEvent(system=self.system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        self.system_manager.deleteSystemEvent(event.system_event_id)
        events = models.SystemEvent.objects.all()
        assert(len(events) == 0)
        
    def testCreateSystemEvent(self):
        local_system = models.System(name="mgoblue_local", description="best appliance ever")
        local_system.save()
        network = models.Network(system=local_system)
        network.save()
        local_system.networks.add(network)
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = self.system_manager.createSystemEvent(local_system, poll_event)
        assert(event is None)
                
        network2 = models.Network(system=local_system, ip_address="1.1.1.1")
        network2.save()
        local_system.networks.add(network2)
        event = self.system_manager.createSystemEvent(local_system, poll_event)
        assert(event is not None)
    
    def testScheduleSystemPollEvent(self):
        self.system_manager.scheduleSystemPollEvent(self.system)
        
        # make sure we have our poll event
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=poll_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testScheduleSystemPollNowEvent(self):
        self.system_manager.scheduleSystemPollNowEvent(self.system)
        
        pn_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL_NOW)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=pn_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.utcnow())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testScheduleSystemActivationEvent(self):
        self.system_manager.scheduleSystemActivationEvent(self.system)
        
        activation_event = models.SystemEventType.objects.get(name=models.SystemEventType.ACTIVATION)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=activation_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= datetime.datetime.utcnow())
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.system_log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
class SystemEventProcessingTestCase(XMLTestCase):
    
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        self.mintConfig = self.system_manager.cfg
        self.mock_cleanupSystemEvent_called = False
        self.mock_scheduleSystemPollEvent_called = False
        self.system_manager.cleanupSystemEvent = self.mock_cleanupSystemEvent
        self.system_manager.scheduleSystemPollEvent = self.mock_scheduleSystemPollEvent
            
    def tearDown(self):
        pass
        
    def mock_cleanupSystemEvent(self, event):
        self.mock_cleanupSystemEvent_called = True;
        
    def mock_scheduleSystemPollEvent(self, system):
        self.mock_scheduleSystemPollEvent_called = True;
        
    def testGetSystemEventsForProcessing(self):
        
        events = self.system_manager.getSystemEventsForProcessing()
        
        # ensure we got our activation event back since it is the highest priority
        assert(len(events) == 1)
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.ACTIVATION)
        
        # remove the activation event and ensure we get the on demand poll event next
        event.delete()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.POLL_NOW)
        
        # remove the poll now event and ensure we get the standard poll event next
        event.delete()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.POLL)
        
        # add another poll event with a higher priority but a future time 
        # and make sure we don't get it (because of the future activation time)
        orgPollEvent = event
        enabled_time = datetime.datetime.now() + datetime.timedelta(1) # now + 1 day
        new_poll_event = models.SystemEvent(system=orgPollEvent.system, 
            event_type=orgPollEvent.event_type, priority=orgPollEvent.priority + 1,
            time_enabled=enabled_time)
        new_poll_event.save()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.system_event_id != new_poll_event.system_event_id)
        
    def testGetSystemEventsForProcessingPollCount(self):
        self.mintConfig.systemPollCount = 3
        
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 3)
        
    def testProcessSystemEvents(self):
        
        #remove the activation event so we handle the poll now event
        events = self.system_manager.getSystemEventsForProcessing()
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.ACTIVATION)
        event.delete()
        
        # make sure next one is poll now event
        events = self.system_manager.getSystemEventsForProcessing()
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.POLL_NOW)
        self.system_manager.processSystemEvents()
        
        # make sure the event was removed and that we have the next poll event 
        # for this system now
        try:
            models.SystemEvent.objects.get(system_event_id=event.system_event_id)
        except models.SystemEvent.DoesNotExist:
            pass
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        local_system = poll_event.systemevent_set.all()[0]
        event = models.SystemEvent.objects.get(system=local_system, event_type=poll_event)
        assert(event is not None)
        
    def testProcessSystemEventsNoTrigger(self):
        # make sure activation event doesn't trigger next poll event
        # start with no regular poll events
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        models.SystemEvent.objects.filter(event_type=poll_event).delete()
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        
        # make sure next one is activation now event
        events = self.system_manager.getSystemEventsForProcessing()
        event = events[0]
        assert(event.event_type.name == models.SystemEventType.ACTIVATION)
        self.system_manager.processSystemEvents()
        
        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=poll_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass
        
    def testDispatchSystemEvent(self):
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        poll_now_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL_NOW)
        act_event = models.SystemEventType.objects.get(name=models.SystemEventType.ACTIVATION)
        
        system = models.System(name="hey")
        system.save()
        
        # sanity check dispatching poll event
        event = models.SystemEvent(system=system,event_type=poll_event, priority=poll_event.priority)
        event.save()
        self.system_manager.dispatchSystemEvent(event)
        assert(self.mock_cleanupSystemEvent_called)
        assert(self.mock_scheduleSystemPollEvent_called)
        
        # sanity check dispatching poll_now event
        self.mock_scheduleSystemPollEvent_called = False # reset it
        event = models.SystemEvent(system=system, event_type=poll_now_event, priority=poll_now_event.priority)
        event.save()
        self.system_manager.dispatchSystemEvent(event)
        assert(self.mock_cleanupSystemEvent_called)
        assert(self.mock_scheduleSystemPollEvent_called == False)
        
        network = models.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.public_dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.primary = True
        network.system = system
        network.save()

        # sanity check dispatching activation event
        self.mock_scheduleSystemPollEvent_called = False # reset it
        event = models.SystemEvent(system=system, event_type=act_event, priority=act_event.priority)
        event.save()
        self.system_manager.dispatchSystemEvent(event)
        assert(self.mock_cleanupSystemEvent_called)
        assert(self.mock_scheduleSystemPollEvent_called == False)
        
        
