#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import mysqlharness
import testsuite
import rephelp
import sys

from webunit import webunittest

from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.lib import openpgpkey, util

from mint import config
from mint import shimclient
from mint import dbversion
from mint import mint_server

MINT_DOMAIN = 'rpath.local'
MINT_HOST = 'test'


class MintApacheServer(rephelp.ApacheServer):
    def __init__(self, name, reposDB, contents, server, serverDir, reposDir,
                 conaryPath, repMap, useCache = False, requireSigs = False):
        self.mintPath = os.environ.get("MINT_PATH", "")
        rephelp.ApacheServer.__init__(self, name, reposDB, contents, server, serverDir, reposDir,
             conaryPath, repMap, useCache, requireSigs)

    def getTestDir(self):
        return os.environ.get("MINT_PATH", "")  + "/test/"

    def getMap(self):
        return { self.name: 'http://localhost:%d/conary/' %self.port }


class MintServerCache(rephelp.ServerCache):
    def getServerClass(self, envname):
        name = "mint.rpath.local"
        server = None
        serverDir = os.environ.get('CONARY_PATH') + '/conary/server'
        serverClass = MintApacheServer

        return server, serverClass, serverDir


rephelp._servers = MintServerCache()
rephelp.SERVER_HOSTNAME = "mint.rpath.local@rpl:devel"

mysql = mysqlharness.MySqlHarness()
mysql.start()

class MintRepositoryDatabase(rephelp.RepositoryDatabase):
    def getDb(self):
        return dbstore.connect('root@localhost.localdomain:%d/mysql' % mysql.port, 'mysql')

    def reset(self):
        db = self.getDb()
        # start a transaction to avoid a race where there is no testdb
        cu = db.transaction()
        cu.execute("drop database %s " % self.name)
        cu.execute("create database %s character set latin1" % self.name)
        self.createSchema()
        self.createUsers()
        db.commit()

    def __init__(self, name = 'testdb'):
        self.name = name
        rephelp.RepositoryDatabase.__init__(self, 'mysql',
                                    'root@localhost.localdomain:%d/%s' % (mysql.port, name))

        db = self.getDb()
        cu = db.transaction()
        cu.execute("create database %s character set latin1;\n" % name)
        db.close()


