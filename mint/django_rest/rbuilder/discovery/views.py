#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django import http

from mint.django_rest.deco import return_xml, requires, access
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.discovery import models

class VersionsService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        api = models.Api()
        return api

class ApiVersionService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getApiVersionInfo()
