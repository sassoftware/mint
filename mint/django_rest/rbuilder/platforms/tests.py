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

from mint.django_rest.rbuilder.platforms import models  # pyflakes=ignore
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
        pass
        
    def testGetPlatforms(self):
        pass
    
    def testGetImageTypeDefinitions(self):
        pass
        
    def testGetPlatformSourceStatus(self):
        pass
        
    def testGetContentSourceStatusNoData(self):
        pass
        
    def testGetContentSourceStatusData(self):
        pass
        
    def testFetSourceTypeStatus(self):
        pass
        
    def testGetSourceTypeStatusSMT(self):
        pass
        
    def testGetSourceDescriptor(self):
        pass
        
    def testGetSourceTypes(self):
        pass
        
    def testGetSourceType(self):
        pass
        
    def testGetSources(self):
        pass
        
    def testGetSource(self):
        pass
        
    def testGetSourcesByPlatform(self):
        pass
        
    def testGetSourceTypesByPlatform(self):
        pass
        
    def testUpdateSource(self):
        pass
        
    def testCreateSource(self):
        pass
        
    def testCreateSource2(self):
        pass
        
    def testUpdatePlatform(self):
        pass
        
    def testGetPlatformStatus(self):
        pass
        
    def testLoadPlatform(self):
        pass
        

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
        pass
        
    def testCreatePlatform_NoProduct(self):
        pass
        
    def testCreatePlatform_NoPlatform(self):
        pass
