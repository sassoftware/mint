#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access

class PackagesService(service.BaseService):
    """docstring for PackageService"""
    
    @return_xml
    def rest_GET(self, request):
        """docstring for rest_GET"""
        return self.get()
    
    def get(self):
        return self.mgr.getPackages()

    # access.admin
    @requires('package')
    @return_xml
    def rest_POST(self, request, package):
        """docstring for rest_POST"""
        return self.mgr.addPackage(package)

class PackageService(service.BaseService):
    """docstring for PackageService"""
    
    @return_xml
    def rest_GET(self, request, package_id):
        """docstring for rest_GET"""
        return self.get(package_id)
    
    def get(self, package_id):
        return self.mgr.getPackage(package_id)
    
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

class PackageActionTypeService(service.BaseService):
    """docstring for PackageTypeService"""
    
    @return_xml
    def rest_GET(self, request, package_action_type_id=None):
        """docstring for rest_GET"""
        return self.get(package_action_type_id)
    
    def get(self, package_action_type_id):
        if package_action_type_id:
            return self.mgr.getPackageActionType(package_action_type_id)
        else:
            return self.mgr.getPackageActionTypes()


class PackagePackageVersionService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_id):
        """docstring for rest_GET"""
        return self.get(package_id)

    def get(self, package_id):
        return self.mgr.getPackagePackageVersions(package_id)

    # access.admin
    @requires('package_version')
    @return_xml
    def rest_POST(self, request, package_id, package_version):
        """docstring for rest_POST"""
        return self.mgr.addPackageVersion(package_id, package_version)

    # @access.admin
    @requires('package_version')
    @return_xml
    def rest_PUT(self, request, package_id, package_version):
        """docstring for rest_PUT"""
        return self.mgr.updatePackageVersion(package_id, package_version)

    # @access.admin
    def rest_DELETE(self, request, package_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackageVersion(package_id)
        response = HttpResponse(status=204)
        return response

class PackageVersionService(service.BaseService):
    """docstring for PackagePackageVersionService"""
    
    @return_xml
    def rest_GET(self, request, package_version_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id)

    def get(self, package_version_id):
        if package_version_id:
            return self.mgr.getPackageVersion(package_version_id)
        else:
            return self.mgr.getAllPackageVersions()

    @requires('package_version')
    @return_xml
    def rest_PUT(self, request, package_version_id, package_version):
        """docstring for rest_PUT"""
        return self.mgr.updatePackageVersion(package_version_id, package_version)

class PackageVersionActionService(service.BaseService):
    """docstring for PackagePackageVersionService"""
    
    @return_xml
    def rest_GET(self, request, package_version_id, package_version_action_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_version_action_id)

    def get(self, package_version_id, package_version_action_id):
        if package_version_action_id:
            return self.mgr.getPackageVersionAction(package_version_action_id)
        else:
            return self.mgr.getPackageVersionActions(package_version_id)

    @requires('package_version_action', save=False)
    @return_xml
    def rest_PUT(self, request, package_version_id, package_version_action_id,
                 package_version_action):
        """docstring for rest_PUT"""
        return self.mgr.updatePackageVersionAction(package_version_id,
            package_version_action)

class PackageVersionUrlService(service.BaseService):
    """docstring for PackageUrlVersionService"""
    
    @return_xml
    def rest_GET(self, request, package_version_id, package_version_url_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_version_url_id)

    def get(self, package_version_id, package_version_url_id):
        if package_version_url_id:
            return self.mgr.getPackageVersionUrl(package_version_id,
                package_version_url_id)
        else:
            return self.mgr.getPackageVersionUrls(package_version_id)

    @requires("package_version_url")
    @return_xml
    def rest_POST(self, request, package_version_id, package_version_url):
        return self.mgr.addPackageVersionUrl(package_version_id,
            package_version_url)

    @access.anonymous
    @requires("package_version_urls")
    @return_xml
    def rest_PUT(self, request, package_version_id, package_version_urls):
        return self.mgr.updatePackageVersionUrls(package_version_id,
            package_version_urls)

class PackageVersionJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_version_job_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_version_job_id)

    def get(self, package_version_id, package_version_job_id):
        if package_version_job_id:
            return self.mgr.getPackageVersionJob(package_version_job_id)
        else:
            return self.mgr.getPackageVersionJobs(package_version_id)

    @requires("package_version_job")
    @return_xml
    def rest_POST(self, request, package_version_id, package_version_job):
        return self.mgr.addPackageVersionJob(package_version_id,
            package_version_job)
        


class PackageSourceService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_source_id)

    def get(self, package_version_id, package_source_id):
        if package_source_id:
            return self.mgr.getPackageSource(package_source_id)
        else:
            return self.mgr.getPackageSources(package_version_id)

    @access.anonymous
    @requires("package_source", save=False)
    @return_xml
    def rest_POST(self, request, package_version_id, package_source):
        return self.mgr.addPackageSource(package_version_id, package_source)

    @access.anonymous
    @requires("package_sources", save=False)
    @return_xml
    def rest_PUT(self, request, package_version_id, package_sources):
        return self.mgr.updatePackageSources(package_version_id,
            package_sources)


class PackageSourceJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_source_job_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_source_id,
            package_source_job_id)

    def get(self, package_version_id, package_source_id,
            package_source_job_id):
        if package_source_job_id:
            return self.mgr.getPackageSourceJob(package_source_job_id)
        else:
            return self.mgr.getPackageSourceJobs(package_version_id)

    @requires("package_source_job")
    @return_xml
    def rest_POST(self, request, package_version_id, package_source_id,
                  package_source_job):
        return self.mgr.addPackageSourceJob(package_source_id,
            package_source_job)

class PackageBuildService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_build_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_source_id,
            package_build_id)

    def get(self, package_version_id, package_source_id, package_build_id):
        if package_build_id:
            return self.mgr.getPackageBuild(package_build_id)
        else:
            return self.mgr.getPackageBuilds(package_source_id)


class PackageBuildJobService(service.BaseService):

    @return_xml
    def rest_GET(self, request, package_version_id, package_source_id,
        package_build_id, package_build_job_id=None):
        """docstring for rest_GET"""
        return self.get(package_version_id, package_source_id,
            package_build_id, package_build_job_id)

    def get(self, package_version_id, package_source_id,
        package_build_id, package_build_job_id):
        if package_build_job_id:
            return self.mgr.getPackageBuildJob(package_build_job_id)
        else:
            return self.mgr.getPackageBuildJobs(package_build_id)


