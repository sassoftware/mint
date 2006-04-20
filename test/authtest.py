#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import server
from mint import users
from mint import shimclient

from fixtures import FixturedUnitTest, fixture

class AuthTest(FixturedUnitTest):
    @fixture("Empty")
    def testNewUser(self, db, client, data):
        auth = client.checkAuth()
        assert(auth.authorized)

    @fixture("Empty")
    def testBadUser(self, db, client, data):
        client = shimclient.ShimMintClient(client._cfg, ("testuser", "badpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

        # ensure capitalization typos in username aren't allowed either
        client = shimclient.ShimMintClient(client._cfg, ("testUser","testpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

    @fixture("Empty")
    def testConflictingUser(self, db, client, data):
        client = self._getAdminClient()

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

    @fixture("Empty")
    def testRequiresAuth(self, db, client, data):
        anonClient = shimclient.ShimMintClient(client._cfg, ('anonymous', 'anonymous'))

        try:
            anonClient.getUserSearchResults('Any String Will Do')
            self.fail("Not-logged-in client was allowed to perform a function requiring authorization")
        except server.PermissionDenied:
            pass

        client.getUserSearchResults('Any String Will Do')

    @fixture("Empty")
    def testRequiresAdmin(self, db, client, data):
        projectId = client.newProject('Foo', 'foo', 'localhost')

        try:
            client.hideProject(projectId)
            self.fail("User was allowed to perform an admin only function")
        except server.PermissionDenied:
            pass

if __name__ == "__main__":
    testsuite.main()
