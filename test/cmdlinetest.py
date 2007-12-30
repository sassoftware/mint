#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
import os

import tempfile
import testsuite
import unittest
import mock
testsuite.setup()

import rephelp
from conary.lib import cfgtypes
from conary.deps import deps
from conary import versions

from mint.cmdline import RBuilderMain, RBuilderShellConfig
from mint.cmdline import builds, users, refs
from mint import buildtypes
from mint import client

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

class CmdLineTest(unittest.TestCase):
    def setUp(self):
        self.oldMintClientInit = client.MintClient.__init__
        client.MintClient.__init__ = lambda x, y: x

    def tearDown(self):
        client.MintClient.__init__ = self.oldMintClientInit

    def checkRBuilder(self, cmd, fn, expectedArgs, cfgValues={},
                  returnVal=None, ignoreKeywords=False, **expectedKw):
        main = RBuilderMain()

        cfgFd, cfgFn = tempfile.mkstemp()
        try:
            cfgF = os.fdopen(cfgFd, "w")
            cfgF.write("serverUrl http://testuser:testpass@test.rpath.local/xmlrpc-private/")
            cfgF.close()

            cmd += " --config-file=%s" % cfgFn
            return rephelp.RepositoryHelper.checkCommand(main.main, 'rbuilder ' + cmd, fn,
                                     expectedArgs, cfgValues, returnVal,
                                     ignoreKeywords, **expectedKw)
        finally:
            os.unlink(cfgFn)

    def testBadConfig(self):
        main = RBuilderMain()
        self.assertRaises(cfgtypes.CfgError, main.main, ['rbuilder', '--config-file=/tmp/doesnotexist', 'config'])

    def testBuildCreate(self):
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        self.checkRBuilder('build-create testproject %s installable_iso' % troveSpec,
            'mint.cmdline.builds.BuildCreateCommand.runCommand',
            [None, None, None, {}, ['build-create', 'testproject', troveSpec, 'installable_iso']])

        self.checkRBuilder('build-create testproject %s installable_iso --wait' % troveSpec,
            'mint.cmdline.builds.BuildCreateCommand.runCommand',
            [None, None, None, {'wait': True}, ['build-create', 'testproject', troveSpec, 'installable_iso']])

        self.checkRBuilder('build-create testproject %s installable_iso '
                           '--option "key val" --option "anotherkey anotherval"' % troveSpec,
            'mint.cmdline.builds.BuildCreateCommand.runCommand',
            [None, None, None, {'option': ['key val', 'anotherkey anotherval']},
            ['build-create', 'testproject', troveSpec, 'installable_iso']])

    def testBuildWait(self):
        self.checkRBuilder('build-wait 111',
            'mint.cmdline.builds.BuildWaitCommand.runCommand',
            [None, None, None, {}, ['build-wait', '111']])

    def testBuildUrl(self):
        self.checkRBuilder('build-url 111',
            'mint.cmdline.builds.BuildUrlCommand.runCommand',
            [None, None, None, {}, ['build-url', '111']])

    def testUserCreate(self):
        self.checkRBuilder('user-create testuser test@example.com --password password',
            'mint.cmdline.users.UserCreateCommand.runCommand',
            [None, None, None, {'password': 'password'}, ['user-create', 'testuser', 'test@example.com']])

    def testUserMembership(self):
        self.checkRBuilder('project-add testuser testproject developer',
            'mint.cmdline.users.UserMembershipCommand.runCommand',
            [None, None, None, {}, ['project-add', 'testuser', 'testproject', 'developer']])

    def testFindRefs(self):
        self.checkRBuilder('find-refs frobtrove',
            'mint.cmdline.refs.FindRefsCommand.runCommand',
            [None, None, None, {}, ['find-refs', 'frobtrove']])




