import testsxml
#from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class ImagesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

    def testCanListAndAccessImages(self):

        # WARNING --
        # these are just stub tests until we can resolve what the unified
        # images table looks like.  We'll need real ones later that
        # inject items into the DB.

        # once rbac for images is implemented this should redirect to a queryset
        # for now, it's just a stub
        url = 'images/'
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.images_get_xml)
 
        # also a stub
        url = "images/1"
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_get_xml)

