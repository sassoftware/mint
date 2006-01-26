#
# Copyright (c) 2005-2006 rPath, Inc.
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
from mint.projects import mysqlTransTable

MINT_DOMAIN = 'rpath.local'
MINT_HOST = 'test'

class MintDatabase:
    def __init__(self, path):
        self.path = path

    def newProjectDb(self, projectName):
        pass # not implemented

    def start(self):
        pass

    def reset(self):
        pass


class SqliteMintDatabase(MintDatabase):
    def reset(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def start(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def newProjectDb(self, projectName):
        p = util.normpath(self.path + "/../repos/" + projectName)
        if os.path.exists(p):
            util.rmtree(p)


class MySqlMintDatabase(MintDatabase):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']

    def connect(self):
        return dbstore.connect(self.path, "mysql")

    def dropAndCreate(self, dbName, create = True):
        db = self.connect()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        if dbName in [x[0] for x in cu.fetchall()]:
            cu.execute("DROP DATABASE %s" % dbName)
        if create:
            cu.execute("CREATE DATABASE %s" % dbName)
        db.close()

    def start(self):
        self.dropAndCreate("minttest")

    def reset(self):
        db = self.connect()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        for dbName in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            cu.execute("DROP DATABASE %s" % dbName)
        self.dropAndCreate("minttest")
        db.close()

    def newProjectDb(self, projectName):
        dbName = projectName.translate(mysqlTransTable)
        self.dropAndCreate(dbName, create = False)


class MintApacheServer(rephelp.ApacheServer):
    def __init__(self, name, reposDB, contents, server, serverDir, reposDir,
                 conaryPath, repMap, useCache = False, requireSigs = False):
        self.mintPath = os.environ.get("MINT_PATH", "")

        rephelp.ApacheServer.__init__(self, name, reposDB, contents, server, serverDir, reposDir,
             conaryPath, repMap, useCache, requireSigs)
        self.getMintCfg()
        f = file(self.serverRoot + "/mint.conf", "w")
        self.mintCfg.display(f)
        f.close()

        mintDb = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if mintDb == "sqlite":
            self.mintDb = SqliteMintDatabase(self.reposDir + "/mintdb")
        elif mintDb == "mysql":
            self.mintDb = MySqlMintDatabase(reposDB.path)

    def start(self):
        rephelp.ApacheServer.start(self)
        self.mintDb.start()

    def reset(self):
        if os.path.exists(self.reposDir + "/repos/"):
            util.rmtree(self.reposDir + "/repos/")
        rephelp.ApacheServer.reset(self)
        self.mintDb.reset()

    def getTestDir(self):
        return os.environ.get("MINT_PATH", "")  + "/test/"

    def getMap(self):
        return { self.name: 'http://localhost:%d/conary/' %self.port }

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

        sqldriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if sqldriver == 'sqlite':
            cfg.dbPath = self.reposDir + '/mintdb'
        elif sqldriver == 'mysql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % self.reposDB.port
        elif sqldriver == 'postgresql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % self.reposDB.port
        else:
            assert 0, "Invalid database type"
        cfg.dbDriver = sqldriver

        reposdriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if reposdriver == 'sqlite':
            cfg.reposDBPath = self.reposDir + "/repos/%s/sqldb"
        elif reposdriver == 'mysql':
            cfg.reposDBPath = 'root@localhost.localdomain:%d/%%s' % self.reposDB.port
        cfg.reposDBDriver = reposdriver

        cfg.dataPath = self.reposDir
        cfg.authDbPath = None
        cfg.imagesPath = self.reposDir + '/images/'
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'

#        cfg.newsRssFeed = 'file://' +mintPath + '/test/archive/news.xml'
        cfg.configured = True
        cfg.debugMode = True
        cfg.sendNotificationEmails = False
        cfg.commitAction = """%s/scripts/commitaction --username mintauth --password mintpass --repmap '%%(repMap)s' --build-label %%(buildLabel)s --module \'%s/mint/rbuilderaction.py --user %%%%(user)s --url http://mintauth:mintpass@%s:%d/xmlrpc-private/'""" % (conaryPath, mintPath, 'test.rpath.local', self.port)
        cfg.postCfg()

        cfg.hideFledgling = True
        cfg.SSL = False

        self.mintCfg = cfg


class MintServerCache(rephelp.ServerCache):
    def getServerClass(self, envname):
        name = "mint.rpath.local"
        server = None
        serverDir = os.environ.get('CONARY_PATH') + '/conary/server'
        serverClass = MintApacheServer

        return server, serverClass, serverDir


rephelp._servers = MintServerCache()
rephelp.SERVER_HOSTNAME = "mint.rpath.local@rpl:devel"


class MintRepositoryHelper(rephelp.RepositoryHelper):
    def openRepository(self, serverIdx = 0, requireSigs = False):
        ret = rephelp.RepositoryHelper.openRepository(self, serverIdx, requireSigs)
        self.port = self.servers.getServer(serverIdx).port
        self.mintCfg = self.servers.getServer(serverIdx).mintCfg

        return ret

    def __init__(self, methodName):
        rephelp.RepositoryHelper.__init__(self, methodName)
        self.imagePath = self.tmpDir + "/images"
        os.mkdir(self.imagePath)

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

        # add this user info to client config object
        if ('*', username, password) not in self.cfg.user:
            self.cfg.user.append(('*', username, password))

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

        # add this user info to client config object
        if ('*', username, password) not in self.cfg.user:
            self.cfg.user.append(('*', username, password))

        return client, userId

    def newProject(self, client, name = "Test Project",
                   hostname = "testproject",
                   domainname = "rpath.local"):
        """Create a new mint project and return that project ID."""
        # save the current openpgpkey cache
        keyCache = openpgpkey.getKeyCache()

        self.servers.getServer().mintDb.newProjectDb(hostname + "." + domainname)

        projectId = client.newProject(name, hostname, domainname)

        # set a default signature key
        project = client.getProject(projectId)
        ascKey = open(testsuite.archivePath + '/key.asc', 'r').read()
        project.addUserKey(client.server._server.authToken[0], ascKey)

        # restore the key cache
        openpgpkey.setKeyCache(keyCache)

        self.cfg.buildLabel = versions.Label("%s.%s@rpl:devel" % \
                                             (hostname, domainname))
        self.cfg.repositoryMap = {"%s.%s" % (hostname, domainname):
            "http://%s.%s:%d/repos/%s/" % (MINT_HOST, MINT_DOMAIN,
                                           self.port, hostname)}

        self.cfg.user.insert(0, ("%s.%s" % (hostname, domainname),
                              client.server._server.authToken[0],
                              client.server._server.authToken[1]))

        # re-open the repos to make changes to repositoryMap have any effect
        self.openRepository()

        return projectId

    def setUp(self):
        #if self.servers.getServer():
        #    self.servers.getServer().start()

        rephelp.RepositoryHelper.setUp(self)
        self.openRepository()

        # if you get permission denied on mysql server, then you need to
        # grant privleges to testuser on minttest:
        # GRANT ALL ON minttest.* TO testuser IDENTIFIED BY 'testpass';

        self.mintServer = mint_server.MintServer(self.mintCfg,
                                                 alwaysReload = True)
        self.db = self.mintServer.db
        self.db.connect()

    def tearDown(self):
        self.db.close()
        #self.servers.getServer().stop()
        rephelp.RepositoryHelper.tearDown(self)

    def stockReleaseFlavor(self, releaseId):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases set troveFlavor=? WHERE releaseId=?",
                   "1#x86:i486:i586:i686:~!sse2|1#x86_64|5#use:X:~!alternatives:~!bootstrap:~!builddocs:~buildtests:desktop:~!dietlibc:emacs:gcj:~glibc.tls:gnome:~grub.static:gtk:ipv6:kde:~!kernel.debug:~!kernel.debugdata:~!kernel.numa:krb:ldap:nptl:~!openssh.smartcard:~!openssh.static_libcrypto:pam:pcre:perl:~!pie:~!postfix.mysql:python:qt:readline:sasl:~!selinux:~sqlite.threadsafe:ssl:tcl:tcpwrappers:tk:~!xorg-x11.xprint", releaseId)
        self.db.commit()

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
