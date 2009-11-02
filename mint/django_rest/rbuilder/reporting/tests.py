from mint.django_rest.rbuilder.models import Images, Products, Users, Versions
from mint.django_rest.rbuilder.reporting.models import ReportType, ReportTypes

from django.test.client import Client

from decimal import Decimal
from datetime import timedelta
import datetime
import time
import unittest

class ReportTypeTestCase(unittest.TestCase):
          
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.reporttype = ReportType.objects.create(name='Test',
            description='Test Descr', _timecreated=str(time.time()),
            _timeupdated=str(time.time()), _active=1, _uri='imagesPerProduct')
        self.client = Client()
        
    def tearDown(self):
        self.reporttype.delete()

    def testTypeModelLookup(self):
        reporttype = ReportType.objects.get(pk = self.reporttype.pk)
        self.assertEquals(reporttype.name, 'Test')

    def testGetTypes(self):
        response = self.client.get('/api/reports/type/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/type/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def testPostTypes(self):
        response = self.client.post('/api/reports/type/')
        self.assertEquals(response.status_code, 405)
        
    def testPutTypes(self):
        response = self.client.put('/api/reports/type/')
        self.assertEquals(response.status_code, 405)
        
    def testDeleteTypes(self):
        response = self.client.delete('/api/reports/type/')
        self.assertEquals(response.status_code, 405)
       
class ReportTypeDescriptorTestCase(unittest.TestCase):
    #Setup all of the objects that will be needed for this TestCase
    def setUp(self):
        self.reporttype = ReportType.objects.create(name='Test',
            description='Test Descr', _timecreated=str(time.time()),
            _timeupdated=str(time.time()), _active=1, _uri='imagesPerProduct')
        self.client = Client()
        
    def tearDown(self):
        self.reporttype.delete()

    def testGetTypesDescriptor(self):
        response = self.client.get('/api/reports/type/'+self.reporttype._uri+'/descriptor/')
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/type/'+self.reporttype._uri+'/descriptor/?_method=GET')
        self.assertEquals(response.status_code, 200)
        
    def testPostTypesDescriptor(self):
        response = self.client.post('/api/reports/type/'+self.reporttype._uri+'/descriptor/')
        self.assertEquals(response.status_code, 405)
    
    def testPutTypesDescriptor(self):
        response = self.client.put('/api/reports/type/'+self.reporttype._uri+'/descriptor/')
        self.assertEquals(response.status_code, 405)
        
    def testDeleteTypesDescriptor(self):
        response = self.client.delete('/api/reports/type/'+self.reporttype._uri+'/descriptor/')
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
            
        self.reporttype = ReportType.objects.create(name='Test',
            description='Test Descr', _timecreated=str(time.time()),
            _timeupdated=str(time.time()), _active=1, _uri='imagesPerProduct') 
            
    def tearDown(self):
        self.user.delete()
        self.product.delete()
        self.version.delete()
        self.reporttype.delete()
        for image in Images.objects.all():
            image.delete()
        
    def testGetImagePerProductReport(self):
        response = self.client.get('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname)
        self.assertEquals(response.status_code, 200)
        
        response = self.client.post('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'?_method=GET')
        self.assertEquals(response.status_code, 200)    
    
    def testGetEmptySet(self):
        """Test to make sure that an empty report is generated for the give query"""
        response = self.client.post('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'?_method=GET&timeunits=day&starttime=100&endtime=200')
        self.assertEquals(response.content, expectedResult)
    
    def testBadRequestGet(self):
        response = self.client.get('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'?timeunits=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'?starttime=bob')
        self.assertEquals(response.status_code, 400)
        
        response = self.client.get('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'?endtime=bob')
        self.assertEquals(response.status_code, 400)
            
    def testNotFoundGet(self):
        response = self.client.get('/api/reports/type/'+ self.reporttype._uri +'/data/'+self.product.shortname+'1')
        self.assertEquals(response.status_code, 404)   
        
        
expectedResult = """<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<imagesPerProduct id="http://testserver/api/reports/type/imagesPerProduct/data/foo?_method=GET&amp;timeunits=day&amp;starttime=100&amp;endtime=200/">
  <timeSegments/>
  <startTime>100</startTime>
  <endTime>200</endTime>
  <timeUnits>day</timeUnits>
</imagesPerProduct>
"""