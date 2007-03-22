#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import os
import shutil
import testsuite
testsuite.setup()

import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN

from repostest import testRecipe
from conary import versions
from conary.conaryclient import ConaryClient

testDirRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"

    def setup(r):
        r.Create("/temp/foo")
        r.MakeDirs("/temp/directory", mode = 0775)
"""

testTransientRecipe1=r"""\
class TransientRecipe1(PackageRecipe):
    name = 'testcase'
    version = '1.0'
    clearBuildReqs()
    fileText = 'bar\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""
testTransientRecipe2=r"""\
class TransientRecipe2(PackageRecipe):
    name = 'testcase'
    version = '1.1'
    clearBuildReqs()
    fileText = 'blah\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""


class WebReposTest(mint_rephelp.WebRepositoryHelper):
    def testRepositoryBrowser(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        # first try anonymous browsing
        page = self.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())

        # now try logged-in
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())

        # now try logged-in, as another user user
        page = page.fetchWithRedirect('/logout')
        client, userId = self.quickMintUser('test2', 'test2pass')
        page = self.webLogin('test2', 'test2pass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())

    def testBrowseTooltips(self):
        raise testsuite.SkipTestException("Not ready for primetime -- yet")
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        page = self.assertContent('/repos/testproject/browse', code = [200],
            content = '1 trove',
            server = self.getProjectServerHostname())

    def testBrowseHiddenProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')
        project = client.getProject(projectId)

        adminClient.hideProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        # anonymous user should see a 404
        page = self.assertCode('/repos/test/browse', code = 404,
                server = self.getProjectServerHostname())

        # logged-in user should see the browser
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/test/browse', code = [200],
                content = 'troveInfo?t=test',
                server = self.getProjectServerHostname())

    def testBrowseExternalProject(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        self.openRepository(1)
        extProjectId = client.newExternalProject("External Project",
            "external", MINT_PROJECT_DOMAIN, "localhost1@rpl:devel",
            'http://localhost:%d/conary/' % self.servers.getServer(1).port, False)

        self.makeSourceTrove("testcase", testRecipe, buildLabel = versions.Label('localhost1@rpl:devel'))
        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

        # log in and make sure we see the same thing
        page = self.webLogin('testuser', 'testpass')
        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

    def testTroveInfoPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        # test that missing troves are a 404 not found error
        page = self.fetchWithRedirect('/repos/foo/troveInfo?t=group-foo',
                                      code = [404])

        self.addQuickTestComponent('test:runtime', '3.0-1-1', filePrimer = 3)

        # test that trove info page renders without error
        page = self.assertContent('/repos/testproject/troveInfo?t=test:runtime',
                                  content = "Information for component",
                                  server = self.getProjectServerHostname())

    def testReposRSS(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        page = self.fetchWithRedirect('/repos/testproject/browse')

        self.failIf('/repos/testproject/rss' in page.body,
                    "Malformed base path for rss feed on repos page")

    def testFileListDirectories(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject')
        project = client.getProject(projectId)

        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])

        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/repos/testproject/troveInfo?t=test:runtime')
        fileLink = [x for x in page.getDOM().getByName('a') if x and x[0] == "Show Contents"][0]

        page = self.assertContent('/repos/testproject/' + \
                fileLink.getattr('href'), code = [200],
                content = 'getFile?path=contents0')

    def testDisallowedMethod(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        self.assertCode('/repos/testproject/log', code = 404)

    def testRepoBrowserPermission(self):
        raise testsuite.SkipTestException('Test is not unittest safe')
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # delete anon access
        nc.deleteAccessGroup(self.cfg.buildLabel, 'anonymous')

        try:
            # check that we get a 403
            self.fetch('/repos/testproject/browse', ok_codes = [403])
        finally:
            # re-add acl. this shouldn't need to be done but seems
            # to be necessary for other unit tests.
            nc.addAccessGroup(self.cfg.buildLabel, 'anonymous')
            nc.addAcl(self.cfg.buildLabel, 'anonymous', '', '',
                      False, False, False)
            nc.changePassword(self.cfg.buildLabel, 'anonymous', 'anonymous')

    def testReposAccessViaStandardPath(self):
        raise testsuite.SkipTestException("Conary's web interface is currently broken with tip conary")
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client, "testproject")

        project = client.getProject(projectId)

        projectFQDN = self.getProjectHostname("testproject")

        # Note this test REQUIRES you to have the following hostnames in
        # your /etc/hosts:
        #
        # 127.0.0.1 testproject.rpath.local
        # 127.0.0.1 testproject.rpath.local2
        #
        # This check will skip the test if it can't resolve the hostname
        try:
            from socket import gethostbyname
            gethostbyname(projectFQDN)
        except:
            raise testsuite.SkipTestException("add %s to your /etc/hosts" % \
                    projectFQDN)

        self.setServer(projectFQDN, self.port)

        # fetch from both URLs, one with and one without the trailing slash
        # both should redirect
        self.assertCode('/conary', code = 301)
        self.assertCode('/conary/', code = 301)

    def testReferencesAndDescendants(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client, "testproject")

        v1 = "/testproject.%s@rpl:linux/1.0-1-1" % MINT_PROJECT_DOMAIN
        f1 = ''

        self.addComponent("trove:runtime", v1, f1)
        self.addCollection("trove", v1, [":runtime"], defaultFlavor = f1)

        # set up a collection that includes both
        v2 = "/testproject.%s@rpl:baz/1.0-1-1" % MINT_PROJECT_DOMAIN
        self.addCollection("group-dist", v2, [("trove", v1)], defaultFlavor = f1)

        # and set up a shadow
        v3 = "/testproject.%s@rpl:linux//prod/1.0-1-1" % MINT_PROJECT_DOMAIN
        self.addComponent("trove:runtime", v3, f1)
        self.addCollection("trove", v3, [":runtime"], defaultFlavor = f1)

        page = self.webLogin('testuser', 'testpass')
        page = self.fetch("/findRefs?trvName=trove;trvVersion=%s" % v1)

        self.failUnless(v3 in page.body)
        self.failUnless(("group-dist=%s" % v2) in page.body)

    def testClonedFrom(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        hostname = 'testproject.%s' % MINT_PROJECT_DOMAIN

        # copied straight from conary-test-1.1/clonetest.py --sgp
        os.chdir(self.workDir)
        self.newpkg("testcase")
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe1)
        self.addfile("testcase.recipe")
        self.commit()
        self.cookFromRepository('testcase')

        self.mkbranch("1.0-1", "%s@rpl:shadow" % hostname, "testcase:source",
                      shadow = True)

        os.chdir(self.workDir)
        shutil.rmtree("testcase")
        self.checkout("testcase", "%s@rpl:shadow" % hostname)
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe2)
        self.commit()

        self.cfg.buildLabel = versions.Label("%s@rpl:shadow" % hostname)
        self.cookFromRepository('testcase')
        self.cfg.buildLabel = versions.Label("%s@rpl:devel" % hostname)

        self.clone('/%s@rpl:devel' % hostname,
                   'testcase:source=%s@rpl:shadow' % hostname)
        self.clone('/%s@rpl:devel' % hostname,
                   'testcase=%s@rpl:shadow' % hostname,
                   fullRecurse=False)

        self.openRepository()
        page = self.webLogin('testuser', 'testpass')
        page = self.fetch("/repos/testproject/troveInfo?t=testcase")
        self.failUnless("Cloned from:" in page.body,
                "Missing cloned from information in repos browser")

        page = self.fetch("/repos/testproject/troveInfo?t=testcase:source")
        self.failUnless("Cloned from:" in page.body,
                "Missing cloned from information from source in repos browser")


if __name__ == "__main__":
    testsuite.main()
