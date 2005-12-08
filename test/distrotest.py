#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import tempfile
import testsuite
testsuite.setup()
import rephelp

from conary import conarycfg, conaryclient
from conary.lib import util

from mint.distro import gencslist

class DistroTest(rephelp.RepositoryHelper):
    def testGencslist(self):
        self.addQuickTestComponent("test:runtime", "1.0-1-1")
        self.addQuickTestCollection("test", "1.0-1-1",
                                    [ "test:runtime" ])
        t = self.addQuickTestCollection("group-foo", "1.0-1-1",
                                    [ ("test", "1.0-1-1") ])
        
        n, v, f = t.getName(), t.getVersion(), t.getFlavor()

        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.repositoryMap = self.servers.getServer().getMap()
        cfg.initializeFlavors()
        client = conaryclient.ConaryClient(cfg)

        csdir = tempfile.mkdtemp()
        # gencslist currently talks to stderr, so captureOuput
        # here isn't very effective. we should consider logging
        # to stdout instead.
        (cslist, groupcs), str = self.captureOutput(
                gencslist.extractChangeSets,
                client, cfg, csdir, n, v, f,
                oldFiles = None, cacheDir = None)
        util.rmtree(csdir)

        assert(cslist == ['test-1.0-1-1-none.ccs test /127.0.0.1@rpl:linux/1.0-1-1 none 1',
                          'group-foo-1.0-1-1-none.ccs group-foo /127.0.0.1@rpl:linux/1.0-1-1 none 1'])


if __name__ == "__main__":
    testsuite.main()
