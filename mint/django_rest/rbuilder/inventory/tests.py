import unittest

from django.test.client import Client

from mint.django_rest.rbuilder.inventory import systemdbmgr
from mint.django_rest.rbuilder.inventory.models import System, SystemEvent, SystemEventType

class InventoryTestCase(unittest.TestCase):
          
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
       
class InventorySystemsTestCase(unittest.TestCase):
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
        
class SystemEventTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
        self.system = System.objects.create(name='mgoblue')
        self.system2 = System.objects.create(name='mgoblue2')
        self.system3 = System.objects.create(name='mgoblue3')
        self.system_event_type = SystemEventType.objects.create(name=SystemEventType.POLL, 
            description=SystemEventType.POLL_DESC, priority=SystemEventType.POLL_PRIORITY)
        self.system_event_type2 = SystemEventType.objects.create(name=SystemEventType.ACTIVATION, 
            description=SystemEventType.ACTIVATION_DESC, priority=SystemEventType.ACTIVATION_PRIORITY)
        self.system_event_type3 = SystemEventType.objects.create(name=SystemEventType.POLL_NOW, 
            description=SystemEventType.POLL_NOW_DESC, priority=SystemEventType.POLL_NOW_PRIORITY)
        self.system_event = SystemEvent.objects.create(system=self.system, event_type=self.system_event_type,
            priority=self.system_event_type.priority)
        self.system_event2 = SystemEvent.objects.create(system=self.system2, event_type=self.system_event_type2,
            priority=self.system_event_type2.priority)
        self.system_event3 = SystemEvent.objects.create(system=self.system3, event_type=self.system_event_type3,
            priority=self.system_event_type3.priority)
            
    def tearDown(self):
        self.system_event.delete()
        self.system_event2.delete()
        self.system_event2.delete()
        self.system_event_type.delete()
        self.system_event_type2.delete()
        self.system_event_type3.delete()
        self.system.delete()
        self.system2.delete()
        self.system3.delete()
        
    def testGetSystemEventsForProcessing(self):
        '''test'''
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)
        
        
