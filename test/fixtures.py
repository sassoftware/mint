#
# Copyright (c) 2004-2006 rPath, Inc.
# All Rights Reserved
#
import inspect
import unittest
import tempfile
from mint_rephelp import MINT_PROJECT_DOMAIN
import mysqlharness
import random
import string
import subprocess
import os

from mint import shimclient
from mint import config
from mint import releasetypes
from mint.distro.flavors import stockFlavors
from mint import server

from conary import dbstore
from conary.deps import deps
from conary.lib import util
import pwd

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
            self._fixtures[key] = fixture()
        try:
            util.rmtree(getDataDir())
        except OSError:
            pass

        return self._fixtures[key]

    def load(self, name):
        raise NotImplementedError

    def getMintCfg(self):
        dataDir = getDataDir()
        cfg = config.MintConfig()
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'
        cfg.reposPath = dataDir + "/repos/"
        cfg.reposContentsDir = [dataDir + "/contents1/%s/", dataDir + "/contents2/%s/"]
        cfg.dataPath = dataDir
        cfg.imagesPath = dataDir + '/images/'
        cfg.sendNotificationEmails = False

        cfg.postCfg()
        return cfg

    def createUser(self, cfg, db, username = 'testuser', password = 'testpass', isAdmin = False):
        client = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        userId = client.registerNewUser(username, password, "Test User",
            "test@example.com", "test at example.com", "", active=True)

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

    def fixtureEmpty(self):
        """Contains one user: ('testuser', 'testpass')"""
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        userId = self.createUser(cfg, db)

        return cfg.dbPath, { 'userId': userId }

    def fixtureAdmin(self):
        """Contains one admin user: ('testuser', 'testpass')"""
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, ('testuser', 'testpass'))
        authUserId = self.createUser(cfg, db, username = 'testuser', password = 'testpass', isAdmin = True)

        return cfg.dbPath, { 'authUserId': authUserId }

    def fixtureRelease(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        userId = self.createUser(cfg, db)

        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")

        stockReleaseFlavor(db, release.id)

        return cfg.dbPath, {'userId': userId, 'projectId': projectId, 'releaseId': release.id}

    # job fixtures
    def fixtureCookJob(self):
        cfg = self.getMintCfg()
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
        return cfg.dbPath, { 'userId': userId }

    def fixtureImageJob(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        userId = self.createUser(cfg, db)

        client = shimclient.ShimMintClient(cfg, self.authToken)

        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        stockReleaseFlavor(db, release.getId())

        relJob = client.startImageJob(release.getId())
        return cfg.dbPath, { 'userId': userId }

    def fixtureBothJobs(self):
        cfg = self.getMintCfg()
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
        return cfg.dbPath, { 'userId': userId }


def getDataDir():
    return '/tmp/mint-test-%s/' % pwd.getpwuid(os.getuid())[0]

class SqliteFixtureCache(FixtureCache):
    def getMintCfg(self):
        cfg = FixtureCache.getMintCfg(self)
        tmp = tempfile.mktemp(prefix = 'fixture', suffix = '.sqlite')

        cfg.dbPath = tmp
        cfg.dbDriver = "sqlite"
        cfg.reposDBPath = cfg.dataPath + "/repos/%s/sqldb"
        cfg.reposDBDriver = "sqlite"

        return cfg

    def load(self, name):
        dbPath, data = self.loadFixture(name)
        tmp = tempfile.mktemp(prefix = 'fixture', suffix = '.sqlite')
        util.copyfile(dbPath, tmp)
        return ((tmp, "sqlite"), data)

    def __del__(self):
        for f in self._fixtures.values():
            os.unlink(f[0])


class MySqlFixtureCache(FixtureCache, mysqlharness.MySqlHarness):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']
    db = None

    def randomName(self):
        return "".join(random.sample(string.lowercase, 10))

    def __init__(self):
        mysqlharness.MySqlHarness.__init__(self)
        self.start()

    def _connect(self):
        if not self.db:
            self.db = dbstore.connect("root@localhost.localdomain:%d/mysql" % self.port, "mysql")

    def _newDb(self, name):
        self._connect()
        cu = self.db.cursor()
        cu.execute("CREATE DATABASE %s" % name)
        self.db.commit()

    def _dropDb(self, name):
        self._connect()
        cu = self.db.cursor()
        cu.execute("DROP DATABASE %s" % name)
        self.db.commit()

    def getMintCfg(self):
        cfg = FixtureCache.getMintCfg(self)

        newName = self.randomName()
        self._newDb(newName)
        cfg.dbPath = "root@localhost.localdomain:%d/%s" % (self.port, newName)
        cfg.dbDriver = "mysql"
        cfg.reposDBPath = "root@localhost.localdomain:%d/%%s" % self.port
        cfg.reposDBDriver = "mysql"

        return cfg

    def loadFixture(self, name):
        ret = FixtureCache.loadFixture(self, name)
        self._connect()

        # drop stray repository tables
        cu = self.db.cursor()
        cu.execute("SHOW DATABASES")
        for table in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            if '_' in table:
                self._dropDb(table)
        return ret

    def load(self, name):
        dbPath, data = self.loadFixture(name)
        dbName = dbPath.split("/")[1]

        newName = name + self.randomName()
        self._newDb(newName)
        output = ["mysqldump", "-u", "root", "-S", "%s/socket" % self.dir, dbName]
        input = ["mysql", "-u", "root", "-S", "%s/socket" % self.dir, newName]
        dump = subprocess.Popen(output, stdout = subprocess.PIPE)
        load = subprocess.Popen(input, stdin = dump.stdout)
        load.communicate()

        return (("root@localhost.localdomain:%d/%s" % (self.port, newName), "mysql"), data)

    def __del__(self):
        self.stop()


class FixturedUnitTest(unittest.TestCase):
    adminClient = None

    def listFixtures(self):
        return fixtureCache.list()

    def loadFixture(self, name):
        db, fixtureData = fixtureCache.load(name)

        self.cfg = fixtureCache.getMintCfg()

        self.cfg.dbPath = db[0]
        self.cfg.dbDriver = db[1]
        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        server.dbConnection = None # reset the cached db connection
        client = shimclient.ShimMintClient(self.cfg, ('testuser', 'testpass'))

        self.imagePath = getDataDir() + "/images/"
        util.mkdirChain(self.imagePath)
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
            util.rmtree(getDataDir())
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
