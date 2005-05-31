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

if __name__ == "__main__":
    testsuite.main()
