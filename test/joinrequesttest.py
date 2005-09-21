#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels

class JoinRequestTest(MintRepositoryHelper):
    def testSetComments(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")


        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)

        # initially the request should not be present
        assert(not client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, userId, '')

        # request should now be present
        assert(client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, userId, 'foo')
        assert(client.getJoinReqComments(projectId, userId) == 'foo')

        client.deleteJoinRequest(projectId, userId)

        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

    def testMembershipEffects(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)

        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)
        client.setJoinReqComments(projectId, userId, '')

        # request should now be present
        assert(client.userHasRequested(projectId, userId))

        project.addMemberById(userId, userlevels.DEVELOPER)
        
        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))

        client.setJoinReqComments(projectId, userId, 'foo')
        
        # request should not have been added -- user is already a member
        assert(not client.userHasRequested(projectId, userId))

        # exercise addMemberByName code path. same as adopting project
        project.delMemberById(userId)
        client.setJoinReqComments(projectId, userId, 'foo')
        for memberId, x, y in project.getMembers():
            project.delMemberById(memberId)
        project.addMemberByName('member', userlevels.OWNER)
        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))
        
    def testCancelAcctEffects(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        userId = client.registerNewUser("member", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=True)

        client = self.openMint(('member', 'memberpass'))
        user = client.getUser(userId)
        client.setJoinReqComments(projectId, userId, 'foo')
        # cancel account and check again
        user.cancelUserAccount()
        # request should no longer be present
        assert(not client.userHasRequested(projectId, userId))
        

if __name__ == "__main__":
    testsuite.main()
