#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import os
import re
import time

import difflib
import shutil
import tempfile
import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, FQDN
from mint.scripts import pkgindexer
from mint.web.repos import ConaryHandler
import recipes

from conary import trove
from conary import repository
from conary.repository import errors
from conary import versions
from conary.conarycfg import ConaryConfiguration, UserInformation
from conary import conarycfg
from conary.conaryclient import ConaryClient
from conary.deps import deps
from conary.lib import sha1helper, util

testRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"
    clearBuildReqs()

    def setup(r):
        r.Create("/temp/foo")
"""

testRecipe2 = """
class TestCase2(PackageRecipe):
    name = "testcase2"
    version = "1.0"
    clearBuildReqs()

    def setup(r):
        r.Create("/temp/foo")
"""

testGroup = """
class GroupTest(GroupRecipe):
    name = "group-test"
    version = "1.0"
    clearBuildReqs()

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

    @testsuite.context("quick", "unfriendly")
    def testBasicRepository(self):
        self.startMintServer()
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
        self.startMintServer()
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
        self.startMintServer()
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
        troveNames.sort()
        assert(troveNames == ['group-test', 'group-test:source',
                   'testcase', 'testcase:runtime', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == ['group-test'])

    def testCookBadPwResponse(self):
        self.startMintServer()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.cfg.user.remove(('testproject.' + MINT_PROJECT_DOMAIN, ('testuser', 'testpass')))
        self.cfg.user.addServerGlob('testproject.rpath.' + MINT_PROJECT_DOMAIN, 'testuser', 'badpass')
        self.assertRaises(errors.InsufficientPermission,
            self.makeSourceTrove, "testcase", testRecipe)

    def testMultipleContentsDirs(self):
        self.startMintServer()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"),
            ignoreDeps = True)

        # compare two contents directories:
        d1 = [x[1:] for x in os.walk(self.reposDir + "-mint/contents1/")]
        d2 = [x[1:] for x in os.walk(self.reposDir + "-mint/contents2/")]
        assert(d1 and d2 and d1 == d2)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(sorted(troveNames) == ['testcase', 'testcase:runtime', 'testcase:source'])

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

        repos = self.startMintServer()
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
                ("nosuchuser", "nonexist")))
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
        nc.deleteUserByName(self.cfg.buildLabel, 'anonymous')

        # now make an anon client
        labels = [x[0] for x in cfg.user]

        while cfg.user:
            cfg.user.pop()

        for l in labels:
            cfg.user.addServerGlob(l, 'anonymous', 'anonymous')

        nc = ConaryClient(cfg).getRepos()

        # test bad anon access. We probably want a permission denied vice
        # openerror
        self.assertRaises(repository.errors.InsufficientPermission,
                          nc.troveNames, self.cfg.buildLabel)

    def testReposNameMap(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        projectId = self.newProject(client, domainname = 'other.host')

        self.makeSourceTrove("testcase", testRecipe)

        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject.other.host@rpl:devel"))
        assert(troveNames == ['testcase:source'])

    def testTroveHelpers(self):
        self.startMintServer()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)
        labelStr = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"
        self.cookFromRepository("testcase",
            versions.Label(labelStr), ignoreDeps = True)

        server = client.server._server

        r = server.getAllTroveLabels(projectId, "testproject." + MINT_PROJECT_DOMAIN, "testcase")
        self.assertEqual(r, [labelStr])

        dct, lst = server.getTroveVersions(projectId, labelStr, "testcase")
        dct = dict((str(versions.ThawVersion(x[0])), x[1]) for x in dct.items())
        lst = [ str(versions.ThawVersion(x)) for x in lst ] 
        self.assertEqual(dct, {'/testproject.rpath.local2@rpl:devel/1.0-1-1': [('(no flavor)', '')]})
        self.assertEqual(lst, ['/testproject.%s@rpl:devel/1.0-1-1' % MINT_PROJECT_DOMAIN])


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
        role = 'entclass-role'
        entkey = 'ENTITLEMENT'
        nc.addRole(self.cfg.buildLabel, role)
        nc.addAcl(self.cfg.buildLabel, role, None, None, write=True, remove=False)
        nc.addEntitlementClass(self.cfg.buildLabel, entclass, role)
        if hasattr(nc, 'addEntitlement'):
            nc.addEntitlement(self.cfg.buildLabel, entclass, entkey)
        elif hasattr(nc, 'addEntitlements'):
            nc.addEntitlements(self.cfg.buildLabel, entclass, [entkey])
        else:
            nc.addEntitlementKeys(self.cfg.buildLabel, entclass, [entkey])

        troveNames = nc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

        server = self.cfg.buildLabel.getHost()
        open(self.workDir + "/%s" % server, "w").write(
            conarycfg.emitEntitlement(server, entclass, entkey))

        entcfg = ConaryConfiguration()
        entcfg.entitlementDirectory = self.workDir
        entcfg.readEntitlementDirectory()
        entcfg.root = cfg.dbPath = ":memory:"
        entcfg.repositoryMap = cfg.repositoryMap
        entcfg.installLabelPath = cfg.installLabelPath

        entclient = ConaryClient(entcfg)
        entnc = entclient.getRepos()
        troveNames = entnc.troveNames(self.cfg.buildLabel)
        assert(troveNames == ['testcase:source'])

    def testUPIExternal(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")

        self.openRepository(1)
        extProjectId = client.newExternalProject("External Project",
            "external", MINT_PROJECT_DOMAIN, "localhost1@rpl:devel",
            'http://localhost:%d/conary/' % self.servers.getServer(1).port, 
            False)

        # two versions, different branches
        for x in "tag1", "tag2":
            v = "/localhost1@rpl:%s/1.0.0" % x
            self.addComponent('testcase:runtime', v)
            self.addCollection('testcase', v, ['testcase:runtime'])

        # add a newer version on tag2
        v = "/localhost1@rpl:tag2/1.0.1"
        self.addComponent('testcase:runtime', v)
        self.addComponent('testcase:source', v)
        self.addCollection('testcase', v, ['testcase:runtime'])

        pkgindexer.UpdatePackageIndexExternal.logFileName = None
        upi = pkgindexer.UpdatePackageIndexExternal(aMintServer=client.server._server)
        upi.logPath = None
        upi.cfg = self.mintCfg
        self.captureOutput(upi.run)

        cu = self.db.cursor()
        cu.execute("SELECT name, version, serverName, branchName, isSource FROM PackageIndex")
        x = [(x[0], x[1], x[2], x[3], x[4]) for x in cu.fetchall()]

        try:
            self.failUnless(('testcase', '/localhost1@rpl:tag1/1.0.0-1-1', 'localhost1', 'rpl:tag1', 0) in x)
            self.failUnless(('testcase', '/localhost1@rpl:tag2/1.0.1-1-1', 'localhost1', 'rpl:tag2', 0) in x)
            self.failUnless(('testcase:source', '/localhost1@rpl:tag2/1.0.1-1', 'localhost1', 'rpl:tag2', 1) in x)
        except:
            # display the error...
            print x
            raise

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
        _fakeCommit('package3:source', projectId, time.time(), userId)

        upi = pkgindexer.UpdatePackageIndex(aMintServer=client.server._server)
        upi.logPath = None
        upi.cfg = self.mintCfg
        x = self.captureOutput(upi.run)
        
        cu = self.db.cursor()
        cu.execute("SELECT name FROM PackageIndex ORDER BY name")
        self.failUnlessEqual([x[0] for x in cu.fetchall()], ['package1', 'package2', 'package3', 'package3:source'])
        cu.execute("SELECT mark FROM PackageIndexMark")
        self.failIf(cu.fetchone()[0] == 0)

        _fakeCommit('package4', projectId, time.time(), userId)
        x = self.captureOutput(upi.run)

        cu.execute("SELECT name, version, serverName, branchName, isSource FROM PackageIndex ORDER BY name")
        x = [(x[0], x[1], x[2], x[3], x[4]) for x in cu.fetchall()]

        self.failUnless(('package1', '/conary.rpath.com@rpl:1/1.0-1-1', 'conary.rpath.com', 'rpl:1', 0) in x)
        self.failUnless(('package2', '/conary.rpath.com@rpl:1/1.0-1-1', 'conary.rpath.com', 'rpl:1', 0) in x)
        self.failUnless(('package3', '/conary.rpath.com@rpl:1/1.0-1-1', 'conary.rpath.com', 'rpl:1', 0) in x)
        self.failUnless(('package3:source', '/conary.rpath.com@rpl:1/1.0-1-1', 'conary.rpath.com', 'rpl:1', 1) in x)
        self.failUnless(('package4', '/conary.rpath.com@rpl:1/1.0-1-1', 'conary.rpath.com', 'rpl:1', 0) in x)

    def testPerProjectRepositoryDatabases(self):
        # create a project
        driver, path = self.mintCfg.database['default']
        if driver != "sqlite":
            raise testsuite.SkipTestException("Only test in sqlite")
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)

        # move the repository database to a different location
        dbName = "testproject." + MINT_PROJECT_DOMAIN
        newPath = tempfile.mktemp()
        os.rename(path % dbName, newPath)

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET database = ? WHERE projectId = ?",
                'sqlite ' + newPath, projectId)
        self.db.commit()

        # make sure we can still access the repository
        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(troveNames == ['testcase:source'])

    def testDescendantsAndReferences(self):
        def _buildReferences(p):
            verlist = [
                "/%s.%s@rpl:linux//devel/1.0-1-1",
                "/%s.%s@rpl:linux//devel//qa/1.0-1-1",
                ]
            for i, v in enumerate(verlist):
                v = v % (p, MINT_PROJECT_DOMAIN)
                for n1 in ["alpha", "beta"]:
                    for n2 in [":runtime", ":data"]:
                        self.addComponent(n1+n2, v)
                    self.addCollection(n1, v, [":runtime", ":data"])
                self.addCollection("alpha%d" % i, v, [("alpha", v), ("alpha:runtime",v)])
                self.addCollection("beta%d" % i, v, [("beta", v), ("beta:runtime",v)], weakRefList = [("alpha:data",v)])


        client, userId = self.quickMintUser("testuser", "testpass")

        # set up some references and shadows
        projectId = self.newProject(client, name = "P1", hostname = "p1")
        _buildReferences("p1")
        projectId = self.newProject(client, name = "P2", hostname = "p2")
        v = "/p2.%s@rpl:linux//devel/1.0-1-1" % MINT_PROJECT_DOMAIN
        v1 = "/p1.%s@rpl:linux//devel" % MINT_PROJECT_DOMAIN
        v2 = "/p1.%s@rpl:linux//devel//qa/1.0-1-1" % MINT_PROJECT_DOMAIN
        self.addCollection("group-alpha", v, [("alpha:runtime", v2)],
                           weakRefList = [("alpha", v2)])

        r = client.getTroveReferences('alpha', v2, [''])
        self.failUnlessEqual(r, { 1: [('alpha1', v2, '')],
                                  2: [('group-alpha', v, '')] })
        d = client.getTroveDescendants('alpha', v1, '')
        # FIXME: should asking p2 for decendant information for troves
        # residing solely in p1 return results?  conary-2.0 does not
        # think so
        #self.failUnlessEqual(d, {1: [(v2, '')], 2: [(v2, '')]})
        self.failUnlessEqual(d, {1: [(v2, '')]})


    def testShadowDiff(self):
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
    version = '1.0'
    clearBuildReqs()
    fileText = 'blah\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""
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
        #self.cookFromRepository('testcase')

        self.mkbranch("1.0-1", "%s@rpl:shadow" % hostname, "testcase:source",
                      shadow = True)

        os.chdir(self.workDir)
        shutil.rmtree("testcase")
        self.checkout("testcase", "%s@rpl:shadow" % hostname)
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe2)
        self.writeFile('test.txt', 'this is a test file\n\n')
        self.addfile('test.txt')
        self.commit()
        self.startMintServer()
        rc = self.openRepository()
        ver = versions.VersionFromString('/testproject.%s@rpl:devel//shadow/1.0-1.1' % MINT_PROJECT_DOMAIN)
        ver2 = versions.VersionFromString('/testproject.%s@rpl:devel//shadow/1.0-1' % MINT_PROJECT_DOMAIN)
        ver3 = versions.VersionFromString('/testproject.%s@rpl:devel/1.0-1' % MINT_PROJECT_DOMAIN)

        for pathid, path, fileid, version in rc.iterFilesInTrove('testcase:source', ver, deps.parseFlavor('')):
            if path == 'testcase.recipe':
                break
        fileId = sha1helper.sha1ToString(fileid) 

        for pathid, path, fileid2, version in rc.iterFilesInTrove('testcase:source', ver2, deps.parseFlavor('')):
            if path == 'testcase.recipe':
                break
        fileId2 = sha1helper.sha1ToString(fileid2) 

        for pathid, path, fileid3, version in rc.iterFilesInTrove('testcase:source', ver3, deps.parseFlavor('')):
            if path == 'testcase.recipe':
                break
        fileId3 = sha1helper.sha1ToString(fileid3) 

        for testpathid, testpath, testfileid, testversion in rc.iterFilesInTrove('testcase:source', ver, deps.parseFlavor('')):
            if testpath == 'test.txt':
                break
        testfileId = sha1helper.sha1ToString(testfileid) 

        try:
            tmpDir = tempfile.mkdtemp()
            oldCacheDir = self.mintCfg.diffCacheDir
            self.mintCfg.diffCacheDir =  tmpDir 
            ch = ConaryHandler(None, None)
            ch.__dict__.update(cfg=self.mintCfg, repos=rc)
            ch._write = lambda *args, **kwargs: (args, kwargs)
            ret = ch.diffShadow(t='testcase:source', v=str(ver), path='testcase.recipe', pathId=None, fileId=fileId, auth=None)
            ret2 = ch.diffShadow(t='testcase:source', v=str(ver2), path='testcase.recipe', pathId=None, fileId=fileId2, auth=None)
            ret3 = ch.diffShadow(t='testcase:source', v=str(ver3), path='testcase.recipe', pathId=None, fileId=fileId3, auth=None)
            ret4 = ch.diffShadow(t='testcase:source', v=str(ver), path='test.txt', pathId=None, fileId=testfileId, auth=None)

            fd = open(os.path.join(tmpDir, 'test_cache.test.test@rpl:1__2_1-1'), 'w')
            fd.write('  Testing cache.\n')
            fd.close()
            ret5 = ch.diffShadow(t='blah', v='/cache.test.test@rpl:1//2/1-1', 
                                 path='baz', pathId=None, fileId='test',
                                 auth=None)
            self.failIf(ret5[1]['diffinfo']['leftFile'] == 'Testing cache.\n',
                        'Cache failed.')
        finally:
            self.mintCfg.diffCacheDir = oldCacheDir
            util.rmtree(tmpDir)

        self.failIf(ret[0][0] != 'shadow_diff', 'Wrong template was rendered for diff')
        self.failIf(ret[1]['diffinfo']['diffedLines'] != [1,5], 'Incorrect lines marked as diffed')
        self.failIf(ret[1]['diffinfo']['leftLineNums'] != ret[1]['diffinfo']['rightLineNums'], 'Line numberings incorrect')
        self.failIf(ret[1]['diffinfo']['leftFile'][1] == ret[1]['diffinfo']['rightFile'][1], 'Incorrect diff contents displayed')
        self.failIf(ret2[0][0] != 'shadow_diff', 'Wrong template rendered for identical diff.')
        self.failIf(ret2[1]['message'] != 'File contents are identical on both branches.', 'Incorrect message returned')
        self.failIf(ret3[0][0] != 'error', 'Error page not rendered.')
        self.failIf(ret4[1]['message'] != 'test.txt was created on the current branch.  No version exists on the parent.', 'Incorrect message returned')

    def testNDiffParse(self):
        """
        Check to see if we are parsing the output of difflib.ndiff corectly.
        """
        f1 = r"""rBuilder provides a great way to deliver applications from development
to production by eliminating the costly step of "porting" the application for
the production environment. Because rBuilder automatically determines the exact
system software stack to
support the application, there is never any uncertainty regarding what needs to
be available in the production instance.

rBuilder also supports all of the major virtualization formats, so you can take
your image straight to production as a virtual appliance. Incremental releases
and maintenance are a snap because rBuilder manages all versioning and
dependency resolution, letting you focus on the application instead of the system software. Read more about rBuilder.

Try rBuilder Online today for free, and experience the simplicity of software
appliances."""

        f2 = r"""rBuilder provides a good way to deliver applications from development
to production by eliminating the costly step of "porting" the application for
the production environment. Because rBuilder automatically determines the exact
system software stack to
support the application, there is never any uncertainty regarding what needs to
be available in the production instance.

Take your image straight to production as a virtual appliance. Incremental releases
and maintenance are easy because rBuilder manages all versioning and
dependency resolution, letting you focus on the application instead of the system software. Read more about rBuilder.

Try rBuilder Online today for free, and experience the simplicity of software
appliances.


That is all."""
        ch = ConaryHandler(None, None)
        res = ch._calcSideBySide(difflib.ndiff(f1.splitlines(), f2.splitlines()))
        self.failIf(res != {'rightLineNums': [1, 2, 3, 4, 5, 6, 7, '', 8, 9, 10, 11, 12, 13, 14, 15, 16], 
            'diffedLines': [0, 7, 8, 9, 14, 15, 16], 
            'leftFile': ['rBuilder provides a great way to deliver applications from development', 
            'to production by eliminating the costly step of "porting" the application for',
            'the production environment. Because rBuilder automatically determines the exact', 
            'system software stack to', 'support the application, there is never any uncertainty regarding what needs to', 
            'be available in the production instance.', 
            '', 
            'rBuilder also supports all of the major virtualization formats, so you can take', 
            'your image straight to production as a virtual appliance. Incremental releases', 
            'and maintenance are a snap because rBuilder manages all versioning and', 
            'dependency resolution, letting you focus on the application instead of the system software. Read more about rBuilder.', 
            '',
            'Try rBuilder Online today for free, and experience the simplicity of software', 
            'appliances.', 
            '',
            '',
            ''],
            'leftLineNums': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, '', '', ''], 
            'rightFile': ['rBuilder provides a good way to deliver applications from development',
            'to production by eliminating the costly step of "porting" the application for', 
            'the production environment. Because rBuilder automatically determines the exact', 
            'system software stack to',
            'support the application, there is never any uncertainty regarding what needs to', 
            'be available in the production instance.',
            '',
            '', 
            'Take your image straight to production as a virtual appliance. Incremental releases',
            'and maintenance are easy because rBuilder manages all versioning and',
            'dependency resolution, letting you focus on the application instead of the system software. Read more about rBuilder.', 
            '', 
            'Try rBuilder Online today for free, and experience the simplicity of software',
            'appliances.',
            '',
            '', 
            'That is all.']},
            'Output of difflib.ndiff not parsed correctly.')


    def testLicenseAndCrypto(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client, "Test Project", "localhost")
        project = client.getProject(projectId)
        repos = ConaryClient(project.getConaryConfig()).getRepos()

        # Add some troves and a group
        for i in range(0, 3):
            self.addComponent('test%d:runtime' % i, '1.0', repos = repos)
            self.addCollection('test%d' % i, '1.0', [ "test%d:runtime" % i ],
                               repos = repos)
        self.addCollection("group-test", "1.0",
                                    [ ("test1"),
                                      ("test2"),
                                    ], repos=repos)

        # Add some metadata
        mi = trove.MetadataItem()
        mi.licenses.set('Test License')
        mi.crypto.set('Test Crypto')
        ver = versions.VersionFromString('/localhost.' + MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1-1')
        fl = deps.parseFlavor('')
        repos.addMetadataItems([(('test0',ver,fl), mi)])
        mi = trove.MetadataItem()
        mi.licenses.set('Different Test License')
        mi.licenses.set('Different Test License part 2')
        mi.crypto.set('Different Test Crypto')
        repos.addMetadataItems([(('test1',ver,fl), mi)])

        mi = trove.MetadataItem()
        mi.licenses.set('Another license')
        repos.addMetadataItems([(('test2',ver,fl), mi)])

        # test
        ch = ConaryHandler(None, None)
        ch.__dict__.update(repos=repos)
        ch._write = lambda *args, **kwargs: (args, kwargs)
        res = ch.licenseCryptoReport(t='group-test', v=ver, f=fl, auth=None)
        self.failIf(res[0][0] != 'lic_crypto_report')
        self.failIf(res[1]['troveName'] != 'group-test')
        expected = {'test0': (['Test License'], ['Test Crypto']),
                    'test1': (['Different Test License',
                                      'Different Test License part 2'], 
                                      ['Different Test Crypto']),
                    'test2': (['Another license'], []),
                    'group-test': ([], [])}
        for x in res[1]['troves']:
            self.failUnlessEqual((x[3], x[4]), expected[x[0]])

        # check error handling
        client.hideProject(projectId)
        repos = ConaryClient(project.getConaryConfig(True, 'anonymous',
                                                     'anonymous')).getRepos()
        ch.__dict__.update(repos=repos)
        res = ch.licenseCryptoReport(t='group-test', v=ver, f=fl, auth=None)
        self.failUnlessEqual(res[0][0], 'error')

if __name__ == "__main__":
    testsuite.main()
