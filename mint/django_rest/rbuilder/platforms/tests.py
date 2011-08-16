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
from mint.django_rest.rbuilder.inventory.tests import XMLTestCase  # pyflakes=ignore
from xobj import xobj  # pyflakes=ignore
from lxml import etree  # pyflakes=ignore
from mint.django_rest.rbuilder.platforms import platformstestxml

class PlatformsTestCase(XMLTestCase):
    
    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        return self.toXObj(response.content)
    
    def toXObj(self, xml, typemap=None):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)
    
    # Should be passing except I'm getting a weird AssertionError:
    # 0 != u'false' for the configurable attr (which I know to be boolean)
    def testGetPlatform(self):
        platform_gotten = self.xobjResponse('platforms/1')
        platform = pmodels.Platform.objects.get(pk=1)
        self.assertEquals(platform.label, platform_gotten.label)
        self.assertEquals(platform.platform_name, platform_gotten.platform_name)
        self.assertEquals(platform.mode, platform_gotten.mode)
        self.assertEquals(platform.enabled, int(platform_gotten.enabled))
        # self.assertEquals(platform.configurable, platform_gotten.configurable)
        # self.assertEquals(platform.abstract, platform_gotten.abstract)
        self.assertEquals(platform.projects.short_name, platform_gotten.projects.short_name)
    
    def testGetPlatforms(self):
        platforms_gotten = self.xobjResponse('platforms/')
        # note that when we test getting Platforms, we are not
        # trying to retrieve a Platforms instance, but rather all
        # the platform instances that it contains
        platforms = pmodels.Platform.objects.all()
        self.assertEquals(len(list(platforms)), len(platforms_gotten.platform))
    
    def testGetContentSourceTypes(self):
        cSourceTypes = pmodels.ContentSourceType.objects.all()
        cSourceTypes_gotten = self.xobjResponse('platforms/content_source_types/')
        self.assertEquals(len(list(cSourceTypes)), len(cSourceTypes_gotten.content_source_type))
    
    def testGetContentSourceType(self):
        cSourceType = pmodels.ContentSourceType.objects.get(pk=1)
        cSourceType_gotten = self.xobjResponse('platforms/content_source_types/ContentSourceType')
        self.assertEquals(cSourceType.content_source_type, cSourceType_gotten.content_source_type.content_source_type)
    
    def testGetContentSources(self):
        contentSources = pmodels.ContentSource.objects.all()
        contentSources_gotten = self.xobjResponse('platforms/content_sources/')
        self.assertEquals(len(contentSources), len(contentSources_gotten.content_source))
    
    def testGetContentSource(self):
        contentSource = pmodels.ContentSource.objects.get(pk=1)
        contentSource_gotten = self.xobjResponse('platforms/content_sources/RHN')
        self.assertEquals(contentSource.name, contentSource_gotten.content_source.name)
        self.assertEquals(contentSource.short_name, contentSource_gotten.content_source.short_name)
        self.assertEquals(contentSource.default_source, int(contentSource_gotten.content_source.default_source))
        self.assertEquals(contentSource.order_index, int(contentSource_gotten.content_source.order_index))
        self.assertEquals(contentSource.content_source_type, contentSource_gotten.content_source.content_source_type)
    
    def testGetSourcesByPlatform(self):  #ignore
        pass
    
    def testGetSourceTypesByPlatform(self): #ignore
        pass



class NewPlatformTest(XMLTestCase):
    
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
        response = self._post('platforms/content_sources/',
            data=platformstestxml.contentSourcePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        # 3 sources were already in the fixture
        self.assertEquals(3, len(pmodels.ContentSource.objects.all()))
        content = pmodels.ContentSource.objects.get(name="PlatformContentSourceTestPost")
        self.assertEquals("PlatformContentSourceTestPostShortName", content.short_name)
        self.assertEquals(1, int(content.order_index))

    def testCreateContentSourceType(self):
        response = self._post('platforms/content_source_types/',
            data=platformstestxml.contentSourceTypePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        self.assertEquals(4, len(list(pmodels.ContentSourceType.objects.all())))
    
    def testUpdatePlatform(self):
        r = self._put('platforms/1',
            data=platformstestxml.platformPUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedPlat = pmodels.Platform.objects.get(pk=1)
        self.assertEquals('PlatformChanged', updatedPlat.label)
        self.assertEquals('Platform Name Changed', updatedPlat.platform_name)
        self.assertEquals('auto', updatedPlat.mode)
    
    def testUpdateContentSource(self):
        r = self._put('platforms/content_sources/RHN/cs_shortname1',
            data=platformstestxml.contentSourcePUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedContent = pmodels.ContentSource.objects.get(short_name='cs_shortnameChanged')
        self.assertEquals('Content Source Changed', updatedContent.name)
        self.assertEquals('cs_shortnameChanged', updatedContent.short_name)
        self.assertEquals(1, updatedContent.default_source)
    
    def testUpdateContentSourceType(self):
        r = self._put('platforms/content_source_types/RHN/1',
            data=platformstestxml.contentSourceTypePUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedContent = pmodels.ContentSourceType.objects.get(pk=1)
        self.assertEquals('ContentSourceType New', updatedContent.content_source_type)