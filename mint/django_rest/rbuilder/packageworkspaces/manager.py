#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.packageworkspaces import models

exposed = basemanager.exposed

class PackageWorkspaceManager(basemanager.BaseManager):
    """docstring for PackageWorkspaceManager"""
    
    @exposed
    def getPackageWorkspaces(self):
        """docstring for getWorkspace"""
        PackageWorkspaces = models.PackageWorkspaces()
        PackageWorkspaces.package_workspace = list(models.PackageWorkspace.objects.all())
        return PackageWorkspaces
    
    @exposed
    def getPackageWorkspace(self, packageWorkspaceId):
        """docstring for PackageWorkspace"""
        packageWorkspace = models.PackageWorkspace.objects.get(pk=packageWorkspaceId)
        return packageWorkspace
        
    @exposed
    def addPackageWorkspace(self, packageWorkspace):
        """docstring for addWorkspace"""
        packageWorkspace.save()
        return packageWorkspace
        
    @exposed
    def updatePackageWorkspace(self, packageWorkspaceId, packageWorkspace):
        """docstring for updateWorkspace"""
        packageWorkspace.save()
        return packageWorkspace
    
    @exposed
    def deletePackageWorkspace(self, packageWorkspaceId):
        """docstring for deletePackageWorkspace"""
        packageWorkspace = models.PackageWorkspace.objects.get(
            pk=packageWorkspaceId)
        packageWorkspace.delete()
