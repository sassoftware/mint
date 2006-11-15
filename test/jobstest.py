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

from mint import shimclient
from mint import config
from mint import jobstatus
from mint import jobs
from mint import buildtypes
from mint import cooktypes
from mint import mint_error
from mint import jsversion
from mint import database
from mint.data import RDT_INT, RDT_STRING, RDT_BOOL
from mint.distro import stub_image
from mint.flavors import stockFlavors
from mint.server import ParameterError, MintServer

from conary import versions
from conary import dbstore
from conary.deps import deps
from conary.lib import util

class JobsTest(fixtures.FixturedUnitTest):
    def stockBuildFlavor(self, db, buildId, arch = "x86_64"):
        cu = db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Builds set troveFlavor=? WHERE buildId=?", flavor, buildId)
        db.commit()

    #####
    # test startNextJob for just images
    #####

    @fixtures.fixture('ImageJob')
    def testStartImageNoJobType(self, db, data):
        # ask for no job types
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned something when nothing wanted")

    @fixtures.fixture('ImageJob')
    def testStartImageNoType(self, db, data):
        # ask for no arch type or job types
        client = self.getClient('test')
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned something when nothing wanted")

    @fixtures.fixture('ImageJob')
    def testStartImageNoArch(self, db, data):
        # ask for no arch
        client = self.getClient('test')
        job = client.startNextJob([],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong image type")

    @fixtures.fixture('ImageJob')
    def testStartImageWrongType(self, db, data):
        # ask for a different image type
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"],
                                  {'buildTypes' : [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong image type")

    @fixtures.fixture('ImageJob')
    def testStartImageWrongArch(self, db, data):
        # ask for a different architecture
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched the wrong architecture")

    @fixtures.fixture('ImageJob')
    def testStartImageCookArch(self, db, data):
        # ask for a cook job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erroneously matched cook "
                    "job for wrong arch")

    @fixtures.fixture('ImageJob')
    def testStartImageCook(self, db, data):
        # ask for a cook job with right arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erreneously matched cook job")

    @fixtures.fixture('ImageJob')
    def testStartImage(self, db, data):
        # ask for the right parameters
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNext job didn't match for correct values")

    #####
    # test startNextJob for just cooks
    #####

    @fixtures.fixture('CookJob')
    def testStartCookWrongArch(self, db, data):
        # ask for a cook job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job for wrong arch")

    @fixtures.fixture('CookJob')
    def testStartCook(self, db, data):
        # ask for a cook job with right arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob matched cook job for wrong arch")

    @fixtures.fixture('CookJob')
    def testStartCookImageArch(self, db, data):
        # ask for a image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job when asked for image")

    @fixtures.fixture('CookJob')
    def testStartCookImage(self, db, data):
        # ask for a image job with right arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job when asked for image")

    @fixtures.fixture('CookJob')
    def testStartCookNoJobType(self, db, data):
        # ask for a no job with right arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixtures.fixture('CookJob')
    def testStartCookNoJobType2(self, db, data):
        # ask for no job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(["1#x86_64"], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixtures.fixture('CookJob')
    def testStartCookNoJob(self, db, data):
        # ask for no job with no arch
        client = self.getClient('test')
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    @fixtures.fixture('CookJob')
    def testStartCookNoJobArch(self, db, data):
        # ask for an image job with no arch
        client = self.getClient('test')
        job = client.startNextJob([],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job but asked for nothing")

    #####
    # test startNextJob for cooks and images together
    #####

    @fixtures.fixture('BothJobs')
    def testStartCompImage(self, db, data):
        # ask for an image job with right arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored an image job")

    @fixtures.fixture('BothJobs')
    def testStartCompCook(self, db, data):
        # ask for an image job with right arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored a cook job")

    @fixtures.fixture('BothJobs')
    def testStartCompImageArch(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched image job wrong arch")

    @fixtures.fixture('BothJobs')
    def testStartCompCookArch(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job wrong arch")


    @fixtures.fixture('BothJobs')
    def testStartCompImageNoArch(self, db, data):
        # ask for an image job with no arch
        client = self.getClient('test')
        job = client.startNextJob([],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched image job no arch")

    @fixtures.fixture('BothJobs')
    def testStartCompCookNoArch(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob([],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched cook job no arch")

    @fixtures.fixture('BothJobs')
    def testStartCompNoArch(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob([], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no arch and no type")

    @fixtures.fixture('BothJobs')
    def testStartCompArch(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86'], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no type")

    @fixtures.fixture('BothJobs')
    def testStartCompArch2(self, db, data):
        # ask for an image job with wrong arch
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64'], {},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched job no type")

    #####
    # test both cooks and images while asking for both
    #####

    @fixtures.fixture('BothJobs')
    def testStartCompBothCook(self, db, data):
        # ask for all jobs with x86 arch (will match cook)
        client = self.getClient('test')
        job = client.startNextJob(['1#x86'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob ignored a cook job")

    @fixtures.fixture('BothJobs')
    def testStartCompBothImage(self, db, data):
        client = self.getClient('test')
        # ask for all jobs with x86_64 arch (will match image)
        job = client.startNextJob(['1#x86_64'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.buildId),
                    "startNextJob ignored an image job")

    @fixtures.fixture('BothJobs')
    def testStartCompBothNoArch(self, db, data):
        # ask for all jobs no arch
        client = self.getClient('test')
        job = client.startNextJob([],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob matched for no arch")

    @fixtures.fixture('BothJobs')
    def testStartCompBothArch(self, db, data):
        # ask for all jobs
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.buildId),
                    "startNextJob didn't match image job")

        # ask for all jobs
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob didn't match group trove")

    @fixtures.fixture('BothJobs')
    def testStartCompBuildType(self, db, data):
        # ask for all jobs but wrong image type
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'buildTypes' : [buildtypes.RAW_HD_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob didn't match cook")

    #####
    # and just to round it out, test for bad parmaeters
    #####

    @fixtures.fixture('Empty')
    def testStartBadArch(self, db, data):
        client = self.getClient('test')
        self.assertRaises(ParameterError,
                          client.startNextJob, ['this is not a frozen flavor'],
                          {'buildTypes' : [buildtypes.RAW_HD_IMAGE],
                           'cookTypes' : [cooktypes.GROUP_BUILDER]},
                          jsversion.getDefaultVersion())

    @fixtures.fixture('Empty')
    def testStartBadImage(self, db, data):
        client = self.getClient('test')
        self.assertRaises(ParameterError,
                          client.startNextJob, ['1#x86'],
                          {'buildTypes' : [9999],
                           'cookTypes' : [cooktypes.GROUP_BUILDER]},
                          jsversion.getDefaultVersion())

    @fixtures.fixture('Empty')
    def testStartBadCook(self, db, data):
        client = self.getClient('test')
        self.assertRaises(ParameterError,
                          client.startNextJob, ['1#x86'],
                          {'buildTypes' : [buildtypes.RAW_HD_IMAGE],
                           'cookTypes' : [9999]},
                          jsversion.getDefaultVersion())

    @fixtures.fixture('ImageJob')
    def testStartLegalImage(self, db, data):
        # ask for an image type that's technically in the list, but not served
        # by this server. historically this raised permission denied.
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64', '1#x86'],
                                  {'buildTypes' : [buildtypes.NETBOOT_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob erroneously matched image")

    #####
    # ensure jobs do not get inadverdently respwaned
    #####

    @fixtures.fixture('CookJob')
    def testStartCookFinished(self, db, data):
        client = self.getClient('test')
        # mark job as finished
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixtures.fixture('CookJob')
    def testStartCookFinished2(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixtures.fixture('CookJob')
    def testStartCookFinished3(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished cook")

    @fixtures.fixture('ImageJob')
    def testStartImageFinished(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixtures.fixture('ImageJob')
    def testStartImageFinished2(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixtures.fixture('ImageJob')
    def testStartImageFinished3(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a finished image")

    @fixtures.fixture('CookJob')
    def testStartCookOwned(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixtures.fixture('CookJob')
    def testStartCookOwned2(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixtures.fixture('CookJob')
    def testStartCookOwned3(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86'],
                                  {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned cook")

    @fixtures.fixture('ImageJob')
    def testStartImageOwned(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixtures.fixture('ImageJob')
    def testStartImageOwned2(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'cookTypes' : [cooktypes.GROUP_BUILDER],
                                   'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixtures.fixture('ImageJob')
    def testStartImageOwned3(self, db, data):
        # mark job as finished
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("UPDATE Jobs SET owner=1")
        db.commit()

        job = client.startNextJob(['1#x86_64'],
                                  {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned an owned image")

    @fixtures.fixture('Empty')
    def testMimicJobServer(self, db, data):
        # historically this always failed with permission denied, but it
        # definitely needs to be allowed. return value doesn't matter
        client = self.getClient('test')
        job = client.startNextJob(['1#x86_64'],
                                  {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                                  jsversion.getDefaultVersion())

    #####
    # test jobserver version
    #####

    @fixtures.fixture('Full')
    def testImageJSVersion(self, db, data):
        # ensure an image job cannot be started for a mismatched job server.
        client = self.getClient('admin')
        cu = db.cursor()
        cu.execute("""UPDATE BuildData SET value='illegal'
                          WHERE name='jsversion'""")
        db.commit()

        self.assertRaises(mint_error.JobserverVersionMismatch,
                          client.startImageJob, data['buildId'])

    @fixtures.fixture('ImageJob')
    def testStartImageJobJSV(self, db, data):
        # masquerading as a job server version that server doesn't support
        # raises parameter error.
        client = self.getClient('test')
        self.assertRaises(ParameterError, client.startNextJob,
                          ['1#x86', '1#x86_64'],
                          {'buildTypes': [buildtypes.RAW_HD_IMAGE]},
                          'wackyversion')

    @fixtures.fixture('ImageJob')
    def testStartImageJobJSV2(self, db, data):
        # ensure image jobs cannot be selected for mismatched job server type
        # using only image types defined
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("""UPDATE BuildData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'buildTypes': [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a mismatched jobserver image")

    @fixtures.fixture('ImageJob')
    def testStartImageJobJSV3(self, db, data):
        # ensure image jobs cannot be selected for mismatched job server type
        # using composite job request
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("""UPDATE BuildData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'buildTypes': [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned a mismatched jobserver image")

    @fixtures.fixture('BothJobs')
    def testStartCookJobJSV(self, db, data):
        # ensure cook jobs don't interact badly with job server version
        client = self.getClient('test')
        cu = db.cursor()
        cu.execute("""UPDATE BuildData SET value='1.0.0'
                          WHERE name='jsversion'""")
        db.commit()

        job = client.startNextJob(['1#x86', '1#x86_64'],
                                  {'buildTypes': [buildtypes.STUB_IMAGE],
                                   'cookTypes' : [cooktypes.GROUP_BUILDER]},
                                  jsversion.getDefaultVersion())

        self.failIf(not (job and job.groupTroveId),
                    "startNextJob ignored a cook job")

    @fixtures.fixture('Full')
    def testJobs(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])

        job = client.startImageJob(build.getId())
        job = build.getJob()
        assert(job.getBuildId() == build.getId())

        # test restarting jobs
        job.setStatus(jobstatus.ERROR, "Error Message")
        job.refresh()
        assert(job.timeFinished)

        client.startImageJob(build.getId())
        job.refresh()
        assert(job.getStatus() == jobstatus.WAITING)

        # test duplicate job handling
        try:
            job2 = client.startImageJob(build.getId())
        except jobs.DuplicateJob:
            pass
        else:
            self.fail("expected exception jobs.DuplicateJob")

        if len(client.server.getJobIds()) != 1:
            self.fail("get all Job Id's returned incorrect results")
        # important to test separately: finishing a job generates
        # follow-on SQL statements
        job.setStatus(jobstatus.FINISHED, "Finished")

        job.refresh()
        assert(job.timeFinished)

    @fixtures.fixture('Full')
    def testStubImage(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        project = client.getProject(data['projectId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(build.getId())

        from mint.distro import jobserver
        isocfg = jobserver.IsoGenConfig()
        isocfg.finishedPath = self.cfg.imagesPath
        imagegen = stub_image.StubImage(client, isocfg, job,
                                        build, project)
        imagegen.write()
        imageFileName = os.path.join(self.cfg.imagesPath, 'stub.iso')
        build.setFiles([[imageFileName, "Stub"]])

        assert(os.path.exists(imageFileName))

        build.refresh()
        files = build.getFiles()
        assert(files == \
                [{'size': os.stat(imageFileName)[6],
                  'sha1': '', 'title': 'Stub',
                  'fileUrls': [(4, 0, imageFileName)],
                  'fileId': 4, 'idx': 0}])

        fileInfo = client.getFileInfo(files[0]['fileId'])
        assert(fileInfo == \
                (1, 0, 'Stub', [(4, 0, imageFileName)]))

        try:
            fileInfo = client.getFileInfo(99999)
            self.fail("Should have failed to find file")
        except jobs.FileMissing:
            pass

    @fixtures.fixture('Full')
    def testStubImageFileOrder(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        # make sure that the incoming ordering of files is preserved
        build.setFiles([['zaaa.iso', 'Zaaa'], ['aaaa.iso', 'Aaaa']])
        assert(build.getFiles() == \
                [{'size': 0, 'sha1': '', 'title': 'Zaaa',
                    'fileUrls': [(4, 0, 'zaaa.iso')], 'fileId': 4, 'idx': 0},
                 {'size': 0, 'sha1': '', 'title': 'Aaaa',
                     'fileUrls': [(5, 0, 'aaaa.iso')], 'fileId': 5, 'idx': 1}])

    @fixtures.fixture('Full')
    def testJobQueue(self, db, data):
        client = self.getClient('admin')
        ownerClient = self.getClient('owner')
        build = ownerClient.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        job = ownerClient.startImageJob(build.getId())

        assert(ownerClient.server.getJobStatus(job.getId())['queueLen'] == 0)
        assert(ownerClient.server.getBuildStatus(build.getId())['queueLen'] == 0)
        assert(ownerClient.server.getJobWaitMessage(job.getId()) == \
               'Next in line for processing')

        project = ownerClient.getProject(data['projectId'])

        groupTrove = ownerClient.createGroupTrove(data['projectId'], 'group-test', '1.0.0',
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
        assert(ownerClient.server.getJobStatus(cookJobId)['queueLen'] == 1)
        assert(ownerClient.server.getJobWaitMessage(cookJobId) == \
               'Number 2 in line for processing')

        job.setStatus(jobstatus.FINISHED, 'Finished')
        assert(ownerClient.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(ownerClient.server.getJobWaitMessage(cookJobId) == \
               'Next in line for processing')

        job = ownerClient.startImageJob(build.getId())
        assert(ownerClient.server.getJobStatus(cookJobId)['queueLen'] == 0)
        assert(ownerClient.server.getJobStatus(job.getId())['queueLen'] == 1)

    @fixtures.fixture('Full')
    def testWaitStatus(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(build.getId())

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

    @fixtures.fixture('Full')
    def testRunningStatus(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(build.getId())

        newMsg = "We are the knights who say 'Ni!'"
        job.setStatus(jobstatus.RUNNING, newMsg)

        # refresh the job object
        job = client.getJob(job.id)

        self.failIf(job.getStatusMessage() == 'Next in line for processing',
                    "job mistook itself for waiting.")

    @fixtures.fixture('Full')
    def testStartTimestamp(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        job = client.startImageJob(build.getId())

        cu = db.cursor()
        cu.execute("UPDATE Jobs set timeStarted = 100 where jobId=?", job.id)
        db.commit()

        # refresh job
        job = client.getJob(job.id)

        self.failIf(job.timeStarted != 100,
                    "pre-start: job doesn't reflect altered timestamp")

        newJob = client.startNextJob(['1#x86', '1#x86_64'],
                                    {'buildTypes':
                                     [buildtypes.STUB_IMAGE]},
                                     jsversion.getDefaultVersion())

        assert(newJob.id == job.id)

        self.failIf(job.timeStarted != 100,
                    "post-start: job doesn't reflect altered timestamp")

        self.failIf(job.timeStarted == newJob.timeStarted,
                    "Job's start timestamp wasn't adjusted. timing metrics "
                    "will be misleading")

    @fixtures.fixture('Empty')
    def testTimestampInteraction(self, db, data):
        client = self.getClient('test')
        projectId = client.newProject("Foo", "foo", "rpath.org")

        cu = db.cursor()

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build.getId())
        job = client.startImageJob(build.getId())

        cu.execute("UPDATE Builds SET troveLastChanged=0")
        db.commit()

        build2 = client.newBuild(projectId, "Test Build")
        build2.setBuildType(buildtypes.STUB_IMAGE)
        build2.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build2.getId())
        job2 = client.startImageJob(build2.getId())

        cu.execute("UPDATE Builds SET troveLastChanged=0")
        db.commit()

        build3 = client.newBuild(projectId, "Test Build")
        build3.setBuildType(buildtypes.STUB_IMAGE)
        build3.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build3.getId())
        job3 = client.startImageJob(build3.getId())

        assert(job.getStatusMessage() == 'Next in line for processing')
        assert(job2.getStatusMessage() == 'Number 2 in line for processing')
        assert(job3.getStatusMessage() == 'Number 3 in line for processing')

        newJob = client.startNextJob(['1#x86', '1#x86_64'],
                                    {'buildTypes':
                                     [buildtypes.STUB_IMAGE]},
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

    @fixtures.fixture('Empty')
    def testJobQueueOrder(self, db, data):
        client = self.getClient('test')
        cu = db.cursor()

        testUserClient = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        build = testUserClient.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build.getId())
        job1 = testUserClient.startImageJob(build.getId())

        # protect this build from being auto-deleted
        cu.execute("UPDATE Builds SET troveLastChanged=1")
        db.commit()

        build2 = testUserClient.newBuild(projectId, "Test Build")
        build2.setBuildType(buildtypes.STUB_IMAGE)
        build2.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build2.getId())
        job2 = testUserClient.startImageJob(build2.getId())

        # protect this build from being auto-deleted
        cu.execute("UPDATE Builds SET troveLastChanged=1")
        db.commit()

        self.failIf(job2.statusMessage == 'Next in line for processing',
                    "Consecutive builds both show up as next.")

        groupTrove = testUserClient.createGroupTrove(projectId, \
                'group-test', '1.0.0', 'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        job3 = testUserClient.getJob(3)

        self.failIf(job3.statusMessage != 'Number 3 in line for processing',
                    "Build before cook caused wrong queue count")

        build3 = testUserClient.newBuild(projectId, "Test Build")
        build3.setBuildType(buildtypes.STUB_IMAGE)
        build3.setDataValue('stringArg', 'Hello World!')

        self.stockBuildFlavor(db, build3.getId())
        job4 = testUserClient.startImageJob(build3.getId())

        # protect this build from being auto-deleted
        cu.execute("UPDATE Builds SET troveLastChanged=1")
        db.commit()

        self.failIf(job4.statusMessage != 'Number 4 in line for processing',
                    "Cook before build caused wrong queue count")

        allJobs = (job1, job2, job3, job4)

        for job in allJobs:
            cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)

        db.commit()

        # regenerate jobs
        job1 = testUserClient.startImageJob(build.getId())
        job2 = testUserClient.startImageJob(build2.getId())
        job3 = testUserClient.getJob(groupTrove.startCookJob("1#x86"))
        job4 = testUserClient.startImageJob(build3.getId())

        self.failIf(job1.statusMessage != 'Next in line for processing',
                    "Didn't properly report status of next job")

        for job in (job2, job3, job4):
            self.failIf(job.statusMessage == 'Next in line for processing',
                        "Improperly reported status of job as next-in-line")

    @fixtures.fixture('Full')
    def testJobData(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])

        job = client.startImageJob(build.getId())
        job.setDataValue("mystring", "testing", RDT_STRING)
        job.setDataValue("myint", 123, RDT_INT)

        assert(job.getDataValue("mystring") == "testing")
        assert(int(job.getDataValue("myint")) == 123)

    @testsuite.context("quick")
    @fixtures.fixture('Full')
    def testStartCookJob(self, db, data):
        client = self.getClient('admin')
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

    @fixtures.fixture('Full')
    def testStartBuildJob(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        relJob = client.startImageJob(build.getId())

        # normally called from job-server
        job = client.startNextJob(["1#x86"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(job, "startNextJob returned the wrong architecture")

        job = client.startNextJob(["1#x86", "1#x86_64"],
                                  {'buildTypes' : [buildtypes.STUB_IMAGE]},
                                  jsversion.getDefaultVersion())

        self.failIf(not job, "startNextJob ignored a valid build job")

        self.failIf(job.status != jobstatus.RUNNING,
                    "job-server is not multi-instance safe")

    @fixtures.fixture('Full')
    def testJobRaceCondition(self, db, data):
        client = self.getClient('admin')
        ownerClient = self.getClient("owner")
        groupTrove = ownerClient.createGroupTrove(data['projectId'], \
                'group-test', '1.0.0', 'No Description', False)

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

        job = ownerClient.startNextJob(["1#x86", "1#x86_64"],
                {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                jsversion.getDefaultVersion())

        self.failIf(job is not None, "job-server is not multi-instance safe")

        cu.execute("UPDATE Jobs set owner=NULL")
        db.commit()

        job = ownerClient.startNextJob(["1#x86", "1#x86_64"],
                {'cookTypes' : [cooktypes.GROUP_BUILDER]},
                jsversion.getDefaultVersion())

    @fixtures.fixture('Full')
    def testStartJobLocking(self, db, data):
        client = self.getClient('admin')
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

    @fixtures.fixture('Full')
    def testStartJobLockBuild(self, db, data):
        client = self.getClient('admin')
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
                    "Lock on job of incompatible type was not buildd")

    @fixtures.fixture('Full')
    def testRegenerateBuild(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)

        relJob = client.startImageJob(build.getId())

        cu = db.cursor()

        cu.execute("SELECT name, value FROM JobData")

        self.failIf(cu.fetchone() != ('arch', '1#x86_64'),
                    "architecture information missing for build")

        cu.execute("UPDATE Jobs SET status=?, owner=1", jobstatus.FINISHED)
        db.commit()

        relJob = client.startImageJob(build.getId())

        cu.execute("SELECT status, owner FROM Jobs")

        self.failIf(cu.fetchone() != (jobstatus.WAITING, None),
                    "Job not regenerated properly. will never run")

    @fixtures.fixture('Empty')
    def testRegenerateCook(self, db, data):
        client = self.getClient('test')
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

    @fixtures.fixture('Full')
    def testListActiveJobs(self, db, data):
        client = self.getClient('admin')
        def listActiveJobs(client, filter):
            return [x['jobId'] for x in client.listActiveJobs(filter)]

        projectId = data['projectId']
        ownerClient = self.getClient("owner")

        jobIds = []

        for i in range(3):
            groupTrove = ownerClient.createGroupTrove(projectId, 'group-test',
                    '1.0.0', 'No Description', False)

            trvName = 'testtrove'
            trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                    '@rpl:devel/1.0-1-1'
            trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
            subGroup = ''

            groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                subGroup, False, False, False)

            jobIds.append(groupTrove.startCookJob("1#x86"))
            job = ownerClient.getJob(jobIds[i])
            job.setDataValue("hostname", "127.0.0.1", RDT_STRING)
            # hack to ensure timestamps are different.
            time.sleep(1)

        self.failIf(listActiveJobs(ownerClient, True) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        self.failIf(listActiveJobs(ownerClient, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu = db.cursor()
        cu.execute("UPDATE Jobs SET timeSubmitted=0 WHERE jobId=?", jobIds[0])
        db.commit()

        self.failIf(listActiveJobs(ownerClient, True) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        self.failIf(listActiveJobs(ownerClient, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu.execute("UPDATE Jobs SET status=? WHERE jobId=?",
                   jobstatus.FINISHED, jobIds[-1])
        db.commit()

        self.failIf(listActiveJobs(ownerClient, True) != jobIds[:-1],
                    "listActiveJobs should have listed %s" % str(jobIds[:-1]))

        self.failIf(listActiveJobs(ownerClient, False) != jobIds,
                    "listActiveJobs should have listed %s" % str(jobIds))

        cu.execute("UPDATE Jobs SET status=? WHERE jobId=?",
                   jobstatus.FINISHED, jobIds[0])
        db.commit()

        self.failIf(listActiveJobs(ownerClient, True) != [jobIds[1]],
                    "listActiveJobs should have listed %s" % str([jobIds[1]]))

        self.failIf(listActiveJobs(ownerClient, False) != jobIds[1:],
                    "listActiveJobs should have listed %s" % str(jobIds[1:]))

        self.failIf(ownerClient.listActiveJobs(False)[0]['hostname'] != '127.0.0.1')

    @fixtures.fixture('Full')
    def testCookStartDenied(self, db, data):
        client = self.getClient('user')
        self.assertRaises(mint_error.PermissionDenied,
                          client.getGroupTrove, data['groupTroveId'])
        self.assertRaises(mint_error.PermissionDenied,
                          client.server._server.startCookJob,
                          data['groupTroveId'], 'x86')

    @fixtures.fixture('Full')
    def testGetJobCompat(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])
        job2 = client.server._server.getJob(job.id)
        del job2['timeSubmitted']
        assert job2 == {'status': 0, 'timeFinished': 0.0, 'timeStarted': 0.0,
                        'userId': 1, 'releaseId': 1, 'groupTroveId': 0,
                        'statusMessage': 'Next in line for processing'}

    @fixtures.fixture('Full')
    def testMissingGetJobCompat(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])
        self.assertRaises(database.ItemNotFound, client.server._server.getJob, 99)

    @fixtures.fixture('Full')
    def testMissingGetJob(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])

        self.assertRaises(database.ItemNotFound, client.server._server.getJob2, 99)


    @fixtures.fixture('Full')
    def testHostnameListActiveJobs(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])

        jobData = client.listActiveJobs(False)
        del jobData[0]['timeSubmitted']
        assert jobData == [{'status': 0, 'timeFinished': 0.0,
                            'timeStarted': 0.0, 'buildId': 1,
                            'hostname': 'None', 'userId': 1, 'jobId': 1,
                            'groupTroveId': '',
                            'statusMessage': 'Next in line for processing'}]

    @fixtures.fixture('Full')
    def testJobIdCookPerms(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])

        client.server._server.getJobIdForCook(job.id)

        client = self.getClient('nobody')

        job = client.getJob(data['buildId'])

        self.assertRaises(mint_error.PermissionDenied,
                          client.server._server.getJobIdForCook, job.id)

    @fixtures.fixture('Full')
    def testGetMissingJobQueue(self, db, data):
        client = self.getClient('admin')
        job = client.startImageJob(data['buildId'])

        self.assertRaises(database.ItemNotFound,
                          client.server._server._getJobQueueLength, 99)

if __name__ == "__main__":
    testsuite.main()
