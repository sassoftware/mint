#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MINT_PROJECT_DOMAIN
import time
import os

import fixtures
from fixtures import fixture

from mint import shimclient
from mint import config
from mint import jobstatus
from mint import jobs
from mint import releasetypes
from mint import cooktypes
from mint import mint_error
from mint.data import RDT_INT, RDT_STRING, RDT_BOOL
from mint.distro import stub_image, jsversion
from mint.distro.flavors import stockFlavors
from mint.server import ParameterError, MintServer

from conary import versions
from conary import dbstore
from conary.deps import deps
from conary.lib import util

class JobsTest(fixtures.FixturedUnitTest):
    def stockReleaseFlavor(self, db, releaseId, arch = "x86_64"):
        cu = db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Releases set troveFlavor=? WHERE releaseId=?", flavor, releaseId)
        db.commit()

    #####
    # test startNextJob for just images
    #####

    @fixture('ImageJob')
    def testStartImageNoJobType(self, db, client, data):
        # ask for no job types
        job = client.startNextJob(["1#x86_64"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned something when nothing wanted")

    @fixture('ImageJob')
    def testStartImageNoType(self, db, client, data):
        # ask for no arch type or job types
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned something when nothing wanted")

    @fixture('ImageJob')
    def testStartImageNoArch(self, db, client, data):
        # ask for no arch
        job = client.startNextJob([],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong image type")

    @fixture('ImageJob')
    def testStartImageWrongType(self, db, client, data):
        # ask for a different image type
        job = client.startNextJob(["1#x86_64"],
                                  {'imageTypes' : [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong image type")

    @fixture('ImageJob')
    def testStartImageWrongArch(self, db, client, data):
        # ask for a different architecture
        job = client.startNextJob(["1#x86"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched the wrong architecture")

    @fixture('ImageJob')
    def testStartImageCookArch(self, db, client, data):
        # ask for a cook job with wrong arch
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erroneously matched cook "
                    "job for wrong arch")

    @fixture('ImageJob')
    def testStartImageCook(self, db, client, data):
        # ask for a cook job with right arch
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erreneously matched cook job")

    @fixture('ImageJob')
    def testStartImage(self, db, client, data):
        # ask for the right parameters
        job = client.startNextJob(["1#x86_64"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNext job didn't match for correct values")

    #####
    # test startNextJob for just cooks
    #####

    @fixture('CookJob')
    def testStartCookWrongArch(self, db, client, data):
        # ask for a cook job with wrong arch
        job = client.startNextJob(["1#x86_64"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job for wrong arch")

    @fixture('CookJob')
    def testStartCook(self, db, client, data):
        # ask for a cook job with right arch
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob matched cook job for wrong arch")

    @fixture('CookJob')
    def testStartCookImageArch(self, db, client, data):
        # ask for a image job with wrong arch
        job = client.startNextJob(["1#x86_64"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job when asked for image")

    @fixture('CookJob')
    def testStartCookImage(self, db, client, data):
        # ask for a image job with right arch
        job = client.startNextJob(["1#x86"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job when asked for image")

    @fixture('CookJob')
    def testStartCookNoJobType(self, db, client, data):
        # ask for a no job with right arch
        job = client.startNextJob(["1#x86"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixture('CookJob')
    def testStartCookNoJobType2(self, db, client, data):
        # ask for no job with wrong arch
        job = client.startNextJob(["1#x86_64"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixture('CookJob')
    def testStartCookNoJob(self, db, client, data):
        # ask for no job with no arch
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixture('CookJob')
    def testStartCookNoJobArch(self, db, client, data):
        # ask for an image job with no arch
        job = client.startNextJob([],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    #####
    # test startNextJob for cooks and images together
    #####

    @fixture('BothJobs')
    def testStartCompImage(self, db, client, data):
        # ask for an image job with right arch
        job = client.startNextJob(['1#x86_64'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored an image job")

    @fixture('BothJobs')
    def testStartCompCook(self, db, client, data):
        # ask for an image job with right arch
        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored a cook job")

    @fixture('BothJobs')
    def testStartCompImageArch(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob(['1#x86'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched image job wrong arch")

    @fixture('BothJobs')
    def testStartCompCookArch(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job wrong arch")


    @fixture('BothJobs')
    def testStartCompImageNoArch(self, db, client, data):
        # ask for an image job with no arch
        job = client.startNextJob([],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched image job no arch")

    @fixture('BothJobs')
    def testStartCompCookNoArch(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob([],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job no arch")

    @fixture('BothJobs')
    def testStartCompNoArch(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no arch and no type")

    @fixture('BothJobs')
    def testStartCompArch(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob(['1#x86'], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no type")

    @fixture('BothJobs')
    def testStartCompArch2(self, db, client, data):
        # ask for an image job with wrong arch
        job = client.startNextJob(['1#x86_64'], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no type")

    #####
    # test both cooks and images while asking for both
    #####

    @fixture('BothJobs')
    def testStartCompBothCook(self, db, client, data):
        # ask for all jobs with x86 arch (will match cook)
        job = client.startNextJob(['1#x86'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob ignored a cook job")

    @fixture('BothJobs')
    def testStartCompBothImage(self, db, client, data):
        # ask for all jobs with x86_64 arch (will match image)
        job = client.startNextJob(['1#x86_64'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.releaseId),
                    "startNextJob ignored an image job")

    @fixture('BothJobs')
    def testStartCompBothNoArch(self, db, client, data):
        # ask for all jobs no arch
        job = client.startNextJob([],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched for no arch")

    @fixture('BothJobs')
    def testStartCompBothArch(self, db, client, data):
        # ask for all jobs
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.releaseId),
                    "startNextJob didn't match image job")

        # ask for all jobs
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob didn't match group trove")

    @fixture('BothJobs')
    def testStartCompImageType(self, db, client, data):
        # ask for all jobs but wrong image type
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'imageTypes' : [releasetypes.RAW_HD_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob didn't match cook")

    #####
    # and just to round it out, test for bad parmaeters
    #####

    @fixture('Empty')
    def testStartBadArch(self, db, client, data):
        self.assertRaises(ParameterError,
                          client.startNextJob, ['this is not a frozen flavor'],
                          {'imageTypes' : [releasetypes.RAW_HD_IMAGE],
                           'cookTypes' : [cooktypes.GROUP_BUILDER]},
                          jsversion.getDefaultVersion())

    @fixture('Empty')
    def testStartBadImage(self, db, client, data):
        self.assertRaises(ParameterError,
                          client.startNextJob, ['1#x86'],
                          {'imageTypes' : [9999],
                           'cookTypes' : [cooktypes.GROUP_BUILDER]},
                          jsversion.getDefaultVersion())

    @fixture('Empty')
    def testStartBadCook(self, db, client, data):
        self.assertRaises(ParameterError,
                          client.startNextJob, ['1#x86'],
                          {'imageTypes' : [releasetypes.RAW_HD_IMAGE],
                           'cookTypes' : [9999]},
                          jsversion.getDefaultVersion())

    @fixture('ImageJob')
    def testStartLegalImage(self, db, client, data):
        # ask for an image type that's technically in the list, but not served
        # by this server. historically this raised permission denied.
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'imageTypes' : [releasetypes.NETBOOT_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erroneously matched image")

    #####
    # ensure jobs do not get inadverdently respwaned
    #####

    @fixture('CookJob')
    def testStartCookFinished(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixture('CookJob')
    def testStartCookFinished2(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixture('CookJob')
    def testStartCookFinished3(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixture('ImageJob')
    def testStartImageFinished(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixture('ImageJob')
    def testStartImageFinished2(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixture('ImageJob')
    def testStartImageFinished3(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixture('CookJob')
    def testStartCookOwned(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixture('CookJob')
    def testStartCookOwned2(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixture('CookJob')
    def testStartCookOwned3(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixture('ImageJob')
    def testStartImageOwned(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixture('ImageJob')
    def testStartImageOwned2(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixture('ImageJob')
    def testStartImageOwned3(self, db, client, data):
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixture('Empty')
    def testMimicJobServer(self, db, client, data):
        # historically this always failed with permission denied, but it
        # definitely needs to be allowed. return value doesn't matter
        job = client.startNextJob(['1#x86_64'],
                                  {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

    #####
    # test jobserver version
    #####

    @fixture('Release')
    def testImageJSVersion(self, db, client, data):
        # ensure an image job cannot be started for a mismatched job server.
        cu = db.cursor()
        cu.execute("""UPDATE ReleaseData SET value='illegal'
                          WHERE name='jsversion'""")
        db.commit()

        self.assertRaises(mint_error.JobserverVersionMismatch,
                          client.startImageJob, data['releaseId'])

    @fixture('ImageJob')
    def testStartImageJobJSV(self, db, client, data):
        # masquerading as a job server version that server doesn't support
        # raises parameter error.
        self.assertRaises(ParameterError, client.startNextJob,
                          ['1#x86', '1#x86_64'],
                          {'imageTypes': [releasetypes.RAW_HD_IMAGE]},
                          'wackyversion')

    @fixture('ImageJob')
    def testStartImageJobJSV2(self, db, client, data):
        # ensure image jobs cannot be selected for mismatched job server type
        # using only image types defined
        cu = db.cursor()
        cu.execute("""UPDATE ReleaseData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'imageTypes': [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a mismatched jobserver image")

    @fixture('ImageJob')
    def testStartImageJobJSV3(self, db, client, data):
        # ensure image jobs cannot be selected for mismatched job server type
        # using composite job request
        cu = db.cursor()
        cu.execute("""UPDATE ReleaseData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'imageTypes': [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a mismatched jobserver image")

    @fixture('BothJobs')
    def testStartCookJobJSV(self, db, client, data):
        # ensure cook jobs don't interact badly with job server version
        cu = db.cursor()
        cu.execute("""UPDATE ReleaseData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'imageTypes': [releasetypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob ignored a cook job")

# ############################################################################
##############################################################################

    @fixture('Release')
    def testJobs(self, db, client, data):
        release = client.getRelease(data['releaseId'])

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

    @fixture('Release')
    def testStubImage(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        project = client.getProject(data['projectId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        from mint.distro import jobserver
        isocfg = jobserver.IsoGenConfig()
        isocfg.finishedPath = self.imagePath
        imagegen = stub_image.StubImage(client, isocfg, job,
                                        release, project)
        imagegen.write()
        release.setFiles([[self.imagePath + "/stub.iso", "Stub"]])

        assert(os.path.exists(self.imagePath + "/stub.iso"))

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

    @fixture('Release')
    def testStubImageFileOrder(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        # make sure that the incoming ordering of files is preserved
        release.setFiles([['zaaa.iso', 'Zaaa'], ['aaaa.iso', 'Aaaa']])
        assert(release.getFiles() == [{'size': 0, 'title': 'Zaaa',
                                       'filename': 'zaaa.iso', 'fileId': 1},
                                      {'size': 0, 'title': 'Aaaa',
                                       'filename': 'aaaa.iso', 'fileId': 2}])

    @fixture('Release')
    def testJobQueue(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        assert(client.server.getJobStatus(job.getId())['queueLen'] == 0)
        assert(client.server.getReleaseStatus(release.getId())['queueLen'] == 0)
        assert(client.server.getJobWaitMessage(job.getId()) == \
               'Next in line for processing')

        project = client.getProject(data['projectId'])

        groupTrove = client.createGroupTrove(data['projectId'], 'group-test', '1.0.0',
                                             'No Description', False)
        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
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

    @fixture('Release')
    def testWaitStatus(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        self.failIf(client.server.getJobWaitMessage(job.id) != \
                    'Next in line for processing',
                    "Job failed to recognize that it was next")

        newMessage = "And now for something completely different"
        job.setStatus(jobstatus.WAITING, newMessage)

        cu = db.cursor()
        cu.execute("SELECT statusMessage FROM Jobs WHERE jobId=?", job.id)

        self.failIf(cu.fetchone()[0] != newMessage,
                    "database status message did not reflect true value.")

        self.failIf(client.server.getJobWaitMessage(job.id) != \
                    'Next in line for processing',
                    "Job failed to recognize that it was next")

        cu = db.cursor()
        cu.execute("SELECT statusMessage FROM Jobs WHERE jobId=?", job.id)

        self.failIf(cu.fetchone()[0] != newMessage,
                    "database status message was altered.")

    @fixture('Release')
    def testRunningStatus(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        newMsg = "We are the knights who say 'Ni!'"
        job.setStatus(jobstatus.RUNNING, newMsg)

        # refresh the job object
        job = client.getJob(job.id)

        self.failIf(job.getStatusMessage() == 'Next in line for processing',
                    "job mistook itself for waiting.")

    @fixture('Release')
    def testStartTimestamp(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(release.getId())

        cu = db.cursor()
        cu.execute("UPDATE Jobs set timeStarted = 100 where jobId=?", job.id)
        db.commit()

        # refresh job
        job = client.getJob(job.id)

        self.failIf(job.timeStarted != 100,
                    "pre-start: job doesn't reflect altered timestamp")

        newJob = client.startNextJob(['1#x86', '1#x86_64'],
                                    {'imageTypes':
                                     [releasetypes.STUB_IMAGE]},
                                     jsversion.getDefaultVersion())

        assert(newJob.id == job.id)

        self.failIf(job.timeStarted != 100,
                    "post-start: job doesn't reflect altered timestamp")

        self.failIf(job.timeStarted == newJob.timeStarted,
                    "Job's start timestamp wasn't adjusted. timing metrics "
                    "will be misleading")

    @fixture('Empty')
    def testTimestampInteraction(self, db, client, data):
        projectId = client.newProject("Foo", "foo", "rpath.org")

        cu = db.cursor()

        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(db, release.getId())
        job = client.startImageJob(release.getId())

        cu.execute("UPDATE Releases SET troveLastChanged=0")
        db.commit()

        release2 = client.newRelease(projectId, "Test Release")
        release2.setImageTypes([releasetypes.STUB_IMAGE])
        release2.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(db, release2.getId())
        job2 = client.startImageJob(release2.getId())

        cu.execute("UPDATE Releases SET troveLastChanged=0")
        db.commit()

        release3 = client.newRelease(projectId, "Test Release")
        release3.setImageTypes([releasetypes.STUB_IMAGE])
        release3.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(db, release3.getId())
        job3 = client.startImageJob(release3.getId())

        assert(job.getStatusMessage() == 'Next in line for processing')
        assert(job2.getStatusMessage() == 'Number 2 in line for processing')
        assert(job3.getStatusMessage() == 'Number 3 in line for processing')

        newJob = client.startNextJob(['1#x86', '1#x86_64'],
                                    {'imageTypes':
                                     [releasetypes.STUB_IMAGE]},
                                     jsversion.getDefaultVersion())

        job = client.getJob(job.id)
        job2 = client.getJob(job2.id)
        job3 = client.getJob(job3.id)

        # testing this method directly ensures the getJob call has the correct
        # status message at the moment of instantiation.
        assert(job.getStatusMessage() == 'Starting')
        assert(job2.getStatusMessage() == 'Next in line for processing')
        assert(job3.getStatusMessage() == 'Number 2 in line for processing')

        # of special importance is the queue length. should be zero for jobs
        # not actually in the queue...
        assert(client.server._server.getJobStatus(job.id) == \
               {'status': 1,
                'message': 'Starting',
                'queueLen': 0})

        assert(client.server._server.getJobStatus(job2.id) == \
               {'status': 0,
                'message': 'Next in line for processing',
                'queueLen': 0})

        assert(client.server._server.getJobStatus(job3.id) == \
               {'status': 0,
                'message': 'Number 2 in line for processing',
                'queueLen': 1})

    @fixture('Empty')
    def testJobQueueOrder(self, db, client, data):
        cu = db.cursor()

        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([releasetypes.STUB_IMAGE])
        release.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(db, release.getId())
        job1 = client.startImageJob(release.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        db.commit()

        release2 = client.newRelease(projectId, "Test Release")
        release2.setImageTypes([releasetypes.STUB_IMAGE])
        release2.setDataValue('stringArg', 'Hello World!')

        self.stockReleaseFlavor(db, release2.getId())
        job2 = client.startImageJob(release2.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        db.commit()

        self.failIf(job2.statusMessage == 'Next in line for processing',
                    "Consecutive releases both show up as next.")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
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

        self.stockReleaseFlavor(db, release3.getId())
        job4 = client.startImageJob(release3.getId())

        # protect this release from being auto-deleted
        cu.execute("UPDATE Releases SET troveLastChanged=1")
        db.commit()

        self.failIf(job4.statusMessage != 'Number 4 in line for processing',
                    "Cook before release caused wrong queue count")

        allJobs = (job1, job2, job3, job4)

        for job in allJobs:
            cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)

        db.commit()

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

    @fixture('Release')
    def testJobData(self, db, client, data):
        release = client.getRelease(data['releaseId'])

        job = client.startImageJob(release.getId())
        job.setDataValue("mystring", "testing", RDT_STRING)
        job.setDataValue("myint", 123, RDT_INT)

        assert(job.getDataValue("mystring") == "testing")
        assert(int(job.getDataValue("myint")) == 123)

    @fixture('Release')
    def testStartCookJob(self, db, client, data):
        projectId = data['projectId']

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        job = client.startNextJob(["1#x86_64"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong architecture")

        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored a valid cook job")

        self.failIf(job.status != jobstatus.RUNNING,
                    "job-server is not multi-instance safe")

    @fixture('Release')
    def testStartReleaseJob(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])
        relJob = client.startImageJob(release.getId())

        # normally called from job-server
        job = client.startNextJob(["1#x86"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong architecture")

        job = client.startNextJob(["1#x86", "1#x86_64"],
                                  {'imageTypes' : [releasetypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored a valid release job")

        self.failIf(job.status != jobstatus.RUNNING,
                    "job-server is not multi-instance safe")

    @fixture('Release')
    def testJobRaceCondition(self, db, client, data):
        groupTrove = client.createGroupTrove(data['projectId'], 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        cu = db.cursor()
        cu.execute("UPDATE Jobs set owner=1")
        db.commit()

        job = client.startNextJob(["1#x86", "1#x86_64"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job is not None, "job-server is not multi-instance safe")

        cu.execute("UPDATE Jobs set owner=NULL")
        db.commit()

        job = client.startNextJob(["1#x86", "1#x86_64"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

    @fixture('Release')
    def testStartJobLocking(self, db, client, data):
        projectId = data['projectId']
        for i in range(5):
            groupTrove = client.createGroupTrove(projectId, 'group-test',
                                                 '1.0.0', '', False)

            groupTroveId = groupTrove.getId()
            trvName = 'testtrove'
            trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                    '@rpl:devel/1.0-1-1'
            trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
            subGroup = ''

            trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                        subGroup, False, False, False)

            cookJobId = groupTrove.startCookJob("1#x86")

        cu = db.cursor()
        # make a job unavailable
        cu.execute("UPDATE Jobs SET status=4 WHERE jobId=2")
        # make a job taken
        cu.execute("UPDATE Jobs SET owner=4 WHERE jobId=4")
        db.commit()

        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job.id != 1, "Jobs retreived out of order")

        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job.id != 3, "Non-waiting job was selected")

        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job.id != 5, "owned job was selected")

    @fixture('Release')
    def testStartJobLockRelease(self, db, client, data):
        groupTrove = client.createGroupTrove(data['projectId'], 'group-test',
                                             '1.0.0', '', False)

        groupTroveId = groupTrove.getId()
        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86_64")

        cu = db.cursor()

        cu.execute("SELECT owner FROM Jobs")

        self.failIf(cu.fetchall()[0] != (None,),
                    "Lock on job of incompatible type was not released")

    @fixture('Release')
    def testRegenerateRelease(self, db, client, data):
        release = client.getRelease(data['releaseId'])
        release.setImageTypes([releasetypes.STUB_IMAGE])

        relJob = client.startImageJob(release.getId())

        cu = db.cursor()

        cu.execute("SELECT name, value FROM JobData")

        self.failIf(cu.fetchone() != ('arch', '1#x86_64'),
                    "architecture information missing for release")

        cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)
        db.commit()

        relJob = client.startImageJob(release.getId())

        cu.execute("SELECT status, owner FROM Jobs")

        self.failIf(cu.fetchone() != (jobstatus.WAITING, None),
                    "Job not regenerated properly. will never run")

    @fixture('Empty')
    def testRegenerateCook(self, db, client, data):
        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        cu = db.cursor()

        cu.execute("SELECT name, value FROM JobData")

        self.failIf(cu.fetchone() != ('arch', '1#x86'),
                    "architecture information missing for cook")

        cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)
        db.commit()

        cookJob = groupTrove.startCookJob("1#x86")

        cu.execute("SELECT status, owner FROM Jobs")

        self.failIf(cu.fetchone() != (jobstatus.WAITING, None),
                    "Job not regenerated properly. will never run")

    @fixture('Release')
    def testListActiveJobs(self, db, client, data):
        def listActiveJobs(client, filter):
            return [x['jobId'] for x in client.listActiveJobs(filter)]

        projectId = data['projectId']

        jobIds = []

        for i in range(3):
            groupTrove = client.createGroupTrove(projectId, 'group-test',
                                                 '1.0.0', 'No Description',
                                                 False)

            trvName = 'testtrove'
            trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                    '@rpl:devel/1.0-1-1'
            trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
            subGroup = ''

            groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                subGroup, False, False, False)

            jobIds.append(groupTrove.startCookJob("1#x86"))
            job = client.getJob(jobIds[i])
            job.setDataValue("hostname", "127.0.0.1", RDT_STRING)
            # hack to ensure timestamps are different.
            time.sleep(1)

        self.failIf(listActiveJobs(client, True) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        self.failIf(listActiveJobs(client, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu = db.cursor()
        cu.execute("UPDATE Jobs SET timeSubmitted=0 WHERE jobId=?", jobIds[0])
        db.commit()

        self.failIf(listActiveJobs(client, True) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        self.failIf(listActiveJobs(client, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu.execute("UPDATE Jobs SET status=? WHERE jobId=?",
                   jobstatus.FINISHED, jobIds[-1])
        db.commit()

        self.failIf(listActiveJobs(client, True) != jobIds[:-1],
                    "listActiveJobs should have listed %s" % str(jobIds[:-1]))

        self.failIf(listActiveJobs(client, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu.execute("UPDATE Jobs SET status=? WHERE jobId=?",
                   jobstatus.FINISHED, jobIds[0])
        db.commit()

        self.failIf(listActiveJobs(client, True) != [jobIds[1]],
                    "listActiveJobs should have listed %s" % str([jobIds[1]]))

        self.failIf(listActiveJobs(client, False) != jobIds[1:],
                    "listActiveJobs should have listed %s" % str(jobIds[1:]))

        self.failIf(client.listActiveJobs(False)[0]['hostname'] != '127.0.0.1')


if __name__ == "__main__":
    testsuite.main()
