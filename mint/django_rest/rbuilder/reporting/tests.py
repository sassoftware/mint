from mint.django_rest.rbuilder.models import Images, Products, Users, Versions
from mint.django_rest.rbuilder.reporting.models import Report, Reports

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
        self.user = Users.objects.create(username='user',fullname='User T. Foo',passwd='foo',
            email='foo@bar.com', timecreated=str(time.time()), timeaccessed=str(time.time()),
            active=1)
        self.product = Products.objects.create(hostname='foo',name='foo Applicance', 
            namespace='rpath',domainname='eng.rpath.com',repositoryHostName='foo.eng.rpath.com',
            prodtype='Appliance',hidden=0,creatorid=self.user,timecreated=str(time.time()),
            timemodified=str(time.time()), shortname='foo')
        self.version = Versions.objects.create(productId=self.product,namespace='foo',name='bar',
            timecreated=str(time.time()))
            
        dt = datetime.date(2008,1,1)
        timeint = time.mktime(dt.timetuple())
        
        for i in range(0,50):
            Images.objects.create(name='Image'+str(i),productId=self.product, createdby=self.user, buildtype=1,
                timecreated=str(timeint), trovename='foo', troveversion='bar',troveflavor='baz',
                trovelastchanged=str(time.time()), deleted=0, stagename='Development',productversionid=
                self.version, buildcount=1, status=300)
                
            timeint += 60*60*72
            
    def tearDown(self):
        self.user.delete()
        self.product.delete()
        self.version.delete()
        for image in Images.objects.all():
            image.delete()
        
    def notestGetImagePerProductReport(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.shortname)
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/imagesReport/data/'+self.product.shortname+'?_method=GET')
        self.assertEquals(response.status_code, 200)    
    
    def notestGetEmptySet(self):
        """Test to make sure that an empty report is generated for the give query"""
        response = self.client.post('/api/reports/imagesReport/data/'+self.product.shortname+'?_method=GET&timeunits=day&starttime=100&endtime=200')
        self.assertEquals(response.content, expectedResult)
    
    def notestBadRequestGet(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.shortname+'?timeunits=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.shortname+'?starttime=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.shortname+'?endtime=bob')
        self.assertEquals(response.status_code, 400)
            
    def notestNotFoundGet(self):
        response = self.client.get('/api/reports/imagesReport/data/'+self.product.shortname+'1')
        self.assertEquals(response.status_code, 404)   
        
        
expectedResult = """<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<imagesReport id="http://testserver/api/reports/imagesReport/data/foo?_method=GET&amp;timeunits=day&amp;starttime=100&amp;endtime=200">
  <timeSegments/>
  <startTime>100</startTime>
  <endTime>200</endTime>
  <timeUnits>day</timeUnits>
</imagesReport>
"""
