#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


import sys
import os
import StringIO

from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import constants
from mint.lib import mintutils
from mint.scripts import backup

from conary import dbstore
from conary.conaryclient import ConaryClient
from conary.lib import util

from testutils import mock

import fixtures

goodMetadata = """
rBuilder_schemaVersion=37
NVF=group-rbuilder-dist=/products.rpath.com@rpath:rba-3/%s-1-1[is: x86]
""" % constants.mintVersion

badMetadata_oldSchema = """
rBuilder_schemaVersion=10
NVF=group-rbuilder-dist=/products.rpath.com@rpath:rba-3/%s-1-1[is: x86]
""" % constants.mintVersion

badMetadata_oldGroup = """
rBuilder_schemaVersion=37
NVF=group-rbuilder-dist=/products.rpath.com@rpath:rba-3/3.1.4-1-1[is: x86]
"""

badMetadata_mangledTrovespec= """
rBuilder_schemaVersion=37
NVF=group-rbuilder-dist=/products.rpath.coxxxxllxljfkldsmdrpath:rba-3/3.1.3-1-1[is: x86]
"""

metadataPattern = """
rBuilder_schemaVersion=37
NVF=group-rbuilder-dist=/products.rpath.com@rpath:rba-3/%s-1-1[is: x86]
"""

class BackupTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testBackup(self, db, data):

        if self.cfg.dbDriver != 'sqlite' or self.cfg.reposDBDriver != 'sqlite':
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

        # And touch some configs
        config_path = os.path.join(self.cfg.dataPath, 'config')
        util.mkdirChain(config_path)
        for file_name in ('rbuilder.conf', 'rbuilder-generated.conf'):
            open(os.path.join(config_path, file_name), 'w').close()

        oldUtilExecute = util.execute
        util.execute = mock.MockObject()

        oldUtilMkdirChain = util.mkdirChain
        util.mkdirChain= mock.MockObject()

        backup.backup(self.cfg, out)

        # spot check some things
        self.failUnless(os.path.join(self.cfg.dataPath, 'tmp', 'backup') \
                in out.getvalue())
        self.failUnless(os.path.join(self.cfg.dataPath, 'config/rbuilder-generated.conf') \
                in out.getvalue())
        self.failUnless(os.path.join(self.cfg.dataPath, 'config/rbuilder.conf') \
                not in out.getvalue())
        self.failUnless(os.path.join(reposContentsDir % \
                'foo.' + MINT_PROJECT_DOMAIN) in out.getvalue())

        self.failIf(os.path.join(reposContentsDir % \
                'externalproj.' + MINT_PROJECT_DOMAIN) in out.getvalue())

        out.close()

        util.execute = oldUtilExecute
        util.mkdirChain = oldUtilMkdirChain


    @fixtures.fixture("Full")
    def testRestore(self, db, data):

        if self.cfg.dbDriver != 'sqlite' or self.cfg.reposDBDriver != 'sqlite':
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
            "http://localhost/repos/mirrored/", "userpass", "mintauth",
            "mintpass", "")
        client.addInboundMirror(mirroredId, ['mirrored.bar.baz@rpl:1'],
            "http://mirrored.bar.baz/conary/", "userpass", "mirror", "mirror",
            "")

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
             [('mirrored.bar.baz', ('mirror', 'mirror'))], [])) # original user/pass, not internal

    @fixtures.fixture("Full")
    def testHandleException(self, db, data):

        def _tosscookies():
            raise Exception()

        oldStdErr = sys.stderr
        sys.stderr = StringIO.StringIO()

        oldSysExit = sys.exit
        sys.exit = mock.MockObject()

        backup.handle(_tosscookies, dropPriv=False)

        sys.stderr.close()
        sys.stderr = oldStdErr
        sys.exit = oldSysExit


    @fixtures.fixture("Full")
    def testRun(self, db, data):
        self.usageRan = False
        def newUsage():
            self.usageRan = True

        oldUsage = backup.usage
        oldSetup = mintutils.setupLogging
        try:
            backup.usage = newUsage
            mintutils.setupLogging = lambda *a, **b: None
            backup.run()
        finally:
            backup.usage = oldUsage
            mintutils.setupLogging = oldSetup

        self.failIf(not self.usageRan,
                "run method did not execute to completion")

    @fixtures.fixture("Full")
    def testClean(self, db, data):

        tosh = StringIO.StringIO()
        backup.backup(self.cfg, tosh)
        tosh.close()
        backup.clean(self.cfg)

        self.failIf(os.path.exists(os.path.join(self.cfg.dataPath, 'tmp', 'backup')))

    @fixtures.fixture("Full")
    def testPrerestore(self, db, data):

        out = StringIO.StringIO()
        self.cmds = []
        def fakeExecute(cmd):
            self.cmds.append(cmd)
        execute = util.execute
        try:
            util.execute = fakeExecute
            backup.prerestore(self.cfg)
        finally:
            util.execute = execute
        self.assertEquals (self.cmds, ["service httpd stop",
            "service pgbouncer stop"])

    @fixtures.fixture("Empty")
    def testIsValid_GoodMetadata(self, db, data):
        metadataIO = StringIO.StringIO(goodMetadata)
        valid = backup.isValid(self.cfg, metadataIO)
        self.failUnless(valid, "Metadata was invalid; check mint.scripts.backup.knownGroupVersions")

    @fixtures.fixture("Empty")
    def testIsValid_BadMetadata_OldSchema(self, db, data):
        metadataIO = StringIO.StringIO(badMetadata_oldSchema)
        valid = backup.isValid(self.cfg, metadataIO)
        self.failIf(valid, "Schema is too old, test should have failed")

    @fixtures.fixture("Empty")
    def testIsValid_BadMetadata_OldGroup(self, db, data):
        metadataIO = StringIO.StringIO(badMetadata_oldGroup)
        valid = backup.isValid(self.cfg, metadataIO)
        self.failIf(valid, "Group is too old, test should have failed")

    @fixtures.fixture("Empty")
    def testIsValid_BadMetadata_MangledSpec(self, db, data):
        metadataIO = StringIO.StringIO(badMetadata_mangledTrovespec)
        valid = backup.isValid(self.cfg, metadataIO)
        self.failIf(valid, "Group was malformed, test should have failed")

    @fixtures.fixture("Empty")
    def testIsValid_MissingMetadata(self, db, data):
        metadataIO = StringIO.StringIO()
        valid = backup.isValid(self.cfg, metadataIO)
        self.failIf(valid, "Metadata was missing, test should have failed")

    @fixtures.fixture("Empty")
    def testKnownGoodVersions(self, db, data):
        shouldPass = ('3.1.5', '3.1.5.1', '3.1.6', '3.1.7', '3.1.8',
                      '3.1.9', '3.1.10', '3.1.11', '3.1.12', '3.1.13',
                      '3.1.14', '3.1.15', '4.0.2', '4.1.0', '4.9.9')

        shouldFail = ('3.1.0', '2.0.0', '3.1.1', '3.1.2', '3.1.3',
                      '3.1.4', '1.6.3')

        for x in shouldPass:
            gvs = metadataPattern % x
            mIO = StringIO.StringIO(gvs)
            self.failUnless(backup.isValid(self.cfg, mIO),
                    "Version %s was expected to be a known good version" % x)

        for x in shouldFail:
            gvs = metadataPattern % x
            mIO = StringIO.StringIO(gvs)
            self.failIf(backup.isValid(self.cfg, mIO),
                    "Version %s isn't supposed to be a known good version" % x)

    def tearDown(self):
        if os.path.isdir('ignoreme'):
            util.rmtree('ignoreme')

