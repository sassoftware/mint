#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import mint_server

from mint import users

class AuthTest(MintRepositoryHelper):
    def testNewUser(self):
        client = self.getMintClient("testuser", "testpass")
        auth = client.checkAuth()
        assert(auth.authorized)

    def testBadUser(self):
        client = self.getMintClient("testuser", "testpass")

        client = self.openMint(("testuser", "badpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

        # ensure capitlization typos in username aren't allowed either
        client = self.openMint(("testUser","testpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)


    def testConflictingUser(self):
        client = self.getMintClient("testuser", "testpass")
        # make two accounts with a case sensitive clash.
        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)
        try:
            userId = client.registerNewUser("Member", "memberpass", "Test Member",
                                            "test@example.com", "test at example.com", "", active=True)
            # the above line should have raised an exception. if code flow
            # reaches this point, that's an error.
            assert (1 == 0)
        except users.GroupAlreadyExists:
            pass
        userId = client.registerNewUser("different", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)

if __name__ == "__main__":
    testsuite.main()
