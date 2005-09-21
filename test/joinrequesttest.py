#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp
from mint import userlevels

class JoinRequestTest(rephelp.RepositoryHelper):
    def testSetComments(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        userId = client.getUserIdByName("testuser")

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

if __name__ == "__main__":
    testsuite.main()
