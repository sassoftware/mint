#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, requires
from mint.django_rest.rbuilder import service

class XmlResourcesService(service.BaseService):

    @requires('xml_resource', save=False)
    @return_xml
    def rest_POST(self, request, xml_resource):
        return self.mgr.validateXmlResource(xml_resource)
