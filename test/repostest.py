#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

from time import sleep
import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
import recipes

from repository import netclient
import versions

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
    def testBasicRepository(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
       
        self.makeSourceTrove("testcase", testRecipe)
        project = client.getProject(projectId)

        cfg = project.getConaryConfig()
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)

        # test that the source trove landed properly
        troveNames = nc.troveNames(versions.Label("test.localhost@rpl:devel"))
        assert(troveNames == ["testcase:source"])

        # test that the commits table was updated
        sleep(1) # make sure that the commitaction runs
        assert(project.getCommits() == [('testcase:source', '1.0-1')])

    def testCook(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
       
        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.localhost@rpl:devel"),
            ignoreDeps = True)

        self.makeSourceTrove("group-test", testGroup)
        self.cookFromRepository("group-test",
            versions.Label("test.localhost@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)

        troveNames = nc.troveNames(versions.Label("test.localhost@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'test.localhost@rpl:devel': ['group-test']})


if __name__ == "__main__":
    testsuite.main()
