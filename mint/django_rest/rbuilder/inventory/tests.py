import datetime
from django.test import TestCase
from django.test.client import Client

from mint.django_rest.rbuilder.inventory import systemdbmgr
from mint.django_rest.rbuilder.inventory.models import System, SystemEvent, SystemEventType

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
       
class InventorySystemsTestCase(TestCase):
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.client = Client()

    def notestGetTypesDescriptor(self):
        response = self.client.get('/api/inventory/systems/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/inventory/systems/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def notestPostTypesDescriptor(self):
        response = self.client.post('/api/inventory/systems/')
        self.assertEquals(response.status_code, 405)
    
    def notestPutTypesDescriptor(self):
        response = self.client.put('/api/inventory/systems/')
        self.assertEquals(response.status_code, 405)
        
    def notestDeleteTypesDescriptor(self):
        response = self.client.delete('/api/inventory/systems/')
        self.assertEquals(response.status_code, 405)
        
class SystemEventTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
            
    def tearDown(self):
        pass
        
class SystemEventProcessingTestCase(TestCase):
    
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
            
    def tearDown(self):
        pass
        
    def testGetSystemEventsForProcessing(self):
        
        events = self.system_manager.getSystemEventsForProcessing()
        
        # ensure we got our activation event back since it is the highest priority
        assert(len(events) == 1)
        event = events[0]
        assert(events[0].event_type.name == SystemEventType.ACTIVATION)
        
        # remove the activation event and ensure we get the on demand poll event next
        event.delete()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.event_type.name == SystemEventType.POLL_NOW)
        
        # remove the poll now event and ensure we get the standard poll event next
        event.delete()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.event_type.name == SystemEventType.POLL)
        
        # add another poll event with a higher priority but a future time 
        # and make sure we don't get it (because of the future activation time)
        orgPollEvent = event
        activationTime = datetime.datetime.now() + datetime.timedelta(1) # now + 1 day
        newPollEvent = SystemEvent(system=orgPollEvent.system, 
            event_type=orgPollEvent.event_type, priority=orgPollEvent.priority + 1,
            time_activation=activationTime)
        newPollEvent.save()
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        event = events[0]
        assert(event.system_event_id != newPollEvent.system_event_id)
        
        
