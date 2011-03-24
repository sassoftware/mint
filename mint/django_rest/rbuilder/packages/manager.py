#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.packages import models

exposed = basemanager.exposed

class PackageManager(basemanager.BaseManager):
    """docstring for PackageManager"""
    
    @exposed
    def getPackages(self):
        """docstring for getPackage"""
        Packages = models.Packages()
        Packages.package = list(models.Package.objects.all())
        return Packages
    
    @exposed
    def getPackage(self, package_id):
        """docstring for Package"""
        package = models.Package.objects.get(pk=package_id)
        return package
        
    @exposed
    def addPackage(self, package):
        """docstring for addPackage"""
        package.save()
        return package
        
    @exposed
    def updatePackage(self, package_id, package):
        """docstring for updatePackage"""
        package.save()
        return package
    
    @exposed
    def deletePackage(self, package_id):
        """docstring for deletePackage"""
        package = models.Package.objects.get(
            pk=package_id)
        package.delete()

    def downloadPackageVersionUrl(self, packageVersionUrl):
        pass

    def buildPackageSource(self, packageSource):
        pass

    def promotePackageSource(self, packageSource):
        pass

    def commitPackageVersion(self, packageVersion):
        pass

    def promotePackageBuild(self, packageBuild):
        pass


class PackageVersionManager(basemanager.BaseManager):
    
    @exposed
    def getAllPackageVersions(self):
        packageVersions = models.AllPackageVersions()
        packageVersions.package_version = list(models.PackageVersion.objects.all())
        return packageVersions

    @exposed
    def getPackagePackageVersions(self, package_id):
        """docstring for getPackageVersions"""
        package = models.Package.objects.get(pk=package_id)
        packageVersions = models.PackageVersions()
        packageVersions.package_version = list(
            models.PackageVersion.objects.filter(package=package))
        packageVersions._parents = [package]
        return packageVersions

    @exposed
    def getPackageVersions(self, package_id):
        pass

    @exposed
    def getPackageVersion(self, package_version_id):
        """docstring for getPackageVersion"""
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        return packageVersion

    @exposed
    def getPackageVersionJobs(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageVersionJobs = models.PackageVersionJobs()
        packageVersionJobs.package_version_job = list(
            models.PackageVersionJob.objects.filter(package_version=packageVersion))
        packageVersionJobs._parents = [packageVersion]
        return packageVersionJobs

    @exposed
    def getPackageVersionJob(self, package_version_job_id):
        packageVersionJob = models.PackageVersionJob.objects.get(
            pk=package_version_job_id)
        return packageVersionJob

    @exposed
    def addPackageVersion(self, package_id, package_version):
        """docstring for addPackageVersion"""
        package = models.Package.objects.get(pk=package_id)
        package_version.package = package
        package_version.save()
        return package_version
        
    @exposed
    def updatePackageVersion(self, package_version_id, package_version):
        """docstring for updatePackageVersion"""
        package_version.save()
        
    @exposed
    def deletePackageVersion(self, package_version_id):
        """docstring for deletePackageVersion"""
        packageversion = models.PackageVersion.objects.get(
            pk=package_version_id)
        packageversion.delete()

    @exposed
    def getPackageSources(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageSources = models.PackageSources()
        packageSources.package_source = list(
            models.PackageSource.objects.filter(package_version=packageVersion))
        packageSources._parents = [packageVersion]
        return packageSources

    @exposed
    def getPackageSource(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        return packageSource

    @exposed
    def getPackageSourceJobs(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        packageSourceJobs = models.PackageSourceJobs()
        packageSourceJobs.package_source_job = list(
            models.PackageSourceJob.objects.filter(package_source=packageSource))
        packageSourceJobs._parents = [packageSource]
        return packageSourceJobs

    @exposed
    def getPackageSourceJob(self, package_source_job_id):
        packageSourceJob = models.PackageSourceJob.objects.get(
            pk=package_source_job_id)
        return packageSourceJob

    @exposed
    def getPackageBuilds(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        packageBuilds = models.PackageBuilds()
        packageBuilds.package_build = list(
            models.PackageBuild.objects.filter(package_source=packageSource))
        packageBuilds._parents = [packageSource]
        return packageBuilds

    @exposed
    def getPackageBuild(self, package_build_id):
        packageBuild = models.PackageBuild.objects.get(pk=package_build_id)
        return packageBuild

    @exposed
    def getPackageBuildJobs(self, package_build_id):
        packageBuild = models.PackageBuild.objects.get(pk=package_build_id)
        packageBuildJobs = models.PackageBuildJobs()
        packageBuildJobs.package_build_job = list(
            models.PackageBuildJob.objects.filter(package_build=packageBuild))
        packageBuildJobs._parents = [packageBuild]
        return packageBuildJobs

    @exposed
    def getPackageBuildJob(self, package_build_job_id):
        packageBuildJob = models.PackageBuildJob.objects.get(
            pk=package_build_job_id) 
        return packageBuildJob
