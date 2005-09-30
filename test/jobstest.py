#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import jobstatus
from mint import jobs
from mint import releasetypes
from mint.distro import stub_image

class JobsTest(MintRepositoryHelper):
    def testJobs(self):
        client, userId = self.quickMintUser("testuser", "testpass")
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

    def testStubImage(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageType(releasetypes.STUB_IMAGE)
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())
       
        imagegen = stub_image.StubImage(client, client.getCfg(), job, release.getId())
        imagegen.write()
        
        self.verifyFile(self.reposDir + "/images/stub.iso", "Hello World!\n")
        
        
if __name__ == "__main__":
    testsuite.main()
