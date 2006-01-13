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
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        # first try anonymous browsing
        page = self.assertContent('/repos/test/browse', ok_codes = [200],
            content = 'troveInfo?t=testcase:runtime')

        # now try logged-in
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/test/browse', ok_codes = [200],
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
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser("testuser", "testpass")
        extProjectId = self.newProject(client, "External Project", "external")

        extProject = client.getProject(extProjectId)
        labelId = extProject.getLabelIdMap()['external.rpath.local@rpl:devel']
        extProject.editLabel(labelId, "external.rpath.local@rpl:devel",
            'http://localhost:%d/conary/' % self.getPort(), 'anonymous', 'anonymous')

        self.makeSourceTrove("testcase", testRecipe, label = versions.Label('localhost@rpl:linux'))

        page = self.assertCode('/repos/test/browse', code = 200)


if __name__ == "__main__":
    testsuite.main()
