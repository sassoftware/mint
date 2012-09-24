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
        
        success = False
        status_code = None
        status_msg = None
        status_details = None
        try:
            success, status_code, status_msg, status_details = self._validateXmlResource(xml_resource)
        except Exception, e:
            code = hasattr(e, "errno") and e.errno or 500
            success, status_code, status_msg, status_details = self._processValidationException(code, e, traceback.format_exc())

        # add the status node
        xml_resource.status = self._buildStatusNode(success, status_code, status_msg, status_details)

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
        except (etree.DocumentInvalid, etree.XMLSyntaxError), e:
            return self._processValidationException(70, e, traceback.format_exc())
        
    def _processValidationException(self, code, exception, tb):
        
        msg = None;
        if hasattr(exception, "error_log"):
            msg = "%s\n"  % str(exception.error_log)
        else:
            msg = "Unknown error while validating XML"
        
        if "References from this schema to components in no namespace are not allowed, since not indicated by an import statement" in msg:
            # details will contain the original info, make this a better message
            tb = "%s : %s" % (msg, tb)
            msg = "Invalid XML: Make sure the XML is properly wrapped as CDATA"
        
        return False, code, msg, tb
    
    def _buildStatusNode(self, success, code, message, details):
        status_node = models.XmlResourceStatus()
        status_node.success = success
        status_node.code = code
        status_node.message = message
        status_node.details = details
        
        return status_node
