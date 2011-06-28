#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from mint.django_rest.rbuilder.platforms import models as pmodels  # pyflakes=ignore
from mint.django_rest.rbuilder.platforms import testsxml  # pyflakes=ignore
from mint.django_rest.rbuilder.inventory.tests import XMLTestCase  # pyflakes=ignore
from xobj import xobj  # pyflakes=ignore
from lxml import etree  # pyflakes=ignore


class PlatformsTestCase(XMLTestCase):
    fixtures = ['platformstestxml']
    
    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        return self.toXObj(response.content)

    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)
        
    def testGetPlatform(self):
		# get django model instance corresponding to
        # platforms/1 (ie platform with id = 1)
        platform_gotten = self.xobjResponse('/api/v1/platforms/1')
        # load platform/1 from db to check
        platform = pmodels.Platform.objects.get(pk=1)
        # now test that the platform attributes are equal
        self.assertEquals(platform.label,platform_gotten.label)
        self.assertEquals(platform.platform_trove_name,platform_gotten.platform_trove_name)
        self.assertEquals(platform.repository_host_name,platform_gotten.repository_host_name)
        self.assertEquals(platform.product_version,platform_gotten.product_version)
        self.assertEquals(platform.platform_name,platform_gotten.platform_name)
        self.assertEquals(platform.platform_usage_terms,platform_gotten.platform_usage_terms)
        self.assertEquals(platform.mode,platform_gotten.mode)
        self.assertEquals(platform.enabled,platform_gotten.enabled)
        self.assertEquals(platform.configurable,platform_gotten.configurable)
        self.assertEquals(platform.mirror_permission,platform_gotten.mirror_permission)
        self.assertEquals(platform.abstract,platform_gotten.abstract)
        self.assertEquals(platform.platform_type,platform_gotten.platform_type)
        self.assertEquals(platform.platform_status,platform_gotten.platform_status)
        self.assertEquals(platform.content_source_types,platform_gotten.content_source_types)
        self.assertEquals(platform.load,platform_gotten.load)
        self.assertEquals(platform.is_platform,platform_gotten.is_platform)
        self.assertEquals(platform.platform_versions,platform_gotten.platform_versions)
        self.assertEquals(platform.project,platform_gotten.project)
        
    def testGetPlatforms(self):
		platforms = pmodels.Platform.objects.all()
		platforms_gotten = self.xobjResponse('platforms/')
		self.assertEquals(len(platforms), len(platforms_gotten))
        
    
    def testGetImageTypeDefinitions(self): #ignore
        pass
        
    #platformSourceStatus and ContentSourceStatus are merged into SourceStatus    
    def testGetPlatformSourceStatus(self):
		pSourceStatus = pmodels.SourceStatus.objects.get(pk=1)
		pSourceStatus_gotten = self.xobjResponse('/api/v1/platforms/sourcestatus/1')  #not sure
		self.asserEquals(pSourceStatus.connected,pSourceStatus_gotten.connected)
		self.asserEquals(pSourceStatus.valid,pSourceStatus_gotten.valid)
		self.asserEquals(pSourceStatus.message,pSourceStatus_gotten.message)
		self.asserEquals(pSourceStatus.content_source_type,pSourceStatus_gotten.content_source_type)
		self.asserEquals(pSourceStatus.short_name,pSourceStatus_gotten.short_name)
        
        
    def testGetContentSourceStatusNoData(self):
        pass
        
    def testGetContentSourceStatusData(self):
        pass
        
    def testGetSourceTypeStatus(self): #ignore
        pass
        
    def testGetSourceTypeStatusSMT(self): #ignore
        pass
        
    def testGetSourceDescriptor(self): #ignore
        pass
        
    def testGetContentSourceTypes(self):
        cSourceTypes = pmodels.ContentSourceType.objects.all()
        cSourceTypes_gotten = self.xobjResponse('/api/v1/platforms/contentsourcetypes/')  #not sure
        self.assertEquals(len(cSourceTypes), len(cSourceTypes_gotten))
        
        
    def testGetContentSourceType(self):
        cSourceType = pmodels.ContentSourceType.objects.get(pk=1)
        cSourceType_gotten = self.xobjResponse('/api/v1/platforms/contentsourcetypes/1')  #not sure
        self.assertEquals(cSourceType.content_source_type,cSourceType_gotten.content_source_type)
        self.assertEquals(cSourceType.required,cSourceType_gotten.required)
        self.assertEquals(cSourceType.singleton,cSourceType_gotten.singleton)
        
        
    def testGetContentSources(self):
        contentSources = pmodels.ContentSources.objects.all()
        contentSources_gotten = self.xobjResponse('/api/v1/platforms/contentsources/') #not sure
        self.assertEquals(len(contentSources),len(contentSources_gotten))
        
    def testGetContentSource(self):
        contentSource = pmodels.ContentSources.objects.get(pk=1)
        contentSource_gotten = self.xobjResponse('/api/v1/platforms/contentsources/1') #not sure
        self.assertEquals(contentSource.name,contentSource_gotten.name)
        self.assertEquals(contentSource.short_name,contentSource_gotten.short_name)
        self.assertEquals(contentSource.default_source,contentSource_gotten.default_source)
        self.assertEquals(contentSource.order_index,contentSource_gotten.order_index)
        self.assertEquals(contentSource.content_source_type,contentSource_gotten.content_source_type)
        self.assertEquals(contentSource.enabled,contentSource_gotten.enabled)
        self.assertEquals(contentSource.content_source_status,contentSource_gotten.content_source_status)        
        
                
    def testGetSourcesByPlatform(self):  #ignore
        pass
        
    def testGetSourceTypesByPlatform(self): #ignore
        pass
        
    def testUpdateSource(self):
        pass
        
    def testCreateSource(self):
        pass
        
    def testCreateSource2(self):
        pass
        
    def testUpdatePlatform(self):
        pass
        
    def testGetPlatformStatus(self): #ignore
        pass
        
    def testGetPlatformLoadStatus(self):  #added
        pLoadStatus = pmodels.PlatformLoadStatus.objects.get(pk=1)
        pLoadStatus_gotten = self.xobjResponse('/api/v1/platforms/platformloadstatus/1') #not sure
        self.assertEquals(pLoadStatus.code,pLoadStatus_gotten.code)
        self.assertEquals(pLoadStatus.message,pLoadStatus_gotten.message)
        self.assertEquals(pLoadStatus.is_final,pLoadStatus_gotten.is_final)
        
    def testGetLoadPlatform(self):
       loadPlatform = pmodels.PlatformLoad.objects.get(pk=1)
       loadPlatform_gotten = self.xobjResponse('/api/v1/platforms/platformload/1') #not sure
       self.assertEquals(loadPlatform.load_uri, loadPlatform_gotten.load_uri)
       self.assertEquals(loadPlatform.job_id, loadPlatform_gotten.job_id)
       self.assertEquals(loadPlatform.platform_id, loadPlatform_gotten.platform_id)
       self.assertEquals(loadPlatform.platform_load_status, loadPlatform_gotten.platform_load_status)
       
        

