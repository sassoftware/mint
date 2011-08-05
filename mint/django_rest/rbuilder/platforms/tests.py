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
from mint.django_rest.rbuilder.platforms import platformstestxml

class PlatformsTestCase(XMLTestCase):
    # fixtures = ['platformstestxml']
    
    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        return self.toXObj(response.content)
    
    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)
    
    def testGetPlatform(self):
        platform_gotten = self.xobjResponse('platforms/1')           #unsure about the url
        platform = pmodels.Platform.objects.get(pk=1)
        self.assertEquals(platform.label, platform_gotten.label)
        self.assertEquals(platform.platform_name, platform_gotten.platform_name)
        self.assertEquals(platform.mode, platform_gotten.mode)
        self.assertEquals(platform.enabled, platform_gotten.enabled)
        self.assertEquals(platform.configurable, platform_gotten.configurable)
        self.assertEquals(platform.abstract, platform_gotten.abstract)
        self.assertEquals(platform.content_source_types, platform_gotten.content_source_types)
        self.assertEquals(platform.project, platform_gotten.project)
    
    def testGetPlatforms(self):
        platforms_gotten = self.xobjResponse('platforms/')
        # note that when we test getting Platforms, we are not
        # trying to retrieve a Platforms instance, but rather all
        # the platform instances that it contains
        platforms = pmodels.Platform.objects.all()
        import pdb; pdb.set_trace()
        self.assertEquals(len(list(platforms)), len(platforms_gotten))
    
    def testGetContentSourceTypes(self):
        cSourceTypes = pmodels.ContentSourceType.objects.all()
        import pdb; pdb.set_trace()
        cSourceTypes_gotten = self.xobjResponse('platforms/content_source_types/')
        self.assertEquals(len(list(cSourceTypes)), len(cSourceTypes_gotten))
    
    def testGetContentSourceType(self):
        cSourceType = pmodels.ContentSourceType.objects.get(pk=1)
        cSourceType_gotten = self.xobjResponse('platforms/content_source_types/1')
        self.assertEquals(cSourceType.content_source_type, cSourceType_gotten.content_source_type)
        self.assertEquals(cSourceType.required, cSourceType_gotten.required)
        self.assertEquals(cSourceType.singleton, cSourceType_gotten.singleton)
    
    def testGetContentSources(self):
        contentSources = pmodels.ContentSource.objects.all()
        import pdb; pdb.set_trace()
        contentSources_gotten = self.xobjResponse('platforms/content_sources/')
        self.assertEquals(len(list(contentSources)), len(contentSources_gotten))
    
    def testGetContentSource(self):
        contentSource = pmodels.ContentSources.objects.get(pk=1)
        contentSource_gotten = self.xobjResponse('platforms/content_sources/1')
        self.assertEquals(contentSource.name, contentSource_gotten.name)
        self.assertEquals(contentSource.short_name, contentSource_gotten.short_name)
        self.assertEquals(contentSource.default_source, contentSource_gotten.default_source)
        self.assertEquals(contentSource.order_index, contentSource_gotten.order_index)
        self.assertEquals(contentSource.content_source_type, contentSource_gotten.content_source_type)
        self.assertEquals(contentSource.enabled, contentSource_gotten.enabled)
    
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
    
    ## All tests (including legacy tests from apui/v0) which won't run until
    ## certain models are moved into the db
    
