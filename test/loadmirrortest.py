#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#

import tempfile
import testsuite
import unittest
testsuite.setup()

from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN
from mint import loadmirror

import fixtures
from conary.lib import util

import sys
import os

class LoadMirrorFixturedTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testErrors(self, db, data):
        loader = loadmirror.LoadMirror(None, None)

        loader.client = self.getClient("admin")
        # fails due to no project
        self.assertRaises(RuntimeError, loader.findTargetProject, "doesnotexist")

        # fails properly because the project is internal
        self.assertRaises(RuntimeError, loader.findTargetProject, "foo." + MINT_PROJECT_DOMAIN)

        cu = db.cursor()
        cu.execute('UPDATE Projects SET external=1 WHERE projectId=?', data['projectId'])
        db.commit()

        proj = loader.findTargetProject("foo." + MINT_PROJECT_DOMAIN)
        self.failUnlessEqual(proj.id, data['projectId'])

        # mirror it
        loader.client.addInboundLabel(proj.id, proj.id,
            "http://www.example.com/conary/",
            "mirror", "mirrorpass")

        # fail since we're already mirrored
        self.assertRaises(RuntimeError, loader.findTargetProject, "foo." + MINT_PROJECT_DOMAIN)

    @fixtures.fixture("Full")
    def testParseMirrorInfo(self, db, data):
        loader = loadmirror.LoadMirror(None, None)

        loader.sourceDir = tempfile.mkdtemp()
        try:
            os.mkdir(loader.sourceDir + "/test.example.com")
            f = open(loader.sourceDir + "/test.example.com/MIRROR-INFO", "w")
            f.write("test.example.com\n0/0\n42\n")
            f.close()

            self.failUnlessEqual(loader.parseMirrorInfo('test.example.com'), 42)
        finally:
            util.rmtree(loader.sourceDir)


class LoadMirrorUnitTest(unittest.TestCase):
    def setUp(self):
        # find archiveDir
        for dir in sys.path:
            thisdir = os.path.normpath(os.sep.join((dir, 'archive')))
            if os.path.isdir(thisdir):
                self.archiveDir = thisdir
                break

    def testGetMountPoints(self):
        points = loadmirror.getMountPoints(source = self.archiveDir + "/partitions")
        self.failUnlessEqual(['/dev/sda1'], points)

    def testGetFsLabel(self):
        def mockPopen(path, mode):
            return open(self.archiveDir + "/dumpe2fs", "r")

        oldPopen = os.popen
        os.popen = mockPopen
        self.failUnlessEqual('MIRRORLOAD', loadmirror.getFsLabel(None))
        os.popen = oldPopen


if __name__ == "__main__":
    testsuite.main()
