#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#


from mint import mint_error
from mint import server
from mint import users
from mint import shimclient

import fixtures

class AuthTest(fixtures.FixturedUnitTest):
    @testsuite.context("quick")
    @fixtures.fixture("Empty")
    def testNewUser(self, db, data):
        client = self.getClient("test")
        auth = client.checkAuth()
        assert(auth.authorized)

    @fixtures.fixture("Empty")
    def testBadUser(self, db, data):
        throwaway = self.getClient("test")
        cfg = throwaway._cfg
        client = shimclient.ShimMintClient(cfg, ("test", "badpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

        # ensure capitalization typos in username aren't allowed either
        client = shimclient.ShimMintClient(cfg, ("tEsT","testpass"))
        auth = client.checkAuth()
        assert(not auth.authorized)

    @fixtures.fixture("Empty")
    def testConflictingUser(self, db, data):
        client = self.getClient('admin')

        # make two accounts with a case sensitive clash.
        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)
        try:
            userId = client.registerNewUser("Member", "memberpass", "Test Member",
                                            "test@example.com", "test at example.com", "", active=True)
            self.fail("conflicting usernames allowed to be created")
        except users.UserAlreadyExists:
            pass
        userId = client.registerNewUser("different", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)

    @fixtures.fixture("Empty")
    def testRequiresAuth(self, db, data):
        client = self.getClient("test")
        cfg = client._cfg
        anonClient = shimclient.ShimMintClient(cfg, ('anonymous', 'anonymous'))

        try:
            anonClient.getUserSearchResults('Any String Will Do')
            self.fail("Not-logged-in client was allowed to perform a function requiring authorization")
        except mint_error.PermissionDenied:
            pass

        client.getUserSearchResults('Any String Will Do')

    @fixtures.fixture("Full")
    def testRequiresAdmin(self, db, data):
        client = self.getClient("owner")

        try:
            client.hideProject(data['projectId'])
            self.fail("User was allowed to perform an admin only function")
        except mint_error.PermissionDenied:
            pass

