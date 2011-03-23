#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml #, access, ACCESS

# from mint.django_rest.rbuilder.packageworkspaces import models

class PackageService(service.BaseService):
    """docstring for PackageService"""
    
    @return_xml
    def rest_GET(self, request, package_id=None):
        """docstring for rest_GET"""
        if package_id:
            return self.mgr.getPackage(package_id)
        else:
            return self.mgr.getPackage()
    
    # access.admin
    @requires('package')
    @return_xml
    def rest_POST(self, request, package):
        """docstring for rest_POST"""
        return self.mgr.addPackage(package)
    
    # @access.admin
    @requires('package')
    @return_xml
    def rest_PUT(self, request, package_id, package):
        """docstring for rest_PUT"""
        return self.mgr.updatePackage(package_id, package)
    
    # @access.admin   
    def rest_DELETE(self, request, package_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackagee(package_id)
        response = HttpResponse(status=204)
        return response

class PackageVersionService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_id=None):
        """docstring for rest_GET"""
        if package_workspace_id:
            return self.mgr.getPackage(package_id)
        else:
            return self.mgr.getPackage()
    
    # access.admin
    @requires('package')
    @return_xml
    def rest_POST(self, request, package):
        """docstring for rest_POST"""
        return self.mgr.addPackage(package)
    
    # @access.admin
    @requires('package')
    @return_xml
    def rest_PUT(self, request, package_id, package):
        """docstring for rest_PUT"""
        return self.mgr.updatePackage(package_id, package)
    
    # @access.admin   
    def rest_DELETE(self, request, package_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackage(package_id)
        response = HttpResponse(status=204)
        return response

