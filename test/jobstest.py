#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp
from mint import jobstatus

class JobsTest(rephelp.RepositoryHelper):
    def testJobs(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        job = client.startImageJob(release.getId())
        jobs = list(client.iterJobs(releaseId = release.getId()))
        assert(jobs[0].getReleaseId() == release.getId())

        job.setStatus(jobstatus.ERROR, "Error Message")
        client.startImageJob(release.getId())

        assert(job.getStatus() == jobstatus.WAITING)

if __name__ == "__main__":
    testsuite.main()
