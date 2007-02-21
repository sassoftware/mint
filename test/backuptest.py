#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys
import os
import mock
import StringIO

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN, PFQDN

from mint import backup

from conary import dbstore
from conary.conaryclient import ConaryClient
from conary.lib import util

import fixtures

class BackupTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testBackup(self, db, data):

        if self.cfg.dbDriver != 'sqlite':
            raise testsuite.SkipTestException("Test only works on sqlite")

        client = self.getClient("admin")
        client.newExternalProject('External Project Not to be Backed Up',
                'externalproj', MINT_PROJECT_DOMAIN, 'foo.bar.baz@rpl:1',
                'http://foo.bar.baz/conary/')

        out = StringIO.StringIO()
        reposContentsDir = self.cfg.reposContentsDir.split(' ')[0]

        # create some directories we expect to be backed up
        for d in backup.staticPaths:
            p = os.path.join(self.cfg.dataPath, d)
            util.mkdirChain(p)

        # and a few that shouldn't be
        util.mkdirChain('ignoreme')

        oldUtilExecute = util.execute
        util.execute = mock.MockObject()

        oldUtilMkdirChain = util.mkdirChain
        util.mkdirChain= mock.MockObject()

        backup.backup(self.cfg, out)

        # spot check some things
        self.failUnless(os.path.join(self.cfg.dataPath, 'tmp', 'backup') \
                in out.getvalue())
        self.failUnless(os.path.join(self.cfg.dataPath, 'config') \
                in out.getvalue())
        self.failUnless(os.path.join(reposContentsDir % \
                'foo.' + MINT_PROJECT_DOMAIN) in out.getvalue())

        self.failIf(os.path.join(reposContentsDir % \
                'externalproj.' + MINT_PROJECT_DOMAIN) in out.getvalue())

        out.close()

        util.execute = oldUtilExecute
        util.mkdirChain = oldUtilMkdirChain


    @fixtures.fixture("Full")
    def testRestore(self, db, data):

        if self.cfg.dbDriver != 'sqlite':
            raise testsuite.SkipTestException("Test only works on sqlite")

        client = self.getClient("admin")
        client.newExternalProject('External Project Not to be Backed Up',
                'externalproj', MINT_PROJECT_DOMAIN, 'foo.bar.baz@rpl:1',
                'http://foo.bar.baz/conary/')

        mirroredId = client.newExternalProject('Mirrored project',
                'mirrored', MINT_PROJECT_DOMAIN, 'mirrored.bar.baz@rpl:1',
                'http://mirrored.bar.baz/conary/', mirror = True)
        project = client.getProject(mirroredId)
        labelId = project.getLabelIdMap().values()[0]
        project.editLabel(labelId, "mirrored.bar.baz@rpl:1",
            "http://localhost/repos/mirrored/", "mintauth", "mintpass")
        client.addInboundMirror(mirroredId, ['mirrored.bar.baz@rpl:1'],
            "http://mirrored.bar.baz/conary/", "mirror", "mirror")

        tosh = StringIO.StringIO()
        backup.backup(self.cfg, tosh)
        tosh.close()
        backup.restore(self.cfg)

        self.failUnless(os.path.exists(self.cfg.dbPath))

        # all restored projects are reverted to simple external projects
        self.failUnlessEqual(client.getInboundMirrors(), [])

        # make sure the url, user, and pass are preserved:
        self.failUnlessEqual(client.getLabelsForProject(mirroredId),
            ({'mirrored.bar.baz@rpl:1': mirroredId},
             {'mirrored.bar.baz': 'http://mirrored.bar.baz/conary/'}, # original URL, not the internal
             {'mirrored.bar.baz': ('mirror', 'mirror')})) # original user/pass, not internal

    @fixtures.fixture("Full")
    def testHandleException(self, db, data):

        def _tosscookies():
            raise Exception()

        oldStdErr = sys.stderr
        sys.stderr = StringIO.StringIO()

        oldSysExit = sys.exit
        sys.exit = mock.MockObject()

        backup.handle(_tosscookies)

        sys.stderr.close()
        sys.stderr = oldStdErr
        sys.exit = oldSysExit


    @fixtures.fixture("Full")
    def testRun(self, db, data):
        oldsetgid = os.setgid
        os.setgid = mock.MockObject()

        oldsetuid = os.setuid
        os.setuid = mock.MockObject()

        backup.run()

        os.setgid = oldsetgid
        os.setuid = oldsetuid


    @fixtures.fixture("Full")
    def testClean(self, db, data):

        tosh = StringIO.StringIO()
        backup.backup(self.cfg, tosh)
        tosh.close()
        backup.clean(self.cfg)

        self.failIf(os.path.exists(os.path.join(self.cfg.dataPath, 'tmp', 'backup')))


if __name__ == "__main__":
    testsuite.main()
