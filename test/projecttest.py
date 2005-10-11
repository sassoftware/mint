#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.database import DuplicateItem

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

    def testGetProjectsByMember(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Test Project", "test", "localhost")

        projects = client.getProjectsByMember(userId)
        assert(projects[0][0].getId() == projectId)
        assert(projects[0][1] == userlevels.OWNER)



if __name__ == "__main__":
    testsuite.main()
