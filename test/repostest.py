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
    def testBasicRepository(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = self.newProject(client)
       
        self.makeSourceTrove("testcase", recipes.testRecipe1)

if __name__ == "__main__":
    testsuite.main()
