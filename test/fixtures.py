#
# Copyright (c) 2004-2006 rPath, Inc.
# All Rights Reserved
#
import copy
import inspect
import unittest
import tempfile
import mysqlharness
import random
import string
import subprocess
import os
import pwd

from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import shimclient
from mint import config
from mint import releasetypes
from mint.distro.flavors import stockFlavors
from mint import server

from conary import dbstore
from conary.deps import deps
from conary.lib import util

def stockReleaseFlavor(db, releaseId, arch = "x86_64"):
    cu = db.cursor()
    flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
    cu.execute("UPDATE Releases set troveFlavor=? WHERE releaseId=?", flavor, releaseId)
    db.commit()


class FixtureCache(object):
    _fixtures = {}
    authToken = ('testuser', 'testpass')

    def list(self):
        fixtureNames = [x for x in self.__class__.__base__.__dict__ \
                        if x.startswith('fixture')]
        return dict([(x.replace('fixture', ''),
                      self.__getattribute__(x).__doc__) for x in fixtureNames])

    def loadFixture(self, key):
        name = 'fixture' + key
        if key not in self._fixtures:
            fixture = self.__getattribute__(name)
            self._fixtures[key] = fixture(self.newMintCfg(key))
        return self._fixtures[key]

    def load(self, name):
        raise NotImplementedError

    def newMintCfg(self, name):
        cfg = config.MintConfig()
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'
        cfg.dataPath = tempfile.mkdtemp(prefix = "fixture%s" % name)
        cfg.reposPath = os.path.join(cfg.dataPath, 'repos')
        cfg.reposContentsDir = [os.path.join(cfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s')]
        cfg.imagesPath = os.path.join(cfg.dataPath, 'images')
        util.mkdirChain(cfg.imagesPath)
        cfg.sendNotificationEmails = False
        cfg.postCfg()
        return cfg

    def delRepos(self):
        raise NotImplementedError

    def createUser(self, cfg, db, username = 'testuser', password = 'testpass', fullname = 'Test User', email = 'test@example.com', blurb = 'test at example.com', isAdmin = False):
        client = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        userId = client.registerNewUser(username, password, fullname,
            email, blurb, "", active=True)

        if isAdmin:
            cu = db.cursor()
            cu.execute("""SELECT COUNT(*) FROM UserGroups
                              WHERE UserGroup = 'MintAdmin'""")
            if cu.fetchone()[0] == 0:
                cu.execute("""SELECT IFNULL(MAX(userGroupId) + 1, 1)
                                 FROM UserGroups""")
                groupId = cu.fetchone()[0]
                cu.execute("INSERT INTO UserGroups VALUES(?, 'MintAdmin')",
                           groupId)
                db.commit()
            else:
                cu.execute("""SELECT userGroupId FROM UserGroups
                                  WHERE UserGroup = 'MintAdmin'""")
                groupId = cu.fetchone()[0]

            cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                       groupId, userId)
            db.commit()

        return userId

    def fixtureEmpty(self, cfg):
        """Contains one user: ('testuser', 'testpass')"""
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        userId = self.createUser(cfg, db)

        return cfg, { 'userId': userId }

    def fixtureAdmin(self, cfg):
        """Contains one admin user: ('testuser', 'testpass')"""
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, ('testuser', 'testpass'))
        authUserId = self.createUser(cfg, db, username = 'testuser', password = 'testpass', isAdmin = True)

        return cfg, { 'authUserId': authUserId }

    def fixtureRelease(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        userId = self.createUser(cfg, db)

        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
        release = client.newRelease(projectId, "Test Release")

        stockReleaseFlavor(db, release.id)

        return cfg, {'userId': userId, 'projectId': projectId, 'releaseId': release.id}

    def fixtureMembers(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        userId = self.createUser(cfg, db)

        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)

        memberId = self.createUser(cfg, db, username = 'member', password = 'memberpass', fullname = 'Test Member', email = 'member@example.com', blurb = 'member at example.com')
        memberClient = shimclient.ShimMintClient(cfg, ('member', 'memberpass'))

        return cfg, {'userId': userId, 'memberId': memberId, 'projectId': projectId, 'memberClient': memberClient}

    def fixtureCookJob(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        userId = self.createUser(cfg, db)
        client = shimclient.ShimMintClient(cfg, self.authToken)

        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")
        return cfg, { 'userId': userId }

    def fixtureImageJob(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        userId = self.createUser(cfg, db)

        client = shimclient.ShimMintClient(cfg, self.authToken)

        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        stockReleaseFlavor(db, release.getId())

        relJob = client.startImageJob(release.getId())
        return cfg, { 'userId': userId }

    def fixtureBothJobs(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        userId = self.createUser(cfg, db)

        client = shimclient.ShimMintClient(cfg, ('testuser', 'testpass'))
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        stockReleaseFlavor(db, release.getId())

        relJob = client.startImageJob(release.getId())

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
            'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        db.commit()
        return cfg, { 'userId': userId }


class SqliteFixtureCache(FixtureCache):
    def newMintCfg(self, name):
        cfg = FixtureCache.newMintCfg(self, name)
        cfg.dbDriver = cfg.reposDBDriver = 'sqlite'
        cfg.dbPath = os.path.join(cfg.dataPath, 'mintdb')
        cfg.reposDBPath = os.path.join(cfg.dataPath, 'repos', '%s', 'sqldb')
        return cfg

    def load(self, name):
        cfg, data = self.loadFixture(name)

        # make a copy of the data directory and update the cfg
        testDataPath = tempfile.mkdtemp(prefix = "fixture%s" % name, suffix = '.copy')
        util.copytree(os.path.join(cfg.dataPath,'*'), testDataPath)
        testCfg = copy.deepcopy(cfg)
        testCfg.dataPath = testDataPath
        testCfg.dbPath = os.path.join(testCfg.dataPath, 'mintdb')
        testCfg.imagesPath = os.path.join(testCfg.dataPath, 'images')
        testCfg.reposContentsDir = [os.path.join(testCfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s')]
        testCfg.reposDBPath = os.path.join(testCfg.dataPath, 'repos', '%s', 'sqldb')
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')

        return testCfg, data

    def delRepos(self):
        pass # this space left intentionally blank

    def __del__(self):
        for f in self._fixtures.values():
            util.rmtree(f[0].dataPath)



class MySqlFixtureCache(FixtureCache, mysqlharness.MySqlHarness):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']
    db = None

    def __init__(self):
        mysqlharness.MySqlHarness.__init__(self)
        self.start()

    def _randomName(self):
        return "".join(random.sample(string.lowercase, 5))

    def _getConnectStringForDb(self, dbName = None):
        if dbName:
            return "root@localhost.localdomain:%d/%s" % (self.port, dbName)
        else:
            return "root@localhost.localdomain:%d/%%s" % self.port

    def _connect(self):
        if not self.db:
            self.db = dbstore.connect(self._getConnectStringForDb('mysql'), 'mysql')

    def _newDb(self, name):
        self._connect()
        cu = self.db.cursor()
        try:
            cu.execute("DROP DATABASE %s" % name)
        except:
            pass
        cu.execute("CREATE DATABASE %s" % name)
        self.db.commit()

    def _dropDb(self, name):
        self._connect()
        cu = self.db.cursor()
        cu.execute("DROP DATABASE %s" % name)
        self.db.commit()

    def _dupDb(self, srcDb, destDb):
        self._newDb(destDb)
        output = ["mysqldump", "-u", "root", "-S", "%s/socket" % self.dir, srcDb]
        input = ["mysql", "-u", "root", "-S", "%s/socket" % self.dir, destDb]
        dump = subprocess.Popen(output, stdout = subprocess.PIPE)
        load = subprocess.Popen(input, stdin = dump.stdout)
        load.communicate()

    def newMintCfg(self, name):
        cfg = FixtureCache.newMintCfg(self, name)
        dbName = "mf%s" % name
        self.keepDbs.append(dbName.lower())
        self._newDb(dbName)
        cfg.dbDriver = cfg.reposDBDriver = "mysql"
        cfg.dbPath = self._getConnectStringForDb(dbName)
        cfg.reposDBPath = self._getConnectStringForDb()
        return cfg

    def loadFixture(self, name):
        ret = FixtureCache.loadFixture(self, name)

        # save repos tables off for later
        self._connect()
        cu = self.db.cursor()
        cu.execute("SHOW DATABASES")
        for table in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            if '_' in table and not table.startswith('cr'):
                newName = "cr%s%s" % (name, table)
                self._dupDb(table, newName)
                self._dropDb(table)
                self.keepDbs.append(newName.lower())
        return ret

    def load(self, name):
        cfg, data = self.loadFixture(name)

        # get a random name for this particular instance of the fixture
        # in order to create unique copies
        randomDbName = self._randomName()

        # make a copy of the data directory and update the cfg
        testDataPath = tempfile.mkdtemp(prefix = "fixture%s" % name, suffix = '.copy')
        util.copytree(os.path.join(cfg.dataPath,'*'), testDataPath)
        testCfg = copy.deepcopy(cfg)
        testCfg.dataPath = testDataPath
        testCfg.imagesPath = os.path.join(testCfg.dataPath, 'images')
        testCfg.reposContentsDir = [os.path.join(testCfg.dataPath, 'contents1', '%s'), os.path.join(testCfg.dataPath, 'contents2', '%s')]
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')

        # restore the mint db into a unique copy
        fixtureMintDbName = "mf%s" % name
        fixtureCopyMintDbName = "cmf%s%s" % (name, randomDbName)
        self._dupDb(fixtureMintDbName, fixtureCopyMintDbName)
        testCfg.dbPath = self._getConnectStringForDb(fixtureCopyMintDbName)

        # restore the repos dbs
        self._connect()
        cu = self.db.cursor()
        cu.execute("SHOW DATABASES LIKE 'cr%s%%'" % name.lower())
        for table in [x[0] for x in cu.fetchall()]:
            fixtureCopyReposDbName = table[2+len(name):]
            self._dupDb(table, fixtureCopyReposDbName)

        return testCfg, data

    def delRepos(self):
        self._connect()
        cu = self.db.cursor()
        cu.execute("SHOW DATABASES")
        for table in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
           if '_' in table and not table.startswith('cr'):
               self._dropDb(table)

    def __del__(self):
        self.stop()


class FixturedUnitTest(unittest.TestCase):
    adminClient = None

    def listFixtures(self):
        return fixtureCache.list()

    def loadFixture(self, name):
        self.cfg, fixtureData = fixtureCache.load(name)

        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        server.dbConnection = None # reset the cached db connection
        client = shimclient.ShimMintClient(self.cfg, ('testuser', 'testpass'))

        return db, client, fixtureData

    def _getAdminClient(self):
        if not self.adminClient:
            self.adminClient = shimclient.ShimMintClient(self.cfg, ('mintauth', 'mintpass'))
        return self.adminClient

    def quickMintUser(self, username, password, email = "test@example.com"):
        client = self._getAdminClient()
        userId = client.registerNewUser(username, password, "Test User",
            email, "test at example.com", "", active=True)
        client = shimclient.ShimMintClient(self.cfg, (username, password))
        return client, userId

    def tearDown(self):
        try:
            fixtureCache.delRepos()
            util.rmtree(self.cfg.dataPath)
        except OSError:
            pass


driver = os.environ.get("CONARY_REPOS_DB", "sqlite")
if driver == "sqlite":
    fixtureCache = SqliteFixtureCache()
elif driver == "mysql":
    fixtureCache = MySqlFixtureCache()
else:
    raise RuntimeError, "Invalid database driver specified"

# test case decorator
def fixture(arg):
    def deco(func):
        def wrapper(self):
            db, client, data = self.loadFixture(arg)
            return func(self, db, client, data)
        wrapper.__name__ = func.__name__
        wrapper.__dict__.update(func.__dict__)
        return wrapper
    return deco
