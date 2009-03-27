#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import re
import time
import tempfile

from conary import versions
from conary.lib import util
from mint import notices_callbacks

class NoticesTest(testsetup.testsuite.TestCase):
    def setUp(self):
        self.workDir = tempfile.mkdtemp(prefix = "/tmp/mint-servertest-")
        self.userId = "JeanValjean"

    def tearDown(self):
        util.rmtree(self.workDir, ignore_errors = True)

    def testNoticesCallback(self):
        class Counter(object):
            counter = 0
            def _generateString(slf, length):
                slf.__class__.counter += 1
                return str(slf.counter)
        counter = Counter()
        cb = notices_callbacks.PackageNoticesCallback(DummyConfig(self.workDir), self.userId)
        cb.store.userStore._generateString = counter._generateString
        job = FakeJob()
        tb = FakeTroveBuilder()

        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        expBinaries = """\
<item><title>Package calibre=1.2-3-4 built</title><description>&lt;b&gt;Trove Name:&lt;/b&gt; calibre&lt;br/&gt;
&lt;b&gt;Trove Version:&lt;/b&gt; localhost@rpl:linux/1.2-3-4&lt;br/&gt;
&lt;br/&gt;
&lt;b&gt;Created On:&lt;/b&gt; Fri Feb 13 18:31:30 UTC-04:00 2009&lt;br/&gt;
&lt;b&gt;Duration:&lt;/b&gt; 00:45:43&lt;br/&gt;
</description><date>13 Feb 2009 18:31:30 -0400</date><guid></guid></item>"""
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)

        self.failUnlessEqual(actual, expBinaries)

        job._isFailed = True
        cb.notify_error(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)

        self.failUnlessEqual(actual, expBinaries.replace(
            "built", "failed"))

        job = FakeJobNoBinaries()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        expNoBinaries = """\
<item><title>Package calibre:source=1.2-3 built</title><description>No troves built</description><date>31 Dec 1969 19:00:00 -0400</date><guid></guid></item>"""
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)
        self.failUnlessEqual(actual, expNoBinaries)

        # Same test, but with an appliance callback
        cb = notices_callbacks.ApplianceNoticesCallback(DummyConfig(self.workDir), self.userId)
        cb.store.userStore._generateString = counter._generateString

        job = FakeJob()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)

        self.failUnlessEqual(actual, expBinaries.replace(
            "Package ", "Build "))

        job._isFailed = True
        cb.notify_error(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)
        self.failUnlessEqual(actual, expBinaries.replace(
            "Package ", "Build ").replace("built", "failed"))

        job = FakeJobNoBinaries()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        actual = re.sub(r"<guid>.*</guid>",
                "<guid></guid>",
                actual)
        self.failUnlessEqual(actual, expNoBinaries.replace(
            "Package ", "Build "))


class DummyConfig(object):
    def __init__(self, workDir):
        self.dataPath = workDir

class FakeJob(object):
    tstamp = 1234567890.1
    version = versions.VersionFromString('/localhost@rpl:linux/1.2-3-4', timeStamps = [tstamp])
    start = tstamp - 2741
    finish = tstamp + 2
    _isFailed = False
    def isFailed(self):
        return self._isFailed

    def getBuiltTroveList(self):
        troves = [
            ('calibre', self.version),
        ]
        return troves

    def iterTroveList(self):
        return iter([
            ('calibre:source', self.version.getSourceVersion()),
        ])

class FakeJobNoBinaries(FakeJob):
    jobId = 1
    def getBuiltTroveList(self):
        return []

class FakeTroveBuilder(object):
    def __init__(self):
        self.helper = FakeHelper()

class FakeHelper(object):
    def getJob(self, jobId, withTroves = False):
        return FakeJobNoBinaries()

if __name__ == "__main__":
        testsetup.main()
