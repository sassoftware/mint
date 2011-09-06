import testsxml
#from xobj import xobj
#from mint.django_rest.rbuilder.images import models as imagemodels

# Suppress all non critical msg's from output
# still emits traceback for failed tests

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class ImagesDescriptorTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

    def testListImageDescriptors(self):
        response = self._get('images/image_definition_descriptors')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_descriptors_list_xml)
        
    #def testGetSpecificImageDescriptor(self):
    #    response = self._get('images/image_definition_descriptors/vmware')
    #    self.assertEquals(response.status_code, 200)
    #    self.assertXmlEquals(response.content, '<wrong></wrong>')


