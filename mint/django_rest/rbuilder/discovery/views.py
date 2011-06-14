#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, access
from mint.django_rest.rbuilder import service

class VersionsService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getApi()

class ApiVersionService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getApiVersionInfo()
