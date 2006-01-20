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

from conary import conarycfg, conaryclient
from conary.repository import changeset
from conary.lib import util

from mint.distro import gencslist

class DistroTest(rephelp.RepositoryHelper):
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
        # gencslist currently talks to stderr, so captureOuput
        # here isn't very effective. we should consider logging
        # to stdout instead.
        # nasty hack: temporarily route stderr to devnull
        oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)
        try:
            (cslist, groupcs), str = self.captureOutput(
                gencslist.extractChangeSets,
                client, cfg, csdir, n, v, f,
                oldFiles = None, cacheDir = None)
        finally:
            #recover old fd
            os.dup2(oldFd, sys.stderr.fileno())
            os.close(oldFd)

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

if __name__ == "__main__":
    testsuite.main()
