#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()
import versions

from mint_rephelp import MintRepositoryHelper
import recipes

from mint import userlevels
from lib import openpgpkey

class RepositoryTest(MintRepositoryHelper):
    def newProject(self, client, name = "Test Project",
                         hostname = "test",
                         domainname = "localhost",
                         username = "testuser"):
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

    def testBasicRepository(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = self.newProject(client)
       
        self.makeSourceTrove("testcase", recipes.testRecipe1)

if __name__ == "__main__":
    testsuite.main()
