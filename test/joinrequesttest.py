#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels

from fixtures import FixturedUnitTest, fixture

class JoinRequestTest(FixturedUnitTest):
    @fixture("Release")
    def testSetComments(self, db, client, data):
        projectId = data['projectId']
        # abandon the old user. you can't make requests against
        # projects you're a member of, so that one's useless for testing
        client, userId = self.quickMintUser("seconduser", "testpass")

        # initially the request should not be present
        assert(not client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, '')

        # request should now be present
        assert(client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, 'foo')
        assert(client.getJoinReqComments(projectId, userId) == 'foo')

        client.deleteJoinRequest(projectId, userId)

        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

    @fixture("Release")
    def testMembershipEffects(self, db, client, data):
        projectId = data['projectId']

        # uses original client -- meaning has auth tokens for project owner
        project = client.getProject(projectId)

        # abandon the old user so we can make join reqs
        client, userId = self.quickMintUser("newuser", "testpass")
        client.setJoinReqComments(projectId, '')

        # request should now be present
        assert(client.userHasRequested(projectId, userId))

        project.addMemberById(userId, userlevels.DEVELOPER)

        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, 'foo')

        # request should not have been added -- user is already a member
        assert(not client.userHasRequested(projectId, userId))

        # exercise addMemberByName code path. same as adopting project
        project.delMemberById(userId)
        client.setJoinReqComments(projectId, 'foo')
        for memberId, x, y in project.getMembers():
            project.delMemberById(memberId)
        project.addMemberByName('newuser', userlevels.OWNER)
        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

    def testUserEffects(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)

        project.delMemberById(userId)
        project.addMemberById(userId, userlevels.USER)

        client.setJoinReqComments(projectId, '')

        # request should now be present. watching a project should not
        # preclude being allowed to join
        assert(client.userHasRequested(projectId, userId))

        project.updateUserLevel(userId, userlevels.OWNER)

        # request should no longer be present. updating user level to a
        # writing member status should clear a join request
        assert(not client.userHasRequested(projectId, userId))

    @fixture("Release")
    def testCancelAcctEffects(self, db, client, data):
        projectId = data['projectId']
        userId = data['userId']
        newClient, newUserId = self.quickMintUser("member", "memberpass")

        user = newClient.getUser(newUserId)
        newClient.setJoinReqComments(projectId, 'foo')
        # cancel account and check again
        user.cancelUserAccount()
        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

    # FIXME. need to exercise listJoinRequests
    @fixture("Release")
    def testListJoinRequests(self, db, client, data):
        projectId = data['projectId']

        for i in range(2, 7):
            newClient, newUserId = self.quickMintUser('newUser_%d' %i,'testpass')
            newClient.setJoinReqComments(projectId, 'foo-%d' %i)
        joinReqs = client.listJoinRequests(projectId)
        if len(joinReqs) != 5:
                self.fail("listJoinRequest returned wrong number of results")
        for req in  joinReqs:
            #if (len(req) != 2)  or (type(req[1]) != str):
            if (len(req) != 2) or (req[0] not in range(2,7)) or (type(req[1]) != str):
                self.fail("join Request returned improper format")

if __name__ == "__main__":
    testsuite.main()
