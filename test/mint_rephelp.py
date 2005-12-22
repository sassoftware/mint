#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import testsuite
import rephelp

from webunit import webunittest

from conary import sqlite3
from conary import versions
from conary.lib import openpgpkey

from mint import config
from mint import shimclient
from mint import dbversion
from mint import mint_server

class MintRepositoryHelper(rephelp.RepositoryHelper):
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
                                           self.getPort(), hostname)}
        self.cfg.user.addServerGlob("%s.%s" % (hostname, domainname),
                                    "testuser", "testpass")

        # re-open the repos to make changes to repositoryMap have any effect
        self.openRepository()

        return projectId
        
    def tearDown(self):
        rephelp.RepositoryHelper.tearDown(self) 
        try:
            if self.mintCfg.dbDriver == "sqlite":
                os.unlink(self.servers.getServer().serverRoot + "/mintdb")
            if self.mintCfg.dbDriver == "mysql":
                cu.execute("DROP DATABASE minttest")
        except:
            pass

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)

        self.openRepository()
        self.mintCfg = self.servers.getServer().mintCfg
        self.mintCfg.postCfg()

        if self.mintCfg.dbDriver == "mysql":
            os.system("echo DROP DATABASE minttest\; CREATE DATABASE minttest | mysql --password=testpass -u testuser minttest")

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
