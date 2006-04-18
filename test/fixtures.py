#
# Copyright (c) 2004-2006 rPath, Inc.
# All Rights Reserved
#
import inspect
import unittest
import tempfile
from mint_rephelp import MINT_PROJECT_DOMAIN
import os

from mint import shimclient
from mint import config
from mint import releasetypes
from mint.distro.flavors import stockFlavors
from mint.server import MintServer

from conary import dbstore
from conary.deps import deps
from conary.lib import util
import pwd

class FixtureCache(object):
    fixtures = {}
    authToken = ('testuser', 'testpass')

    def getDataDir(self):
        return '/tmp/mint-test-%s/' % pwd.getpwuid(os.getuid())[0]

    def loadFixture(self, key):
        name = 'fixture' + key
        if key not in self.fixtures:
            fixture = self.__getattribute__(name)
            self.fixtures[key] = fixture()
        try:
            util.rmtree(self.getDataDir())
        except OSError:
            pass

        return self.fixtures[key]

    def load(self, name):
        raise NotImplementedError

    def getMintCfg(self):
        raise NotImplementedError

    def stockReleaseFlavor(self, db, releaseId, arch = "x86_64"):
        cu = db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Releases set troveFlavor=? WHERE releaseId=?", flavor, releaseId)
        db.commit()

    def setUpUser(self, cfg, db):
        client = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        userId = client.registerNewUser('testuser', 'testpass', "Test User",
            "test@example.com", "test at example.com", "", active=True)

        cu = db.cursor()
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        db.commit()

    def fixtureEmpty(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        self.setUpUser(cfg, db)

        return cfg.dbPath, {}

    def fixtureRelease(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = MintServer(cfg, db, alwaysReload = True)
        client = shimclient.ShimMintClient(cfg, self.authToken)
        self.setUpUser(cfg, db)

        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")

        self.stockReleaseFlavor(db, release.id)

        return cfg.dbPath, {'projectId': projectId, 'releaseId': release.id}

    # job fixtures
    def fixtureCookJob(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = MintServer(cfg, db, alwaysReload = True)
        self.setUpUser(cfg, db)
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
        return cfg.dbPath, {}

    def fixtureImageJob(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = MintServer(cfg, db, alwaysReload = True)
        self.setUpUser(cfg, db)

        client = shimclient.ShimMintClient(cfg, self.authToken)

        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        self.stockReleaseFlavor(db, release.getId())

        relJob = client.startImageJob(release.getId())
        return cfg.dbPath, {}

    def fixtureBothJobs(self):
        cfg = self.getMintCfg()
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = MintServer(cfg, db, alwaysReload = True)
        self.setUpUser(cfg, db)

        client = shimclient.ShimMintClient(cfg, ('testuser', 'testpass'))
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        self.stockReleaseFlavor(db, release.getId())

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
        return cfg.dbPath, {}


class SqliteFixtureCache(FixtureCache):
    def getMintCfg(self):
        dataDir = self.getDataDir()
        cfg = config.MintConfig()
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'
        cfg.reposPath = dataDir + "/repos/"
        cfg.reposContentsDir = [dataDir + "/contents1/%s/", dataDir + "/contents2/%s/"]
        cfg.reposDBPath = dataDir + "/repos/%s/sqldb"
        cfg.reposDBDriver = "sqlite"

        cfg.dataPath = dataDir
        cfg.imagesPath = dataDir + '/images/'

        cfg.postCfg()

        tmp = tempfile.mktemp(prefix = 'fixture', suffix = '.sqlite')
        cfg.dbPath = tmp
        cfg.dbDriver = "sqlite"

        return cfg

    def load(self, name):
        dbPath, data = self.loadFixture(name)
        tmp = tempfile.mktemp(prefix = 'fixture', suffix = '.sqlite')
        util.copyfile(dbPath, tmp)
        return ((tmp, "sqlite"), data)

    def __del__(self):
        for f in self.fixtures.values():
            os.unlink(f[0])

class FixturedUnitTest(unittest.TestCase):
    def loadFixture(self, name):
        db, fixtureData = fixtureCache.load(name)

        self.cfg = fixtureCache.getMintCfg()
        self.cfg = config.MintConfig()
        self.cfg.authUser = 'mintauth'
        self.cfg.authPass = 'mintpass'
        self.cfg.postCfg()

        self.cfg.dbPath = db[0]
        self.cfg.dbDriver = db[1]
        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        client = shimclient.ShimMintClient(self.cfg, ('testuser', 'testpass'))

        self.imagePath = fixtureCache.getDataDir() + "/images/"
        util.mkdirChain(self.imagePath)
        return db, client, fixtureData

    def tearDown(self):
        try:
            util.rmtree(fixtureCache.getDataDir())
        except OSError:
            pass

fixtureCache = SqliteFixtureCache()