class MintRepositoryHelper(rephelp.RepositoryHelper):
    port = 59999

    def openRepository(self, serverIdx = 0, requireSigs = False):
        ret = rephelp.RepositoryHelper.openRepository(self, serverIdx, requireSigs)
        self.port = self.servers.getServer().port
        self.getMintCfg()

        # write mint.conf to disk
        f = open("%s/mint.conf" % self.servers.getServer().serverRoot, "w")
        self.mintCfg.display(out = f)
        f.close()

        return ret

    def __init__(self, methodName):
        rephelp.RepositoryHelper.__init__(self, methodName)
        self.getMintCfg()
        self.imagePath = self.tmpDir + "/images"
        os.mkdir(self.imagePath)

    def getMintCfg(self):
        # write Mint configuration
        
        conaryPath = os.environ.get("CONARY_PATH", "")
        mintPath = os.environ.get("MINT_PATH", "")

        cfg = config.MintConfig()

        cfg.siteDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.projectDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.externalDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.hostName = MINT_HOST
        cfg.secureHost = "%s.%s" % (MINT_HOST, MINT_DOMAIN)

        sqldriver = os.environ.get('MINT_SQL', 'sqlite')
        if sqldriver == 'sqlite':
            cfg.dbPath = self.tmpDir + '/mintdb'
        elif sqldriver == 'mysql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % mysql.port
        elif sqldriver == 'postgresql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % mysql.port
        else:
            assert 0, "Invalid database type"
        cfg.dbDriver = sqldriver

        reposdriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if reposdriver == 'sqlite':
            cfg.reposDBPath = self.reposDir + "/repos/%s/sqldb"
        elif reposdriver == 'mysql':
            cfg.reposDBPath = 'root@localhost.localdomain:%d/%%s' % mysql.port
        cfg.reposDBDriver = reposdriver

        cfg.dataPath = self.reposDir
        cfg.authDbPath = None
        cfg.imagesPath = self.reposDir + '/images/'
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'

        cfg.configured = True
        cfg.debugMode = True
        cfg.sendNotificationEmails = False
        cfg.commitAction = """%s/scripts/commitaction --username mintauth --password mintadmin --repmap '%%(repMap)s' --build-label %%(buildLabel)s --module \'%s/mint/rbuilderaction.py --user %%%%(user)s --url http://mintauth:mintpass@%s:%d/xmlrpc-private/'""" % (conaryPath, mintPath, 'test.rpath.local', self.port)
        cfg.postCfg()
        self.mintCfg = cfg

    def openMintClient(self, authToken=('mintauth', 'mintpass')):
        """Return a mint client authenticated via authToken, defaults to 'mintauth', 'mintpass'"""
        return shimclient.ShimMintClient(self.mintCfg, authToken)

    def quickMintUser(self, username, password):
        """Retrieves a client, creates a user as specified by username and
        password, and returns a connection to mint as that new user, and the
        user ID.:"""
        client = self.openMintClient()
        userId = client.registerNewUser(username, password, "Test User",
                "test@example.com", "test at example.com", "", active=True)

        cu = self.db.cursor()
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        self.db.commit()

        return self.openMintClient((username, password)), userId

    def quickMintAdmin(self, username, password):
        # manipulate the UserGroups and UserGroup
        cu = self.db.cursor()

        cu.execute("""SELECT COUNT(*) FROM UserGroups
                          WHERE UserGroup = 'MintAdmin'""")
        if cu.fetchone()[0] == 0:
            cu.execute("""SELECT IFNULL(MAX(userGroupId) + 1, 1)
                             FROM UserGroups""")
            groupId = cu.fetchone()[0]
            cu.execute("INSERT INTO UserGroups VALUES(?, 'MintAdmin')",
                       groupId)
            self.db.commit()
        else:
            cu.execute("""SELECT userGroupId FROM UserGroups
                              WHERE UserGroup = 'MintAdmin'""")
            groupId = cu.fetchone()[0]
        client, userId = self.quickMintUser(username, password)

        cu.execute("SELECT userId from Users where username=?", username)
        authUserId = cu.fetchone()[0]

        cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                   groupId, authUserId)
        self.db.commit()
        return client, userId

    def newProject(self, client, name = "Test Project",
                         hostname = "test",
                         domainname = "rpath.local",
                         username = "mintauth"):
        """Create a new mint project and return that project ID."""
        # save the current openpgpkey cache
        keyCache = openpgpkey.getKeyCache()

        dbName = ("%s.%s" % (hostname, domainname)).replace(".", "_")
        repos = MintRepositoryDatabase(name = dbName)

        projectId = client.newProject(name, hostname, domainname)

        # set a default signature key
        project = client.getProject(projectId)
        ascKey = open(testsuite.archivePath + '/key.asc', 'r').read()
        project.addUserKey(username, ascKey)

        # restore the key cache
        openpgpkey.setKeyCache(keyCache)

        self.cfg.buildLabel = versions.Label("%s.%s@rpl:devel" % \
                                             (hostname, domainname))
        self.cfg.repositoryMap = {"%s.%s" % (hostname, domainname):
            "http://%s.%s:%d/repos/%s/" % (hostname, domainname,
                                           self.port, hostname)}
        self.cfg.user.insert(0, ("%s.%s" % (hostname, domainname),
                                    "testuser", "testpass"))

        # re-open the repos to make changes to repositoryMap have any effect
        self.openRepository()
        
                                                                                

        return projectId
    
    def tearDown(self):
        rephelp.RepositoryHelper.tearDown(self)
        try:
            util.rmtree(self.reposDir + "/repos/")
            os.unlink(self.tmpDir + "/mintdb")
        except:
            pass

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)

        if self.mintCfg.dbDriver == "mysql":
            db = dbstore.connect("root@localhost.localdomain:%d/mysql" % mysql.port, driver=self.mintCfg.dbDriver)
            cu = db.cursor()
            try:
                cu.execute("DROP DATABASE minttest")
            except:
                pass
            cu.execute("CREATE DATABASE minttest")
            db.commit()
            db.close() 
        elif self.mintCfg.dbDriver == "postgresql":
            os.system("dropdb -U testuser minttest; createdb -U testuser minttest") 
        elif self.mintCfg.dbDriver == "sqlite":
            try:
                os.unlink(self.tmpDir + "/mintdb")
            except:
                pass

        # if you get permission denied on mysql server, then you need to
        # grant privleges to testuser on minttest:
        # GRANT ALL ON minttest.* TO testuser IDENTIFIED BY 'testpass';

        self.mintServer = mint_server.MintServer(self.mintCfg,
                                                 alwaysReload = True)
        self.db = self.mintServer.db
        self.db.connect()


class WebRepositoryHelper(MintRepositoryHelper, webunittest.WebTestCase):
    def __init__(self, methodName):
        webunittest.WebTestCase.__init__(self, methodName)
        MintRepositoryHelper.__init__(self, methodName)

    def getServerData(self):
        server = 'test.rpath.local'
        # spawn a server if needed, then point our code at it...
        if self.servers.servers[0] is None:
            self.openRepository()
        return server, self.servers.servers[0].port

    def getMintUrl(self):
        return 'http://%s:%d/' % (self.getServerData())

    def setUp(self):
        webunittest.WebTestCase.setUp(self)
        MintRepositoryHelper.setUp(self)
        self.openRepository()
        self.setAcceptCookies(True)
        self.server, self.port = self.getServerData()
        self.URL = self.getMintUrl()
        # this is tortured, but webunit won't run without it.
        webunittest.HTTPResponse._TestCase__testMethodName = \
                                          self._TestCase__testMethodName
        # set the cookie to stop the redirect madness
        page = self.fetch('')

    def tearDown(self):
        self.clearCookies()
        MintRepositoryHelper.tearDown(self)
        webunittest.WebTestCase.tearDown(self)
        # tear down the running server...

    def webLogin(self, username, password):
        page = self.fetch('')
        page = self.fetch('/processLogin', postdata = \
            {'username': username,
             'password': password})
        page = self.fetch('')
        return page
