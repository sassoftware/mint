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
        raise testsuite.SkipTestException
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

        self.openRepository(1)
        self.makeSourceTrove("testcase", testRecipe, buildLabel = versions.Label('localhost1@rpl:linux'))

        extProject.editLabel(labelId, "localhost1@rpl:devel",
            'http://localhost1:%d/conary/' % self.servers.getServer(1).port, 'anonymous', 'anonymous')

        page = self.assertCode('/repos/external/browse', code = 200)

        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

if __name__ == "__main__":
    testsuite.main()
