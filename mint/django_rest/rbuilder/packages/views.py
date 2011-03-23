#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml #, access, ACCESS

class PackageService(service.BaseService):
    """docstring for PackageService"""
    
    @return_xml
    def rest_GET(self, request, package_id=None):
        """docstring for rest_GET"""
        if package_id:
            return self.mgr.getPackage(package_id)
        else:
            return self.mgr.getPackages()
    
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

class PackagePackageVersionService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_id=None, package_version_id=None):
        """docstring for rest_GET"""
        if package_id:
            return self.mgr.getPackagePackageVersion(package_id)
        else:
            return self.mgr.getPackagePackageVersions()
    
    # access.admin
    @requires('package_version')
    @return_xml
    def rest_POST(self, request, package_version):
        """docstring for rest_POST"""
        return self.mgr.addPackagePackageVersion(package_version)
    
    # @access.admin
    @requires('package_version')
    @return_xml
    def rest_PUT(self, request, package_id, package_version):
        """docstring for rest_PUT"""
        return self.mgr.updatePackagePackageVersion(package_id, package_version)
    
    # @access.admin   
    def rest_DELETE(self, request, package_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackagePackageVersion(package_id)
        response = HttpResponse(status=204)
        return response


class PackageVersionService(service.BaseService):
    """docstring for PackagePackageVersionService"""
    
    @return_xml
    def rest_GET(self, package_version_id=None):
        """docstring for rest_GET"""
        if package_version_id:
            return self.mgr.getPackageVersion(package_version_id)
        else:
            return self.mgr.getPackageVersions()