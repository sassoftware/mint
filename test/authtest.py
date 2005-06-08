#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 Specifix, Inc.
#

import testsuite
testsuite.setup()

import rephelp

from mint import users

class AuthTest(rephelp.RepositoryHelper):
    def testNewUser(self):
        client = self.openMint(('test', 'foo'))

        userId = client.registerNewUser("testuser", "testpass", "Test User",
                                        "test@example.com", active=True)
        
        client = self.openMint(("testuser", "testpass"))
        auth = client.checkAuth()
        assert(auth.authorized)
        assert(auth.userId == userId)
        
if __name__ == "__main__":
    testsuite.main()
