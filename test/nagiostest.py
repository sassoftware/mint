#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
import sys
import os
import tempfile

import testsuite
import unittest
testsuite.setup()

from conary.lib import util

try:
    sys.path.insert(0, "../nagios/")
    import nagpy
    from mint_nagpy import checkjobs, config as nagios_config
except ImportError:
    nagpy = None


class NagiosTest(unittest.TestCase):
    def setUp(self):
        if not nagpy:
            raise testsuite.SkipTestException("nagpy module not installed, skipping nagios test")

        self.workDir = tempfile.mkdtemp()

        cfg = nagios_config.CheckJobsConfig()

        cfg.retries = 2
        cfg.timeStampFile = self.workDir + "/timestamp"
        cfg.iterationFile = self.workDir + "/iteration"
        cfg.filterExp = ['good error', 'another error']

        fd, fn = tempfile.mkstemp(suffix='.cfg')
        os.close(fd)

        cfg.writeToFile(fn)
        checkjobs.CheckJobs.cfgPath = fn

    def tearDown(self):
        util.rmtree(self.workDir)
        os.unlink(checkjobs.CheckJobs.cfgPath)

    def testTimeStamps(self):
        cj = checkjobs.CheckJobs()

        self.failUnlessEqual(cj.getTimeStamp(), 0)
        cj.setTimeStamp(100)
        self.failUnlessEqual(cj.getTimeStamp(), 100)

    def testIterate(self):
        cj = checkjobs.CheckJobs()

        self.failUnlessEqual(cj.iterate(reset = True), False)
        self.failUnlessEqual(cj.iterate(), False)
        self.failUnlessEqual(cj.iterate(), True)

    def testFilterJobErrors(self):
        cj = checkjobs.CheckJobs()

        self.failUnlessEqual(cj.filterJobErrors("good error"), True)
        self.failUnlessEqual(cj.filterJobErrors("another error"), True)
        self.failUnlessEqual(cj.filterJobErrors("bad error!"), False)


if __name__ == "__main__":
    testsuite.main()

