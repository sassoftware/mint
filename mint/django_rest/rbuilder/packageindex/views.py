#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, requires
from mint.django_rest.rbuilder import service

class BasePackageService(service.BaseService):
    pass

class PackageService(BasePackageService):

    @return_xml
    def rest_GET(self, request, package_id=None):
        return self.get(package_id)

    def get(self, package_id):
        if package_id:
            return self.mgr.getPackage(package_id)
        else:
            return self.mgr.getPackages()
        
    @requires('package')
    @return_xml
    def rest_POST(self, request, package):
        return self.mgr.addPackage(package)

    @requires('package')
    @return_xml
    def rest_PUT(self, request, package_id, package):
        return self.mgr.updatePackage(package)
