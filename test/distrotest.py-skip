#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import stat
import sys
import tempfile
import md5

import rephelp
from mint_rephelp import MintRepositoryHelper
from mint_rephelp import EmptyCallback
from mint_rephelp import MINT_PROJECT_DOMAIN, PFQDN

from mint import buildtypes
from mint.distro import gencslist, anaconda_images, splitdistro
from mint.distro import installable_iso
from mint.distro.gencslist import _validateChangeSet

from conary import conarycfg, conaryclient
from conary import sqlite3
from conary import versions
from conary.deps import deps
from conary.lib import util
from conary.lib import sha1helper
from conary.repository import changeset


VFS = versions.VersionFromString
Flavor = deps.parseFlavor

class DistroTest(MintRepositoryHelper):
    def testGencslist(self):
        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])
        self.addComponent("foo:runtime", "1.0")
        self.addComponent("bar:runtime", '1.0')
        self.addComponent("bar:debuginfo", '1.0')
        self.addComponent("baz:runtime", "1.0")
        self.addCollection("bar", "1.0", [ (":runtime", True),
                                           (":debuginfo", False)])

        # test:devel is not byDefault in test, so that changeset
        # should not include test:devel.
        # foo:runtime is also not-by-default and should not be included.
        # bar:runtime is not-by-default in group-foo, but by default
        # in group-dist-extras

        self.addCollection('group-dist-extras', '1.0', ['bar', 'baz:runtime'])

        self.addCollection("group-core", "1.0",
                                [ ("test", True),
                                  ('foo:runtime', False),
                                  ('bar', False)],
                               weakRefList=[('test:runtime', True),
                                            ('test:devel', False), # changed
                                                                   # from trove
                                            ('bar:runtime', False),
                                            ('bar:debuginfo', False)])
                                     
        t = self.addCollection('group-dist', '1.0', 
                            # include group-core by default true,
                            # but not group-dist-extras
                            [('group-dist-extras', False),
                             ('group-core', True)])

        
        n, v, f = t.getName(), t.getVersion(), t.getFlavor()

        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.repositoryMap = self.servers.getServer().getMap()
        cfg.initializeFlavors()
        client = conaryclient.ConaryClient(cfg)

        csdir = tempfile.mkdtemp(dir=self.workDir)

        try:
            self.hideOutput()
            (cslist, groupcs), str = self.captureOutput(
                gencslist.extractChangeSets,
                client, cfg, csdir, n, v, f,
                oldFiles = None, cacheDir = None)
        finally:
            self.showOutput()

        assert(set(cslist) == set(
            ['test-1.0-1-1-none.ccs test /localhost@rpl:linux/1.0-1-1 none 1', 
             'group-dist-1.0-1-1-none.ccs group-dist /localhost@rpl:linux/1.0-1-1 none 1', 
             'group-core-1.0-1-1-none.ccs group-core /localhost@rpl:linux/1.0-1-1 none 1', 
             'group-dist-extras-1.0-1-1-none.ccs group-dist-extras /localhost@rpl:linux/1.0-1-1 none 1', 
             'bar-1.0-1-1-none.ccs bar /localhost@rpl:linux/1.0-1-1 none 1',
             'baz:runtime-1.0-1-1-none.ccs baz:runtime /localhost@rpl:linux/1.0-1-1 none 1',
             ]))

        expected = {'test'              : ['test', 'test:runtime'],
                    'group-dist'        : ['group-dist'],
                    'group-core'        : ['group-core'],
                    'group-dist-extras' : ['group-dist-extras'],
                    'bar'               : ['bar', 'bar:runtime'],
                    'baz:runtime'       : ['baz:runtime']}

        for csName, expectedTroves in expected.iteritems():
            csPath = '%s/%s-1.0-1-1-none.ccs' % (csdir, csName)
            cs = changeset.ChangeSetFromFile(csPath)
            troveNames = set(x.getName() for x in cs.iterNewTroveList())
            assert(troveNames == set(expectedTroves))

        # write a sqldb out and ensure its sanity:
        gencslist.writeSqldb(groupcs, self.tmpDir + "/gencslist-sqldb")
        sqldb = sqlite3.connect(self.tmpDir + "/gencslist-sqldb")
        cu = sqldb.cursor()
        cu.execute("SELECT item FROM Items ORDER BY item")
        assert(cu.fetchall() == [('ALL',), ('bar',), ('bar:debuginfo',),
                                 ('bar:runtime',), ('bar:source',),
                                 ('baz:runtime',), ('baz:source',),
                                 ('foo:runtime',), ('group-core',),
                                 ('group-core:source',), ('group-dist',),
                                 ('group-dist-extras',), ('group-dist:source',),
                                 ('test',), ('test:devel',), ('test:runtime',),
                                 ('test:source',)])

        util.rmtree(csdir)

    def testCache(self):
        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0", filePrimer=1)
        self.addComponent("test:debuginfo", '1.0', filePrimer=2)
        trv = self.addCollection("test", "1.0", [ ":runtime", ":devel",
                                                 (':debuginfo', False)])

        client = conaryclient.ConaryClient(self.cfg)

        name, version, flavor = (trv.getName(), trv.getVersion(), trv.getFlavor())
        compNames = ['test:runtime']

        cacheName = gencslist._getCacheFilename(name, version, flavor, compNames)
        cachePath = self.workDir + '/' + cacheName


        repos = self.openRepository()
        csRequest = [(name, (None, None), (version, flavor), True)]
        csRequest += [ (x, (None, None), (version, flavor), True) for x in compNames ]

        repos.createChangeSetFile(csRequest, cachePath,
                                  recurse = False,
                                  primaryTroveList = [(name, version, flavor)])


        groupTrv = self.addCollection("group-dist", "1.0", [ "test" ] )
        groupChg = ('group-dist', (None, None), (groupTrv.getVersion(), groupTrv.getFlavor()), 0)
        group = client.createChangeSet([groupChg], withFiles=False,
                                       withFileContents=False,
                                       skipNotByDefault = False)
        assert(_validateChangeSet(cachePath, group, name, version, flavor, compNames))

        os.remove(cachePath)
        # test to make sure too large fails to validate
        tooLarge = csRequest + [('test:devel', (None, None), (version, flavor), True)]
        repos.createChangeSetFile(tooLarge,
                                  cachePath,
                                  recurse = False,
                                  primaryTroveList = [(name, version, flavor)])
        assert(not _validateChangeSet(cachePath, group, name, version, flavor, 
                                      compNames))

        tooSmall = list(csRequest)
        tooSmall.remove(('test:runtime', (None, None), (version, flavor), True))

        # test to make sure too small also fails to validate
        os.remove(cachePath)
        repos.createChangeSetFile(tooSmall,
                                  cachePath,
                                  recurse = False,
                                  primaryTroveList = [(name, version, flavor)])
        assert(not _validateChangeSet(cachePath, group, name, version, flavor, 
                                      compNames))

    def testAnacondaImages(self):
        util.mkdirChain(self.tmpDir + "/ai")
        ai = anaconda_images.AnacondaImages("Mint Test Suite",
            "../scripts/data/pixmaps/", self.tmpDir + "/ai/",
            "/usr/share/fonts/bitstream-vera/Vera.ttf")
        ai.processImages()

        sha1s = {
            'anaconda_header.png': '01b37e19cb4a6f7384fd08fe6a954dd9850f0e26',
            'first-lowres.png': '45f64c471e5f290698f3fccf1e64625b2080da36',
            'first.png': '1ce4a9fa599e1440eae0b4994ba896eec4999862',
            'progress_first-375.png': '9fcc14b1785c22a53e54e23cc55a15226b05ab80',
            'progress_first.png': '74d30f33a1d5c06c518631f8c04a62bb44ff0d05',
            'splash.png': 'd935e0a02547f0becbd6b3085ce4a965d067fec2',
            'syslinux-splash.png': '3880e3f18bec6580a7f338920c5492a296a3058c',
        }

        for f in os.listdir(self.tmpDir + "/ai/"):
            sha1 = sha1helper.sha1ToString(sha1helper.sha1FileBin(os.path.join(self.tmpDir, 'ai', f)))
            assert(sha1 == sha1s[f])

    def testAnacondaImagesOversizedText(self):
        util.mkdirChain(self.tmpDir + "/ai")
        ai = anaconda_images.AnacondaImages("This is a really long input string to force AnacondaImages to scale appropriately!",
            "../scripts/data/pixmaps/", self.tmpDir + "/ai/",
            "/usr/share/fonts/bitstream-vera/Vera.ttf")
        ai.processImages()

        sha1s = {
            'first-lowres.png': '6bbd85d7379a569beceaa3f00e651841601a6564',
            'anaconda_header.png': '3739d0588704367d285577bdec7114b7a2b4b482',
            'progress_first.png': 'd4c4d6087da670fc1739a874f7ef044318d57a0f',
            'syslinux-splash.png': 'b5aa477cf62ce570eb5a8a17c5d5e3f6717b1dc1',
            'first.png': '3b5aee9a37551c6889a568f7e2d639295c0f8ad2',
            'splash.png': '29931484c8f8bd5b9055aa88a9cbd0314183f573',
            'progress_first-375.png': '6031ba99c41d0d4874ef10d5aef600ba11b577dc'
        }

        sha1s = {
            'first-lowres.png': '37ef4561df8381dcb5b62b7056b2d3daf735ecfd',
            'anaconda_header.png': 'cdf8cad458a267132ad705ea6593d5c048286b63',
            'progress_first.png': '6d32bb69c5ff5b906247615d6b76ba9a883a82ab',
            'syslinux-splash.png': '38580822ca5bce41299bb64c175c412c4b1b25dd',
            'first.png': '4fd642626b6137dbc72665a0753b9bb2cea3a1ad',
            'splash.png': '6dcd8f068a95f625a7fcaa5d2b06e646455bbaa4',
            'progress_first-375.png': '072407829547b0640ba20626614d67b94b75ae9c'
        }

        for f in os.listdir(self.tmpDir + "/ai/"):
            sha1 = sha1helper.sha1ToString(sha1helper.sha1FileBin(os.path.join(self.tmpDir, 'ai', f)))
            assert(sha1 == sha1s[f])

    def testCloneTree(self):
        def mkfile(path, fileName, contents = ""):
            tmpFile = open(os.path.join(path, fileName), 'w')
            tmpFile.write(contents)
            tmpFile.close()

        def getContents(*args):
            tmpFile = open(os.path.join(*args))
            res = tmpFile.read()
            tmpFile.close()
            return res

        # prepare source dir
        srcDir = tempfile.mkdtemp()
        subDir = os.path.join(srcDir, 'subdir')
        os.mkdir(subDir)
        destDir = tempfile.mkdtemp()

        # stock some initial files in the source tree
        mkfile(srcDir, 'EULA', "Nobody expects the Spanish Inquisition!")
        mkfile(srcDir, 'LICENSE', "Tell him we've already got one.")
        mkfile(subDir, 'README', "None shall pass.")

        # now make a colliding dir
        os.mkdir(os.path.join(srcDir, 'collide'))
        os.mkdir(os.path.join(destDir, 'collide'))

        # and collide a file
        mkfile(destDir, 'LICENSE', "Spam, Spam, Spam, Spam...")

        try:
            splitdistro.lndir(srcDir, destDir)
            # ensure basic files were cloned
            assert(getContents(destDir, 'EULA') == getContents(srcDir, 'EULA'))

            # ensure initial contents were overwritten
            self.failIf(getContents(destDir, 'LICENSE') == \
                        getContents(srcDir, 'LICENSE'),
                        "File contents were illegally overridden.")

            # ensure sub directories were properly traversed
            assert(getContents(destDir, 'subdir', 'README') == \
                   "None shall pass.")
        finally:
            # clean up dirs
            util.rmtree(srcDir)
            util.rmtree(destDir)

    def testStoreUpdateJob(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        build = client.newBuild(projectId, "Test Build")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-1-1", "1#x86")
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        job = client.startImageJob(build.id)
        isocfg = self.writeIsoGenCfg()

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0",
            [("test:runtime", True)])

        iso = installable_iso.InstallableIso(client, isocfg, job, build, project)
        iso.callback = EmptyCallback()

        cclient = conaryclient.ConaryClient(project.getConaryConfig())
        uJob = iso._getUpdateJob(cclient, 'test')
        iso._storeUpdateJob(uJob)

        data = build.getDataDict()
        assert(data['test'] == 'test=/testproject.' + \
                MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1-1[]')

        # update and make sure the next getUpdateJob returns the older revision
        self.addComponent("test:runtime", "1.1")
        uJob = iso._getUpdateJob(cclient, "test")
        job = uJob.getPrimaryJobs().pop()
        assert(job == ('test', (None, None), (VFS('/testproject.' + \
                MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1-1'), Flavor('')), True))

        assert(not iso._getUpdateJob(cclient, "notfound"))

        # enforce blocked auxillary troves
        build.setDataValue("media-template", "NONE")
        assert(not iso._getUpdateJob(cclient, "media-template"))

    def testSameFilename(self):
        csdir = tempfile.mkdtemp(dir=self.workDir)
        savedCsdir = tempfile.mkdtemp(dir=self.workDir)
        try:
            client, userId = self.quickMintUser('foouser', 'foopass')
            projectId = self.newProject(client)
            project = client.getProject(projectId)
            name = 'sidebyside:runtime'
            verStr = "/testproject.%s@rpl:devel/1.0.0-1-1" % \
                     MINT_PROJECT_DOMAIN

            ver = versions.VersionFromString(verStr)
            self.addComponent(name, verStr, 'smp', filePrimer=0)
            self.addComponent(name, verStr, '!smp', filePrimer=1)
            self.addComponent(name, verStr, 'foo', filePrimer=1)
            t = self.addCollection('group-sidebyside', verStr,
                                   [('sidebyside:runtime', ver, 'smp'),
                                    ('sidebyside:runtime', ver, '!smp'),
                                    ('sidebyside:runtime', ver, 'foo')])
            n, v, f = t.getName(), t.getVersion(), t.getFlavor()

            cfg = conarycfg.ConaryConfiguration()
            cfg.dbPath = ':memory:'
            cfg.root = ':memory:'
            useSsl = not os.environ.get('MINT_TEST_NOSSL', 0)
            cfg.repositoryMap = {'testproject.%s' % MINT_PROJECT_DOMAIN :
                                 'http%s://%s.%s/repos/testproject/' % \
                                 (useSsl and 's' or '', self.mintCfg.hostName,
                                 self.mintCfg.projectDomainName)}
            cfg.initializeFlavors()
            client = conaryclient.ConaryClient(cfg)

            try:
                self.hideOutput()
                (cslist, groupcs), str = self.captureOutput(
                    gencslist.extractChangeSets,
                    client, cfg, csdir, n, v, f,
                    oldFiles = None, cacheDir = None)
            finally:
                self.showOutput()

            self.failIf([x.split()[0] for x in cslist if 'runtime' in x] != \
                        ['sidebyside:runtime-1.0.0-1-1-none.ccs',
                         'sidebyside:runtime-1.0.0-1-1-none2.ccs',
                         'sidebyside:runtime-1.0.0-1-1-none3.ccs'],
                        "changesets didn't get numbered one-up")

            savedCsDict = dict([(x.split()[3], x.split()[0]) for x \
                                in cslist if 'runtime' in x])
            for baseDir, dirs, files in os.walk(csdir):
                for file in files:
                    util.copyfile(os.path.join(baseDir, file),
                                  os.path.join(savedCsdir, file))

            verStr = "/testproject.%s@rpl:devel/1.0.0-1-2" % \
                     MINT_PROJECT_DOMAIN

            # repeat test but re-order the troves...
            t = self.addCollection('group-sidebyside', verStr,
                                   [('sidebyside:runtime', ver, 'foo'),
                                    ('sidebyside:runtime', ver, 'smp'),
                                    ('sidebyside:runtime', ver, '!smp')])
            n, v, f = t.getName(), t.getVersion(), t.getFlavor()

            try:
                self.hideOutput()
                (cslist, groupcs), str = self.captureOutput(
                    gencslist.extractChangeSets,
                    client, cfg, csdir, n, v, f,
                    oldFiles = None, cacheDir = None)
            finally:
                self.showOutput()

            for flav, trvfn in [(x.split()[3], x.split()[0]) for x \
                               in cslist if 'runtime' in x]:
                csA = changeset.ChangeSetFromFile(os.path.join(csdir, trvfn))
                trvA = [x for x in csA.iterNewTroveList()][0]
                csB = changeset.ChangeSetFromFile( \
                    os.path.join(savedCsdir, savedCsDict[flav]))
                trvB = [x for x in csB.iterNewTroveList()][0]
                self.failIf(trvA.newFlavor() != trvB.newFlavor(),
                            "gencslist missed reordering an old changeset")
        finally:
            util.rmtree(csdir)
            util.rmtree(savedCsdir)

    def getInstallableIso(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        isocfg = self.writeIsoGenCfg()
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        build.setTrove("group-dist", "/testproject." + \
            MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setDataValue("bugsUrl", "test")
        job = client.startImageJob(build.id)

        ii = installable_iso.InstallableIso(None, isocfg, job, build, project)
        ii.isocfg = isocfg
        ii.callback = EmptyCallback()
        ii._setupTrove()

        return ii


    def testAnacondaTemplates(self):
        if not os.path.exists("/sbin/mksquashfs"):
            raise testsuite.SkipTestException("squashfstools not installed, skipping this test")

        testDir = self.servers.getServer(0).getTestDir()
        templateDir = tempfile.mkdtemp()
        tmpDir = tempfile.mkdtemp()

        try:
            util.copytree(os.path.join(testDir, 'archive', 'anaconda'), tmpDir)
            ii = self.getInstallableIso()
            ii.isocfg = installable_iso.IsoConfig()
            ii.isocfg.rootstatWrapper = os.path.abspath(testDir + "../scripts/rootstat_wrapper.so")

            self.captureAllOutput(ii._makeTemplate, templateDir, tmpDir + '/anaconda', None, None)
            for f in 'cpiogz.out', 'cramfs.img', 'isofs.iso', 'squashfs.img':
                assert(os.stat(os.path.join(templateDir, f))[stat.ST_SIZE])
        finally:
            util.rmtree(templateDir)
            util.rmtree(tmpDir)

    def checkSha1(self, fileName, sum):
        assert(sha1helper.sha1ToString(sha1helper.sha1FileBin(fileName)) == sum)

    def testConvertSplash(self):
        testDir = self.servers.getServer(0).getTestDir()

        ii = self.getInstallableIso()

        d1 = tempfile.mkdtemp()
        d2 = tempfile.mkdtemp()

        self.hideOutput()
        try:
            util.mkdirChain(os.path.join(d1, 'isolinux'))
            util.mkdirChain(os.path.join(d2, 'pixmaps'))
            util.copyfile(os.path.join(testDir, 'archive', 'syslinux-splash.png'),
                          os.path.join(d2, 'pixmaps', 'syslinux-splash.png'))
            ii.convertSplash(d1, d2)

            result = os.path.join(d1, 'isolinux', 'splash.lss')
            self.checkSha1(result, 'b36af127d5336db0a39a9955cd44b3a8466aa048')
        finally:
            util.rmtree(d1)
            util.rmtree(d2)

    def testBuildStamp(self):
        ii = self.getInstallableIso()

        d = tempfile.mkdtemp()
        try:
            ii.writeBuildStamp(d)
            self.verifyContentsInFile(os.path.join(d, ".buildstamp"),
                "group-dist /testproject." + MINT_PROJECT_DOMAIN + 
                "@rpl:devel/1.0-1-1 1#x86")
        finally:
            util.rmtree(d)

    def testLinkRecurse(self):
        d1 = tempfile.mkdtemp()
        d2 = tempfile.mkdtemp()

        try:
            util.mkdirChain(d1 + "/bar")
            file(d1 + "/foo", "w").write("hello world")
            file(d1 + "/bar/baz", "w").write("goodbye world")

            installable_iso._linkRecurse(d1, d2)

            # make sure that linkRecurse recursively links files and dirs
            assert(os.path.exists(d2 + "/foo"))
            assert(os.path.exists(d2 + "/bar/baz"))
        finally:
            util.rmtree(d1)
            util.rmtree(d2)

    def testConaryClient(self):
        ii = self.getInstallableIso()

        # check the returned conary client cfg for sanity
        cc = ii.getConaryClient('/', '1#x86')
        assert(cc.cfg.installLabelPath == [versions.Label('testproject.' + MINT_PROJECT_DOMAIN + '@rpl:devel')])

    def testGetTemplatePath(self):
        ii = self.getInstallableIso()

        d = tempfile.mkdtemp()
        try:
            ii.isocfg.templatePath = d
            ii.isocfg.templatesLabel = "localhost@rpl:linux"

            self.addComponent("anaconda-templates:runtime", "1.0")
            tr = self.addCollection("anaconda-templates", "1.0",
                 [("anaconda-templates:runtime", True)])

            troveSpec = tr.getName() + '=' + str(tr.getVersion()) + '[' + \
                        str(tr.getFlavor()) + ']'
            # md5, actually
            sha1 = md5.md5(troveSpec).hexdigest()

            util.mkdirChain(os.path.join(d, sha1))

            path = ii._getTemplatePath()
            assert(path == os.path.join(d, sha1))
        finally:
            util.rmtree(d)


if __name__ == "__main__":
    testsuite.main()
