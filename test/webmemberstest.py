#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import mint_rephelp
import rephelp

from mint import userlevels

class WebMemberTest(mint_rephelp.WebRepositoryHelper):
    def testJoinRequestLink(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')
        client3, userId3 = self.quickMintUser('user3', 'user3')
        self.quickMintAdmin('adminuser', 'adminuser')

        projectId = self.newProject(client)

        # try as unrelated user
        self.webLogin('user2', 'user2')

        self.assertContent('/project/testproject/members',
                           '/project/testproject/joinRequest',
                           server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        project = client.getProject(projectId)
        project.addMemberById(userId2, userlevels.DEVELOPER)

        # try as developer
        self.webLogin('user2', 'user2')
        self.assertNotContent('/project/testproject/members',
                              '/project/testproject/joinRequest',
                              server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        # try as admin
        self.webLogin('adminuser', 'adminuser')
        self.assertContent('/project/testproject/members',
                           '/project/testproject/joinRequest',
                           server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        # try as owner
        self.webLogin('user1', 'user1')
        self.assertNotContent('/project/testproject/members',
                              '/project/testproject/joinRequest',
                              server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        project = client3.getProject(projectId)
        project.addMemberById(userId3, userlevels.USER)

        # try as watcher
        self.webLogin('user3', 'user3')
        self.assertContent('/project/testproject/members',
                           '/project/testproject/joinRequest',
                           server = self.getProjectServerHostname())

    def testWatchLink(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')
        client3, userId3 = self.quickMintUser('user3', 'user3')
        self.quickMintAdmin('adminuser', 'adminuser')

        projectId = self.newProject(client)

        # try as unrelated user
        self.webLogin('user2', 'user2')
        self.assertContent('/project/testproject/members',
                           '/project/testproject/watch',
                           server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        project = client.getProject(projectId)
        project.addMemberById(userId2, userlevels.DEVELOPER)

        # try as developer
        self.webLogin('user2', 'user2')
        self.assertNotContent('/project/testproject/members',
                              '/project/testproject/watch',
                              server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        # try as admin
        self.webLogin('adminuser', 'adminuser')
        self.assertContent('/project/testproject/members',
                           '/project/testproject/watch',
                           server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        # try as owner
        self.webLogin('user1', 'user1')
        self.assertNotContent('/project/testproject/members',
                              '/project/testproject/watch',
                              server = self.getProjectServerHostname())

        self.fetchWithRedirect('/logout')

        project = client3.getProject(projectId)
        project.addMemberById(userId3, userlevels.USER)

        # try as watcher
        self.webLogin('user3', 'user3')
        self.assertContent('/project/testproject/members',
                           '/project/testproject/unwatch',
                           server = self.getProjectServerHostname())

    def testJoinRequest(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)

        self.webLogin('user2', 'user2')

        # using the project server for this test
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/testproject/joinRequest')

        # perform the join
        commentStr = "It's Brian's shoe!"
        page.postForm(1, self.post, {'comments': commentStr,
                                     'keepReq' : '1'})

        page = self.assertContent('/project/testproject/joinRequest',
                                  commentStr)

        # now retract request
        page.postForm(1, self.post, {'comments': commentStr,
                                     'keepReq' : '0'})

        page = self.assertNotContent('/project/testproject/joinRequest',
                                     commentStr)

    def testRequestPending(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)

        self.webLogin('user2', 'user2')

        page = self.fetch('/project/testproject/joinRequest',
                server = self.getProjectServerHostname())

        # perform the join
        commentStr = "What do you mean? African or European?"
        page = page.postForm(1, page.post, {'comments': commentStr,
                                            'keepReq' : '1'})

        page.fetchWithRedirect('/logout')
        self.webLogin('user1', 'user1')

        page = self.fetchWithRedirect('/')
        self.assertContent('/', 'Requests Pending')

    def testRejectJoinReq(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)
        client2.setJoinReqComments(projectId, '')

        self.webLogin('user1', 'user1')

        # using the project server for this test
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent( '/project/testproject/members',
                                   'viewJoinRequest?userId=%d' % userId2)

        page = self.fetch('/project/testproject/viewJoinRequest?userId=%d' % \
                          userId2)

        # reject it
        page = page.postForm(1, self.post, {"reject" : "1"})
        page.postForm(1, self.post, {})

        cu = self.db.cursor()
        cu.execute("SELECT * FROM MembershipRequests")

        self.failIf(cu.fetchall(), "Join request was not rejected")

    def testOwnerJoinReq(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)
        client2.setJoinReqComments(projectId, '')

        self.webLogin('user1', 'user1')

        # using the project server for this test
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent( '/project/testproject/members',
                                   'viewJoinRequest?userId=%d' % userId2)

        page = self.fetch('/project/testproject/viewJoinRequest?userId=%d' % \
                          userId2)

        # accept as owner
        page = page.postForm(1, self.post, {"makeOwner" : "1"})

        project = client.getProject(projectId)
        self.failIf(project.listJoinRequests() != [],
                    "Join request was not erased")

        self.failIf([userId2, 'user2', userlevels.OWNER] \
                    not in project.getMembers(),
                    "user was not promoted to owner")

    def testDevelJoinReq(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)
        client2.setJoinReqComments(projectId, '')

        self.webLogin('user1', 'user1')

        # using the project server for this test
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent( '/project/testproject/members',
                                   'viewJoinRequest?userId=%d' % userId2)

        page = self.fetch('/project/testproject/viewJoinRequest?userId=%d' % \
                          userId2)

        # accept as developer
        page = page.postForm(1, self.post, {"makeDevel" : "1"})

        project = client.getProject(projectId)
        self.failIf(project.listJoinRequests() != [],
                    "Join request was not erased")

        self.failIf([userId2, 'user2', userlevels.DEVELOPER] \
                    not in project.getMembers(),
                    "user was not promoted to developer")

    def testPromote(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        project.addMemberById(userId2, userlevels.DEVELOPER)
        self.webLogin('user1', 'user1')
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetchWithRedirect('/project/testproject/promoteMember?userId=%d' % userId2)
        assert(project.getMembers() == [[userId, 'user1', userlevels.OWNER],
                                        [userId2, 'user2', userlevels.OWNER]])

    def testDemote(self):
        client, userId = self.quickMintUser('user1', 'user1')
        client2, userId2 = self.quickMintUser('user2', 'user2')

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        project.addMemberById(userId2, userlevels.OWNER)
        self.webLogin('user1', 'user1')
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetchWithRedirect('/project/testproject/demoteMember?userId=%d' % userId2)
        assert(project.getMembers() == [[userId, 'user1', userlevels.OWNER],
                                        [userId2, 'user2', userlevels.DEVELOPER]])


if __name__ == '__main__':
    testsuite.main()
