#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

#
# A basic selenium wrapper and some test cases. Requires:
#
# selenium-remote-control=selenium.rpath.org@rpl:devel
# selenium-remote-control-python=selenium.rpath.org@rpl:devel
#
# Start the selenium-server before running this test suite:
#
#  /usr/sbin/selenium-server
#

import re
import testsuite
testsuite.setup()

from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
from seleniumharness import SeleniumHelper

from mint import buildtypes

class WebPageTest(SeleniumHelper):
    def createTestGroup(self, client, hostname = 'test', domainname = MINT_PROJECT_DOMAIN):
        self.setupProject(client, hostname, domainname)

        self.addComponent('testcase:source', '1.0.0', 'is: x86')
        self.addComponent('testcase:runtime', '1.0.0', 'is: x86')
        self.addCollection('testcase', '1.0.0', ['testcase:runtime'], defaultFlavor = 'is: x86')
        self.addComponent('group-test:source', '1.0.0')
        trv = self.addCollection('group-test', '1.0.0', ['testcase'], defaultFlavor = 'is: x86')

    def testCreateProject(self):
        client, userId = self.quickMintUser("foouser", "foopass")

        self.setOptIns("foouser")

        self.s.open(self.URL)
        self.s.type("username", "foouser")
        self.s.type("password", "foopass")
        self.clickAndWait("signInSubmit")

        self.failUnless("Edit my account" in self.s.get_body_text())

        self.clickAndWait("link=create a new project")
        self.s.type("hostname", "test")
        self.s.type("title", "Test Project")

        self.clickAndWait("newProject")
        self.failUnless("This is a fledgling project" in self.s.get_body_text())

    def testQueryParamsLogin(self):
        client, userId = self.quickMintUser("foouser", "foopass")

        self.setOptIns("foouser")

        projectId = self.newProject(client, hostname = 'test')
        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])
        build.setTrove("group-trove", "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")

        self.s.open(self.URL + "/project/test/build?id=%d" % build.id)
        self.failUnless(re.search(r'name="to" value=".*/project/test/build%3Fid%3D\d+"',
            self.s.get_html_source(), re.MULTILINE))

    def testGroupBuilder(self):
        client, userId = self.quickMintUser("foouser", "foopass")
        self.newProject(client, hostname = 'test')

        self.setOptIns("foouser")

        self.s.open(self.URL)
        self.s.type("username", "foouser")
        self.s.type("password", "foopass")
        self.clickAndWait("signInSubmit")

        self.failUnless("Edit my account" in self.s.get_body_text())

        self.createTestGroup(client)

        self.clickAndWait("link=Test Project")
        self.clickAndWait("link=Manage Builds")
        self.clickAndWait("link=Create a new build")

        # Create Build button should be disabled
        self.failUnless(not self.s.is_editable("submitButton"))

        # pick the available group
        self.clickAjax("link=group-test", "test.%s@rpl:devel" % MINT_PROJECT_DOMAIN)
        self.clickAjax("link=test.%s@rpl:devel" % MINT_PROJECT_DOMAIN, "1.0.0-1-1")
        self.clickAjax("link=1.0.0-1-1", "is: x86")
        self.clickAjax("flavorId0", "group-test=1.0.0-1-1 [is: x86]")

        # Create Build button should be enabled now
        self.failUnless(self.s.is_editable("submitButton"))

        # select stub image
        self.s.click("buildtype_%d_label" % buildtypes.STUB_IMAGE)
        self.clickAndWait("submitButton")

        self.failUnless("Build: Test Project" in self.s.get_body_text())


    def testDeleteMultipleBuilds(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, "Build 1")
        build.setDesc("Test build 1")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        build2 = client.newBuild(projectId, "Build 2")
        build2.setDesc("Test build 2")
        build2.setBuildType(buildtypes.STUB_IMAGE)
        build2.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build2.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        build3 = client.newBuild(projectId, "Build 3")
        build3.setDesc("Test build 3")
        build3.setBuildType(buildtypes.STUB_IMAGE)
        build3.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build3.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        release = client.newPublishedRelease(projectId)
        release.name = "Published Build"
        release.version = "0.1"
        release.addBuild(build2.id)
        release.save()

        self.setOptIns("foouser")

        self.s.open(self.URL)
        self.s.type("username", "foouser")
        self.s.type("password", "foopass")
        self.clickAndWait("signInSubmit")

        self.failUnless("Edit my account" in self.s.get_body_text())

        self.clickAndWait("link=Foo")
        self.clickAndWait("link=Manage Builds")

        self.failUnless("Build 1" in self.s.get_body_text())
        self.failUnless("Build 2" in self.s.get_body_text())
        self.failUnless("Build 3" in self.s.get_body_text())

        self.clickAndWait("deleteBuildsSubmit")

        self.failUnless("No builds specified" in self.s.get_body_text())

        self.s.check("name=buildIdsToDelete value=%d" % build.id)
        self.s.check("name=buildIdsToDelete value=%d" % build3.id)

        self.clickAndWait("deleteBuildsSubmit")

        self.failUnless("Are you sure" in self.s.get_body_text())
        self.failIf("part of a release" in self.s.get_body_text())

        self.clickAndWait("yes")

        self.failUnless("Builds deleted" in self.s.get_body_text())
        self.failIf("Build 1" in self.s.get_body_text())
        self.failUnless("Build 2" in self.s.get_body_text())
        self.failIf("Build 3" in self.s.get_body_text())

        self.s.check("name=buildIdsToDelete value=%d" % build2.id)

        self.clickAndWait("deleteBuildsSubmit")

        self.failUnless("Are you sure" in self.s.get_body_text())
        self.failUnless("part of a release" in self.s.get_body_text())

        self.clickAndWait("yes")

        self.failIf("Build 3" in self.s.get_body_text())
        self.failUnless("no builds" in self.s.get_body_text())

if __name__ == "__main__":
    testsuite.main()
