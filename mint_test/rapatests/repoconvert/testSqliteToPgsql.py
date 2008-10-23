#
# Copyright (C) 2006 rPath, Inc.
# All rights reserved.
#
import cherrypy
import tempfile
import os
from testrunner import resources

from conary.repository.netrepos.netserver import ServerConfig
from conary import dbstore
from conary.server import schema

import unittest
import raatest
import raa.crypto
import raa.service.lib
import raatest.service.tests.fakeclasses
from mintraatests import webPluginTest
from rPath.repoconvert.srv import repoconvert
import pgsql
import time
import types
import raa.db.schedule
from raa import constants, rpath_error
import raa.web
import testsuite
from testrunner import testhelp

from mint import config, projects
import mint_rephelp

class fakeCursor(object):
    _exec = []
    _fetchOneRet = 1
    def execute(s, *args):
        s._exec.append(*args)
    def fetchone(s):
        return  [s._fetchOneRet]
class fakeDbstore(object):
    def __init__(s, retval):
        s._retVal = retval
    def cursor(s):
        fcu = fakeCursor()
        fcu._fetchOneRet = s._retVal
        return fcu

class runCommandStub(object):
    commandList = []

    def __init__(self):
        self.commandList = []
    def clear(self):
        self.commandList = []
    def __call__(self, *args, **kwargs):
        self.commandList.append((args, kwargs))

def setupConfig(cfg):
    #Start with a directory
    topdir = tempfile.mkdtemp('', 'sqlitetopgsql-config-')
    # Then create the original file
    fd, fn = tempfile.mkstemp(dir=topdir)
    f = os.fdopen(fd, 'w')

    # The final file
    fd, genFn = tempfile.mkstemp(dir=topdir)
    os.close(fd)


    for x in ['reposDBDriver', 'reposDBPath', 'dbPath', 'dbDriver']:
        cfg.displayKey(x, out=f)
    f.write('includeConfigFile %s\n'% genFn)

    f.close()

    return topdir, fn, genFn

