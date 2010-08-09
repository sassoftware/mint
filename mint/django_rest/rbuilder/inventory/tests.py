import datetime
from django.test import TestCase
from django.test.client import Client

from mint.django_rest.rbuilder.inventory import systemdbmgr
from mint.django_rest.rbuilder.inventory import models

class InventoryTestCase(TestCase):
          
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.client = Client()

    def notestGetTypes(self):
        response = self.client.get('/api/inventory/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/inventory/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def notestPostTypes(self):
        response = self.client.post('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def notestPutTypes(self):
        response = self.client.put('/api/inventory/')
        self.assertEquals(response.status_code, 405)
        
    def notestDeleteTypes(self):
        response = self.client.delete('/api/inventory/')
        self.assertEquals(response.status_code, 405)
       
class SystemsTestCase(TestCase):
    
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
        system = models.System(name="mgoblue", description="best appliance ever", activated=False)
        self.system_manager.addSystem(system)
        assert(system is not None)
        
        # make sure we scheduled our activation event
        assert(self.mock_scheduleSystemActivationEvent_called)
        
    def testAddActivatedSystem(self):
        # create the system
        system = models.System(name="mgoblue", description="best appliance ever", activated=True)
        self.system_manager.addSystem(system)
        assert(system is not None)
        
        # make sure we did not schedule activation
        assert(self.mock_scheduleSystemActivationEvent_called == False)
        
        # make sure we scheduled poll event
        assert(self.mock_scheduleSystemPollEvent_called)
        
class SystemEventTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        
        # need a system
        self.system = models.System(name="mgoblue", description="best appliance ever")
        self.system.save()
        
        # start with no logs/system events
        models.SystemLog.objects.all().delete()
        models.SystemEvent.objects.all().delete()
            
    def tearDown(self):
        pass
    
    def testScheduleSystemPollEvent(self):
        self.system_manager.scheduleSystemPollEvent(self.system)
        
        # make sure we have our poll event
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=poll_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
    def testScheduleSystemActivationEvent(self):
        self.system_manager.scheduleSystemActivationEvent(self.system)
        
        activation_event = models.SystemEventType.objects.get(name=models.SystemEventType.ACTIVATION)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=activation_event).get()
        assert(event is not None)
        
        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_activated_entries = log.log_entries.all()
        assert(len(sys_activated_entries) == 1)
        
class SystemEventProcessingTestCase(TestCase):
    
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        self.mintConfig = self.system_manager.cfg
            
    def tearDown(self):
        pass
        
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
        event = models.SystemEvent.objects.get(system=event.system, event_type=poll_event)
        assert(event is not None)
        assert(event.time_enabled > datetime.datetime.now())
        
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
