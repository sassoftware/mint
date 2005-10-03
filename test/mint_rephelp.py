#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
import rephelp
import sqlite3

import versions
from lib import openpgpkey

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

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)

        self.openRepository()
        self.mintCfg = config.MintConfig()
        self.mintCfg.read("%s/mint.conf" % self.servers.getServer().serverRoot)

        self.mintServer = mint_server.MintServer(self.mintCfg)
        self.db = self.mintServer.db

#        self.versionTable = dbversion.VersionTable(self.db)
#        self.db.commit()
