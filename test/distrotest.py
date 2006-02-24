#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import tempfile
import testsuite
testsuite.setup()
import rephelp

import os
import sys
import tempfile

from mint_rephelp import MintRepositoryHelper

from conary import conarycfg, conaryclient
from conary import versions
from conary.deps import deps
from conary.repository import changeset
from conary.lib import util
from conary import sqlite3

from mint.distro import gencslist, anaconda_images, splitdistro
from mint.distro.gencslist import _validateChangeSet

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

    def testUpdatedStockFlavors(self):
        from mint.distro.flavors import stockFlavors

        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = cfg.root = ":memory:"
        label = versions.Label('conary.rpath.com@rpl:1')

        repos = conaryclient.ConaryClient(cfg).getRepos()
        versionDict = repos.getTroveLeavesByLabel({'group-dist': {label: None}})['group-dist']
        latestVersion = None
        for version, flavorList in versionDict.iteritems():
            if latestVersion is None or version > latestVersion:
                latestVersion = version

        overrideDict = {'x86':      deps.parseFlavor('is: x86(~cmov, ~i486, ~i586, ~i686)'),
                        'x86_64':   deps.parseFlavor('is: x86(~i486, ~i586, ~i686) x86_64')}

        flavors = versionDict[latestVersion]
        for f in flavors:
            for arch in f.members[deps.DEP_CLASS_IS].members.keys():
                for flag in f.members[deps.DEP_CLASS_IS].members[arch].flags:
                    f.members[deps.DEP_CLASS_IS].members[arch].flags[flag] = deps.FLAG_SENSE_PREFERRED
        x86 = deps.parseFlavor(stockFlavors['1#x86'])
        x86_64 = deps.parseFlavor(stockFlavors['1#x86_64'])

        assert(deps.overrideFlavor(x86, overrideDict['x86']) in flavors)
        assert(deps.overrideFlavor(x86_64, overrideDict['x86_64']) in flavors)

    def testAnacondaImages(self):
        util.mkdirChain(self.tmpDir + "/ai")
        ai = anaconda_images.AnacondaImages("Mint Test Suite",
            "../scripts/data/pixmaps/", self.tmpDir + "/ai/",
            "/usr/share/fonts/bitstream-vera/Vera.ttf")
        ai.processImages()

        from conary.lib import sha1helper
        sha1s = {
            'first-lowres.png': '9806b35fb077a1971c67645cd1e316078ae5000d',
            'anaconda_header.png': '818d5c1f4e7838037ae91ad68ebd975a6c1fec46',
            'progress_first.png': '0f4ebf8f39c94b7e678e2a3a5aaddfa4685881de',
            'syslinux-splash.png': 'c187339e5f1e39059f8277f542525942b4005332',
            'first.png': 'e5c9f81694c4fe1d74efe4f26d9ea737b2ee283d',
            'splash.png': '7022e7e156ac253e772b06751a7670148e8ce851',
            'progress_first-375.png': '3a510f4d87259442389a78b7af434087fae4e178'
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

        from conary.lib import sha1helper
        sha1s = {
            'first-lowres.png':         '6bbd85d7379a569beceaa3f00e651841601a6564',
            'anaconda_header.png':      '3739d0588704367d285577bdec7114b7a2b4b482',
            'progress_first.png':       'd4c4d6087da670fc1739a874f7ef044318d57a0f',
            'syslinux-splash.png':      'b5aa477cf62ce570eb5a8a17c5d5e3f6717b1dc1',
            'first.png':                '3b5aee9a37551c6889a568f7e2d639295c0f8ad2',
            'splash.png':               '29931484c8f8bd5b9055aa88a9cbd0314183f573',
            'progress_first-375.png':   '6031ba99c41d0d4874ef10d5aef600ba11b577dc'
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

if __name__ == "__main__":
    testsuite.main()
