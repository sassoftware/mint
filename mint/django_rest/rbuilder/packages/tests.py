#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

from mint.django_rest.rbuilder.packages import manager
from mint.django_rest.rbuilder.packages import models
from mint.django_rest.rbuilder.packages import testsxml

class PackagesTestCase(XMLTestCase):
    fixtures = ['packages']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mgr = manager.PackageManager()

    def testAddPackage(self):
        # Create a new package
        response = self._post('/api/packages/',
            data=testsxml.package_post_xml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)

        # 3 packages were already in the fixture
        self.assertEquals(4, len(models.Package.objects.all()))
        package = models.Package.objects.get(name="conary")
        self.assertEquals("Conary Package Manager", package.description)


    def testAddPackageVersion(self):
        # create package version
        r = self._post('/api/packages/1/package_versions/',
            data=testsxml.package_version_post_xml,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)

        # 4 already in fixture
        self.assertEquals(5, len(models.PackageVersion.objects.all()))
        pv = models.PackageVersion.objects.get(pk=5)
        self.assertEquals('3.0', pv.name)
        self.assertEquals(True, pv.consumable)

        # now add an url
        r = self._post('/api/package_versions/5/urls/',
            data=testsxml.package_version_url_post_xml,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)
        self.assertEquals(1, len(pv.package_version_urls.all()))
        self.assertEquals("http://httpd.apache.org/download.cgi#apache30",
            pv.package_version_urls.all()[0].url)

        # add another url
        r = self._post('/api/package_versions/5/urls/',
            data=testsxml.package_version_url_post_xml2,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)
        self.assertEquals(2, len(pv.package_version_urls.all()))
        self.assertEquals("http://httpd.apache.org/download.cgi#apache31",
            pv.package_version_urls.all()[1].url)


    def testUpdatePackage(self):
        pass


    def testUpdatePackageVersion(self):
        pass

