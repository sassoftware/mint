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
        except DuplicateItem: # XXX this shouldn't be generic
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

        project = client.getProjectByFQDN("test1.rpath.local")
        assert(projectId == project.getId())
   
    def testMembers(self):
        client = self.openMintClient(("test", "foo"))
        otherUserId = client.registerNewUser("member", "memberpass",
                                             "Test Member",
                        "test@example.com", "test at example.com", "",
                                             active=True)
 
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)

        project.addMemberById(otherUserId, userlevels.DEVELOPER)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'member',
                                         userlevels.DEVELOPER]])

        project.delMemberById(otherUserId)
        assert(project.getMembers() == [[userId, 'testuser',
                                         userlevels.OWNER]])

        project.addMemberByName('member', userlevels.OWNER)
        assert(project.getMembers() == [[otherUserId, 'member',
                                         userlevels.OWNER],
                                        [userId, 'testuser',
                                         userlevels.OWNER]])

        project.updateUserLevel(otherUserId, userlevels.DEVELOPER)
        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'member',
                                         userlevels.DEVELOPER]])

    def testWatcher(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        otherClient, otherUserId = self.quickMintUser("another", "testpass")

        projectId = client.newProject("Test", "test", "rpath.local")
        project = otherClient.getProject(projectId)
        project.addMemberByName("another", userlevels.USER)

        assert(project.getMembers() == [[userId, 'testuser', userlevels.OWNER],
                                        [otherUserId, 'another',
                                         userlevels.USER]])

        assert([x[0].id for x in otherClient.getProjectsByMember(otherUserId)]\
               == [projectId])

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
        cu = self.db.cursor()
        cu.execute("DELETE FROM Users WHERE username=?", newUsername)
        self.db.commit()
        projectId = client.newProject("Foo", "foo", "localhost")
        project = client.getProject(projectId)
        self.assertRaises(ItemNotFound, project.addMemberById, newUserId,
                          userlevels.DEVELOPER)

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
        otherUserId = client.registerNewUser("member", "memberpass",
                                             "Test Member",
                                             "test@example.com",
                                             "test at example.com", "",
                                             active=True)
        unconfirmedUserId = client.registerNewUser("unconfirmed",
                                                   "memberpass",
                                                   "Unconfirmed Member",
                                                   "test@example.com",
                                                   "test at example.com",
                                                   "", active=False)
 
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

        if client.server.getProjectsByUser(userId) !=  [['test.localhost',
                                                         'Test Project', 0]]:
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

        self.assertRaises(ItemNotFound, client.getProject, projectId)
        self.assertRaises(ItemNotFound, watcherClient.getProject, projectId)

        self.assertRaises(ItemNotFound, client.server.getProjectIdByFQDN,
                          "test.localhost")
        self.assertRaises(ItemNotFound, client.server.getProjectIdByHostname,
                          "test")

        self.failIf(client.server.getProjectIdsByMember(watcherId),
                    "Nonmember found hidden project (getProjectIdsByMember)")

        self.failIf(not adminClient.server.getProjectIdsByMember(adminUserId),
                    "Admin missed hidden project (getProjectIdsByMember)")

        self.failIf(not memberClient.server.getProjectIdsByMember(memberId),
                    "Owner missed hidden project (getProjectIdsByMember)")

        self.failIf(watcherClient.server.getProjectIdsByMember(watcherId),
                    "Watcher saw hidden project (getProjectIdsByMember)")

        self.assertRaises(ItemNotFound, client.server.getMembersByProjectId,
                          projectId)

        adminClient.server.getOwnersByProjectName(project.getName())

        self.assertRaises(ItemNotFound, client.userHasRequested, projectId,
                          userId)

        self.assertRaises(ItemNotFound, client.setJoinReqComments,
                          projectId, "foo")
        self.assertRaises(ItemNotFound, client.getJoinReqComments,
                          projectId, userId)
        self.assertRaises(ItemNotFound, client.deleteJoinRequest,
                          projectId, userId)
        self.assertRaises(ItemNotFound, client.listJoinRequests, projectId)


        self.assertRaises(ItemNotFound, project.addMemberById,
                         userId, userlevels.USER)

        self.assertRaises(ItemNotFound, client.server.lastOwner,
                          projectId, adminUserId)
        self.assertRaises(ItemNotFound, client.server.onlyOwner,
                          projectId, adminUserId)
        self.assertRaises(ItemNotFound,
                          watcherClient.server.delMember, projectId, watcherId,
                                                         False)

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

    def testExternalProject(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client, "External Project", "external")
        
        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?", projectId)

        project = client.getProject(projectId)
        assert(client.server._server.getGroupTroves(projectId) == {'external.rpath.local@rpl:devel': []})
        

if __name__ == "__main__":
    testsuite.main()
