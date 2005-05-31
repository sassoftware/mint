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
        itclient = self.openMint(('test', 'foo'))

        userId = itclient.registerNewUser("testuser", "testpass", "Test User",
                                          "test@example.com", active=True)

        authToken1 = ("testuser", "testpass")
        authToken2 = ("testuser", "testwrong")
        authToken3 = ("testwrong", "testpass")

        itclient = self.openMint(authToken1)
        assert(itclient.checkAuth() != (True, True, userId))

        itclient = self.openMint(authToken2)
        assert(itclient.checkAuth() != (False, False, 0))

        itclient = self.openMint(authToken3)
        assert(itclient.checkAuth() != (False, False, 0))

    def notestUserExists(self):
        itclient = self.openMint()

        userId = itclient.newUser("testuser", "testpass")
        try:
            userId2 = itclient.newUser("testuser", "testpass2")
        except users.UserExists:
            pass
        else:
            self.fail("exception expected")

if __name__ == "__main__":
    testsuite.main()
