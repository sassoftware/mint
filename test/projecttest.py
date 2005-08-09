#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp
from mint import userlevels

class ProjectTest(rephelp.RepositoryHelper):
    def testBasicAttributes(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        project = client.getProject(projectId)
        project.setDesc("Description")

        project = client.getProject(projectId)
        assert(project.getFQDN() == "foo.rpath.org")
        assert(project.getHostname() == "foo")
        assert(project.getDomainname() == "rpath.org")
        assert(project.getName() == "Foo")
        assert(project.getDesc() == "Description")
        assert(project.getMembers() ==\
            [[2, 'testuser', userlevels.OWNER]])
    
    def testMembers(self):
        # XXX disabled
        return
        
        client = self.openMint(("test", "foo"))
        otherUserId = client.registerNewUser("member", "memberpass", "Test Member",
                        "test@example.com", "test at example.com", "", active=True)
 
        client = self.getMintClient("testuser", "testpass")
                                                       
        projectId = client.newProject("Foo", "foo", "rpath.org")
        project = client.getProject(projectId)

        project.addMemberById(otherUserId, userlevels.DEVELOPER)
        print project.getMembers()
                    
    def testLabels(self):
        client = self.getMintClient("testuser", "testpass")

        projectId = client.newProject("Foo", "foo", "rpath.org")
        project = client.getProject(projectId)
    
        assert(project.getRepoMap() ==\
            ["foo.rpath.org http://testuser:testpass@foo.rpath.org/conary/"])
        assert(project.getLabelIdMap() ==\
            {"foo.rpath.org@rpl:devel": 1})
        
        newLabelId = project.addLabel("bar.rpath.org@rpl:devel",
            "http://bar.rpath.org/conary/", "user1", "pass1")
        assert(project.getLabelById(newLabelId) == "bar.rpath.org@rpl:devel")

        assert(project.getRepoMap() ==\
            ['foo.rpath.org http://testuser:testpass@foo.rpath.org/conary/',
             'bar.rpath.org http://user1:pass1@bar.rpath.org/conary/'])
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
