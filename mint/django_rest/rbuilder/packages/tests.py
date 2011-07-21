#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

# from mint.django_rest.rbuilder.packages import manager
from mint.django_rest.rbuilder.packages import models
from mint.django_rest.rbuilder.packages import testsxml
from mint.rmake3_package_creator import client 
from mint.lib import data as mintdata

from lxml import etree
from xobj import xobj
from testutils import mock

# urls.py comments out the entry points into the code, so we disable these tests
#class PackagesTestCase(XMLTestCase):
class PackagesTestCase(object):
    fixtures = ['packages']

    def setUp(self):
        XMLTestCase.setUp(self)
        mock.mock(client.Client, "pc_packageSourceCommit")

    def tearDown(self):
        mock.unmockAll()
        XMLTestCase.tearDown(self)

    def xobjResponse(self, url):
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        root_name = etree.XML(response.content).tag
        return getattr(xobjModel, root_name)

    def testAddPackage(self):
        # Create a new package
        response = self._post('packages/',
            data=testsxml.package_post_xml,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)

        # 3 packages were already in the fixture
        self.assertEquals(4, len(models.Package.objects.all()))
        package = models.Package.objects.get(name="conary")
        self.assertEquals("Conary Package Manager", package.description)

    def testAddPackageVersion(self):
        # create package version
        r = self._post('packages/1/package_versions/',
            data=testsxml.package_version_post_xml,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)

        # 4 already in fixture
        self.assertEquals(7, len(models.PackageVersion.objects.all()))
        pv = models.PackageVersion.objects.get(pk=5)
        self.assertEquals('3.0', pv.name)
        self.assertEquals(True, pv.consumable)

        # now add an url
        r = self._post('package_versions/5/urls/',
            data=testsxml.package_version_url_post_xml,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)
        self.assertEquals(4, len(pv.package_version_urls.all()))
        self.assertEquals("http://httpd.apache.org/download.cgi#apache30",
            pv.package_version_urls.all()[3].url)

        # add another url
        r = self._post('package_versions/5/urls/',
            data=testsxml.package_version_url_post_xml2,
            username="admin", password="password")
        self.assertEquals(200, r.status_code)
        self.assertEquals(5, len(pv.package_version_urls.all()))
        self.assertEquals("http://httpd.apache.org/download.cgi#apache31",
            pv.package_version_urls.all()[4].url)

    def testUpdatePackage(self):
        # 1 already in fixture
        pkg = models.Package.objects.get(pk=1)
        # change name from apache to Apache and change desciption
        # from Apache Web Server (httpd) to Apache Renamed
        r = self._put('packages/1',
            data=testsxml.package_put_xml,
            username='admin', password='password')
        self.failUnlessEqual(r.status_code, 200)
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
        r = self._put('package_versions/1',
                 data=testsxml.package_version_put_xml,
                 username="admin", password="password")
        self.assertEquals(200, r.status_code)         
        updatedPV = models.PackageVersion.objects.get(pk=1)
        self.assertEquals(u'3.1', updatedPV.name)
        self.assertEquals(False, updatedPV.consumable)
        
    def testGetPackage(self):
        pkg = models.Package.objects.get(pk=1)
        pkg_gotten = self.xobjResponse('packages/1')
        # p.package_id returns an int so cast to unicode string
        self.assertEquals(unicode(pkg.package_id), pkg_gotten.package_id)
        self.assertEquals(pkg.name, pkg_gotten.name)
        self.assertEquals(pkg.description, pkg_gotten.description)
        
    def testGetPackages(self):
        pkgs = models.Packages.objects.all()
        pkgs_gotten = self.xobjResponse('packages/')
        self.assertEquals(len(list(pkgs)), len(pkgs_gotten))
    
    def testGetPackageVersion(self):
        pv = models.PackageVersion.objects.get(pk=1)
        pv_gotten = self.xobjResponse('package_versions/1')
        self.assertEquals(unicode(pv.package_version_id), pv_gotten.package_version_id)
        self.assertEquals(pv.name, pv_gotten.name)
        self.assertEquals(pv.description, pv_gotten.description)
        self.assertEquals(pv.license, pv_gotten.license)
        # if don't cast to unicode then True != u'true' and False != u'false'
        self.assertEquals(unicode(pv.consumable).lower(), pv_gotten.consumable)
        self.assertEquals(unicode(pv.committed).lower(), pv_gotten.committed)
        # FIXME pv.package_name is returning None when I *know* its not None
        # self.assertEquals(pv.package_name, pv_gotten.package_name)
      
    def testGetPackageVersions(self):
        pvs = models.PackageVersions.objects.all()
        pvs_gotten = self.xobjResponse('package_versions/')
        self.assertEquals(len(list(pvs)), len(pvs_gotten))
        
    def testGetPackageUrl(self):
        pUrl = models.PackageVersionUrl.objects.get(pk=1)
        pUrl_gotten = self.xobjResponse('package_versions/1/urls/1')
        self.assertEquals(pUrl.url, pUrl_gotten.url)
        
    def testGetPackageUrls(self):
        pUrls = models.PackageVersionUrls.objects.all()
        pUrls_gotten = self.xobjResponse('package_versions/1/urls/')
        self.assertEquals(len(list(pUrls)), len(pUrls_gotten))
    

    def testCommitPackageVersion(self):
        client.Client.pc_packageSourceCommit._mock.setDefaultReturn(
            ("testjobuuid", None))
        response = self._post('package_versions/6/package_version_jobs',
            data=testsxml.package_version_commit_job_post_xml,
            username='admin', password='password')
        self.assertEquals(200, response.status_code)         
        packageVersion = models.PackageVersion.objects.get(pk=6)

        # job was created
        self.assertEquals(1, len(packageVersion.jobs.all()))
        job = packageVersion.jobs.all()[0]
        self.assertEquals("testjobuuid", job.job.job_uuid)

        unMarshalledJobData = mintdata.unmarshalGenericData(job.job_data)
        self.assertEquals('testlabel.eng.rpath.com@rpath:test-1-devel',
            unMarshalledJobData['commit_label'])

        # Now GET the job and verify it
        response = self._get(
            'package_versions/6/package_version_jobs/%s' % \
            job.package_version_job_id,
            username="admin", password="password")
        self.assertEquals(200, response.status_code)
        job = xobj.parse(response.content).package_version_job
        self.assertEquals("testlabel.eng.rpath.com@rpath:test-1-devel",
            job.job_data.commit_label)
        self.assertEquals("admin", job.created_by)
        self.assertEquals("admin", job.modified_by)
        self.assertEquals("Commit package version",
            job.package_action_type)

    # complete crap, doesn't work...FIXME or take it out
    def generateGETTests(self, model, url, pk=1, ignore=None):
        """
        Automatically calls self.assertEquals(api_value, db_value)
        for each field on a model not in ignore=['ignored fields'] 
        """
        if not ignore:
            ignore = []
        from_api = self.xobjResponse(url)
        from_db = model.objects.get(pk=pk)
        fields = from_api._xobj.elements
        for field in fields:
            if field not in ignore:
                from_db_field_value = getattr(from_db, field, None)
                from_api_field_value = getattr(from_api, field, None)
                if not from_api_field_value or not from_db_field_value:
                    raise AssertionError('Field values == None')
                self.assertEquals(from_db_field_value, from_api_field_value)
            else:
                continue
