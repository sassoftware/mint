#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse, HttpResponseRedirect

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.rbac.rbacauth import rbac, manual_rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.xmlresources import models as xmlresources
from mint import userlevels
from mint.django_rest.rbuilder.modellib import Flags
import time

class XmlResourcesService(service.BaseService):

    @requires('xml_resource', save=False)
    @return_xml
    def rest_POST(self, request, xml_resource):
        return self.mgr.validateXmlResource(xml_resource)