class SqliteToPgsqlTest(raatest.rAATest, mint_rephelp.MintRepositoryHelper):
    def __init__(self, *args, **kwargs):
        if testhelp._conaryDir is None:
            testhelp._conaryDir = os.getenv('CONARY_PATH')
        raatest.rAATest.__init__(self, *args, **kwargs)
        raa.service.lib.service = raatest.service.tests.fakeclasses.fakeServer()
        mint_rephelp.MintRepositoryHelper.__init__(self, *args, **kwargs)

    def setUp(self):
        raaFramework = webPluginTest()
        self.pseudoroot = raa.web.getWebRoot().repoconvert.SqliteToPgsql
        raatest.rAATest.setUp(self)
        mint_rephelp.MintRepositoryHelper.setUp(self)

        #Setup the configuration
        self.topdir, rbconfig, rbgenconfig = setupConfig(self.mintCfg)
        self.oldrbuider_config = config.RBUILDER_CONFIG
        self.oldrbuider_generated_config = config.RBUILDER_GENERATED_CONFIG
        config.RBUILDER_CONFIG = rbconfig
        config.RBUILDER_GENERATED_CONFIG = rbgenconfig

        #Stub out the srv constructor
        repoconvert.SqliteToPgsql.__init__ = lambda *args: None

        #Use our own runCommand
        self.oldRunCommand = raa.lib.command.runCommand
        raa.lib.command.runCommand = runCommandStub()
        self.srvPlugin = repoconvert.SqliteToPgsql()
        self.srvPlugin.server = self.pseudoroot

        #shim the backend call
        self.oldcallBackend = self.pseudoroot.callBackend
        self.pseudoroot.callBackend = lambda method, *args: \
            getattr(self.srvPlugin, method)(1, 1, *args)

    def tearDown(self):
        try:
            util.rmtree(self.topdir)
        except:
            pass
        config.RBUILDER_CONFIG = self.oldrbuider_config
        config.RBUILDER_GENERATED_CONFIG = self.oldrbuider_generated_config
        self.pseudoroot.callBackend = self.oldcallBackend
        raatest.rAATest.tearDown(self)
        mint_rephelp.MintRepositoryHelper.tearDown(self)
        raa.lib.command.runCommand = self.oldRunCommand

    def _writeConvertedConfig(self, cfgPath):
        f = open(cfgPath, 'w')
        f.write('reposDBDriver  postgresql\n')
        f.write('reposDBPath  NotUsed\n')
        f.close()

    def test_resetfinalized(self):
        #setup
        self._writeConvertedConfig(config.RBUILDER_GENERATED_CONFIG)
        ret = self.callWithIdent(self.pseudoroot.finalize, confirm=True)
        self.assertEquals(ret, {'message': 'Conversion finalized'})
        os.unlink(config.RBUILDER_GENERATED_CONFIG)

        #Do the test
        cfg = self.pseudoroot._getConfig()
        self.assertEquals(cfg['finalized'], False)

    def test_startPostgresql(self):
        class FailingDBStore:
            def connect(self, path, driver):
                raise pgsql.ProgrammingError('Fake')

        class WorkingDBStore:
            def __init__(self):
                self.path = self.driver = None
                self.commands = []
            def connect(self, path, driver):
                self.path, self.driver = path, driver
                return self
            def cursor(self):
                return self
            def execute(self, command):
                self.commands.append(command)

        def raiseErrorRunCommand(*x, **y):
            raise rpath_error.UnknownException('blah', 'blahblah')

        oldsleep = time.sleep
        time.sleep = lambda x: None
        try:
            # First, postgresql isn't running. Check if it is automatically
            # started.
            repoconvert.dbstore = FailingDBStore()
            self.assertRaises(repoconvert.PreparationError, repoconvert._startPostgresql)
            self.assertEquals(len(raa.lib.command.runCommand.commandList), 1)

            # Now, starting postgresql fails.
            _runCommand = raa.lib.command.runCommand
            raa.lib.command.runCommand = raiseErrorRunCommand
            try:
                self.assertRaises(rpath_error.UnknownException, repoconvert._startPostgresql)
            finally:
                raa.lib.command.runCommand = _runCommand

            # Finally, postgresql is already running
            raa.lib.command.runCommand.commandList=[]
            repoconvert.dbstore = WorkingDBStore()
            assert repoconvert._startPostgresql(), 'Did not return as expected'
            self.assertEquals(len(raa.lib.command.runCommand.commandList), 0)
            self.assertEquals(repoconvert.dbstore.driver, 'postgresql')
            self.assertEquals(repoconvert.dbstore.commands, ['CREATE LANGUAGE plpgsql'])

        finally:
            repoconvert.dbstore = dbstore
            time.sleep = oldsleep

    def test_getConfig(self):
        #Add two schedules, and start them
        sched = raa.db.schedule.ScheduleOnce()
        schedId1 = self.pseudoroot.schedule(sched)
        execId = raa.web.getWebRoot().execution.addExecution(schedId1, time.time(), status=constants.TASK_SCHEDULED)
        sched = raa.db.schedule.ScheduleOnce()
        schedId2 = self.pseudoroot.schedule(sched)
        execId = raa.web.getWebRoot().execution.addExecution(schedId2, time.time(), status=constants.TASK_RUNNING)

        cfg = self.pseudoroot._getConfig()
        self.assertEquals(cfg['running'], True)
        self.assertEquals(cfg['schedId'], schedId2)

    def test_method(self):
        "the index method should return a string called now"
        result = self.callWithIdent(self.pseudoroot.index)
        assert type(result) == types.DictType

    def test_finalize(self):
        res = self.callWithIdent(self.pseudoroot.finalize, False)
        assert res['error']
        res = self.callWithIdent(self.pseudoroot.finalize, True)
        assert res['message']
        self.assertEquals(True, self.pseudoroot.getPropertyValue('raa.hidden'))
        self.assertEquals(True, self.pseudoroot.getPropertyValue('FINALIZED'))

    def test_convert(self):
        res = self.callWithIdent(self.pseudoroot.convert, False)
        assert res['error']
        res = self.callWithIdent(self.pseudoroot.convert, True)
        assert res['schedId']

    def test_hideplugin(self):
        res = self.callWithIdent(self.pseudoroot.finalize, True)

        self.pseudoroot.initPlugin()
        self.assertEquals(self.pseudoroot.getPropertyValue('raa.hidden'), False)

        self._writeConvertedConfig(config.RBUILDER_GENERATED_CONFIG)

        #The already converted case
        self.pseudoroot.initPlugin()
        self.assertEquals(self.pseudoroot.getPropertyValue('raa.hidden'), True)

        #The fresh install case
        self.pseudoroot.deletePropertyValue('FINALIZED')
        self.pseudoroot.initPlugin()
        self.assertEquals(self.pseudoroot.getPropertyValue('raa.hidden'), True)

    def test_indextitle(self):
        "The mainpage should have the right title"
        self.requestWithIdent("/repoconvert/SqliteToPgsql/")
        assert "<title>postgresql conversion - index</title>" in cherrypy.response.body[0].lower()

        assert "convert to postgresql" in cherrypy.response.body[0].lower()

    def _setupConvertScript(self, exitCode=0):
        fd, self.srvPlugin.convertScript = tempfile.mkstemp('.sh', 'testdbconversion-', dir=self.topdir)
        os.write(fd, 
"""#!/bin/sh

echo Fake script to convert the database 1>&2
sleep 4
for x in {0..9}; do
    echo Numbered output $x
done
touch %s/scriptrun
exit %d
""" % (self.topdir, exitCode))
        os.close(fd)

        os.chmod(self.srvPlugin.convertScript, 0700)

    def test_getDBNames(self):
        client, userid = self.quickMintAdmin("admin", 'adminpass')
        projIds = []
        for x in 'a', 'b', 'c', 'd':
            projId = client.newProject('Appliance %s' % x, x, mint_rephelp.MINT_PROJECT_DOMAIN, appliance='no', shortname=x, version='1', prodtype='Component')
            projIds.append(projId)

        #get the projects
        repnamemap, dbNames=self.srvPlugin._getDBNames(self.mintCfg.dbPath, self.mintCfg.dbDriver)

        self.assertEquals(dbNames, ['%s.%s' % (x, mint_rephelp.MINT_PROJECT_DOMAIN) for x in ['a', 'b', 'c', 'd']])
        # TODO: Add external projects
        self.assertEquals(repnamemap, {})

    def test_srvDoTask(self):
        self._setupConvertScript()
        sched = raa.db.schedule.ScheduleOnce()
        schedId = self.pseudoroot.schedule(sched)
        execId = raa.web.getWebRoot().execution.addExecution(schedId, time.time(), status=constants.TASK_RUNNING)
        oldreportMessage = self.srvPlugin.reportMessage
        self.srvPlugin.reportMessage = runCommandStub()
        oldStartPgsql = repoconvert._startPostgresql
        repoconvert._startPostgresql = lambda: None
        oldCreateProject = self.srvPlugin._createNewProjectTable
        self.srvPlugin._createNewProjectTable = lambda x,y: None
        try:
            #Set up a user
            client, userid = self.quickMintAdmin("admin", 'adminpass')
            #And a project
            hostname = "nap0"
            projId = client.newProject('Not an appliance (%s)' % hostname, hostname,
                mint_rephelp.MINT_PROJECT_DOMAIN, appliance="no", shortname=hostname,
                version='5.4', prodtype='Component')
            hostname = "nap1"
            projId = client.newProject('Not an appliance (%s)' % hostname, hostname,
                mint_rephelp.MINT_PROJECT_DOMAIN, appliance="no", shortname=hostname,
                version='5.4', prodtype='Component')

            #now run the conversion
            self.srvPlugin.doTask(execId, schedId)
            #Check the results
            cmdList = [x[0][1] for x in self.srvPlugin.reportMessage.commandList]

            #check to see that stuff got run
            # Should have run both httpd stop and httpd start
            self.assertEqual(len(raa.lib.command.runCommand.commandList), 2)

            #TODO: Add tests for acceptance
            try:
                assert 'Shutting down httpd' in cmdList
                assert 'Checking that PostgreSQL is running, and if not, starting it' in cmdList
                assert 'Running database conversion script' in cmdList
                assert 'Migrating rBuilder Repositories to PostgreSQL...' in cmdList
                assert 'Converting nap0.%s repository' % mint_rephelp.MINT_PROJECT_DOMAIN in cmdList
                assert 'Conversion completed successfully for nap0.%s' % mint_rephelp.MINT_PROJECT_DOMAIN in cmdList
                assert 'Converting nap1.%s repository' % mint_rephelp.MINT_PROJECT_DOMAIN in cmdList
                assert 'Conversion completed successfully for nap1.%s' % mint_rephelp.MINT_PROJECT_DOMAIN in cmdList
                assert 'Saving new database configuration values' in cmdList
                assert 'Migration complete' in cmdList
                assert 'Starting httpd' in cmdList
            except AssertionError, e:
                assert False, str(e) + str(cmdList)

            #Check the new config
            mc = config.MintConfig()
            mc.read(config.RBUILDER_GENERATED_CONFIG)
            self.assertEqual(mc.reposDBDriver, 'postgresql')
            self.assertEqual(mc.reposDBPath, 'postgres@localhost.localdomain:5439/%s')
        finally:
            self.srvPlugin.reportMessage = oldreportMessage
            repoconvert._startPostgresql = oldStartPgsql
            self.srvPlugin._createNewProjectTable = oldCreateProject

testsuite.setup()
if __name__ == "__main__":
    testsuite.main()