class NewPlatformTest(XMLTestCase):
    fixtures = ['platformstestxml']
    
    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        return self.toXObj(response.content)

    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)
    
    def testCreatePlatform(self):
		#Creates a new platform
        response = self._post('platforms/',
            data=platformstestxml.platformPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        
        # 3 platforms were already in the fixture
        self.assertEquals(4, len(pmodels.Platform.objects.all()))
        platform = pmodels.Platform.objects.get(platform_name="Platform Post")
        self.assertEquals("PlatformTest Post", platform.label)
        self.assertEquals("Platform Post",platform.product_version)
        
    def testCreateContentSource(self):
		#Creates a new platform
        response = self._post('platforms/',
            data=platformstestxml.contentSourcePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        
        # 3 sources were already in the fixture
        self.assertEquals(4, len(pmodels.ContentSource.objects.all()))
        content = pmodels.ContentSource.objects.get(name="PlatformTestPost")
        self.assertEquals("PlatformTestPost",content.short_name)
        self.asserEquals("1",content.order_index)
        
   
    def testCreateContentSourceType(self):
		#Creates a new contentsourcetype
        response = self._post('platforms/',
            data=platformstestxml.contentSourceTypePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code) 
        
         # 3 sources were already in the fixture
        self.assertEquals(4, len(pmodels.ContentSourceType.objects.all()))
        contentType = pmodels.ContentSourceType.objects.get(content_source_type="ContentSourceTypePost")
        self.assertEquals("true",contentType.required)
        self.asserEquals("true",contentType.singleton)  
        
        
    def testCreatePlatformLoadStatus(self):
		#Creates a new contentsourcetype
        response = self._post('platforms/',
            data=platformstestxml.platformLoadStatusPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)             
        
         # 3 stasus were already in the fixture
        self.assertEquals(4, len(pmodels.PlatformLoadStatus.objects.all()))
        pLoadStatus = pmodels.PlatformLoadStatus.objects.get(code=10)
        self.assertEquals("PlatformLoadStatusPostTest",pLoadStatus.message)
        self.asserEquals("true",pLoadStatus.is_final)  
        
        
    def testCreatePlatformLoad(self):
		#Creates a new contentsourcetype
        response = self._post('platforms/',
            data=platformstestxml.platformLoadPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code) 
        
         # 3 stasus were already in the fixture
        self.assertEquals(4, len(pmodels.PlatformLoad.objects.all()))
        pLoad = pmodels.PlatformLoad.objects.get(load_uri="platformLoadUri")
        self.assertEquals(10,pLoad.job_id)
        self.asserEquals(10,pLoad.platform_id)  
        
        
    def testCreatePlatformVersion(self):
		#Creates a new contentsourcetype
        response = self._post('platforms/',
            data=platformstestxml.platformVersionPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code) 
        
        # 3 stasus were already in the fixture
        self.assertEquals(4, len(pmodels.PlatformVersion.objects.all()))
        platformVersion = pmodels.PlatformVersion.objects.get(name="PlatformVersionPostTest")
        self.assertEquals("Post",platformVersion.version)
        self.asserEquals("PlatformVersionPostTest",platformVersion.label) 
        
        
    def testCreateSourceStatus(self):
		#Creates a new contentsourcetype
        response = self._post('platforms/',
            data=platformstestxml.sourceStatusPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)  
        
        # 3 stasus were already in the fixture
        self.assertEquals(4, len(pmodels.SourceStatus.objects.all()))
        sourceStatus = pmodels.SourceStatus.objects.get(message="sourceStatusPostTest")
        self.assertEquals(true,sourceStatus.connected)
        self.asserEquals("sourceStatusPostTest",sourceStatus.short_name)                    
		        
        
    def testCreatePlatform_NoProduct(self):
        pass
        
    def testCreatePlatform_NoPlatform(self):
        pass
