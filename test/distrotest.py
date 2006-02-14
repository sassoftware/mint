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

from mint_rephelp import MintRepositoryHelper

from conary import conarycfg, conaryclient
from conary import versions
from conary.deps import deps
from conary.repository import changeset
from conary.lib import util

from mint.distro import gencslist
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


if __name__ == "__main__":
    testsuite.main()
