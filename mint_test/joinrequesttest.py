#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


from mint import userlevels

from fixtures import FixturedUnitTest, fixture
import fixtures

class JoinRequestTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testSetComments(self, db, data):
        client = self.getClient("nobody")
        projectId = data['projectId']
        userId = data['nobody']

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

    @fixtures.fixture("Full")
    def testMembershipEffects(self, db, data):
        # uses original client -- meaning has auth tokens for project owner
        client = self.getClient("owner")
        projectId = data['projectId']
        project = client.getProject(projectId)

        # abandon the old user so we can make join reqs
        nobodyClient = self.getClient("nobody")
        nobodyUserId = data['nobody']
        nobodyClient.setJoinReqComments(projectId, '')

        # request should now be present
        assert(nobodyClient.userHasRequested(projectId, nobodyUserId))

        project.addMemberById(nobodyUserId, userlevels.DEVELOPER)

        # request should no longer be present
        assert(not nobodyClient.userHasRequested(projectId, nobodyUserId))

        nobodyClient.setJoinReqComments(projectId, 'foo')

        # request should not have been added -- user is already a member
        assert(not nobodyClient.userHasRequested(projectId, nobodyUserId))

        # exercise addMemberByName code path. same as adopting project
        project.delMemberById(nobodyUserId)
        nobodyClient.setJoinReqComments(projectId, 'foo')
        project.delMemberById(data['developer'])
        project.delMemberById(data['owner'])
        project.addMemberByName('nobody', userlevels.OWNER)
        # request should no longer be present
        assert(not nobodyClient.userHasRequested(projectId, nobodyUserId))

    @fixtures.fixture("Full")
    def testUserEffects(self, db, data):
        client = self.getClient("nobody")
        projectId = data['projectId']
        project = client.getProject(projectId)
        userId = data['nobody']

        project.addMemberById(userId, userlevels.USER)

        client.setJoinReqComments(projectId, '')

        # request should now be present. watching a project should not
        # preclude being allowed to join
        assert(client.userHasRequested(projectId, userId))

        project.updateUserLevel(userId, userlevels.OWNER)

        # request should no longer be present. updating user level to a
        # writing member status should clear a join request
        assert(not client.userHasRequested(projectId, userId))

    @fixtures.fixture("Full")
    def testCancelAcctEffects(self, db, data):
        ownerClient = self.getClient("owner")
        nobodyClient = self.getClient("nobody")

        nobodyUser = nobodyClient.getUser(data['nobody'])
        nobodyClient.setJoinReqComments(data['projectId'], 'foo')
        # cancel account and check again
        nobodyUser.cancelUserAccount()
        # request should no longer be present
        assert(not ownerClient.userHasRequested(data['projectId'],
            data['owner']))

    # FIXME. need to exercise listJoinRequests
    @fixtures.fixture("Empty")
    def testListJoinRequests(self, db, data):
        client = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "localhost",
                        shortname="foo", version="1.0", prodtype="Component")

        for i in range(2, 7):
            newClient, newUserId = self.quickMintUser('newUser_%d' %i,'testpass')
            newClient.setJoinReqComments(projectId, 'foo-%d' %i)
        joinReqs = client.listJoinRequests(projectId)
        if len(joinReqs) != 5:
                self.fail("listJoinRequest returned wrong number of results")
        for req in  joinReqs:
            #if (len(req) != 2)  or (type(req[1]) != str):
            if (len(req) != 2) or (req[0] not in range(3,8)) or (type(req[1]) != str):
                self.fail("join Request returned improper format")

    @fixtures.fixture("Full")
    def testWatchHonorsRequest(self, db, data):
        client = self.getClient("nobody")
        projectId = data['projectId']
        project = client.getProject(projectId)
        client.setJoinReqComments(projectId, 'foo')
        project.addMemberByName('nobody', userlevels.USER)
        self.failIf(not client.getJoinReqComments(projectId, data['nobody']),
                    "User watching a project killed join request.")


