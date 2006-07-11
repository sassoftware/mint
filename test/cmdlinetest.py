#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
import os

import tempfile
import testsuite
import unittest
testsuite.setup()

import rephelp

from mint.cmdline import RBuilderMain, RBuilderShellConfig
from mint.cmdline import builds, users
from mint import buildtypes

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

class CmdLineTest(unittest.TestCase):
    def checkRBuilder(self, cmd, fn, expectedArgs, cfgValues={},
                  returnVal=None, ignoreKeywords=False, **expectedKw):
        main = RBuilderMain()
        cmd += ' --skip-default-config'

        cfgFd, cfgFn = tempfile.mkstemp()
        try:
            cfgF = os.fdopen(cfgFd, "w")
            # this value doesn't really matter--just needs to be a parseable url
            cfgF.write("serverUrl http://testuser:testpass@mint.rpath.local/xmlrpc-private/")
            cfgF.close()

            cmd += " --config-file=%s" % cfgFn
            return rephelp.RepositoryHelper.checkCommand(main.main, 'rbuilder ' + cmd, fn,
                                     expectedArgs, cfgValues, returnVal,
                                     ignoreKeywords, **expectedKw)
        finally:
            os.unlink(cfgFn)

    def testBuildCreate(self):
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        self.checkRBuilder('build-create testproject %s installable_iso' % troveSpec,
            'mint.cmdline.builds.BuildCreateCommand.runCommand',
            [None, None, None, {}, ['build-create', 'testproject', troveSpec, 'installable_iso']])

        self.checkRBuilder('build-create testproject %s installable_iso --wait' % troveSpec,
            'mint.cmdline.builds.BuildCreateCommand.runCommand',
            [None, None, None, {'wait': True}, ['build-create', 'testproject', troveSpec, 'installable_iso']])

    def testBuildWait(self):
        self.checkRBuilder('build-wait 111',
            'mint.cmdline.builds.BuildWaitCommand.runCommand',
            [None, None, None, {}, ['build-wait', '111']])

    def testReleaseUrl(self):
        self.checkRBuilder('release-url 111',
            'mint.cmdline.releases.ReleaseUrlCommand.runCommand',
            [None, None, None, {}, ['release-url', '111']])

    def testUserCreate(self):
        self.checkRBuilder('user-create testuser test@example.com --password password',
            'mint.cmdline.users.UserCreateCommand.runCommand',
            [None, None, None, {'password': 'password'}, ['user-create', 'testuser', 'test@example.com']])

    def testUserMembership(self):
            self.checkRBuilder('project-add testuser testproject developer',
                'mint.cmdline.users.UserMembershipCommand.runCommand',
                [None, None, None, {}, ['project-add', 'testuser', 'testproject', 'developer']])


class CmdLineFuncTest(MintRepositoryHelper):
    def testBuildCreate(self):
        client, userId = self.quickMintUser("test", "testpass")

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        cmd = builds.BuildCreateCommand()
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        cmd.runCommand(client, None, {}, ['build-create', 'testproject', troveSpec, 'installable_iso'])

        project = client.getProject(projectId)
        build = project.getBuilds()[0]
        assert(build.getTrove()[0] == 'group-test')
        assert(build.getJob())

    def testUserCreate(self):
        client, userId = self.quickMintAdmin("adminuser", "adminpass")

        cmd = users.UserCreateCommand()
        userId = cmd.runCommand(client, None, {'password': 'testpass'},
            ['user-create', 'testuser', 'test@example.com'])
        user = client.getUser(userId)
        assert(user.email == 'test@example.com')

    def testUserMembership(self):
        adminClient, userId = self.quickMintAdmin("adminuser", "adminpass")
        newProjectId = adminClient.newProject("testproject", "testproject",
            MINT_PROJECT_DOMAIN)

        client, userId = self.quickMintUser("testuser", "testpass")

        cmd = users.UserMembershipCommand()
        cmd.runCommand(adminClient, None, {}, ['project-add', 'testuser', 'testproject', 'owner'])
        cmd = users.UserCreateCommand()

        project = client.getProject(newProjectId)
        assert(project.getMembers() == [[1, 'adminuser', 0], [2, 'testuser', 0]])

    def testReleaseUrl(self):
        client, userId = self.quickMintAdmin("adminuser", "adminpass")
        cfg = RBuilderShellConfig(False)
        cfg.serverUrl = 'http://testuser:testpass@mint.rpath.local/xmlrpc-private/'

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)
        release = client.newRelease(projectId, 'release 1')
        release.setImageTypes([releasetypes.INSTALLABLE_ISO])
        release.setFiles([["file1", "File Title 1"],
                          ["file2", "File Title 2"]])

        cmd = releases.ReleaseUrlCommand()
        rc, res = self.captureOutput(cmd.runCommand, client, cfg, {}, ['release-url', release.id])

        assert(res == "http://mint.rpath.local//downloadImage/1/file1\n"
                      "http://mint.rpath.local//downloadImage/2/file2\n")


if __name__ == "__main__":
    testsuite.main()
