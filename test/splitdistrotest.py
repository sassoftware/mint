#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os

from mint.distro import splitdistro
import tempfile
from conary.lib import util

import fixtures

ISOBLOCK_SIZE = 2048

class SplitDistroTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Empty')
    def testSpaceUsed(self, db, data):
        tmpdir = tempfile.mkdtemp()
        try:
            assert splitdistro.spaceused(tmpdir, ISOBLOCK_SIZE) == 0
            for blocks, fn in [(x + 1, os.path.join(tmpdir, str(x))) \
                               for x in range(10)]:
                f = open(fn, 'w')
                f.write('a')
                f.close()
                assert splitdistro.spaceused(tmpdir, ISOBLOCK_SIZE) == \
                       ISOBLOCK_SIZE * blocks
                assert splitdistro.spaceused(fn, ISOBLOCK_SIZE) == 2048
        finally:
            util.rmtree(tmpdir)

    @fixtures.fixture('Empty')
    def testPrepareDir(self, db, data):
        unified = tempfile.mkdtemp()
        f = open(os.path.join(unified, 'README'), 'w')
        f.close()
        util.mkdirChain(os.path.join(unified, 'media-template', 'all'))
        path = tempfile.mkdtemp()
        f = open(os.path.join(path, 'junk'), 'w')
        f.close()
        csdir = 'foo/changesets'
        try:
            self.captureAllOutput(splitdistro.preparedir, unified, path, csdir)
            dirList = os.listdir(path)
            assert 'junk' not in dirList, \
                   "Cruft from last run present"
            assert 'README' in dirList, 'common files not imported'
            assert 'foo' in dirList, 'missing changeset directory'
            assert os.listdir(os.path.join(path, 'foo')) == ['changesets']
        finally:
            for dir in (unified, path, csdir):
                try:
                    util.rmtree(dir)
                except:
                    pass

    @fixtures.fixture('Empty')
    def testWriteDiscInfo(self, db, data):
        tmpdir = tempfile.mkdtemp()
        try:
            splitdistro.writediscinfo(tmpdir, 1, 6 * ['a'])
            f = open(os.path.join(tmpdir, '.discinfo'))
            assert f.read() == 'a\na\na\n1\na\na\n'
        finally:
            util.rmtree(tmpdir)

    @fixtures.fixture('Empty')
    def testLnDir(self, db, data):
        tmpdir = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()

        try:
            for sub in ('a', 'b', 'c'):
                subdir = os.path.join(tmpdir, sub)
                os.mkdir(subdir)
            for dir in (tmpdir, subdir):
                for fn in [os.path.join(dir, str(x)) for x in range(10)]:
                    f = open(fn, 'w')
                    f.close()
            os.mkdir(os.path.join(tmpdir2, 'c'))

            splitdistro.lndir(tmpdir, tmpdir2, excludes = ['b', '9'])

            assert sorted(os.listdir(tmpdir2)) == \
                   ['0', '1', '2', '3', '4', '5', '6', '7', '8', 'a', 'c']
            assert sorted(os.listdir(os.path.join(tmpdir2, 'c'))) == \
                   ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        finally:
            util.rmtree(tmpdir)
            util.rmtree(tmpdir2)

    @fixtures.fixture('Empty')
    def testLnDirModes(self, db, data):
        tmpdir = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        try:
            for dir in (tmpdir, tmpdir2):
                os.mkdir(os.path.join(dir, 'b'))
                f = open(os.path.join(dir, 'b', 'a'), 'w')
                f.close()
                os.chmod(os.path.join(dir, 'b', 'a'), 0)
                os.chmod(os.path.join(dir, 'b'), 0500)
            splitdistro.lndir(tmpdir, tmpdir2)
        finally:
            for dir in (tmpdir, tmpdir2):
                self.captureAllOutput(util.rmtree, dir)

    @fixtures.fixture('Empty')
    def testLnDirErr(self, db, data):
        tmpdir = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        try:
            os.mkdir(os.path.join(tmpdir, 'b'))
            f = open(os.path.join(tmpdir, 'b', 'a'), 'w')
            f.close()
            os.chmod(tmpdir2, 0)
            self.assertRaises(OSError, splitdistro.lndir, tmpdir, tmpdir2)
        finally:
            for dir in (tmpdir, tmpdir2):
                try:
                    self.captureAllOutput(util.rmtree, dir)
                except:
                    pass


if __name__ == "__main__":
    testsuite.main()
