#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
import recipes

class RepositoryTest(MintRepositoryHelper):
    def testBasicRepository(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
       
        self.makeSourceTrove("testcase", recipes.testRecipe1)

if __name__ == "__main__":
    testsuite.main()
