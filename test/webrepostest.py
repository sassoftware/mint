#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
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


class WebReposTest(mint_rephelp.WebRepositoryHelper):
    def testRepositoryBrowser(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        l = versions.Label("testproject." + MINT_PROJECT_DOMAIN + \
                "@rpl:devel")
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l,
            ignoreDeps = True)

        # first try anonymous browsing
        page = self.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=testcase:runtime',
            server = self.getProjectServerHostname())

        # now try logged-in
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=testcase:runtime',
            server = self.getProjectServerHostname())

        # now try logged-in, as another user user
        page = page.fetchWithRedirect('/logout')
        client, userId = self.quickMintUser('test2', 'test2pass')
        page = self.webLogin('test2', 'test2pass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=testcase:runtime',
            server = self.getProjectServerHostname())

    def testBrowseHiddenProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')
        project = client.getProject(projectId)

        adminClient.hideProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)

        self.cookFromRepository("testcase",
            versions.Label("test." + MINT_PROJECT_DOMAIN + "@rpl:devel"),
            ignoreDeps = True)

        # anonymous user should see a 404
        page = self.assertCode('/repos/test/browse', code = 404,
                server = self.getProjectServerHostname())

        # logged-in user should see the browser
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/test/browse', code = [200],
                content = 'troveInfo?t=testcase:runtime',
                server = self.getProjectServerHostname())

    def testBrowseExternalProject(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        extProjectId = self.newProject(client, "External Project", "external",
                MINT_PROJECT_DOMAIN)

        cu = self.db.cursor()
        cu.execute("UPDATE projects SET external = 1 WHERE projectId=?",
                extProjectId)
        self.db.commit()

        extProject = client.getProject(extProjectId)
        labelId = extProject.getLabelIdMap()['external.' + \
                MINT_PROJECT_DOMAIN + '@rpl:devel']
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
        page = self.fetchWithRedirect('/repos/foo/troveInfo?t=group-foo',
                                      code = [404])

        self.openRepository(1)
        self.addQuickTestComponent('foo:source',
                                   '/testproject.' + MINT_PROJECT_DOMAIN + \
                                           '@rpl:devel/1.0-1')

        # shuffle the label around to talk to server #2
        self.moveToServer(project, 1)

        # test that trove info page renders without error
        page = self.assertContent('/repos/testproject/troveInfo?t=foo:source',
                                  content = "Trove information for")

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

        self.openRepository(1)
        l = versions.Label("testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel")
        self.makeSourceTrove("testcase", testDirRecipe, l)
        self.cookFromRepository("testcase", l,
            ignoreDeps = True)

        self.moveToServer(project, 1)

        # using the project server for this test
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/repos/testproject/troveInfo?t=testcase:runtime')
        fileLink = [x for x in page.getDOM().getByName('a') if x[0] == "Show Troves"][0]

        page = self.assertContent('/repos/testproject/' + \
                fileLink.getattr('href'), code = [200],
                content = '<span title="/temp/directory">/temp/directory</span>')

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


if __name__ == "__main__":
    testsuite.main()
