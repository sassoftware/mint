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


class PackageVersionService(service.BaseService):
    """docstring for PackagePackageVersionService"""
    
    @return_xml
    def rest_GET(self, request, package_version_id=None):
        """docstring for rest_GET"""
        if package_version_id:
            return self.mgr.getPackageVersion(package_version_id)
        else:
            return self.mgr.getAllPackageVersions()


class PackageVersionJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_version_job_id=None):
        """docstring for rest_GET"""
        if package_version_job_id:
            return self.mgr.getPackageVersionJob(package_version_job_id)
        else:
            return self.mgr.getPackageVersionJobs(package_version_id)


class PackageSourceService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id=None):
        """docstring for rest_GET"""
        if package_source_id:
            return self.mgr.getPackageSource(package_source_id)
        else:
            return self.mgr.getPackageSources(package_version_id)
        

class PackageSourceJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_source_job_id=None):
        """docstring for rest_GET"""
        if package_source_job_id:
            return self.mgr.getPackageSourceJob(package_source_job_id)
        else:
            return self.mgr.getPackageSourceJobs(package_version_id)


class PackageBuildService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_build_id=None):
        """docstring for rest_GET"""
        if package_build_id:
            return self.mgr.getPackageBuild(package_build_id)
        else:
            return self.mgr.getPackageBuilds(package_source_id)


class PackageBuildJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_build_id, package_build_job_id=None):
        """docstring for rest_GET"""
        if package_build_job_id:
            return self.mgr.getPackageBuildJob(package_build_job_id)
        else:
            return self.mgr.getPackageBuildJobs(package_build_id)


