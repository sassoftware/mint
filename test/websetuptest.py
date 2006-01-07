#!/usr/bin/python2.4
#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import mint_rephelp

from repostest import testRecipe
from conary import versions

class MintTest(mint_rephelp.WebRepositoryHelper):
    def testFirstTimeSetupRedirect(self):
        self.mintCfg.configured = False
        self.resetRepository() 

        page = self.assertCode('/', code = 302)
        assert(page.headers['Location'] == '/setup/')
  
        page = self.assertContent('/setup/', ok_codes = [302],
            content = "Please create a file called")
        
        sid = self.cookies.items()[0][1]['/']['pysid'].value
        secureFile = self.mintCfg.dataPath + "/" + sid + ".txt"

        f = file(secureFile, 'w')
        f.close()
  
        page = self.assertContent('/setup/', ok_codes = [200],
            content = "rBuilder Product Setup")
 
        # set site back to configured
        self.mintCfg.configured = True
       
  
if __name__ == "__main__":
    testsuite.main()
