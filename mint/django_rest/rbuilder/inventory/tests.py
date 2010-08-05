from django.test.client import Client
from django.test import TestCase

from mint.django_rest.rbuilder.inventory import systemdbmgr
#from mint.django_rest.rbuilder.inventory.models import System, SystemEvent, SystemEventType

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
    fixtures = ['system_events']
    
    def setUp(self):
        self.client = Client()
        self.system_manager = systemdbmgr.SystemDBManager()
            
    def tearDown(self):
        pass
        
    def testGetSystemEventsForProcessing(self):
        '''test'''
        events = self.system_manager.getSystemEventsForProcessing()
        assert(len(events) == 1)      
