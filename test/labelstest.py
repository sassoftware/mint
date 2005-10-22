#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import mint_server
from mint import users
from mint.projects import LabelMissing

class LabelsTest(MintRepositoryHelper):
    def testBasicAttributes(self):
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

        assert client.server.getLabel(newLabelId) == ('bar.rpath.org@rpl:testbranch', 'http://bar.rpath.org/conary/', 'user1', 'pass1')

        project.removeLabel(newLabelId)
        assert(project.getLabelIdMap() ==\
            {"foo.rpath.org@rpl:devel": 1})

        try:
            client.server.getLabel(newLabelId)
            self.fail("label should not exist")
        except LabelMissing:
            pass

    def testSSL(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Test Project", "test", "localhost")
        project = client.getProject(projectId)

        # require no SSL repository map
        noSSL = project.getConaryConfig(useSSL = False)
        assert(noSSL.repositoryMap.values()[0].startswith("http://"))
        
        # require SSLized repository map
        SSL = project.getConaryConfig(useSSL = True)
        assert(SSL.repositoryMap.values()[0].startswith("https://"))
        
        # let the database decide
        default = project.getConaryConfig()
        assert(default.repositoryMap.values()[0].startswith("http://"))
 

if __name__ == "__main__":
    testsuite.main()
