#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
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

        if len(client.server.getJobIds(-1)) != 1:
            self.fail("get all Job Id's returned incorrect results")
        # important to test separately: finishing a job generates
        # follow-on SQL statements
        job.setStatus(jobstatus.FINISHED,"Finished")

    def testStubImage(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageType(releasetypes.STUB_IMAGE)
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())
       
        client.getCfg().imagesPath = self.imagePath
        imagegen = stub_image.StubImage(client, client.getCfg(), job, release.getId())
        imagegen.write()
        release.setFiles([(self.imagePath + "/stub.iso", "Stub")])
        
        self.verifyFile(self.imagePath + "/stub.iso", "Hello World!\n")
        
        release.refresh()
        files = release.getFiles()
        assert(files == [(1, "stub.iso", "Stub")])

        fileInfo = client.getFileInfo(files[0][0])
        assert(fileInfo == (release.getId(), 0, self.imagePath + '/stub.iso', 'Stub'))

        try:
            fileInfo = client.getFileInfo(99999)
            self.fail("Should have failed to find file")
        except jobs.FileMissing:
            pass

if __name__ == "__main__":
    testsuite.main()
