#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
# A little hack to track performance changes during development:
#
# 1. Run this test before making changes. It will save performance
#    based on a few 'ab' (apachebench) runs.
#
# 2. Make changes to the code.
#
# 3. Run this test again. It will compare the new numbers with
#    the old numbers and tell you if you have sped up the codebase
#    or not.
#
# TODO:
#
# * Needs more granular tests so you can say:
#
#     ./test-performance.py testLogin
#

import os
import re
import time
import pickle

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, FQDN, PFQDN

timingsFile = ".perftimings.pck"
abRe = re.compile('Requests per second:    ([\d\.]+).*')

class PerformanceTest(MintRepositoryHelper):
    def setUp(self):
        MintRepositoryHelper.setUp(self)

        self.timings = {}

        try:
            self.timings = pickle.load(open(timingsFile))
        except Exception, e:
            print e
        print "\n"

    def tearDown(self):
        try:
            pickle.dump(self.timings, open(timingsFile, 'w'))
        except Exception, e:
            print e

        MintRepositoryHelper.tearDown(self)

    def apacheBench(self, name, url, num = 200):
        x = self.captureAllOutput(os.popen, 'ab -n %d %s' % (num, url))

        for x in x.readlines():
            m = abRe.match(x)
            if m:
                c = float(m.groups()[0])

        print "%d requests for '%s': %f req/sec" % (num, name, c),
        if name in self.timings:
            if self.timings[name] < c:
                print "(%02.02f%% FASTER than last run)" % (((c - self.timings[name]) / self.timings[name]) * 100.0)
            elif self.timings[name] > c:
                print "(%02.02f%% SLOWER than last run)" % (((self.timings[name] - c) / c) * 100.0)
            else:
                print "(no change)"

        self.timings[name] = c

    def testPerformance(self):
        client, userId = self.quickMintUser('testuser', 'testpsas')
        projectId = client.newProject("test", "testproject", MINT_PROJECT_DOMAIN)

        self.apacheBench("front page, anonymous", "http://%s:%d/" % (FQDN, self.port))
        self.apacheBench("project page, anonymous", "http://%s:%d/project/testproject/" % (PFQDN, self.port))


if __name__ == "__main__":
    testsuite.main()
