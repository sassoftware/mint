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
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        job = client.startImageJob(release.getId())
        jobs = list(client.iterJobs(releaseId = release.getId()))
        assert(jobs[0].getReleaseId() == release.getId())

if __name__ == "__main__":
    testsuite.main()
