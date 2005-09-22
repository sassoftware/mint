#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels

class ProjectTest(MintRepositoryHelper):
    def testBasicAttributes(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)
        project.editProject("http://example.com/", "Description")

        project = client.getProject(projectId)
        assert(project.getFQDN() == "foo.rpath.org")
        assert(project.getHostname() == "foo")
        assert(project.getDomainname() == "rpath.org")
        assert(project.getName() == "Foo")
        assert(project.getDesc() == "Description")
        assert(project.getProjectUrl() == "http://example.com/")
        assert(project.getMembers() ==\
            [[2, 'testuser', userlevels.OWNER]])
    
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
        
    def testLabels(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Foo", "foo", "rpath.org")
        project = client.getProject(projectId)
    
        assert(project.getRepoMap() ==\
            ["foo.rpath.org http://mintauth:mintpass@localhost:%i/repos/foo/" %self.getPort()])
        assert(project.getLabelIdMap() ==\
            {"foo.rpath.org@rpl:devel": 1})
        
        newLabelId = project.addLabel("bar.rpath.org@rpl:devel",
            "http://rpath.org/repos/bar/", "user1", "pass1")
        assert(project.getLabelById(newLabelId) == "bar.rpath.org@rpl:devel")

        assert(project.getRepoMap() ==\
            ['foo.rpath.org http://mintauth:mintpass@localhost:%i/repos/foo/' %self.getPort(),
             'bar.rpath.org http://user1:pass1@rpath.org/repos/bar/'])
        assert(project.getLabelIdMap() ==\
            {'bar.rpath.org@rpl:devel': newLabelId,
             'foo.rpath.org@rpl:devel': 1})
        
        project.editLabel(newLabelId, "bar.rpath.org@rpl:testbranch",
            "http://bar.rpath.org/conary/", "user1", "pass1")
        assert(project.getLabelById(newLabelId) == "bar.rpath.org@rpl:testbranch")
                
        project.removeLabel(newLabelId)
        assert(project.getLabelIdMap() ==\
            {"foo.rpath.org@rpl:devel": 1})


if __name__ == "__main__":
    testsuite.main()
