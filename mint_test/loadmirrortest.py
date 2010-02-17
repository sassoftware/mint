#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import tempfile
import testsuite
import unittest
testsuite.setup()

from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN
from mint import helperfuncs
from mint.scripts import loadmirror
from mint.client import MintClient
from mint.projects import Project
from mint.config import MintConfig

import fixtures
from conary.lib import util

from testrunner import pathManager
from testutils import mock

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
        label = proj.getLabel()
        loader.client.addInboundMirror(proj.id, [label],
            "http://www.example.com/conary/",
            "userpass", "mirror", "mirrorpass")

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

            self.failUnlessEqual(loader.parseMirrorInfo('test.example.com'), 43)
        finally:
            util.rmtree(loader.sourceDir)


def makeMockCall(callLog, retCode):
    def r(cmd):
        callLog.append(cmd)
        return retCode
    return r

def makeMockPopen(source):
    def r(x, y):
        return open(source, "r")

    return r

class LoadMirrorUnitTest(unittest.TestCase):
    def setUp(self):
        # save stuff we're going to blow away
        self.oldPopen = os.popen
        self.oldCall = loadmirror.call

    def tearDown(self):
        os.popen = self.oldPopen
        loadmirror.call = self.oldCall

    def testGetMountPoints(self):
        points = loadmirror.getMountPoints(source = pathManager.getPath('MINT_ARCHIVE_PATH') + "/partitions")
        self.failUnlessEqual(['/dev/sda1'], points)

    def testGetFsLabel(self):
        os.popen = makeMockPopen(pathManager.getPath('MINT_ARCHIVE_PATH') + "/dumpe2fs")
        self.failUnlessEqual('MIRRORLOAD', loadmirror.getFsLabel(None))

    def testMounting(self):
        callLog = []
        loadmirror.call = makeMockCall(callLog, 0)

        loadmirror.unmountIfMounted("/dev/sda1", pathManager.getPath('MINT_ARCHIVE_PATH') + "/mounts")
        self.failUnlessEqual(callLog, ['umount /dev/sda1'])
        callLog.pop()

        loadmirror.mountTarget("/dev/sda1")
        self.failUnlessEqual(callLog, ['mount /dev/sda1 /mnt/mirror/'])

    def testMountMirrorLoadDrive(self):
        callLog = []
        loadmirror.call = makeMockCall(callLog, 0)
        os.popen = makeMockPopen(pathManager.getPath('MINT_ARCHIVE_PATH') + "/dumpe2fs")

        loadmirror.mountMirrorLoadDrive(
            partitions = pathManager.getPath('MINT_ARCHIVE_PATH') + "/partitions",
            mounts = pathManager.getPath('MINT_ARCHIVE_PATH') + "/mounts")
        self.failUnlessEqual(callLog, ['umount /dev/sda1', 'mount /dev/sda1 /mnt/mirror/'])

        self.assertRaises(loadmirror.NoMirrorLoadDiskFound,
            loadmirror.mountMirrorLoadDrive,
            partitions = pathManager.getPath('MINT_ARCHIVE_PATH') + "/partitions-missing",
            mounts = pathManager.getPath('MINT_ARCHIVE_PATH') + "/mounts")

    def createFile(self, fileName, contents = ''):
        f = open(fileName, "w")
        f.write(contents)
        f.close()

    def testCopyFiles(self):
        # heavily mocked test case for LoadMirror.copyFiles
        project = mock.MockInstance(Project)
        project._mock.set(id = 1, hostname = 'test')

        from conary.repository.netrepos import netserver
        oldNetworkRepositoryServer = netserver.NetworkRepositoryServer
        netserver.NetworkRepositoryServer = mock.MockObject()

        try:
            callback = loadmirror.Callback('test.rpath.local', 1)
            lm = loadmirror.LoadMirror(None, None)
            lm.cfg = MintConfig()
            mock.mockMethod(lm._addUsers)
            lm.cfg.namespace = 'yournamespace'
            lm.cfg.dataPath = tempfile.mkdtemp()
            lm.cfg.siteHost = 'test.rpath.local'
            lm.cfg.projectDomainName = 'rpath.local'

            lm.client = mock.MockObject(getLabelsForProject = lambda id: ({0: ('test.rpath.local', id)}, None, None, None))
            lm.sourceDir = tempfile.mkdtemp()

            util.mkdirChain(lm.sourceDir + '/test.rpath.local')
            self.createFile(lm.sourceDir + '/test.rpath.local/MIRROR-INFO')
            self.createFile(lm.sourceDir + '/test.rpath.local/sqldb', 'contents of testfile')

            # Skip failing chown calls to cut down on noise
            oldCall = loadmirror.call
            def call(cmd):
                if cmd.startswith('chown'):
                    return
                oldCall(cmd)
            loadmirror.call = call

            lm.copyFiles('test.rpath.local', project, callback = callback.callback)

        finally:
            # clean up
            util.rmtree(lm.cfg.dataPath)
            util.rmtree(lm.sourceDir)
            loadmirror.call = oldCall
            netserver.NetworkRepositoryServer = oldNetworkRepositoryServer


if __name__ == "__main__":
    testsuite.main()
