#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.xmlresources import models
from mint.django_rest.rbuilder.xmlresources import testsxml
from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.rbac.tests import RbacEngine

from xobj import xobj

class XmlResourcesTestCase(RbacEngine):

    def setUp(self):
        RbacEngine.setUp(self)
        self.mgr = rbuildermanager.RbuilderManager()
        self.mintConfig = self.mgr.cfg

        # invalidate the querysets so tags can be applied
  
    def testValidateXmlResource(self):

        response = self._post('xml_resources',
            data=testsxml.schema_and_data_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
    def testValidateXmlResourceInvalidXml1(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidxml1_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.error.code, u'70')
        
    def testValidateXmlResourceInvalidSchema1(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidschema1_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.error.code, u'70')
        
    def testValidateXmlResourceInvalidSchema2(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidschema2_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.error.code, u'70')
