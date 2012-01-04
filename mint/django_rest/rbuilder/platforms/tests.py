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

from mint.django_rest.rbuilder.platforms import models as platform_models
from mint.django_rest.rbuilder.projects import models as project_models
from mint.django_rest.rbuilder.images import models as imagemodels
from xobj import xobj
from lxml import etree
from mint.django_rest.rbuilder.platforms import platformstestxml as testsxml
import mint.buildtypes

from mint.django_rest.test_utils import XMLTestCase, SmartformMixIn

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
        platform = platform_models.Platform.objects.get(pk=1)
        self.assertEquals(platform.label, platform_gotten.label)
        self.assertEquals(platform.platform_name, platform_gotten.platform_name)
        self.assertEquals(platform.mode, platform_gotten.mode)
        self.assertEquals(platform.enabled, int(platform_gotten.enabled))
        # self.assertEquals(platform.configurable, platform_gotten.configurable)
        # self.assertEquals(platform.abstract, platform_gotten.abstract)
        self.assertEquals(platform.project.short_name, platform_gotten.project.short_name)
    
    def testGetPlatforms(self):
        platforms_gotten = self.xobjResponse('platforms/')
        # note that when we test getting Platforms, we are not
        # trying to retrieve a Platforms instance, but rather all
        # the platform instances that it contains
        platforms = platform_models.Platform.objects.order_by('platform_id')
        self.failUnlessEqual(
            [ x.platform_name for x in platforms_gotten.platform ],
            [ x.platform_name for x in platforms ])

    def testGetContentSourceTypes(self):
        cSourceTypes = platform_models.ContentSourceType.objects.all()
        cSourceTypes_gotten = self.xobjResponse('platforms/content_source_types/')
        self.assertEquals(len(list(cSourceTypes)), len(cSourceTypes_gotten.content_source_type))
    
    def testGetContentSourceType(self):
        cSourceType = platform_models.ContentSourceType.objects.get(pk=1)
        cSourceType_gotten = self.xobjResponse('platforms/content_source_types/ContentSourceType')
        self.assertEquals(cSourceType.content_source_type, cSourceType_gotten.content_source_type.content_source_type)
    
    def testGetContentSources(self):
        contentSources = platform_models.ContentSource.objects.all()
        contentSources_gotten = self.xobjResponse('platforms/content_sources/')
        self.assertEquals(len(contentSources), len(contentSources_gotten.content_source))
    
    def testGetContentSource(self):
        contentSource = platform_models.ContentSource.objects.get(pk=1)
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



