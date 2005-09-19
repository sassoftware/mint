#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp
from mint import jobstatus
from mint import jobs

class JobsTest(rephelp.RepositoryHelper):
    def testJobs(self):
        client = self.getMintClient("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        job = client.startImageJob(release.getId())
        jobList = list(client.iterJobs(releaseId = release.getId()))
        assert(jobList[0].getReleaseId() == release.getId())

        # test restarting jobs
        job.setStatus(jobstatus.ERROR, "Error Message")
        client.startImageJob(release.getId())

        assert(job.getStatus() == jobstatus.WAITING)

        # test duplicate job handling
        try:
            job2 = client.startImageJob(release.getId())
        except jobs.DuplicateJob:
            pass
        else:
            self.fail("expected exception jobs.DuplicateJob")
        
if __name__ == "__main__":
    testsuite.main()
