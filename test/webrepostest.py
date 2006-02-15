#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import mint_rephelp

from repostest import testRecipe
from conary import versions

class WebReposTest(mint_rephelp.WebRepositoryHelper):
    def testRepositoryBrowser(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject')

        l = versions.Label("testproject.rpath.local@rpl:devel")
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l,
            ignoreDeps = True)

        # first try anonymous browsing
        page = self.assertContent('/repos/testproject/browse', ok_codes = [200],
            content = 'troveInfo?t=testcase:runtime')

        # now try logged-in
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/testproject/browse', ok_codes = [200],
            content = 'troveInfo?t=testcase:runtime')

        # now try logged-in, as another user user
        client, userId = self.quickMintUser('test2', 'test2pass')
        page = self.webLogin('test2', 'test2pass')
        page = page.assertContent('/repos/testproject/browse', ok_codes = [200],
            content = 'troveInfo?t=testcase:runtime')

    def testBrowseHiddenProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')

        adminClient.hideProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)

        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        # anonymous user should see a 404
        page = self.assertCode('/repos/test/browse', code = 404)

        # logged-in user should see the browser
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/test/browse', ok_codes = [200],
            content = 'troveInfo?t=testcase:runtime')

    def testBrowseExternalProject(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        extProjectId = self.newProject(client, "External Project", "external")

        extProject = client.getProject(extProjectId)
        labelId = extProject.getLabelIdMap()['external.rpath.local@rpl:devel']

        self.openRepository(1)
        self.makeSourceTrove("testcase", testRecipe, buildLabel = versions.Label('localhost1@rpl:linux'))

        extProject.editLabel(labelId, "localhost1@rpl:devel",
            'http://localhost:%d/conary/' % self.servers.getServer(1).port, 'anonymous', 'anonymous')

        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

        # log in and make sure we see the same thing
        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

    def testTroveInfoPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        # test that missing troves are a 404 not found error
        page = self.fetch('/repos/foo/troveInfo?t=group-foo', ok_codes = [404])

        self.openRepository(1)
        self.addQuickTestComponent('foo:source',
                                   '/testproject.rpath.local@rpl:devel/1.0-1')

        # shuffle the label around to talk to server #2
        self.moveToServer(project, 1)

        # test that trove info page renders without error
        page = self.assertContent('/repos/testproject/troveInfo?t=foo:source',
                                  content = "Trove information for")

    def testReposRSS(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        page = self.fetch('/repos/testproject/browse')

        self.failIf('/repos/testproject/rss' in page.body,
                    "Malformed base path for rss feed on repos page")

if __name__ == "__main__":
    testsuite.main()
