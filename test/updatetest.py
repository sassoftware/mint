#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()


import os, sys
import tempfile

from conary.lib import util

from mint import config
from mint import mint_update
from mint import maintenance

class UpgradePathTest(testsuite.TestCase):
    def setUp(self):
        self.commonPostCommands = mint_update.commonPostCommands
        mint_update.commonPostCommands = lambda *args, **kwargs: None
        tmpDir = tempfile.mkdtemp()
        rBuilderConfigPath = os.path.join(tmpDir, 'rbuilder.config')
        lockPath = os.path.join(tmpDir, 'lock')
        self.origConfigPath = config.RBUILDER_CONFIG
        config.RBUILDER_CONFIG = rBuilderConfigPath
        f = open(rBuilderConfigPath, 'w')
        f.write("maintenanceLockPath %s" % lockPath)
        f.close()
        self.tmpDir = tmpDir
        self.cfg = config.MintConfig()
        self.cfg.read(rBuilderConfigPath)

    def tearDown(self):
        util.rmtree(self.tmpDir)
        config.RBUILDER_CONFIG = self.origConfigPath
        mint_update.commonPostCommands = self.commonPostCommands

    def captureAllOutput(self, func, *args, **kwargs):
        oldErr = os.dup(sys.stderr.fileno())
        oldOut = os.dup(sys.stdout.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.dup2(fd, sys.stdout.fileno())
        os.close(fd)
        try:
            return func(*args, **kwargs)
        finally:
            os.dup2(oldErr, sys.stderr.fileno())
            os.dup2(oldOut, sys.stdout.fileno())

    def testMissingLineal(self):
        migrateTo_1 = mint_update.__dict__.get('migrateTo_1')
        migrateTo_2 = mint_update.__dict__.get('migrateTo_2')
        try:
            mint_update.migrateTo_1 = lambda *args, **kwargs: None
            if 'migrateTo_2' in mint_update.__dict__:
                del mint_update.migrateTo_2

            self.assertRaises(mint_update.SchemaMigrationError,
                    self.captureAllOutput, mint_update.handleUpdate, 0, 2)
        finally:
            if migrateTo_2:
                mint_update.migrateTo_2 = migrateTo_2
            mint_update.migrateTo_1 = migrateTo_1

    def testErrorLineal(self):
        migrateTo_1 = mint_update.__dict__.get('migrateTo_1')
        migrateTo_2 = mint_update.__dict__.get('migrateTo_2')
        try:
            mint_update.migrateTo_1 = lambda *args, **kwargs: None
            def rogueUpdate(*args, **kwargs):
                # we're testing to see that SchemaMigrationError is raised
                # for any error, so use a different one
                assert False, "forced error to alter codepath"
            mint_update.migrateTo_2 = rogueUpdate
            self.assertRaises(mint_update.SchemaMigrationError,
                    self.captureAllOutput, mint_update.handleUpdate, 0, 2)
        finally:
            if migrateTo_2:
                mint_update.migrateTo_2 = migrateTo_2
            mint_update.migrateTo_1 = migrateTo_1

    def testPostCommandsRunOnce(self):
        migrateTo_1 = mint_update.__dict__.get('migrateTo_1')
        migrateTo_2 = mint_update.__dict__.get('migrateTo_2')
        commonPostCommands = mint_update.commonPostCommands
        try:
            mint_update.migrateTo_1 = lambda *args, **kwargs: None
            mint_update.migrateTo_2 = lambda *args, **kwargs: None
            def MockPost(*args, **kwargs):
                self.postCount += 1
            self.postCount = 0
            mint_update.commonPostCommands = MockPost
            mint_update.handleUpdate(1, 2)
            self.failUnlessEqual(self.postCount, 1,
                    "commonPostCommands was not called exactly once")
        finally:
            if migrateTo_2:
                mint_update.migrateTo_2 = migrateTo_2
            mint_update.migrateTo_1 = migrateTo_1
            mint_update.commonPostCommands = commonPostCommands

    def testMainVersions(self):
        assert not os.getenv('CONARY_OLD_COMPATIBILITY_CLASS')
        assert not os.getenv('CONARY_NEW_COMPATIBILITY_CLASS')
        handleUpdate = mint_update.handleUpdate
        try:
            os.environ['CONARY_OLD_COMPATIBILITY_CLASS'] = '1'
            os.environ['CONARY_NEW_COMPATIBILITY_CLASS'] = '2'
            def mockUpdate(oldVer, newVer):
                self.versions = (oldVer, newVer)
            self.versions = None
            mint_update.handleUpdate = mockUpdate
            mint_update.postUpdate()
            self.failIf(self.versions != (1, 2),
                    "mint_update.postUpdate did not honor environment variables")
        finally:
            mint_update.handleUpdate = handleUpdate
            del os.environ['CONARY_OLD_COMPATIBILITY_CLASS']
            del os.environ['CONARY_NEW_COMPATIBILITY_CLASS']

    def testMainVersionOverride(self):
        handleUpdate = mint_update.handleUpdate
        try:
            def mockUpdate(oldVer, newVer):
                self.versions = (oldVer, newVer)
            self.versions = None
            mint_update.handleUpdate = mockUpdate
            mint_update.postUpdate(3, 4)
            self.failIf(self.versions != (3, 4),
                    "mint_update.postUpdate did not honor parameters")
        finally:
            mint_update.handleUpdate = handleUpdate

    def testMainVersionMissingOld(self):
        message = ''
        try:
            self.captureOutput(mint_update.postUpdate)
        except AssertionError, e:
            message = str(e)
        self.failIf(message != \
                'set environment variable CONARY_OLD_COMPATIBILITY_CLASS',
                'mint_update.postUpdate did not trap environment setting')

    def testMainVersionMissingNew(self):
        message = ''
        try:
            self.captureAllOutput(mint_update.postUpdate, 1)
        except AssertionError, e:
            message = str(e)
        self.failIf(message != \
                'set environment variable CONARY_NEW_COMPATIBILITY_CLASS',
                'mint_update.postUpdate did not trap environment setting')

    def testMaintModeBadExit(self):
        mode = maintenance.NORMAL_MODE
        try:
            self.captureAllOutput(mint_update.postUpdate)
        except:
            mode = maintenance.getMaintenanceMode(self.cfg)
        self.failIf(mode != maintenance.LOCKED_MODE,
                "update failure exited maintenace mode")

    def testMaintModeGoodExit(self):
        mode = maintenance.NORMAL_MODE
        handleUpdate = mint_update.handleUpdate
        try:
            mint_update.handleUpdate = lambda *args, **kwargs: None
            mint_update.postUpdate(3, 4)
        finally:
            mint_update.handleUpdate = handleUpdate
        self.failIf(mode != maintenance.NORMAL_MODE,
                "update success didn't exit maintenace mode")

    def testPreUpdate(self):
        mint_update.preUpdate()
        mode = maintenance.getMaintenanceMode(self.cfg)
        self.failIf(mode != maintenance.LOCKED_MODE,
                    "pre update did not set maintenace mode")

    def testMigrateAllRepositories(self):
        raise testsuite.SkipTestException('Fails in buildbot')
        execute = util.execute
        def MockExecute(cmd):
            self.commands.append(cmd)
        self.commands = []
        try:
            util.execute = MockExecute
            mint_update.migrateAllRepositories()
        finally:
            util.execute = execute
        file = os.path.split(self.commands.pop())[0]
        script = os.path.join(os.path.abspath( \
                './test').split()[0], 'scripts', file)
        self.failIf(not os.path.exists(script),
                "group script migration depends on a script " \
                        "that no longer exists: %s" % file)

    def testMigrationLineal1(self):
        migrateAllRepositories = mint_update.migrateAllRepositories
        def MockCall():
            self.called = True
        self.called = False
        try:
            mint_update.migrateAllRepositories = MockCall
            mint_update.migrateTo_1()
        finally:
            mint_update.migrateAllRepositories = migrateAllRepositories
        self.failIf(not self.called,
                "migration lineal 1 did not migrate repositories")

    def testPostCommands(self):
        execute = util.execute
        def MockExecute(cmd):
            self.commands.append(cmd)
        self.commands = []
        try:
            util.execute = MockExecute
            self.commonPostCommands()
        finally:
            util.execute = execute
        cmd = self.commands.pop()
        self.failIf(cmd != '/sbin/service sendmail start',
                "expected command to start sendmail")


if __name__ == "__main__":
    testsuite.main()
