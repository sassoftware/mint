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
from mint.mint_server import ParameterError

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
        except DuplicateItem:
            pass
        else:
            self.fail("expected DuplicateItem exception")
   
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
        for hostname in ('admin', 'a bad name', None):
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



if __name__ == "__main__":
    testsuite.main()