class NewPlatformTest(XMLTestCase, SmartformMixIn):
    def setUp(self):
        XMLTestCase.setUp(self)
        self.setUpSchemaDir()
    
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
            data=testsxml.platformPOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        # 3 platforms were already in the fixture
        self.assertEquals(4, len(list(platform_models.Platform.objects.all())))
        platform = platform_models.Platform.objects.get(platform_name="Platform")
        self.assertEquals("Platform", platform.label)
    
    def testCreateContentSource(self):
        response = self._post('platforms/content_sources/',
            data=testsxml.contentSourcePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        # 3 sources were already in the fixture
        self.assertEquals(3, len(platform_models.ContentSource.objects.all()))
        content = platform_models.ContentSource.objects.get(name="PlatformContentSourceTestPost")
        self.assertEquals("PlatformContentSourceTestPostShortName", content.short_name)
        self.assertEquals(1, int(content.order_index))

    def testCreateContentSourceType(self):
        response = self._post('platforms/content_source_types/',
            data=testsxml.contentSourceTypePOSTXml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        self.assertEquals(4, len(list(platform_models.ContentSourceType.objects.all())))
    
    def testUpdatePlatform(self):
        r = self._put('platforms/1',
            data=testsxml.platformPUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedPlat = platform_models.Platform.objects.get(pk=1)
        self.assertEquals('PlatformChanged', updatedPlat.label)
        self.assertEquals('Platform Name Changed', updatedPlat.platform_name)
        self.assertEquals('auto', updatedPlat.mode)
    
    def testUpdateContentSource(self):
        r = self._put('platforms/content_sources/RHN/cs_shortname1',
            data=testsxml.contentSourcePUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedContent = platform_models.ContentSource.objects.get(short_name='cs_shortnameChanged')
        self.assertEquals('Content Source Changed', updatedContent.name)
        self.assertEquals('cs_shortnameChanged', updatedContent.short_name)
        self.assertEquals(1, updatedContent.default_source)
    
    def testUpdateContentSourceType(self):
        r = self._put('platforms/content_source_types/RHN/1',
            data=testsxml.contentSourceTypePUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedContent = platform_models.ContentSourceType.objects.get(pk=1)
        self.assertEquals('ContentSourceType New', updatedContent.content_source_type)

    def testCanGetImageTypeDefinitionDescriptor(self):

        # make sure we can load all the valid types
        for image_type in mint.buildtypes.xmlTagNameImageTypeMap.keys():
            # we do not have XML for netboot/live because they're deprecated
            # and deferred is special so we want to test differently
            if image_type in ['netbootImage', 'liveIsoImage', 'deferredImage']:
                continue
            # verify we can get the descriptor
            url = "platforms/image_type_definition_descriptors/%s" % image_type
            response = self._get(url) #, username='admin', password='password')
            self.assertEquals(response.status_code, 200)
            model = xobj.parse(response.content)
            self.failUnlessEqual(model.descriptor._xobj.tag, 'descriptor')

        # FIXME
        # we want to leave ITD's anonymous, but this is interesting... we're populating
        # the list of valid target base images here, which COULD contain some confidental
        # information.  If the type is deferred we may want to filter the list based
        # on request._authUser and what they can see, as we'll need to do in the
        # general collection / queryset as well.

        # insert some placeholder images for the test
        project = project_models.Project(
           name='blippy', hostname='blippy', short_name='blippy', 
           project_url='http://blippy.example.com', namespace='blippy'
        ).save()
        project = project_models.Project.objects.get(name='blippy') 

        output_trove = 'dummy-trove=/example.rpath.com@dummy:label/1.0-1-1'

        i1 = imagemodels.Image(
            project=project, name='alpha', output_trove=output_trove
        )
        i2 = imagemodels.Image(
            project=project, name='beta', output_trove=output_trove
        )
        i3 = imagemodels.Image(
            project=project, name='gamma', output_trove=None
        )

        def noop(*args, **kwargs):
            return None
            
        imagemodels.Image._computeMetadata = noop

        for x in [ i1, i2, i3 ]:
            # keep app from making call to repos service
            x.save()

        response = self._get('platforms/image_type_definition_descriptors/deferredImage')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.deferred_image_descriptor_xml)

        # an invalid one should 404
        response = self._get('platforms/image_type_definition_descriptors/doesNotExist')
        #    username='admin', password='password')
        self.assertEquals(response.status_code, 404)
         
    def testCanGetImageTypeDefinitionDescriptorWithNoImages(self):

        # make sure we can load all the valid types
        for image_type in mint.buildtypes.xmlTagNameImageTypeMap.keys():
            # we do not have XML for netboot/live because they're deprecated
            # and deferred is special so we want to test differently
            if image_type in ['netbootImage', 'liveIsoImage', 'deferredImage']:
                continue
            # verify we can get the descriptor
            url = "platforms/image_type_definition_descriptors/%s" % image_type
            response = self._get(url) #, username='admin', password='password')
            self.assertEquals(response.status_code, 200)
            model = xobj.parse(response.content)
            self.failUnlessEqual(model.descriptor._xobj.tag, 'descriptor')

        # FIXME
        # we want to leave ITD's anonymous, but this is interesting... we're populating
        # the list of valid target base images here, which COULD contain some confidental
        # information.  If the type is deferred we may want to filter the list based
        # on request._authUser and what they can see, as we'll need to do in the
        # general collection / queryset as well.

        # insert some placeholder images for the test
        project = project_models.Project(
           name='blippy', hostname='blippy', short_name='blippy', 
           project_url='http://blippy.example.com', namespace='blippy'
        ).save()
        project = project_models.Project.objects.get(name='blippy') 

        output_trove = 'dummy-trove=/example.rpath.com@dummy:label/1.0-1-1'

        def noop(*args, **kwargs):
            return None
            
        imagemodels.Image._computeMetadata = noop

        response = self._get('platforms/image_type_definition_descriptors/deferredImage')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, 
            testsxml.deferred_image_descriptor_no_base_images_xml)

        # an invalid one should 404
        response = self._get('platforms/image_type_definition_descriptors/doesNotExist')
        #    username='admin', password='password')
        self.assertEquals(response.status_code, 404)
        

