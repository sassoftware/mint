#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import jobstatus
from mint import jobs
from mint import releasetypes
from mint.data import RDT_INT, RDT_STRING, RDT_BOOL
from mint.distro import stub_image

from repostest import testRecipe
from conary import versions

class JobsTest(MintRepositoryHelper):
    def testJobs(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        self.stockReleaseFlavor(release.getId())

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
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(release.getId())

        job = client.startImageJob(release.getId())

        client.getCfg().imagesPath = self.imagePath
        imagegen = stub_image.StubImage(client, client.getCfg(), job,
                                        release.getId())
        imagegen.write()
        release.setFiles([[self.imagePath + "/stub.iso", "Stub"]])

        self.verifyFile(self.imagePath + "/stub.iso", "Hello World!\n")

        release.refresh()
        files = release.getFiles()
        assert(files == [{'fileId': 1, 'filename': 'stub.iso',
                          'title': 'Stub', 'size': 13}])

        fileInfo = client.getFileInfo(files[0]['fileId'])
        assert(fileInfo == (release.getId(), 0, self.imagePath + '/stub.iso',
                            'Stub'))

        try:
            fileInfo = client.getFileInfo(99999)
            self.fail("Should have failed to find file")
        except jobs.FileMissing:
            pass

    def testStubImageFileOrder(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        # make sure that the incoming ordering of files is preserved
        release.setFiles([['zaaa.iso', 'Zaaa'], ['aaaa.iso', 'Aaaa']])
        assert(release.getFiles() == [{'size': 0, 'title': 'Zaaa',
                                       'filename': 'zaaa.iso', 'fileId': 1},
                                      {'size': 0, 'title': 'Aaaa',
                                       'filename': 'aaaa.iso', 'fileId': 2}])

    def testJobQueue(self):
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(release.getId())
        job = client.startImageJob(release.getId())

        assert(client.server.getJobStatus(job.getId())['queueLen'] == 0)
        assert(client.server.getReleaseStatus(release.getId())['queueLen'] == 0)
        assert(client.server.getJobWaitMessage(job.getId()) == \
               'Next in line for processing')

        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)
        cookJobId = groupTrove.startCookJob("1#x86")
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 1)
        assert(client.server.getJobWaitMessage(cookJobId) == \
               'Number 2 in line for processing')

        job.setStatus(jobstatus.FINISHED, 'Finished')
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(client.server.getJobWaitMessage(cookJobId) == \
               'Next in line for processing')

        job = client.startImageJob(release.getId())
        assert(client.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(client.server.getJobStatus(job.getId())['queueLen'] == 1)

    def testJobQueueOrder(self):
        cu = self.db.cursor()
        self.openRepository()
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(release.getId())
        job1 = client.startImageJob(release.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        self.db.commit()

        release2 = client.newRelease(projectId, "Test Release")
        release2.setImageTypes([releasetypes.STUB_IMAGE])
        release2.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(release2.getId())
        job2 = client.startImageJob(release2.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        self.db.commit()

        self.failIf(job2.statusMessage == 'Next in line for processing',
                    "Consecutive releases both show up as next.")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        job3 = client.getJob(3)

        self.failIf(job3.statusMessage != 'Number 3 in line for processing',
                    "Release before cook caused wrong queue count")

        release3 = client.newRelease(projectId, "Test Release")
        release3.setImageTypes([releasetypes.STUB_IMAGE])
        release3.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(release3.getId())
        job4 = client.startImageJob(release3.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        self.db.commit()

        self.failIf(job4.statusMessage != 'Number 4 in line for processing',
                    "Cook before release caused wrong queue count")

        allJobs = (job1, job2, job3, job4)

        for job in allJobs:
            cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)

        self.db.commit()

        # regenerate jobs
        job1 = client.startImageJob(release.getId())
        job2 = client.startImageJob(release2.getId())
        job3 = client.getJob(groupTrove.startCookJob("1#x86"))
        job4 = client.startImageJob(release3.getId())

        self.failIf(job1.statusMessage != 'Next in line for processing',
                    "Didn't properly report status of next job")

        for job in (job2, job3, job4):
            self.failIf(job.statusMessage == 'Next in line for processing',
                        "Improperly reported status of job as next-in-line")

    def testJobData(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        self.stockReleaseFlavor(release.getId())

        job = client.startImageJob(release.getId())
        job.setDataValue("mystring", "testing", RDT_STRING)
        job.setDataValue("myint", 123, RDT_INT)

        assert(job.getDataValue("mystring") == "testing")
        assert(int(job.getDataValue("myint")) == 123)

    def testStartCookJob(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        job = client.startNextJob(["1#x86_64"])

        self.failIf(job, "startNextJob returned the wrong architecture")

        job = client.startNextJob(["1#x86"])

        self.failIf(not job, "startNextJob ignored a valid cook job")

        self.failIf(job.status != jobstatus.RUNNING,
                    "job-server is not multi-instance safe")

    def testStartReleaseJob(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        self.stockReleaseFlavor(release.getId())

        relJob = client.startImageJob(release.getId())

        # normally called from job-server
        job = client.startNextJob(["1#x86"])

        self.failIf(job, "startNextJob returned the wrong architecture")

        job = client.startNextJob(["1#x86", "1#x86_64"])

        self.failIf(not job, "startNextJob ignored a valid release job")

        self.failIf(job.status != jobstatus.RUNNING,
                    "job-server is not multi-instance safe")

    def testJobRaceCondition(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        cu = self.db.cursor()
        cu.execute("UPDATE Jobs set owner=1")
        self.db.commit()

        job = client.startNextJob(["1#x86", "1#x86_64"])

        self.failIf(job is not None, "job-server is not multi-instance safe")

        cu.execute("UPDATE Jobs set owner=NULL")
        self.db.commit()

        job = client.startNextJob(["1#x86", "1#x86_64"])

    def testStartJobLocking(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        for i in range(5):
            groupTrove = client.createGroupTrove(projectId, 'group-test',
                                                 '1.0.0', '', False)

            groupTroveId = groupTrove.getId()
            trvName = 'testtrove'
            trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
            trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
            subGroup = ''

            trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                        subGroup, False, False, False)

            cookJobId = groupTrove.startCookJob("1#x86")

        cu = self.db.cursor()
        # make a job unavailable
        cu.execute("UPDATE Jobs SET status=4 WHERE jobId=2")
        # make a job taken
        cu.execute("UPDATE Jobs SET owner=4 WHERE jobId=4")
        self.db.commit()

        job = client.startNextJob(["1#x86"])

        self.failIf(job.id != 1, "Jobs retreived out of order")

        job = client.startNextJob(["1#x86"])

        self.failIf(job.id != 3, "Non-waiting job was selected")

        job = client.startNextJob(["1#x86"])

        self.failIf(job.id != 5, "owned job was selected")

    def testStartJobLockRelease(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test',
                                             '1.0.0', '', False)

        groupTroveId = groupTrove.getId()
        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86_64")

        cu = self.db.cursor()

        cu.execute("SELECT owner FROM Jobs")

        self.failIf(cu.fetchall()[0] != (None,),
                    "Lock on job of incompatible type was not released")

    def testRegenerateRelease(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])

        self.stockReleaseFlavor(release.getId())

        relJob = client.startImageJob(release.getId())

        cu = self.db.cursor()

        cu.execute("SELECT name, value FROM JobData")

        self.failIf(cu.fetchone() != ('arch', '1#x86_64'),
                    "architecture information missing for release")

        cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)

        self.db.commit()

        relJob = client.startImageJob(release.getId())

        cu.execute("SELECT status, owner FROM Jobs")

        self.failIf(cu.fetchone() != (jobstatus.WAITING, None),
                    "Job not regenerated properly. will never run")

    def testRegenerateCook(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        cu = self.db.cursor()

        cu.execute("SELECT name, value FROM JobData")

        self.failIf(cu.fetchone() != ('arch', '1#x86'),
                    "architecture information missing for cook")

        cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)

        self.db.commit()

        cookJob = groupTrove.startCookJob("1#x86")

        cu.execute("SELECT status, owner FROM Jobs")

        self.failIf(cu.fetchone() != (jobstatus.WAITING, None),
                    "Job not regenerated properly. will never run")


if __name__ == "__main__":
    testsuite.main()
