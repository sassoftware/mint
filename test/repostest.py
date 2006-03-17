#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import os
from time import sleep
import testsuite
import re
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN
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

testRecipe2 = """
class TestCase2(PackageRecipe):
    name = "testcase2"
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

        client.server.registerCommit('testproject.' + MINT_PROJECT_DOMAIN,
                                     'testuser',
                                     'mytrove:source',
                                     '/testproject.' + MINT_PROJECT_DOMAIN + \
                                             '@rpl:devel/1.0-1')
        project = client.getProject(projectId)
        assert([x[:2] for x in project.getCommits()] == [('mytrove:source',
                                                          '1.0-1')])

        # using a bogus username should not fail
        client.server.registerCommit('testproject.' + MINT_PROJECT_DOMAIN,
                                     'nonexistentuser', 'mytrove:source',
                                     '/testproject.' + MINT_PROJECT_DOMAIN + \
                                             '@rpl:devel/1.0-1')

    def testBasicRepository(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)
        project = client.getProject(projectId)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # test that the source trove landed properly
        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
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
        cfg.installLabelPath = ['notfound.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel']
        cfg.repositoryMap = {'notfound.' + MINT_PROJECT_DOMAIN: \
                'http://%s.%s:%d/repos/notfound/' % \
                (MINT_HOST, MINT_PROJECT_DOMAIN, self.port)}
        cfg.root = ':memory:'
        cfg.dbPath = ':memory:'

        repos = ConaryClient(cfg).getRepos()

        try:
            repos.troveNamesOnServer('notfound.' + MINT_PROJECT_DOMAIN)
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
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + \
                "@rpl:devel"),
            ignoreDeps = True)

        self.makeSourceTrove("group-test", testGroup)
        self.cookFromRepository("group-test",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel': ['group-test']})

    def testMultipleContentsDirs(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"),
            ignoreDeps = True)

        # compare two contents directories:
        d1 = [x[1:] for x in os.walk(self.reposDir + "/contents1/")]
        d2 = [x[1:] for x in os.walk(self.reposDir + "/contents2/")]
        assert(d1 and d2 and d1 == d2)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'testcase:source'])

    def testGetTroveVersionsByArch(self):
        # XXX: hardcoded MINT_PROJECT_DOMAIN in this RE, sorry --sgp
        expectedRE = "\{'x86_64': \[\('/testproject.rpath.local2@rpl:devel/1.0-1-2', "\
                   "'/testproject\.rpath\.local2@rpl:devel/\d+\.\d+:1.0-1-2', "\
                   "'1#x86_64'\), "\
                   "\('/testproject.rpath.local2@rpl:devel/1.0-1-1', "\
                   "'/testproject\.rpath\.local2@rpl:devel/\d+\.\d+:1.0-1-1', "\
                   "'1#x86_64'\)\], "\
                   "'x86': "\
                   "\[\('/testproject.rpath.local2@rpl:devel/1.0-1-2', "\
                   "'/testproject.rpath.local2@rpl:devel/\d+\.\d+:1.0-1-2', "\
                   "'1#x86'\), "\
                   "\('/testproject.rpath.local2@rpl:devel/1.0-1-1', "\
                   "'/testproject.rpath.local2@rpl:devel/\d+\.\d+:1.0-1-1', "\
                   "'1#x86'\)\]\}"

        repos = self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        flavors = ("is:x86", "is:x86_64")
        for f in flavors:
            self.addComponent("test:runtime", "1.0", flavor=f)
            self.addCollection("test", "1.0", [(":runtime", "1.0", f) ])
            self.addCollection("group-core", "1.0", [("test", "1.0" , f)])
            self.addCollection("group-core", "1.0-1-2", [("test", "1.0" , f)])

        troveVersions = client.server.getTroveVersionsByArch(projectId,
            "group-core=testproject." + MINT_PROJECT_DOMAIN + " @rpl:devel")

        assert re.compile(expectedRE).match(str(troveVersions))

    def testMultipleRepos(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId1 = self.newProject(client, "Test Project 1", "testp1")
        projectId2 = self.newProject(client, "Test Project 2", "testp2")

        self.cfg.repositoryMap.update({'testp1.' + MINT_PROJECT_DOMAIN: \
            'http://test.%s:%d/repos/testp1/' % \
            (MINT_PROJECT_DOMAIN, self.port) , \
            'testp2.' + MINT_PROJECT_DOMAIN: \
            'http://test.%s:%d/repos/testp2/' % \
            (MINT_PROJECT_DOMAIN, self.port)})

        l1 = versions.Label("testp1." + MINT_PROJECT_DOMAIN + \
                "@rpl:devel")
        l2 = versions.Label("testp2." + MINT_PROJECT_DOMAIN + \
                "@rpl:devel")

        self.makeSourceTrove("testcase", testRecipe, l1)
        self.cookFromRepository("testcase", l1, ignoreDeps = True)

        self.makeSourceTrove("testcase", testRecipe, l2)
        self.cookFromRepository("testcase", l2, ignoreDeps = True)

        # move back to testp1
        self.makeSourceTrove("testcase2", testRecipe2, l1)
        self.cookFromRepository("testcase2", l1, ignoreDeps = True)

    def testAnonymousFallback(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = self.newProject(client)
        self.makeSourceTrove("testcase", testRecipe)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

        # and now try as a non-existent user
        reposMap = cfg.repositoryMap
        cfg = ConaryConfiguration()
        cfg.root = cfg.dbPath = ":memory:"
        cfg.repositoryMap = reposMap

        cfg.user.addServerGlob("testproject." + MINT_PROJECT_DOMAIN, 
                "nosuchuser", "nonexist")
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

        # try as a user with a bad pw
        cfg.user.remove(("testproject." + MINT_PROJECT_DOMAIN,
                "nosuchuser", "nonexist"))
        cfg.user.addServerGlob("testproject." + MINT_PROJECT_DOMAIN,
                "testuser", "badpass")

        troveNames = nc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

    def testReposNameMap(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        projectId = self.newProject(client, domainname = 'other.host')

        client.addRemappedRepository('testproject.' + MINT_PROJECT_DOMAIN,
                'testproject.other.host')
        self.makeSourceTrove("testcase", testRecipe)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject.other.host@rpl:devel"))
        assert(troveNames == ['testcase:source'])


if __name__ == "__main__":
    testsuite.main()
