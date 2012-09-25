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
        status_errors = []
        status_details = None
        try:
            success, status_code, status_errors, status_details = self._validateXmlResource(xml_resource)
        except Exception, e:
            code = hasattr(e, "errno") and e.errno or 500
            success, status_code, status_errors, status_details = self._processValidationResult(False, code, e, traceback.format_exc())

        # add the status node
        xml_resource.status = self._buildStatusNode(success, status_code, status_errors, status_details)

        return xml_resource
    
    def _validateXmlResource(self, xml_resource):

        hasSchema = xml_resource.schema != None
        hasXml = xml_resource.xml != None
        
        if not hasSchema and not hasXml:
            return self._processValidationResult(False, 22, None, None, "Invalid (empty) xml_resource node")
        
        try:
            schemaXml = None
            
            if hasSchema:
                # parse schema
                schemaElement = etree.fromstring(xml_resource.schema.encode("utf-8"))
                schemaXml = etree.XMLSchema(schemaElement)
                
            if hasXml:
                # parse xml
                xmlDoc = etree.fromstring(xml_resource.xml.encode("utf-8"))
                
            if hasSchema and hasXml:
                # validate the xml against the schema
                schemaXml.assertValid(xmlDoc)
                return self._processValidationResult(True, 0, None, None)
        except etree.Error, e:
            return self._processValidationResult(False, 70, e, traceback.format_exc())
        
    def _processValidationResult(self, success, code, exception, tb, message=None):
        
        errors = []
        
        if not success:
            if message:
                errors.append(models.XmlResourceStatusError(message))
            else:
                errors = self._processEtreeException(exception)
            
        return success, code, errors, tb
    
    def _processEtreeException(self, exception):
        errors = []
        if hasattr(exception, "error_log"):
            for e in exception.error_log:
                err = models.XmlResourceStatusError(e.message, e.column, e.domain, 
                    e.domain_name, e.filename, e.level, e.level_name, e.line, 
                    e.type, e.type_name)
                errors.append(err)
        else:
            err = models.XmlResourceStatusError("Unknown error while validating XML")
            errors.append(err)
            
        return errors

    def _buildStatusNode(self, success, code, errors, details):
        status_node = models.XmlResourceStatus()
        status_node.success = success
        status_node.code = code
        for e in errors:
            status_node.errors.error.append(e)
        status_node.details = details
        
        return status_node
