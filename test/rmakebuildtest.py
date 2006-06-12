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
        xml = rMakeBuild.getXML()
        xml = rMakeBuild.getXML('commit')
        cu = db.cursor()
        cu.execute("""SELECT status, statusMessage
                          FROM rMakeBuild
                          WHERE rMakeBuildId=?""",
                   rMakeBuild.id)
        status, statusMessage = cu.fetchone()

        self.failIf(status != 0, "status not reset")
        self.failIf(statusMessage != '', "statusMessage not reset")

    @fixtures.fixture("Full")
    def testCommitOrder(self, db, data):
        client = self.getClient('nobody')
        rMakeBuild = client.createrMakeBuild('foo')

        itemId = rMakeBuild.addTrove('foo', 'test.rpath.local@rpl:devel')
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
        cu.execute("""UPDATE rMakeBuild SET UUID=?, status=1
                          WHERE rMakeBuildId=?""",
                   32 * '0', rMakeBuild.id)
        db.commit()
        xml = rMakeBuild.getXML('commit')

        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuild.id)
        UUID = cu.fetchone()[0]

        self.failIf(UUID == (32 * '0'), "UUID was not cleared by getting XML")

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
        assert UUID in xml
        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>build</name><trove><troveName>foo</troveName><troveVersion>test.rpath.local@rpl:devel</troveVersion><troveFlavor></troveFlavor></trove></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, UUID)

    @fixtures.fixture("Full")
    def testCommitXML(self, db, data):
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

        xml = rMakeBuild.getXML('commit')
        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>commit</name></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, UUID)

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
        assert xml == "<rmake><version>1</version><buildConfig><option><name>includeConfigFile</name><value>http://%sconaryrc</value></option><option><name>subscribe</name><value>rBuilder xmlrpc http://%srmakesubscribe/%s</value></option><option><name>uuid</name><value>%s</value></option></buildConfig><command><name>stop</name></command></rmake>" % \
               (self.cfg.siteHost + self.cfg.basePath,
                self.cfg.siteHost + self.cfg.basePath, UUID, UUID)

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


if __name__ == "__main__":
    testsuite.main()