#   def testGetImageTypeDefinitions(self):
#       pass
#   
#   def testGetPlatformLoadStatus(self):  #added
#       pLoadStatus = pmodels.PlatformLoadStatus.objects.get(pk=1)
#       pLoadStatus_gotten = self.xobjResponse('/api/v1/platforms/platform_status/1') #not sure
#       self.assertEquals(pLoadStatus.code, pLoadStatus_gotten.code)
#       self.assertEquals(pLoadStatus.message, pLoadStatus_gotten.message)
#       self.assertEquals(pLoadStatus.is_final, pLoadStatus_gotten.is_final)
#   
#   def testGetLoadPlatform(self):
#       loadPlatform = pmodels.PlatformLoad.objects.get(pk=1)
#       loadPlatform_gotten = self.xobjResponse('/api/v1/platforms/platform_load/1') #not sure
#       self.assertEquals(loadPlatform.load_uri, loadPlatform_gotten.load_uri)
#       self.assertEquals(loadPlatform.job_id, loadPlatform_gotten.job_id)
#       self.assertEquals(loadPlatform.platform_id, loadPlatform_gotten.platform_id)
#       self.assertEquals(loadPlatform.platform_load_status, loadPlatform_gotten.platform_load_status)
#   
#   def testGetPlatformStatus(self): #ignore
#       pass
#   
#   def testGetPlatformSourceStatus(self):
#       """
#       platformSourceStatus and ContentSourceStatus are merged into SourceStatus
#       """
#   	pSourceStatus = pmodels.SourceStatus.objects.get(pk=1)
#   	pSourceStatus_gotten = self.xobjResponse('/api/v1/platforms/sourcestatus/1')  #not sure
#   	self.asserEquals(pSourceStatus.connected, pSourceStatus_gotten.connected)
#   	self.asserEquals(pSourceStatus.valid, pSourceStatus_gotten.valid)
#   	self.asserEquals(pSourceStatus.message, pSourceStatus_gotten.message)
#   	self.asserEquals(pSourceStatus.content_source_type, pSourceStatus_gotten.content_source_type)
#   	self.asserEquals(pSourceStatus.short_name, pSourceStatus_gotten.short_name)
#   
#   def testGetContentSourceStatusNoData(self):
#       pass
#   
#   def testGetContentSourceStatusData(self):
#       pass
#   
#   def testGetSourceTypeStatus(self): #ignore
#       pass
#   
#   def testGetSourceTypeStatusSMT(self): #ignore
#       pass
#   
#   def testGetSourceDescriptor(self): #ignore
#       pass
        


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
        self.assertEquals(4, len(list(pmodels.Platform.objects.all())))
        platform = pmodels.Platform.objects.get(platform_name="Platform")
        self.assertEquals("Platform", platform.label)
    
    def testCreateContentSource(self):
		#Creates a new platform
        response = self._post('platforms/content_sources/',
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
        response = self._post('platforms/content_source_types',
            data=platformstestxml.contentSourceTypePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
         # 3 sources were already in the fixture
        # self.assertEquals(4, len(list(pmodels.ContentSourceType.objects.all())))
        
    
    def testCreatePlatform_NoProduct(self):
        pass
    
    def testCreatePlatform_NoPlatform(self):
        pass
        
    
    def testUpdatePlatform(self):
		#1 already in fixture
        plat = pmodels.Platform.objects.get(pk=1)
        r = self._put('platforms/1',                              #unsure about the url
            data=platformstestxml.platformPUTXml,
            username='admin', password='password')
        updatedPlat = pmodels.Platform.objects.get(pk=1)
        # Check that name and other fields are updated
        self.assertEquals('PlatformPut', updatedPlat.label)
        self.assertEquals('PlatformPut', updatedPlat.platform_name)
        self.assertEquals('auto', updatedPlat.mode)
		
    
    def testUpdateContentSource(self):
		#1 already in fixture
        content = pmodels.ContentSource.objects.get(pk=1)
        r = self._put('platforms/1/content_source',                              #unsure about the url
            data=platformstestxml.contentSourcePUTXml,
            username='admin', password='password')
        updatedContent = pmodels.ContentSource.objects.get(pk=1)
        # Check that name and other fields are updated
        self.assertEquals('PlatformTestPut', updatedContent.name)
        self.assertEquals('PlatformTestPut', updatedContent.short_name)
        self.assertEquals('true', updatedContent.default_source)
        
    
    def testUpdateContentSourceType(self):
		#1 already in fixture
        content = pmodels.ContentSourceType.objects.get(pk=1)
        r = self._put('platforms/1/content_source_type',                              #unsure about the url
            data=platformstestxml.contentSourceTypePUTXml,
            username='admin', password='password')
        updatedContent = pmodels.Platform.objects.get(pk=1)
        # Check that name and other fields are updated
        self.assertEquals('ContentSourceTypePut', updatedContent.content_source_type)


    ## All tests (including legacy tests from apui/v0) which won't run until
    ## certain models are moved into the db
    
#    def testUpdatePlatformLoad(self):
#		#1 already in fixture
#        pLoad = pmodels.PlatformLoad.objects.get(pk=1)
#        r = self._put('platforms/1',                              #unsure about the url
#            data=platformstestxml.platformLoadPUTXml,
#            username='admin', password='password')
#        updatedPLoad = pmodels.PlatformLoad.objects.get(pk=1)
#        # Check that name and other fields are updated
#        self.assertEquals('platformLoadUriPut', updatedPLoad.load_uri)
#        self.assertEquals(12, updatedPLoad.job_id)
#        self.assertEquals(12, updatedPLoad.platform_id)
#    
#    def testCreatePlatformLoad(self):
#		#Creates a new contentsourcetype
#        response = self._post('platforms/',                  #unsure about the url
#            data=platformstestxml.platformLoadPOSTXml,
#            username="admin", password="password")
#        self.assertEquals(200, response.status_code)
#        # 3 stasus were already in the fixture
#        self.assertEquals(4, len(pmodels.PlatformLoad.objects.all()))
#        pLoad = pmodels.PlatformLoad.objects.get(load_uri="platformLoadUri")
#        self.assertEquals(10, pLoad.job_id)
#        self.asserEquals(10, pLoad.platform_id)
#        
#    
#    def testCreatePlatformVersion(self):
#		#Creates a new contentsourcetype
#        response = self._post('platforms/',                        #unsure about the url
#            data=platformstestxml.platformVersionPOSTXml,
#            username="admin", password="password")
#        self.assertEquals(200, response.status_code)
#        # 3 stasus were already in the fixture
#        self.assertEquals(4, len(pmodels.PlatformVersion.objects.all()))
#        platformVersion = pmodels.PlatformVersion.objects.get(name="PlatformVersionPostTest")
#        self.assertEquals("Post", platformVersion.version)
#        self.asserEquals("PlatformVersionPostTest", platformVersion.label)
#        
#    def testCreatePlatformLoadStatus(self):
#		#Creates a new contentsourcetype
#        response = self._post('platforms/',                    #unsure about the url
#            data=platformstestxml.platformLoadStatusPOSTXml,
#            username="admin", password="password")
#        self.assertEquals(200, response.status_code)
#        # 3 stasus were already in the fixture
#        self.assertEquals(4, len(pmodels.PlatformLoadStatus.objects.all()))
#        pLoadStatus = pmodels.PlatformLoadStatus.objects.get(code=10)
#        self.assertEquals("PlatformLoadStatusPostTest", pLoadStatus.message)
#        self.asserEquals("true", pLoadStatus.is_final)
#
#    def testCreateSourceStatus(self):
#		#Creates a new contentsourcetype
#        response = self._post('platforms/',                         #unsure about the url
#            data=platformstestxml.sourceStatusPOSTXml,
#            username="admin", password="password")
#        self.assertEquals(200, response.status_code)
#        # 3 stasus were already in the fixture
#        self.assertEquals(4, len(pmodels.SourceStatus.objects.all()))
#        sourceStatus = pmodels.SourceStatus.objects.get(message="sourceStatusPostTest")
#        self.assertEquals("true", sourceStatus.connected)
#        self.asserEquals("sourceStatusPostTest", sourceStatus.short_name)
#
#    def testUpdatePlatformLoadStatus(self):
#		#1 already in fixture
#        plStatus = pmodels.PlatformLoadStatus.objects.get(pk=1)
#        r = self._put('platforms/1',                             #unsure about the url
#            data=platformstestxml.platformLoadStatusPUTXml,
#            username='admin', password='password')
#        updatedPlStatus = pmodels.PlatformLoadStatus.objects.get(pk=1)
#        # Check that name and other fields are updated
#        self.assertEquals(12, updatedPlStatus.code)
#        self.assertEquals('PlatformLoadStatusPutTest', updatedPlStatus.message)
#    
#    def testUpdatePlatformVersion(self):
#		#1 already in fixture
#        pVersion = pmodels.PlatformVersion.objects.get(pk=1)
#        r = self._put('platforms/1',                              #unsure about the url
#            data=platformstestxml.platformVersionPUTXml,
#            username='admin', password='password')
#        updatedPVersion = pmodels.PlatformVersion.objects.get(pk=1)
#        # Check that name and other fields are updated
#        self.assertEquals('PlatformVersionPutTest', updatedPVersion.name)
#        self.assertEquals('Put', updatedPVersion.version)
#        self.assertEquals('Put', updatedPVersion.revision)
#        self.assertEquals('PlatformVersionPutTest', updatedPVersion.label)
#        self.assertEquals('PlatformVersionPutTest', updatedPVersion.ordering)
#    
#    def testUpdateSourceStatus(self):
#		#1 already in fixture
#        sourceStatus = pmodels.SourceStatus.objects.get(pk=1)
#        r = self._put('platforms/1',                              #unsure about the url
#            data=platformstestxml.sourceStatusPUTXml,
#            username='admin', password='password')
#        updatedSourceStatus = pmodels.SourceStatus.objects.get(pk=1)
#        # Check that name and other fields are updated
#        self.assertEquals('sourceStatusPutTest', updatedSourceStatus.message)
#        self.assertEquals('sourceStatusPutTest', updatedSourceStatus.short_name)												        
#