from mint.django_rest.rbuilder.inventory.models import System, SystemEvent, SystemEventType

from django.test.client import Client

import unittest

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
        self.system = System.objects.create(name='mgoblue')
        self.system_event_type = SystemEventType.objects.create(name="poll", description="a poll event")
        self.system_event = SystemEvent.objects.create(system=self.system, event_type=self.system_event_type)
            
    def tearDown(self):
        self.system_event.delete()
        self.system_event_type.delete()
        self.system.delete()
