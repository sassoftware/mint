#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp

from mint import mint_server

class AuthTest(rephelp.RepositoryHelper):
    def testNewUser(self):
        client = self.getMintClient("testuser", "testpass")
        auth = client.checkAuth()
        assert(auth.authorized)

    def testBadUser(self):
        client = self.getMintClient("testuser", "testpass")

        client = self.openMint(("testuser", "badpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

if __name__ == "__main__":
    testsuite.main()
