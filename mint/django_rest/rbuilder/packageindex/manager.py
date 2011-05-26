#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.packageindex import models

class PackageManager(basemanager.BaseManager):

    @exposed 
    def getPackages(self):
        packages = models.Packages()
        packages.package = models.Package.objects.all()
        return packages

    @exposed
    def getPackage(self, package_id):
        package = models.Package.objects.get(pk=package_id)
        return package

    @exposed
    def updatePackage(self, package):
        pass

    @exposed
    def addPackage(self, package):
        pass
