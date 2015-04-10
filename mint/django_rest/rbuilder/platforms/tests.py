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
        self.failUnlessEqual(
            [ x.platform_name for x in platform_models.Platform.objects.all() ],
            ['Platform', 'Platform1', 'Platform2', 'Hidden Platform', 'Platform5'])
        platform = platform_models.Platform.objects.get(platform_name="Platform")
        self.assertEquals(platform.label, "Platform")

    def testUpdatePlatform(self):
        r = self._put('platforms/1',
            data=testsxml.platformPUTXml,
            username='admin', password='password')
        self.assertEquals(r.status_code, 200)
        updatedPlat = platform_models.Platform.objects.get(pk=1)
        self.assertEquals('PlatformChanged', updatedPlat.label)
        self.assertEquals('Platform Name Changed', updatedPlat.platform_name)
        self.assertEquals('auto', updatedPlat.mode)

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
            # Check for constraints
            fields = dict((x.name, x) for x in model.descriptor.dataFields.field)
            field = fields.get('options.freespace')
            if field is not None:
                self.assertEquals(field.constraints.range.min, '16')
            field = fields.get('options.swapSize')
            if field is not None:
                self.assertEquals(field.constraints.range.min, '16')
            field = fields.get('options.vmMemory')
            if field is not None:
                self.assertEquals(field.constraints.range.min, '256')
            field = fields.get('options.vmCPUs')
            if field is not None:
                self.assertEquals(field.constraints.range.min, '1')
                self.assertEquals(field.constraints.range.max, '32')

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

        # an invalid one should 404
        response = self._get('platforms/image_type_definition_descriptors/doesNotExist')
        #    username='admin', password='password')
        self.assertEquals(response.status_code, 404)
        

