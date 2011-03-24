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
        # self.mgr = manager.PackageManager()

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
        # 1 already in fixture
        pkg = models.Package.objects.get(pk=1)
        # change name from apache to Apache and change desciption
        # from Apache Web Server (httpd) to Apache Renamed
        r = self._put('/api/packages/1',
            data=testsxml.package_put_xml,
            username='admin', password='password')
        updatedPkg = models.Package.objects.get(pk=1)
        # Check that name and description are updated
        self.assertEquals('Apache', updatedPkg.name)
        self.assertEquals('Apache Renamed', updatedPkg.description)
        # Check that modified date has been incremented
        original_modified_date = pkg.modified_date
        new_modified_date = updatedPkg.modified_date
        self.assertTrue(new_modified_date > original_modified_date)

    def testUpdatePackageVersion(self):
        pv = models.PackageVersion.objects.get(pk=1)
        self.assertEquals(True, pv.consumable)
        # Change consumable from true to false and
        # change name from 3.0 to 3.1
        r = self._put('/api/package_versions/1',
                 data=testsxml.package_version_put_xml,
                 username="admin", password="password")   
        self.assertEquals(200, r.status_code)         
        updatedPV = models.PackageVersion.objects.get(pk=1)
        self.assertEquals(u'3.1', updatedPV.name)
        self.assertEquals(False, updatedPV.consumable)