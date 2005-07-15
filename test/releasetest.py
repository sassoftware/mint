#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp

class ReleaseTest(rephelp.RepositoryHelper):
    def testBasicAttributes(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo")

        release = client.newRelease(projectId, "Test Release")
        assert(release.getName() == "Test Release")
        release.setTrove("group-trove", "/conary.rpath.com@rpl:devel/1.0-1-1", "1#x86")
        assert(release.getTrove() ==\
            ('group-trove', '/conary.rpath.com@rpl:devel/1.0-1-1', '1#x86'))
        assert(release.getArch() == "x86")

        release.setFiles(["file1", "file2"])
        assert(release.getFiles() ==\
            [(1, 'file1'), (2, 'file2')])
        

if __name__ == "__main__":
    testsuite.main()
