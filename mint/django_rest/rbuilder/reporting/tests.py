from mint.django_rest.rbuilder.users.models import User
from mint.django_rest.rbuilder.projects.models import Project

from django.test.client import Client

from decimal import Decimal
from datetime import timedelta
import datetime
import time
import unittest

class ReportTestCase(unittest.TestCase):
          
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.client = Client()

    def notestGetTypes(self):
        response = self.client.get('/api/reports/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def notestPostTypes(self):
        response = self.client.post('/api/reports/')
        self.assertEquals(response.status_code, 405)
        
    def notestPutTypes(self):
        response = self.client.put('/api/reports/')
        self.assertEquals(response.status_code, 405)
        
    def notestDeleteTypes(self):
        response = self.client.delete('/api/reports/')
        self.assertEquals(response.status_code, 405)
       
class ReportTypeDescriptorTestCase(unittest.TestCase):
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.client = Client()

    def notestGetTypesDescriptor(self):
        response = self.client.get('/api/reports/imagesReport/descriptor/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/imagesReport/descriptor/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def notestPostTypesDescriptor(self):
        response = self.client.post('/api/reports/imagesReport/descriptor/')
        self.assertEquals(response.status_code, 405)
    
    def notestPutTypesDescriptor(self):
        response = self.client.put('/api/reports/imagesReport/descriptor/')
        self.assertEquals(response.status_code, 405)
        
    def notestDeleteTypesDescriptor(self):
        response = self.client.delete('/api/reports/imagesReport/descriptor/')
        self.assertEquals(response.status_code, 405)
        
class ImagesPerProductTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        now = time.time()
        self.user = User.objects.create(user_name='user',full_name='User T. Foo',passwd='foo',
            email='foo@bar.com', time_created=now, time_accessed=now,
            active=1)
        self.product = Project.objects.create(hostname='foo',name='foo Applicance', 
            namespace='rpath',domainname='eng.rpath.com',repositoryHostName='foo.eng.rpath.com',
            prodtype='Appliance',hidden=False,creatorid=self.user,timecreated=now,
            timemodified=now, shortname='foo')
        self.version = Project.Version.objects.create(productId=self.product,namespace='foo',name='bar',
            timecreated=now)
            
        dt = datetime.date(2008,1,1)
        timeint = time.mktime(dt.timetuple())
        
        for i in range(0,50):
            Project.Image.objects.create(name='Image'+str(i),product_id=self.product, created_by=self.user, build_type=1,
                time_created=str(timeint), trove_name='foo', trove_version='bar',trove_flavor='baz',
                trove_last_changed=now, deleted=0, stage_name='Development',product_version_id=
                self.version, build_count=1, status=300)
                
            timeint += 60*60*72
            
    def tearDown(self):
        self.user.delete()
        self.product.delete()
        self.version.delete()
        for image in Images.objects.all():
            image.delete()
        
    def notestGetImagePerProductReport(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.short_name)
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/imagesReport/data/'+self.product.short_name+'?_method=GET')
        self.assertEquals(response.status_code, 200)    
    
    def notestGetEmptySet(self):
        """Test to make sure that an empty report is generated for the give query"""
        response = self.client.post('/api/reports/imagesReport/data/'+self.product.short_name+'?_method=GET&timeunits=day&starttime=100&endtime=200')
        self.assertEquals(response.content, expectedResult)
    
    def notestBadRequestGet(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.short_name+'?timeunits=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.short_name+'?starttime=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.short_name+'?endtime=bob')
        self.assertEquals(response.status_code, 400)
            
    def notestNotFoundGet(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.short_name+'1')
        self.assertEquals(response.status_code, 404)   
        
        
expectedResult = """<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<imagesReport id="http://testserver/api/reports/imagesReport/data/foo?_method=GET&amp;timeunits=day&amp;starttime=100&amp;endtime=200">
  <timeSegments/>
  <startTime>100</startTime>
  <endTime>200</endTime>
  <timeUnits>day</timeUnits>
</imagesReport>
"""
