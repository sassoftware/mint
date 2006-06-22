#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
from conary import versions
from mint import database
from mint import mint_error

from grouptrovetest import testRecipe

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

import conary.repository.errors as repo_errors
from mint.rmakeconstants import buildjob, buildtrove, currentApi

class FixturedrMakeBuildTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testCreation(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        assert(rMakeBuild.title == 'foo')

    @fixtures.fixture("Full")
    def testBadAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.getrMakeBuild, rMakeBuild.id)

    @fixtures.fixture("Full")
    def testDuplicateName(self, db, data):
        client = self.getClient('nobody')
        client.createrMakeBuild('foo')
        self.assertRaises(database.DuplicateItem,
                          client.createrMakeBuild, 'foo')

    @fixtures.fixture("Full")
    def testAddItem(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        cu = db.cursor()
        cu.execute("""SELECT trvName, trvLabel
                          FROM rMakeBuildItems
                          WHERE rMakeBuildId=?""", rMakeBuild.id)
        self.failIf([list(x) for x in cu.fetchall()] != \
                    [['foo', 'test.rpath.local@rpl:devel']],
                    "rMake Build trove not stored correctly")

    @fixtures.fixture("Full")
    def testDoubleAdd(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        self.assertRaises(database.DuplicateItem, rMakeBuild.addTrove,
                          'foo', 'test.rpath.local@rpl:devel')

    @fixtures.fixture("Full")
    def testAddMissingItemByProject(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        self.assertRaises(repo_errors.TroveNotFound,
                          rMakeBuild.addTroveByProject, 'foo', 'foo')

    @fixtures.fixture("Full")
    def testAddAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.server.addrMakeBuildTrove,rMakeBuild.id,
                          'foo', 'test.rpath.local')

    @fixtures.fixture("Full")
    def testAddByProjectAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.server.addrMakeBuildTrove,rMakeBuild.id,
                          'foo', 'foo')

    @fixtures.fixture("Full")
    def testDelAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.server.delrMakeBuildTrove, itemId)

    @fixtures.fixture("Full")
    def testDelItem(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        client.delrMakeBuildTrove(itemId)
        cu = db.cursor()
        cu.execute("""SELECT trvName, trvLabel
                          FROM rMakeBuildItems
                          WHERE rMakeBuildId=?""", rMakeBuild.id)
        self.failIf(cu.fetchall(), "rMake Build item not properly deleted")

    @fixtures.fixture("Full")
    def testDelItemAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound, client.delrMakeBuildTrove,
                          itemId)

    @fixtures.fixture("Full")
    def testUUID(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        xml = rMakeBuild.getXML()

        cu = db.cursor()
        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)

        UUID = cu.fetchone()[0]

        self.failIf(not UUID, "UUID was not set by getting XML")

    @fixtures.fixture("Full")
    def testStartStatus(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        xml = rMakeBuild.getXML()
        cu = db.cursor()
        cu.execute("""SELECT status, statusMessage
                          FROM rMakeBuild
                          WHERE rMakeBuildId=?""",
                   rMakeBuild.id)
        status, statusMessage = cu.fetchone()
        self.failIf(status == 0, "status not set")
        self.failIf(statusMessage == '', "statusMessage not set")

    @fixtures.fixture("Full")
    def testStopStatus(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        xml = rMakeBuild.getXML()
        xml = rMakeBuild.getXML('stop')
        cu = db.cursor()
        cu.execute("""SELECT status, statusMessage
                          FROM rMakeBuild
                          WHERE rMakeBuildId=?""",
                   rMakeBuild.id)
        status, statusMessage = cu.fetchone()

        self.failIf(status != 0, "status not reset")
        self.failIf(statusMessage != '', "statusMessage not reset")

    @fixtures.fixture("Full")
    def testCommitStatus(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET status=?, statusMessage='test'
                          WHERE rMakeBuildId=?""",
                   buildjob.JOB_STATE_BUILT, rMakeBuild.id)
        db.commit()
        xml = rMakeBuild.getXML('commit')

        cu.execute("""SELECT status, statusMessage
                          FROM rMakeBuild
                          WHERE rMakeBuildId=?""",
                   rMakeBuild.id)
        status, statusMessage = cu.fetchone()

        self.failIf(status != buildjob.JOB_STATE_COMMITTING,
                    "status was not set to committing")
        self.failIf(statusMessage != 'Waiting for rMake Server',
                    "statusMessage was not updated")

    @fixtures.fixture("Full")
    def testCommitTroveStatus(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET status=?, statusMessage='test'
                          WHERE rMakeBuildId=?""",
                   buildjob.JOB_STATE_BUILT, rMakeBuild.id)
        cu.execute("""UPDATE rMakeBuildItems SET status=?, statusMessage=?
                          WHERE rMakeBuildItemId=?""",
                   buildtrove.TROVE_STATE_BUILT, 'Trove Built', itemId)
        db.commit()
        xml = rMakeBuild.getXML('commit')

        cu.execute("""SELECT status, statusMessage
                          FROM rMakeBuildItems
                          WHERE rMakeBuildItemId=?""",
                   itemId)
        status, statusMessage = cu.fetchone()

        self.failIf(status != 0, "trove status not reset")
        self.failIf(statusMessage != '', "trove status message not reset")

    @fixtures.fixture("Full")
    def testCommitOrder(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        cu = db.cursor()

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        for status in (buildjob.JOB_STATE_FAILED, buildjob.JOB_STATE_INIT,
                       buildjob.JOB_STATE_QUEUED, buildjob.JOB_STATE_STARTED,
                       buildjob.JOB_STATE_BUILD, buildjob.JOB_STATE_COMMITTED):
            cu .execute("UPDATE rMakeBuild SET status=? WHERE rMakeBuildId=?",
                        status, rMakeBuild.id)
            db.commit()
            self.assertRaises(mint_error.rMakeBuildOrder,
                              rMakeBuild.getXML, 'commit')

    @fixtures.fixture("Full")
    def testStopOrder(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        self.assertRaises(mint_error.rMakeBuildOrder,
                          rMakeBuild.getXML, 'stop')

    @fixtures.fixture("Full")
    def testStopUUID(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=1
                          WHERE rMakeBuildId=?""",
                   32 * '0', rMakeBuild.id)
        db.commit()
        xml = rMakeBuild.getXML('stop')

        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        self.failIf(UUID == (32 * '0'), "UUID was not cleared by getting XML")

    @fixtures.fixture("Full")
    def testCommitUUID(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=?
                          WHERE rMakeBuildId=?""",
                   32 * '0', buildjob.JOB_STATE_BUILT, rMakeBuild.id)
        db.commit()
        xml = rMakeBuild.getXML('commit')

        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        self.failIf(UUID != (32 * '0'), "UUID was not cleared by getting XML")

    @fixtures.fixture("Full")
    def testDoubleBuild(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        xml = rMakeBuild.getXML()

        self.assertRaises(mint_error.rMakeBuildCollision, rMakeBuild.getXML)

    @fixtures.fixture("Full")
    def testEmptyBuild(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        self.assertRaises(mint_error.rMakeBuildEmpty, rMakeBuild.getXML)

    @fixtures.fixture("Full")
    def testBuildList(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        assert(rMakeBuild.listTroves() == [])

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        assert(rMakeBuild.listTroves() == [{'rMakeBuildItemId' : itemId,
                                            'rMakeBuildId' : rMakeBuild.id,
                                            'trvName' : trvName,
                                            'trvLabel' : trvLabel,
                                            'status' : 0,
                                            'statusMessage' : '',
                                            'shortHost': 'test'}])

    @fixtures.fixture("Full")
    def testBuildXML(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        assert(rMakeBuild.listTroves() == [])

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        xml = rMakeBuild.getXML()
        cu = db.cursor()
        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>subscribe</name><value>rBuilder apiVersion %d</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>build</name><trove><troveName>foo</troveName><troveVersion>test.rpath.local@rpl:devel</troveVersion><troveFlavor></troveFlavor></trove></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, currentApi, UUID)

    @fixtures.fixture("Full")
    def testCommitXML(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        assert(rMakeBuild.listTroves() == [])

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'
        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET status=?, UUID=?
                          WHERE rMakeBuildId=?""", buildjob.JOB_STATE_BUILT,
                   UUID, rMakeBuild.id)
        db.commit()

        xml = rMakeBuild.getXML('commit')
        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>subscribe</name><value>rBuilder apiVersion %d</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>commit</name></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, currentApi, UUID)

    @fixtures.fixture("Full")
    def testStopXML(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        assert(rMakeBuild.listTroves() == [])

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        xml = rMakeBuild.getXML()
        cu = db.cursor()
        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        xml = rMakeBuild.getXML('stop')
        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>subscribe</name><value>rBuilder apiVersion %d</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>stop</name></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, currentApi, UUID)

    @fixtures.fixture("Full")
    def testInvalidXML(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        self.assertRaises(mint_error.ParameterError, rMakeBuild.getXML,
                          'notavalidcommand')

    @fixtures.fixture("Full")
    def testXMLAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
        client = self.getClient('user')

        self.assertRaises(database.ItemNotFound,
                          client.server.getrMakeBuildXML, rMakeBuild.id,
                          'commit')

    @fixtures.fixture("Full")
    def testInvalidStatus(self, db, data):
        client = self.getClient('nobody')

        # ensure bogus UUIDS get silently ignored.
        assert (client.setrMakeBuildStatus(32 * '1', 1, 'foo') == True)

    @fixtures.fixture("Full")
    def testSetStatus(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        status = 0
        statusMessage = ''

        assert(rMakeBuild.status == status)
        assert(rMakeBuild.statusMessage == statusMessage)

        xml = rMakeBuild.getXML()
        cu = db.cursor()
        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        status = 1
        statusMessage = 'test'

        client.setrMakeBuildStatus(UUID, status, statusMessage)

        rMakeBuild.refresh()
        assert(rMakeBuild.status == status)
        assert(rMakeBuild.statusMessage == statusMessage)

    @fixtures.fixture("Full")
    def testDel(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')

        cu = db.cursor()
        cu.execute("SELECT * FROM rMakeBuildItems")
        assert(cu.fetchall())

        cu.execute("SELECT * FROM rMakeBuild")
        assert(cu.fetchall())

        rMakeBuild.delete()
        cu.execute("SELECT * FROM rMakeBuildItems")
        self.failIf(cu.fetchall(), "rMake Build's troves not deleted")

        cu.execute("SELECT * FROM rMakeBuild")
        self.failIf(cu.fetchall(), "rMake Build not deleted")

    @fixtures.fixture("Full")
    def testDelAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.server.delrMakeBuild, rMakeBuild.id)

    @fixtures.fixture("Full")
    def testListrMakeBuilds(self, db, data):
        client = self.getClient('nobody')
        assert(client.listrMakeBuilds() == [])
        rMakeBuild = client.createrMakeBuild('foo')
        assert [x.title for x in client.listrMakeBuilds()] == ['foo']
        rMakeBuild = client.createrMakeBuild('baz')
        assert [x.title for x in client.listrMakeBuilds()] == ['baz', 'foo']
        rMakeBuild = client.createrMakeBuild('bar')
        assert [x.title for x in client.listrMakeBuilds()] == \
               ['bar', 'baz', 'foo']

    @fixtures.fixture("Full")
    def testRename(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        assert(rMakeBuild.title == 'foo')
        rMakeBuild.rename('bar')
        rMakeBuild.refresh()
        assert(rMakeBuild.title == 'bar')

    @fixtures.fixture("Full")
    def testBadName(self, db, data):
        client = self.getClient('nobody')
        self.assertRaises(mint_error.ParameterError, client.createrMakeBuild,
                          'foo!')

    @fixtures.fixture("Full")
    def testBadReName(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        self.assertRaises(mint_error.ParameterError, rMakeBuild.rename, 'foo!')

    @fixtures.fixture("Full")
    def testgetTrove(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        itemDict = client.getrMakeBuildTrove(itemId)

        assert itemDict == {'status': 0,
                            'trvName': 'foo',
                            'rMakeBuildId': 1,
                            'shortHost': 'test',
                            'trvLabel': 'test.rpath.local@rpl:devel',
                            'rMakeBuildItemId': 1,
                            'statusMessage': ''}

    @fixtures.fixture("Full")
    def testGetTroveAccess(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        client = self.getClient('user')
        self.assertRaises(database.ItemNotFound,
                          client.getrMakeBuildTrove, itemId)

    @fixtures.fixture("Full")
    def testResetJobId(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET status=1, jobId=1")
        db.commit()
        xml = rMakeBuild.getXML('stop')

        cu.execute("SELECT jobId FROM rMakeBuild")
        self.failIf(cu.fetchone()[0] != None, "JobId was not reset with build")

    @fixtures.fixture("Full")
    def testResetBuildItems(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET status=1, jobId=1")
        cu.execute("UPDATE rMakeBuildItems SET status=1, statusMessage='foo'")
        db.commit()
        xml = rMakeBuild.getXML('stop')
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")
        res = cu.fetchone()
        self.failIf(res[0] != 0, "status of trove not reset")
        self.failIf(res[1] != '', "statusMessage of trove not reset")

    @fixtures.fixture("Full")
    def testResetBuildItems2(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET status=1, jobId=1, UUID=?", 32* '0')
        cu.execute("UPDATE rMakeBuildItems SET status=1, statusMessage='foo'")
        db.commit()
        rMakeBuild.resetStatus()
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")
        res = cu.fetchone()
        self.failIf(res[0] != 0, "status of trove not reset")
        self.failIf(res[1] != '', "statusMessage of trove not reset")

        cu.execute("SELECT status, statusMessage, jobId, UUID FROM rMakeBuild")
        res = [x for x in cu.fetchone()]
        self.failIf(res != [0, '', None, None], "rMake Build status not reset")

    @fixtures.fixture("Full")
    def testSetJobId(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        UUID = 32 * '0'
        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET UUID=?", UUID)
        db.commit()
        client.server.setrMakeBuildJobId(UUID, 14)
        rMakeBuild.refresh()
        self.failIf(rMakeBuild.jobId != 14, "Job ID was not updated")

    @fixtures.fixture("Full")
    def testTroveStatusUUID(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        UUID = 32 * '0'
        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET UUID=?", UUID)
        db.commit()

        client.server.setrMakeBuildTroveStatus(UUID, trvName, trvLabel,
                                               1, 'test')
        trvDict = rMakeBuild.listTroves()[0]
        self.failIf(trvDict['status'] != 1, "trove status not updated")
        self.failIf(trvDict['statusMessage'] != 'test',
                    "status message not updated")

    @fixtures.fixture("Full")
    def testTroveStatusBadUUID(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        UUID = 32 * '0'
        cu = db.cursor()
        cu.execute("UPDATE rMakeBuild SET UUID=?", UUID)
        db.commit()

        client.server.setrMakeBuildTroveStatus(32 * '1', trvName, trvLabel,
                                               1, 'test')
        trvDict = rMakeBuild.listTroves()[0]
        self.failIf(trvDict['status'] == 1, "trove status incorrectly updated")
        self.failIf(trvDict['statusMessage'] == 'test',
                    "status message incorrectly updated")

    @fixtures.fixture("Full")
    def testImproperDelete(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        rMakeBuild.getXML()

        self.assertRaises(mint_error.rMakeBuildOrder,
                          client.delrMakeBuildTrove, itemId)

    @fixtures.fixture("Full")
    def testImproperAdd(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)
        rMakeBuild.getXML()

        self.assertRaises(mint_error.rMakeBuildOrder,
                          rMakeBuild.addTrove, trvName + '1', trvLabel)

    @fixtures.fixture("Full")
    def testSourceAdd(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvLabel = 'test.rpath.local@rpl:devel'

        itemId = rMakeBuild.addTrove(trvName, trvLabel)

        self.failIf(rMakeBuild.listTroves()[0]['trvName'] != trvName,
                    "rMakeBuild added package name instead of source trove")

    @fixtures.fixture("Full")
    def testBadAdd(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:devel'
        trvLabel = 'test.rpath.local@rpl:devel'

        self.assertRaises(mint_error.ParameterError,
                          rMakeBuild.addTrove, trvName, trvLabel)

    @fixtures.fixture("Full")
    def testTroveSpanBuilds(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        rMakeBuild2 = client.createrMakeBuild('bar')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        # historical index incorrectly enforced uniqueness
        rMakeBuild2.addTrove(trvName, trvLabel)

    @fixtures.fixture("Full")
    def testTroveSpanBranches(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'
        trvLabel2 = 'test2.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        # ensure the same trove from two separate branches is legal
        rMakeBuild.addTrove(trvName, trvLabel2)

    @fixtures.fixture("Full")
    def testCommitReset(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=?
                          WHERE rMakeBuildId=?""",
                   (UUID, buildjob.JOB_STATE_COMMITTING, rMakeBuild.id))
        db.commit()

        client.server.setrMakeBuildStatus(UUID, buildjob.JOB_STATE_COMMITTED,
                                          'test message')
        rMakeBuild.refresh()

        self.failIf(rMakeBuild.status != buildjob.JOB_STATE_COMMITTED,
                    "status was not set by commit")

    @fixtures.fixture("Full")
    def testCommitCommitting(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=?
                          WHERE rMakeBuildId=?""",
                   (UUID, buildjob.JOB_STATE_COMMITTING, rMakeBuild.id))
        db.commit()

        client.server.setrMakeBuildStatus(UUID, buildjob.JOB_STATE_COMMITTING,
                                          'test message')

        xml = rMakeBuild.getXML('commit')

    @fixtures.fixture("Full")
    def testCommitBuilt(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=?
                          WHERE rMakeBuildId=?""",
                   (UUID, buildjob.JOB_STATE_BUILT, rMakeBuild.id))
        db.commit()

        client.server.setrMakeBuildStatus(UUID, buildjob.JOB_STATE_COMMITTING,
                                          'test message')

        xml = rMakeBuild.getXML('commit')

    @fixtures.fixture("Full")
    def testCollidingTrvs(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        rMakeBuild2 = client.createrMakeBuild('bar')
        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        rMakeBuild2.addTrove(trvName, trvLabel)

        UUID = 32 * '0'
        UUID2 = 32 * '1'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?
                          WHERE rMakeBuildId=?""",
                   (UUID, rMakeBuild.id))
        cu.execute("""UPDATE rMakeBuild SET UUID=?
                          WHERE rMakeBuildId=?""",
                   (UUID2, rMakeBuild2.id))
        db.commit()

        client.server.setrMakeBuildTroveStatus(UUID2, trvName, trvLabel, 1,
                                               'test')

        trv = rMakeBuild.listTroves()[0]

        self.failIf(trv['status'] != 0, "first job status is not 0")
        self.failIf(trv['statusMessage'] != '',
                    "first job statusMessage is not blank")

        trv = rMakeBuild2.listTroves()[0]

        self.failIf(trv['status'] != 1, 'second job status not set')
        self.failIf(trv['statusMessage'] != 'test',
                    'second job status message not set')

    @fixtures.fixture("Full")
    def testSrcStatusBySource(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?
                          WHERE rMakeBuildId=?""",
                   (UUID, rMakeBuild.id))
        db.commit()

        client.server.setrMakeBuildTroveStatus(UUID, trvName, trvLabel, 1,
                                               'test')

        trvDict = rMakeBuild.listTroves()[0]
        self.failIf(trvDict['status'] != 1,
                    "source trove not updated by component name")
        self.failIf(trvDict['statusMessage'] != 'test',
                    "source trove not updated by component name")

    @fixtures.fixture("Full")
    def testSrcStatusByPkg(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)

        UUID = 32 * '0'

        cu = db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=?
                          WHERE rMakeBuildId=?""",
                   (UUID, rMakeBuild.id))
        db.commit()

        client.server.setrMakeBuildTroveStatus(UUID, trvName.split(':')[0],
                                               trvLabel, 1, 'test')

        trvDict = rMakeBuild.listTroves()[0]
        self.failIf(trvDict['status'] != 1,
                    "source trove not updated by package name")
        self.failIf(trvDict['statusMessage'] != 'test',
                    "source trove not updated by package name")

    @fixtures.fixture("Full")
    def testCollidingAddSrc(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvName2 = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        self.assertRaises(database.DuplicateItem, rMakeBuild.addTrove,
                          trvName2, trvLabel)

    @fixtures.fixture("Full")
    def testCollidingAdd(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvName2 = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName2, trvLabel)
        self.assertRaises(database.DuplicateItem, rMakeBuild.addTrove,
                          trvName, trvLabel)

    @fixtures.fixture("Full")
    def testAddFullVer(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvName2 = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'
        trvVersion = '/test.rpath.local@rpl:devel/1.0.0-1-1'

        rMakeBuild.addTrove(trvName2, trvVersion)
        self.failIf(rMakeBuild.listTroves()[0]['trvLabel'] != trvLabel,
                    "Version string was not translated to a label")


    @fixtures.fixture("Full")
    def testAddFrozenVer(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')
        trvName = 'foo:source'
        trvName2 = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'
        trvVersion = '/test.rpath.local@rpl:devel/0.0:1.0.0-1-1'

        rMakeBuild.addTrove(trvName2, trvVersion)
        self.failIf(rMakeBuild.listTroves()[0]['trvLabel'] != trvLabel,
                    "Frozen version was not translated to a label")


class rMakeBuildTest(MintRepositoryHelper):
    def makeCookedTrove(self, branch = 'rpl:devel', hostname = 'testproject'):
        l = versions.Label("%s.%s@%s" % (hostname,
                                         MINT_PROJECT_DOMAIN, branch))
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l, ignoreDeps = True)

    def testAddItemByProject(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)

        rMakeBuild = client.createrMakeBuild('foo')

        self.makeCookedTrove('rpl:devel')

        rMakeBuild.addTroveByProject('testcase', 'testproject')

        cu = self.db.cursor()
        cu.execute("""SELECT trvName, trvLabel
                          FROM rMakeBuildItems
                          WHERE rMakeBuildId=?""", rMakeBuild.id)
        self.failIf([list(x) for x in cu.fetchall()] != \
                    [['testcase', 'testproject.rpath.local2@rpl:devel']],
                    "rMake Build trove not stored correctly")

    def testDoubleAddByProject(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        self.makeCookedTrove('rpl:devel')

        rMakeBuild.addTroveByProject('testcase', 'testproject')
        self.assertRaises(database.DuplicateItem,
                          rMakeBuild.addTroveByProject,
                          'testcase', 'testproject')

    def testAddSourceByProject(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        l = versions.Label("%s.%s@%s" % ('testproject',
                                         MINT_PROJECT_DOMAIN, 'rpl:devel'))

        self.makeSourceTrove("testcase", testRecipe, l)

        rMakeBuild.addTroveByProject('testcase:source', 'testproject')
        cu = self.db.cursor()
        cu.execute("""SELECT trvName, trvLabel
                          FROM rMakeBuildItems
                          WHERE rMakeBuildId=?""", rMakeBuild.id)
        self.failIf([list(x) for x in cu.fetchall()] != \
                    [['testcase:source',
                      'testproject.rpath.local2@rpl:devel']],
                    "rMake Build source component not stored correctly")

    def testDoubleAddSourceByProject(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        l = versions.Label("%s.%s@%s" % ('testproject',
                                         MINT_PROJECT_DOMAIN, 'rpl:devel'))

        self.makeSourceTrove("testcase", testRecipe, l)

        rMakeBuild.addTroveByProject('testcase:source', 'testproject')
        self.assertRaises(database.DuplicateItem,
                          rMakeBuild.addTroveByProject,
                          'testcase:source', 'testproject')


if __name__ == "__main__":
    testsuite.main()
