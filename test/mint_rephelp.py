#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import testsuite
import rephelp

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
        """Retrieves a client, creates a user as specified by username and password,
           and returns a connection to mint as that new user, and the user ID.:"""
        client = self.openMintClient()
        userId = client.registerNewUser(username, password, "Test User",
                "test@example.com", "test at example.com", "", active=True)

        return self.openMintClient((username, password)), userId

    def quickMintAdmin(self, username, password):
        # manipulate the UserGroups and UserGroup
        cu = self.mintServer.authDb.cursor()

        r = cu.execute("SELECT COUNT(*) FROM UserGroups WHERE UserGroup = 'MintAdmin'")
        if r.fetchone()[0] == 0:
            r = cu.execute("SELECT IFNULL(MAX(userGroupId) + 1, 1) FROM UserGroups")
            groupId = r.fetchone()[0]
            cu.execute("INSERT INTO UserGroups VALUES(?, 'MintAdmin')", groupId)
            cu.execute("INSERT INTO UserGroupMembers VALUES (?,?)", groupId, groupId)
            self.mintServer.authDb.commit()
        else:
            r = cu.execute("SELECT userGroupId FROM UserGroups WHERE UserGroup = 'MintAdmin'")
            groupId = r.fetchone()[0]
        client, userId = self.quickMintUser(username, password)

        authUserId = cu.execute("SELECT userId from users where user=?", username).fetchone()[0]

        cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)", groupId, authUserId)
        self.mintServer.authDb.commit()
        return client, userId

    def newProject(self, client, name = "Test Project",
                         hostname = "test",
                         domainname = "localhost",
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

        self.cfg.buildLabel = versions.Label("%s.%s@rpl:devel" % (hostname, domainname))
        self.cfg.repositoryMap = {"%s.%s" % (hostname, domainname):
            "http://testuser:testpass@%s:%d/repos/%s/" % (domainname, self.getPort(), hostname)}

        return projectId
        
    def tearDown(self):
        rephelp.RepositoryHelper.tearDown(self) 
        try:
            if self.mintCfg.dbDriver in ("native_sqlite", "sqlite"):
                os.unlink(self.servers.getServer().serverRoot + "/mintdb")
        except:
            pass

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)

        self.openRepository()
        self.mintCfg = config.MintConfig()
        self.mintCfg.read("%s/mint.conf" % self.servers.getServer().serverRoot)

        if self.mintCfg.dbDriver == "mysql":
            os.system("mysql --password=testpass -u testuser minttest < cleanup-mysql.sql")

        self.mintServer = mint_server.MintServer(self.mintCfg, alwaysReload = True)
        self.db = self.mintServer.db
        if self.db.type != "native_sqlite":
            self.db.connect()
        else:
            cu = self.db.cursor()

            cu.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
            self.db.tables = [ x[0] for x in cu.fetchall() ]
