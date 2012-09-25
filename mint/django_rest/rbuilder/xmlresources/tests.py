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
  
    def testValidateXmlResourceValidXml1(self):

        response = self._post('xml_resources',
            data=testsxml.schema_and_data_validxml1_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.success, u'True')
        
    def testValidateXmlResourceValidXml2(self):

        response = self._post('xml_resources',
            data=testsxml.schema_and_data_validxml2_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.success, u'True')
        
    def testValidateXmlResourceValidXml3(self):

        response = self._post('xml_resources',
            data=testsxml.schema_and_data_validxml3_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, '0')
        self.assertEquals(xml_resource_data.status.success, 'True')
        
    def testValidateXmlResourceInvalidXml1(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidxml1_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, u'70')
        self.assertEquals(xml_resource_data.status.success, u'False')
        
    def testValidateXmlResourceInvalidXml2(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidxml2_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, u'22')
        self.assertEquals(xml_resource_data.status.message, u'Invalid (empty) xml_resource node')
        self.assertEquals(xml_resource_data.status.success, u'False')
        
    def testValidateXmlResourceInvalidSchema1(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidschema1_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, u'70')
        self.assertEquals(xml_resource_data.status.success, u'False')
        
    def testValidateXmlResourceInvalidSchema2(self):
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_invalidschema2_xml,
            username="admin", password="password")
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, u'70')
        self.assertEquals(xml_resource_data.status.success, u'False')

    def testValidateXmlResourceCallHangs(self):
        # The presence of targetNamespace without a default namespace or a
        # qualified reference to the type with a namespace prefix
        # breaks schema validation for lxml
        # (see http://www.xfront.com/DefaultNamespace.pdf)
        response = self._post('xml_resources',
            data=testsxml.schema_and_data_hanging_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        xml_resource_data = xobj.parse(response.content).xml_resource
        self.assertEquals(xml_resource_data.status.code, '70')
        self.assertEquals(xml_resource_data.status.success, 'False')
        self.assertIn(
            'References from this schema to components in no namespace are not allowed, since not indicated by an import statement.',
            xml_resource_data.status.message)
