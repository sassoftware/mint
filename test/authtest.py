#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import mint_server

from mint import users

class AuthTest(MintRepositoryHelper):
    def testNewUser(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        auth = client.checkAuth()
        assert(auth.authorized)

    def testBadUser(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        client = self.openMintClient(("testuser", "badpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

        # ensure capitalization typos in username aren't allowed either
        client = self.openMintClient(("testUser","testpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)


    def testConflictingUser(self):
        client = self.openMintClient()
        # make two accounts with a case sensitive clash.
        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)
        try:
            userId = client.registerNewUser("Member", "memberpass", "Test Member",
                                            "test@example.com", "test at example.com", "", active=True)
            self.fail("conflicting usernames allowed to be created")
        except users.GroupAlreadyExists:
            pass
        userId = client.registerNewUser("different", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)

    def testRequiresAuth(self):
        client = self.openMintClient()

        try:
            client.getUserSearchResults('Any String Will Do')
            self.fail("Not-logged-in client was allowed to perform a function requiring authorization")
        except mint_server.PermissionDenied:
            pass

        client, userid = self.quickMintUser('testuser','testpass')
        client.getUserSearchResults('Any String Will Do')

    def testRequiresAdmin(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = client.newProject('Foo', 'foo', 'localhost')

        try:
            client.hideProject(projectId)
            self.fail("User was allowed to perform an admin only function")
        except mint_server.PermissionDenied:
            pass

if __name__ == "__main__":
    testsuite.main()
