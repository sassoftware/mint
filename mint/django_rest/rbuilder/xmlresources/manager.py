#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import logging

from lxml import etree
import traceback

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.xmlresources import models


log = logging.getLogger(__name__)


class XmlResourceManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)

    @exposed
    def validateXmlResource(self, xml_resource):
        # validate stuff
        xml_resource.error = models.XmlResourceError()
        success, error_code, error_msg, error_details = self._validateXmlResource(xml_resource)
        xml_resource.error.code = error_code
        xml_resource.error.message = error_msg
        xml_resource.error.details = error_details

        return xml_resource
    
    def _validateXmlResource(self, xml_resource):
        
        try:
            if xml_resource.schema:
                #TODO: validate the schema
                schemaxml = etree.fromstring(str(xml_resource.schema))
                xmlschema = etree.XMLSchema(schemaxml)
                if xml_resource.xml_data:
                    xmldata = etree.fromstring(str(xml_resource.xml_data))
                    xmlschema.assertValid(xmldata)
                    return True, 0, None, None
        except (etree.DocumentInvalid, etree.XMLSyntaxError), ex:
            msg = "%s\n"  % str(ex.error_log)
            tb = traceback.format_exc()
            return False, 70, msg, tb
