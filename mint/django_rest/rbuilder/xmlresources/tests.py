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
        xml_resource_data = xobj.parse(response.content).xml_resource
        xml_resource = models.XmlResource()
        xml_resource.schema = xml_resource_data.schema
        xml_resource.xml_data = xml_resource_data.xml_data
        xml_resource.error = xml_resource_data.error
        #self.assertEquals("test-project", project.name)
        #self.assertEquals(1, project.created_by.user_id)
        #self.assertEquals(1, project.modified_by.user_id)
        #self.assertTrue(project.created_date is not None)
        #self.assertTrue(project.modified_date is not None)
