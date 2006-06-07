#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
import os

import testsuite
testsuite.setup()

import rephelp

from mint.cmdline import RBuilderMain
from mint.cmdline import releases

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

# if RepositoryHelper.checkCommand were a classmethod, this test
# wouldn't have to be a RepositoryHelper class and could be faster.
class CmdLineTest(rephelp.RepositoryHelper):
    def checkRBuilder(self, cmd, fn, expectedArgs, cfgValues={},
                  returnVal=None, ignoreKeywords=False, **expectedKw):
        main = RBuilderMain()
        cmd += ' --skip-default-config'

        return self.checkCommand(main.main, 'rbuilder ' + cmd, fn,
                                 expectedArgs, cfgValues, returnVal,
                                 ignoreKeywords, **expectedKw)

    def testReleaseCreate(self):
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        self.checkRBuilder('release-create testproject %s installable_iso' % troveSpec,
            'mint.cmdline.releases.ReleaseCreateCommand.runCommand',
            [None, None, None, {}, ['release-create', 'testproject', troveSpec, 'installable_iso']])

        self.checkRBuilder('release-create testproject %s installable_iso --wait' % troveSpec,
            'mint.cmdline.releases.ReleaseCreateCommand.runCommand',
            [None, None, None, {'wait': True}, ['release-create', 'testproject', troveSpec, 'installable_iso']])

    def testReleaseWait(self):
        self.checkRBuilder('release-wait 111',
            'mint.cmdline.releases.ReleaseWaitCommand.runCommand',
            [None, None, None, {}, ['release-wait', '111']])


class CmdLineFuncTest(MintRepositoryHelper):
    def testReleaseCreate(self):
        client, userId = self.quickMintUser("test", "testpass")

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        cmd = releases.ReleaseCreateCommand()
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        cmd.runCommand(client, None, {}, ['release-create', 'testproject', troveSpec, 'installable_iso'])

        project = client.getProject(projectId)
        release = project.getReleases(showUnpublished = True)[0]
        assert(release.getTrove()[0] == 'group-test')
        assert(release.getJob())


if __name__ == "__main__":
    testsuite.main()
