#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.database import DuplicateItem, ItemNotFound
from mint.projects import InvalidHostname
from mint.mint_server import ParameterError, PermissionDenied

class ProjectTest(MintRepositoryHelper):
    def testBasicAttributes(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)

        project = client.getProject(projectId)
        assert(project.getFQDN() == "foo.rpath.org")
        assert(project.getHostname() == "foo")
        assert(project.getDomainname() == "rpath.org")
        assert(project.getName() == "Foo")
        assert(project.getMembers() ==\
            [[userId, 'testuser', userlevels.OWNER]])

        assert(project.hidden == 0)
        assert(project.external == 0)
        assert(project.disabled == 0)

    def testEditProject(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)
        project.editProject("http://example.com/", "Description", "Foo Title")
        project.refresh()
        
        assert(project.getName() == "Foo Title")
        assert(project.getDesc() == "Description")
        assert(project.getProjectUrl() == "http://example.com/")
  
        # create a new project to conflict with
        newProjectId = client.newProject("Foo2", "foo2", "rpath.org")
        
        try:
            project.editProject("http://example.com/", "Description", "Foo2")
        except: # XXX this shouldn't be generic
            pass
        else:
            self.fail("expected DuplicateItem exception")
   
        # test automatic prepending of http://
        project.editProject("www.example.com", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "http://www.example.com")

        # except when there's no project URL
        project.editProject("", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "")
        
    def testGetProjects(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client, hostname = "test1")

        project = client.getProjectByHostname("test1")
        assert(projectId == project.getId())

        project = client.getProjectByFQDN("test1.localhost")
        assert(projectId == project.getId())
   
    def testMembers(self):
        client = self.openMintClient(("test", "foo"))
        otherUserId = client.registerNewUser("member", "memberpass", "Test Member",
                        "test@example.com", "test at example.com", "", active=True)
 
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)

        project.addMemberById(otherUserId, userlevels.DEVELOPER)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'member', userlevels.DEVELOPER]])

        project.delMemberById(otherUserId)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER]])

        project.addMemberByName('member', userlevels.OWNER)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'member', userlevels.OWNER]])

        project.updateUserLevel(otherUserId, userlevels.DEVELOPER)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'member', userlevels.DEVELOPER]])

    def testDuplicateMembers(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        newClient, newUserId = self.quickMintUser("newuser", "testpass")
        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)
        project.addMemberById(newUserId, userlevels.DEVELOPER)
        # a consecutive addMember should run properly--just becomes an update
        project.addMemberById(newUserId, userlevels.OWNER)

    def testMissingUser(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        newUsername = "newuser"
        newClient, newUserId = self.quickMintUser("newuser", "testpass")
        cu = self.mintServer.authDb.cursor()
        cu.execute("DELETE FROM Users WHERE user=?", newUsername)
        self.mintServer.authDb.commit()
        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)
        try:
            project.addMemberById(newUserId, userlevels.DEVELOPER)
            self.fail("User was allowed to be added to a project without an authrepo entry!")
        except ItemNotFound:
            pass

    def testBadHostname(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        for hostname in ('admin', 'a bad name', ''):
            try:
                projectId = client.newProject("Foo", hostname, 'localhost')
                self.fail("allowed to create a project with a bad name")
            except InvalidHostname:
                pass
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if str(exc_value).split(' ')[0] != 'ParameterError':
                    raise

    def testUnconfirmedMembers(self):
        client = self.openMintClient(("test", "foo"))
        otherUserId = client.registerNewUser("member", "memberpass", "Test Member",
                        "test@example.com", "test at example.com", "", active=True)
        unconfirmedUserId = client.registerNewUser("unconfirmed", "memberpass", "Unconfirmed Member",
                        "test@example.com", "test at example.com", "", active=False)
 
        client, userId = self.quickMintUser("testuser", "testpass")
        
        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)

        #Try to add an unconfirmed member to the project by userName
        try:
            project.addMemberByName("unconfirmed", userlevels.DEVELOPER)
        except ItemNotFound, e:
            pass
        else:
            self.fail("ItemNotFound Exception expected")

        #Try to add an unconfirmed member to the project by userId
        try:
            project.addMemberById(unconfirmedUserId, userlevels.DEVELOPER)
        except ItemNotFound, e:
            pass
        else:
            self.fail("ItemNotFound Exception expected")

    def testGetProjectsByMember(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Test Project", "test", "localhost")

        projects = client.getProjectsByMember(userId)
        assert(projects[0][0].getId() == projectId)
        assert(projects[0][1] == userlevels.OWNER)

        if client.server.getProjectsByUser(userId) !=  [['test.localhost', 'Test Project', 0]]:
            self.fail("getProjectsByUser returned incorrect results")

    def testHideProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")
        client, userId = self.quickMintUser("testuser", "testpass")
        memberClient, memberId = self.quickMintUser("memberuser","testpass")
        watcherClient, watcherId = self.quickMintUser("watcher","testpass")
        #client.server.auth.admin = True
        projectId = adminClient.newProject("Test Project", "test", "localhost")
        project = adminClient.getProject(projectId)
        project.addMemberById(memberId, userlevels.OWNER)
        watcherProject = watcherClient.getProject(projectId)
        watcherProject.addMemberById(watcherId, userlevels.USER)
        project = client.getProject(projectId)
        adminClient.hideProject(projectId)

        # try getting the project from various levels
        memberClient.getProject(projectId)
        adminClient.getProject(projectId)

        try:
            client.getProject(projectId)
            self.fail("getProject: Project should appear to not exist to non-members")
        except ItemNotFound:
            pass

        try:
            watcherClient.getProject(projectId)
            self.fail("getProject: Project should appear to not exist to user-members")
        except ItemNotFound:
            pass

        try:
            client.server.getProjectIdByFQDN("test.localhost")
            self.fail("getProjectIdByFQDN: Project should appear to not exist to non-members")
        except ItemNotFound:
            pass

        try:
            client.server.getProjectIdByHostname("test")
            self.fail("getProjectIdByHostname: Project should appear to not exist to non-members")
        except ItemNotFound:
            pass

        if client.server.getProjectIdsByMember(watcherId):
            self.fail("getProjectIdsByMember returned a hidden project for a nonmember")

#        if watcherClient.server.getProjectIdsByMember(watcherId):
#            self.fail("getProjectIdsByMember returned a hidden project for a user")

        try:
            client.server.getMembersByProjectId(projectId)
            self.fail("getMembersByProjectId: Project should appear to not exist to non-members")
        except ItemNotFound:
            pass

        adminClient.server.getOwnersByProjectName(project.getName())

        try:
            client.userHasRequested(projectId, userId)
            self.fail("userHasRequested: did not result in error for non-member")
        except ItemNotFound:
            pass

        try:
            client.setJoinReqComments(projectId, "foo")
            self.fail("non-member was allowed to set join request")
        except ItemNotFound:
            pass

        try:
            client.getJoinReqComments(projectId, userId)
            self.fail("non-member was allowed to get join request")
        except ItemNotFound:
            pass

        try:
            client.deleteJoinRequest(projectId, userId)
            self.fail("non-member was allowed to delete join request")
        except ItemNotFound:
            pass

        try:
            client.listJoinRequests(projectId)
            self.fail("non-member was allowed to set join request")
        except ItemNotFound:
            pass

        try:
            project.addMemberById(userId, userlevels.USER)
            self.fail("user was allowed to watch a hidden project")
        except ItemNotFound:
            pass

        try:
            client.server.lastOwner(projectId, adminUserId)
            self.fail("lastOwner should have failed")
        except ItemNotFound:
            pass

        try:
            client.server.onlyOwner(projectId, adminUserId)
            self.fail("onlyOwner should have failed")
        except ItemNotFound:
            pass

        try:
            watcherClient.server.delMember(projectId, watcherId, False)
            self.fail("delMember should not have worked")
        except ItemNotFound:
            pass

        memberClient.server.getUserLevel(watcherId, projectId)

        adminClient.unhideProject(projectId)

    def testDisableProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")
        client, userId = self.quickMintUser("testuser", "testpass")
        memberClient, memberId = self.quickMintUser("memberuser","testpass")
        watcherClient, watcherId = self.quickMintUser("watcher","testpass")
        #client.server.auth.admin = True
        projectId = adminClient.newProject("Test Project", "test", "localhost")
        project = adminClient.getProject(projectId)
        project.addMemberById(memberId, userlevels.OWNER)
        watcherProject = watcherClient.getProject(projectId)
        watcherProject.addMemberById(watcherId, userlevels.USER)
        project = client.getProject(projectId)
        adminClient.disableProject(projectId)

        # try getting the project from various levels
        adminClient.getProject(projectId)

        try:
            memberClient.getProject(projectId)
            self.fail("getProject: Members should not be able to see disabled projects")
        except ItemNotFound:
            pass

        try:
            client.getProject(projectId)
            self.fail("getProject: Project should appear to not exist to non-members")
        except ItemNotFound:
            pass

        try:
            watcherClient.getProject(projectId)
            self.fail("getProject: Project should appear to not exist to user-members")
        except ItemNotFound:
            pass

        adminClient.enableProject(projectId)
        adminClient.getProject(projectId)
        memberClient.getProject(projectId)
        client.getProject(projectId)
        watcherClient.getProject(projectId)

if __name__ == "__main__":
    testsuite.main()
