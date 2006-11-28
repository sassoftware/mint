#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import os
import re
import time

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, FQDN, PFQDN
from mint import pkgindex
import recipes

from conary import repository
from conary import versions
from conary.conarycfg import ConaryConfiguration, UserInformation
from conary.conaryclient import ConaryClient

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

    @testsuite.context("quick")
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
            time.sleep(0.5)
            iters += 1
            if project.getCommits() != []:
                break
            if iters > 30:
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
        assert(groupTroves == ['group-test'])

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
        expectedRE = expectedRE.replace("rpath.local2", MINT_PROJECT_DOMAIN)
        expectedRE = expectedRE.replace("rpath\.local2", MINT_PROJECT_DOMAIN)

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

    def testAnonDenied(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # test good anon access
        assert(nc.troveNames(self.cfg.buildLabel) == [])

        # delete anon access
        nc.deleteAccessGroup(self.cfg.buildLabel, 'anonymous')

        # now make an anon client
        labels = [x[0] for x in cfg.user]

        while cfg.user:
            cfg.user.pop()

        for l in labels:
            cfg.user.addServerGlob(l, 'anonymous', 'anonymous')

        nc = ConaryClient(cfg).getRepos()

        # test bad anon access. We probably want a permission denied vice
        # openerror
        self.assertRaises(repository.errors.OpenError,
                          nc.troveNames, self.cfg.buildLabel)

    def testReposNameMap(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        projectId = self.newProject(client, domainname = 'other.host')
        # NOTE: addRemappedRepository happens automatically when
        #       domainname != cfg.projectDomainName

        self.makeSourceTrove("testcase", testRecipe)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject.other.host@rpl:devel"))
        assert(troveNames == ['testcase:source'])

    def testTroveHelpers(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        labelStr = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"
        self.cookFromRepository("testcase",
            versions.Label(labelStr), ignoreDeps = True)

        server = client.server._server

        r = server.getAllTroveLabels(projectId, "testproject." + MINT_PROJECT_DOMAIN, "testcase")
        assert(r == [labelStr])

        r = server.getTroveVersions(projectId, labelStr, "testcase")
        assert(r == {'/testproject.%s@rpl:devel/1.0-1-1' % MINT_PROJECT_DOMAIN: ['']},
                     ['/testproject.%s@rpl:devel/1.0-1-1' % MINT_PROJECT_DOMAIN],
                    {'': ''})


    def testEntitlementAccess(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        projectId = self.newProject(client)
        self.makeSourceTrove("testcase", testRecipe)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # get rid of anonymous access
        nc.deleteUserByName(self.cfg.buildLabel, 'anonymous')
        entclass = 'entclass'
        entkey = 'ENTITLEMENT'
        nc.addEntitlementGroup(self.cfg.buildLabel, entclass, 'testuser')
        if hasattr(nc, 'addEntitlement'):
            nc.addEntitlement(self.cfg.buildLabel, entclass, entkey)
        else:
            nc.addEntitlements(self.cfg.buildLabel, entclass, [entkey])

        troveNames = nc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

        entcfg = ConaryConfiguration()
        entcfg.root = cfg.dbPath = ":memory:"
        entcfg.repositoryMap = cfg.repositoryMap
        entcfg.entitlementDirectory = self.workDir
        entcfg.installLabelPath = cfg.installLabelPath

        server = self.cfg.buildLabel.getHost()
        open(self.workDir + "/%s" % server, "w").write(
            "<server>%s</server>\n"
            "<class>%s</class>\n"
            "<key>%s</key>\n" % (server, entclass, entkey))

        entclient = ConaryClient(entcfg)
        entnc = entclient.getRepos()
        troveNames = entnc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

    def testUPIExternal(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        extProjectId = self.newProject(client, "External Project", "external",
                MINT_PROJECT_DOMAIN)

        cu = self.db.cursor()
        cu.execute("UPDATE projects SET external = 1 WHERE projectId=?",
                extProjectId)
        self.db.commit()

        # two versions, different branches
        for x in "tag1", "tag2":
            v = "/external.%s@rpl:%s/1.0.0" % (MINT_PROJECT_DOMAIN, x)
            self.addComponent('testcase:runtime', v)
            self.addCollection('testcase', v, ['testcase:runtime'])

        # add a newer version on tag2
        v = "/external.%s@rpl:tag2/1.0.1" % MINT_PROJECT_DOMAIN
        self.addComponent('testcase:runtime', v)
        self.addCollection('testcase', v, ['testcase:runtime'])

        # make it really "external"
        port = self.mintCfg.SSL and self.securePort or self.port
        extProject = client.getProject(extProjectId)
        labelId = extProject.getLabelIdMap()['external.'+MINT_PROJECT_DOMAIN+'@rpl:devel']
        extProject.editLabel(labelId, "external.%s@rpl:devel" % MINT_PROJECT_DOMAIN,
            'http%s://%s:%d/repos/external/' % ((self.mintCfg.SSL and 's' or ''), PFQDN, port), 'testuser', 'testpass')

        pkgindex.UpdatePackageIndexExternal.logFileName = None
        upi = pkgindex.UpdatePackageIndexExternal()
        upi.logPath = None
        upi.cfg = self.mintCfg
        self.captureOutput(upi.run)

        cu.execute("SELECT version FROM PackageIndex")
        x = [x[0] for x in cu.fetchall()]

        assert('/external.%s@rpl:tag2/1.0.1-1-1' % MINT_PROJECT_DOMAIN in x)
        assert('/external.%s@rpl:tag1/1.0.0-1-1' % MINT_PROJECT_DOMAIN in x)

    def testUPI(self):
        def _fakeCommit(pkg, projectId, timestamp, userId):
            cu = self.db.cursor()
            r = cu.execute("INSERT INTO Commits VALUES(?, ?, ?, '/conary.rpath.com@rpl:1/1.0-1-1', ?)", projectId, timestamp, pkg, userId)
            self.db.commit()

        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        _fakeCommit('package1', projectId, time.time(), userId)
        _fakeCommit('package2', projectId, time.time(), userId)
        _fakeCommit('package3', projectId, time.time(), userId)

        upi = pkgindex.UpdatePackageIndex()
        upi.logPath = None
        upi.cfg = self.mintCfg
        x = self.captureOutput(upi.run)

        cu = self.db.cursor()
        cu.execute("SELECT name FROM PackageIndex ORDER BY name")
        self.failUnlessEqual([x[0] for x in cu.fetchall()], ['package1', 'package2', 'package3'])
        cu.execute("SELECT mark FROM PackageIndexMark")
        self.failIf(cu.fetchone()[0] == 0)

        _fakeCommit('package4', projectId, time.time(), userId)
        x = self.captureOutput(upi.run)

        cu.execute("SELECT name FROM PackageIndex ORDER BY name")
        self.failUnlessEqual([x[0] for x in cu.fetchall()], ['package1', 'package2', 'package3', 'package4'])


if __name__ == "__main__":
    testsuite.main()
