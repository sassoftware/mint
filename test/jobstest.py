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

from repostest import testRecipe
from conary import versions

class JobsTest(MintRepositoryHelper):
    def testJobs(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        job = client.startImageJob(release.getId())
        job = release.getJob()
        assert(job.getReleaseId() == release.getId())

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

        if len(client.server.getJobIds()) != 1:
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
        release.setFiles([[self.imagePath + "/stub.iso", "Stub"]])
        
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

    def testJobQueue(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageType(releasetypes.STUB_IMAGE)
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        assert(client.server.getJobStatus(job.getId())['queueLen'] == 0)
        assert(client.server.getReleaseStatus(release.getId())['queueLen'] == 0)
        assert(client.server.getJobWaitMessage(job.getId()) == 'Waiting for job server')

        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.localhost@rpl:devel"),
            ignoreDeps = True)

        trvName = 'testtrove'
        trvVersion = '/test.localhost@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)
        cookJobId = groupTrove.startCookJob()
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 1)
        assert(client.server.getJobWaitMessage(cookJobId) == 'Waiting for 1 job to complete')

        job.setStatus(jobstatus.FINISHED, 'Finished')
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(client.server.getJobWaitMessage(cookJobId) == 'Waiting for job server')

        job = client.startImageJob(release.getId())
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(client.server.getJobStatus(job.getId())['queueLen'] == 1)

if __name__ == "__main__":
    testsuite.main()
