#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

from time import sleep
import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
import recipes

from conary.conarycfg import ConaryConfiguration, UserInformation
from conary.conaryclient import ConaryClient
from conary import repository
from conary import versions

testRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"
    
    def setup(r):
        r.Create("/temp/foo")
""" 

testGroup = """
class GroupTest(GroupRecipe):
    name = "group-test"
    version = "1.0"

    def setup(r):
        r.add('testcase')
"""

class RepositoryTest(MintRepositoryHelper):
    def testCommitStats(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        client.server.registerCommit('testproject.rpath.local', 'testuser',
                                     'mytrove:source',
                                     '/testproject.rpath.local@rpl:devel/1.0-1')
        project = client.getProject(projectId)
        assert([x[:2] for x in project.getCommits()] == [('mytrove:source',
                                                          '1.0-1')])

        # using a bogus username should not fail
        client.server.registerCommit('testproject.rpath.local',
                                     'nonexistentuser', 'mytrove:source',
                                     '/testproject.rpath.local@rpl:devel/1.0-1')

    def testBasicRepository(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)
        project = client.getProject(projectId)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # test that the source trove landed properly
        troveNames = nc.troveNames(versions.Label("testproject.rpath.local@rpl:devel"))
        assert(troveNames == ["testcase:source"])

        # test that the commits table was updated
        # give some time for the commit action to run
        iters = 0
        while True:
            sleep(0.1)
            iters += 1
            if project.getCommits() != []:
                break
            if iters > 50:
                self.fail("commits didn't show up")

        assert([x[:2] for x in project.getCommits()] == [('testcase:source', '1.0-1')])

    def testHooksResponse(self):
        self.openRepository()
        cfg = ConaryConfiguration(readConfigFiles = False)
        cfg.installLabelPath = ['notfound.rpath.local@rpl:devel']
        cfg.repositoryMap = {'notfound.rpath.local': 'http://test.rpath.local:%d/repos/notfound/' % self.port}
        cfg.root = ':memory:'
        cfg.dbPath = ':memory:'

        repos = ConaryClient(cfg).getRepos()

        try:
            repos.troveNamesOnServer('notfound.rpath.local')
        except repository.errors.OpenError, e:
            assert "404 Not Found" in str(e), \
            "accessing a non-existent repository did not return a "
            "404 Not Found error"
            pass
        else:
            self.fail("accessing a non-existent repository did not return "
                      "an error")


    def testCook(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
       
        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject.rpath.local@rpl:devel"),
            ignoreDeps = True)

        self.makeSourceTrove("group-test", testGroup)
        self.cookFromRepository("group-test",
            versions.Label("testproject.rpath.local@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject.rpath.local@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'testproject.rpath.local@rpl:devel': ['group-test']})


if __name__ == "__main__":
    testsuite.main()
