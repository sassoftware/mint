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

from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN

from mint import shimclient
from mint import config
from mint import buildtypes
from mint.distro.flavors import stockFlavors
from mint import server
from mint import userlevels

from conary import dbstore
from conary.deps import deps
from conary.lib import util

def stockBuildFlavor(db, buildId, arch = "x86_64"):
    cu = db.cursor()
    flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
    cu.execute("UPDATE Builds set troveFlavor=? WHERE buildId=?", flavor, buildId)
    db.commit()


class FixtureCache(object):
    _fixtures = {}

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
        cfg.hostName = MINT_HOST
        cfg.projectDomainName = MINT_PROJECT_DOMAIN
        cfg.externalDomainName = MINT_DOMAIN
        cfg.secureHostName = "%s.%s" % (MINT_HOST, MINT_PROJECT_DOMAIN)
        cfg.dataPath = tempfile.mkdtemp(prefix = "fixture%s" % name)
        cfg.reposPath = os.path.join(cfg.dataPath, 'repos')
        cfg.reposContentsDir = "%s %s" % (os.path.join(cfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s'))
        cfg.imagesPath = os.path.join(cfg.dataPath, 'images')
        util.mkdirChain(cfg.imagesPath)
        cfg.sendNotificationEmails = False
        cfg.conaryRcFile = os.path.join(cfg.dataPath, 'run', 'conaryrc')
        util.mkdirChain(os.path.join(cfg.dataPath, 'run'))
        util.mkdirChain(os.path.join(cfg.dataPath, 'tmp'))

        cfg.reposLog = False
        f = open(cfg.conaryRcFile, 'w')
        f.close()
        cfg.postCfg()
        return cfg

    def delRepos(self):
        raise NotImplementedError

    def createUser(self, cfg, db, username, isAdmin = False):
        """
        Creates a user named "username" filled with the following data:
        password -> "<username>pass"
        fullname -> "A User Named <username>"
        email    -> "<username>@example.com"
        contactInfo -> "<username> at example.com"

        If isAdmin is True, then the user will be given admin privileges.

        Returns the user id of the user.
        """

        client = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        assert(username)
        password = "%spass" % username
        fullname = "A User Named %s" % username
        email = "%s@example.com" % username
        contactInfo = "%s at example.com" % username

        userId = client.registerNewUser(username, password, fullname,
            email, contactInfo, "", active=True)

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
        """
        Empty fixture. Should be used when you want a (mostly) blank setup
        for testing.

        Creates the following setup:
            - Two users:
                - test (a basic user with no special privileges)
                - admin (a user wih admin privileges)

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
                - C{admin} - the id of the user "admin"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)

        testId = self.createUser(cfg, db, "test")
        adminId = self.createUser(cfg, db, "admin", isAdmin=True)

        return cfg, { 'test': testId, 'admin': adminId }

    def fixtureFull(self, cfg):
        """
        Full (featured) fixture. This fixture should be good enough for
        90% of the tests written and should be used UNLESS the absence of
        data provided by this fixture is needed.

        Creates the following setup:
            - One project called "foo"
            - Six users
                - admin (a user with admin privileges)
                - owner (who owns the "foo" project)
                - developer (who is a developer in the "foo" project)
                - user (a user or watcher of the "foo" project
                - nobody (a user with no allegiance to any project)
            - Two published release objects
                - One publishd, or published, containing one build
                - One not publishd, containing another build
            - Three builds inside the "foo" project:
                - one published (i.e. belongs to the published release)
                - one unpublished (belongs to a release not yet published)
                - one available (not belonging to any release)
        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
                - C{user} - the id of the user "user"
                - C{admin} - the id of the user "admin"
                - C{owner} - the id of the user "owner"
                - C{developer} - the id of the user "developer"
                - C{nobody} - the id of the user "nobody"
                - C{projectId} - the id of the "Foo" project
                - C{buildId} - the id of the build in the "Foo" project
        """

        # connect to the database and open a MintServer instance
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)

        # create the users
        adminId = self.createUser(cfg, db, username = "admin", isAdmin = True)
        ownerId = self.createUser(cfg, db, username = "owner")
        developerId = self.createUser(cfg, db, username = "developer")
        userId = self.createUser(cfg, db, username = "user")
        nobodyId = self.createUser(cfg, db, username = "nobody")

        # create the project
        client = shimclient.ShimMintClient(cfg, ("owner", "ownerpass"))
        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)

        # add the developer
        project.addMemberById(developerId, userlevels.DEVELOPER)

        # add the watcher
        # (note: you have to use a separate client with the watcher's
        # credentials to add the watcher)
        userClient = shimclient.ShimMintClient(cfg, ("user", "userpass"))
        userProject = userClient.getProject(projectId)
        userProject.addMemberById(userId, userlevels.USER)

        # create a build for the "foo" project called "Test Build"
        # and add it to an unpublished (not final) release
        build = client.newBuild(projectId, "Test Build")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, build.id)
        pubRelease = client.newPublishedRelease(projectId)
        pubRelease.name = "(Not final) Release"
        pubRelease.version = "1.1"
        pubRelease.addBuild(build.id)
        pubRelease.save()

        # create another build for the "foo" project and publish it
        # i.e. make it a part of a published release
        pubBuild = client.newBuild(projectId, "Test Published Build")
        pubBuild.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-1", "1#x86")
        pubBuild.setBuildType(buildtypes.STUB_IMAGE)
        pubBuild.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, pubBuild.id)
        pubReleaseFinal = client.newPublishedRelease(projectId)
        pubReleaseFinal.name = "Published Release"
        pubReleaseFinal.version = "1.0"
        pubReleaseFinal.addBuild(pubBuild.id)
        pubReleaseFinal.save()
        pubReleaseFinal.publish()

        # Create another build that just lies around somewhere
        # unattached to any published releases
        anotherBuild = client.newBuild(projectId, "Test Extra Build")
        anotherBuild.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-2", "1#x86")
        anotherBuild.setBuildType(buildtypes.STUB_IMAGE)
        anotherBuild.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, anotherBuild.id)

        # create a group trove for the "foo" project
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
            'No Description', False)

        return cfg, { 'projectId':      projectId,
                      'admin':          adminId,
                      'owner':          ownerId,
                      'developer':      developerId,
                      'user':           userId,
                      'nobody':         nobodyId,
                      'buildId':        build.id,
                      'pubBuildId':     pubBuild.id,
                      'pubReleaseId':   pubRelease.id,
                      'pubReleaseFinalId':   pubReleaseFinal.id,
                      'anotherBuildId': anotherBuild.id,
                      'groupTroveId':   groupTrove.id }


    def fixtureCookJob(self, cfg):
        """
        CookJob fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A build called "Test Build"
                - A group trove called "testtrove"
                - A single group trove cook job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)

        userId = self.createUser(cfg, db, 'test')
        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))

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
        """
        ImageJob fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A build called "Test Build"
                - A single image job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)
        testId = self.createUser(cfg, db, 'test')

        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))

        projectId = client.newProject("Foo", "foo", "rpath.org")

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)

        stockBuildFlavor(db, build.getId())

        prodJob = client.startImageJob(build.getId())
        return cfg, { 'test': testId }

    def fixtureBothJobs(self, cfg):
        """
        BothJobs fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A group trove called "testtrove"
                - A build called "Test Build"
                - A single image job, in the "started" state
                - A single group trove cook job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        ms = server.MintServer(cfg, db, alwaysReload = True)

        testId = self.createUser(cfg, db, 'test')

        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))
        projectId = client.newProject("Foo", "foo", "rpath.org")

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)

        stockBuildFlavor(db, build.getId())

        prodJob = client.startImageJob(build.getId())

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
        return cfg, { 'test': testId }


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
        testCfg.reposContentsDir = "%s %s" % (os.path.join(testCfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s'))
        testCfg.reposDBPath = os.path.join(testCfg.dataPath, 'repos', '%s', 'sqldb')
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')
        testCfg.conaryRcFile = os.path.join(testCfg.dataPath, 'run', 'conaryrc')

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
        testCfg.conaryRcFile = os.path.join(testCfg.dataPath, 'run', 'conaryrc')

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
    cfg = None

    def listFixtures(self):
        return fixtureCache.list()

    def loadFixture(self, name):
        """
        Loads the fixture for the unit test.
        @param name: the name of the fixture (e.g. "Full")
        @returns: A 3-typle consisting of a database connection,
           a Mint client with admin credentials, and a dictionary of 
           fixture data (may be empty).
        """

        self.cfg, fixtureData = fixtureCache.load(name)
        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        server.dbConnection = None # reset the cached db connection

        return db, fixtureData

    def _getAdminClient(self):
        if not self.adminClient:
            self.adminClient = shimclient.ShimMintClient(self.cfg, ('mintauth', 'mintpass'))
        return self.adminClient

    def getClient(self, username):
        if username == 'anonymous':
            password = 'anonymous'
        else:
            password = '%spass' % username
        return shimclient.ShimMintClient(self.cfg, (username, password))

    def quickMintUser(self, username, password, email = "test@example.com"):
        client = self._getAdminClient()
        userId = client.registerNewUser(username, password, "Test User",
            email, "test at example.com", "", active=True)
        client = shimclient.ShimMintClient(self.cfg, (username, password))
        return client, userId

    def getMirrorAcl(self, project, username):
        """
        Given a project and a username, will determine whether or not the
        user has the ability to mirror.
        @param project: the project to check against
        @param username: the user whose credentials should be checked
        @returns: C{True} if C{username} can mirror C{project}; C{False}
            otherwise.
        """
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT canMirror
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN UserGroups ON UserGroups.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=?""", username)

        try:
            # nonexistent results trigger value error
            canMirror = max([x[0] for x in cu.fetchall()])
        except ValueError:
            canMirror = None
        db.close()
        return canMirror

    def getWriteAcl(self, project, username):
        return self.getPermission('canWrite', project, username)

    def getAdminAcl(self, project, username):
        return self.getPermission('admin', project, username)

    def getPermission(self, column, project, username):
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT MAX(%s)
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN Permissions ON Permissions.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=?""" % column, username)
        return cu.fetchone()[0]

    def tearDown(self):
        try:
            fixtureCache.delRepos()
            self.cfg and util.rmtree(self.cfg.dataPath)
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
            db, data = self.loadFixture(arg)
            return func(self, db, data)
        wrapper.__name__ = func.__name__
        wrapper.__dict__.update(func.__dict__)
        return wrapper
    return deco
