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
        """docstring for addWorkspace"""
        package.save()
        return package
        
    @exposed
    def updatePackage(self, package_id, package):
        """docstring for updateWorkspace"""
        package.save()
        return package
    
    @exposed
    def deletePackage(self, package_id):
        """docstring for deletePackageWorkspace"""
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
    def addPackageVersion(self, package_version):
        """docstring for addPackageVersion"""
        package_version.save()
        
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
        return packageSources

    @exposed
    def getPackageSource(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        return packageSource