class CmdLineFuncTest(MintRepositoryHelper):
    def testBuildCreateCMD(self):
        raise testsuite.SkipTestException("Un-logged internal server error")
        client, userId = self.quickMintUser("test", "testpass")

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        cmd = builds.BuildCreateCommand()
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        cmd.runCommand(client, None, {'option': ['bugsUrl thisisatest']},
            ['build-create', 'testproject', troveSpec, 'installable_iso'])

        project = client.getProject(projectId)
        build = client.getBuild(project.getBuilds()[0])
        assert(build.getTrove()[0] == 'group-test')
        assert(build.getJob())
        assert(build.getDataValue('bugsUrl') == 'thisisatest')

    def testBuildCreateCmdErrors(self):
        client, userId = self.quickMintUser("test", "testpass")

        cmd = builds.BuildCreateCommand()
        self.assertRaises(RuntimeError, cmd.runCommand, client, None, {},
            ['build-create', 'testproject', 'troveSpec', 'doesnotexist'])

        self.assertRaises(RuntimeError, cmd.runCommand, client, None,
            {'option': ['doesnotexist setting']},
            ['build-create', 'testproject', 'troveSpec', 'installable_iso'])

    def testUserCreateCMD(self):
        client, userId = self.quickMintAdmin("adminuser", "adminpass")

        cmd = users.UserCreateCommand()
        userId = cmd.runCommand(client, None, {'password': 'testpass'},
            ['user-create', 'testuser', 'test@example.com'])

    def testUserMembershipCMD(self):
        adminClient, userId = self.quickMintAdmin("adminuser", "adminpass")
        newProjectId = adminClient.newProject("testproject", "testproject",
            MINT_PROJECT_DOMAIN)

        client, userId = self.quickMintUser("testuser", "testpass")

        cmd = users.UserMembershipCommand()
        cmd.runCommand(adminClient, None, {}, ['project-add', 'testuser', 'testproject', 'owner'])
        cmd = users.UserCreateCommand()

        project = client.getProject(newProjectId)
        assert(project.getMembers() == [[1, 'adminuser', 0], [2, 'testuser', 0]])

    def testBuildUrlCMD(self):
        client, userId = self.quickMintAdmin("adminuser", "adminpass")
        cfg = RBuilderShellConfig(False)
        cfg.serverUrl = 'http://testuser:testpass@mint.rpath.local/xmlrpc-private/'

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)
        b = client.newBuild(projectId, 'build 1')
        b.setBuildType(buildtypes.INSTALLABLE_ISO)
        b.setFiles([["file1", "File Title 1"],
                          ["file2", "File Title 2"]])

        cmd = builds.BuildUrlCommand()
        rc, res = self.captureOutput(cmd.runCommand, client, cfg, {}, ['build-url', b.id])

        assert(res == "http://mint.rpath.local//downloadImage?fileId=1\n"
                      "http://mint.rpath.local//downloadImage?fileId=2\n")

    def testFindRefsCMD(self):
        cfg = RBuilderShellConfig(False)
        cfg.serverUrl = 'http://testuser:testpass@mint.rpath.local/xmlrpc-private/'

        c = mock.MockInstance(client.MintClient)
        c._mock.enableMethod("getTroveReferences")
        c._mock.enableMethod("getTroveDescendants")

        c.getTroveReferences = lambda *args: {
            1: [('alpha1', '/p1.rpath.local@rpl:linux//devel//qa/1.0-1-1', '')]}
        c.getTroveDescendants = lambda *args: {
            1: [('/p1.rpath.local@rpl:linux//devel//desc/1.0-1-1', '')]}

        cmd = refs.FindRefsCommand()
        cmd.findTrove = lambda nc, cc, n, v, f: (n, v and versions.VersionFromString("/conary.rpath.com@rpl:1/1.0-1-1") or None, deps.parseFlavor(''))

        rc, res = self.captureOutput(cmd.runCommand, c, cfg, {},
            ['find-refs', 'dummy=conary.rpath.com@rpl:1[]'])
        self.failUnless("Projects that include a reference" in res)

        rc, res = self.captureOutput(cmd.runCommand, c, cfg, {'flat-list': True},
            ['find-refs', 'dummy=conary.rpath.com@rpl:1[]'])
        self.failUnless("alpha1=/p1.rpath.local@rpl:linux//devel//qa/1.0-1-1[]" in res)
        self.failUnless("dummy=/p1.rpath.local@rpl:linux//devel//desc/1.0-1-1[]" in res)

        self.assertRaises(RuntimeError, cmd.runCommand, c, cfg, {},
            ['find-refs', 'dummy'])


if __name__ == "__main__":
    testsuite.main()
