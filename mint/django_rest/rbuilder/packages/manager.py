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


class PackageVersionService(object):
    
    @exposed
    def getPackageVersions(self, package_id):
        """docstring for getPackageVersions"""
        Packages = models.Packages.get(pk=package_id)
        Packages.package_version = list(models.PackageVersions.objects.all())
        return Packages


class PackagePackageVersionManager(basemanager.BaseManager):
    """docstring for PackageManager"""

    @exposed
    def getPackagePackageVersions(self):
        """docstring for getPackage"""
        PackageVersions = models.PackageVersions()
        PackageVersions.package = list(models.PackageVersion.objects.all())
        return PackageVersions

    @exposed
    def getPackagePackageVersion(self, package_version_id):
        """docstring for Package"""
        PackageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        return PackageVersion

    @exposed
    def addPackagePackageVersion(self, package_version):
        """docstring for addWorkspace"""
        package_version.save()
        return package_version

    @exposed
    def updatePackagePackageVersion(self, package_version_id, package_version):
        """docstring for updateWorkspace"""
        package_version.save()
        return package_version

    @exposed
    def deletePackagePackageVersion(self, package_version_id):
        """docstring for deletePackageWorkspace"""
        PackageVersion = models.PackageVersion.objects.get(
            pk=package_version_id)
        PackageVersion.delete()
