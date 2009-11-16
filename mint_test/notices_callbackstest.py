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
        testsetup.testsuite.TestCase.setUp(self)
        self.workDir = tempfile.mkdtemp(prefix = "/tmp/mint-servertest-")
        self.userId = "JeanValjean"

    def tearDown(self):
        util.rmtree(self.workDir, ignore_errors = True)
        testsetup.testsuite.TestCase.tearDown(self)

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
        tstamp = 1234567890
        ltime = notices_callbacks.PackageNoticesCallback.formatTime(tstamp)
        stime = notices_callbacks.PackageNoticesCallback.formatRFC822Time(tstamp)
        expBinaries = """\
<item><title>Package Build calibre=1.2-3-4 completed</title><description>&lt;b&gt;Name:&lt;/b&gt; calibre&lt;br/&gt;&lt;b&gt;Version:&lt;/b&gt; localhost@rpl:linux/1.2-3-4&lt;br/&gt;&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @LTIME@&lt;br/&gt;&lt;b&gt;Duration:&lt;/b&gt; 00:45:43&lt;br/&gt;</description><date>@STIME@</date><category>success</category><guid>/api/users/JeanValjean/notices/contexts/builder/@GUID@</guid></item>"""
        expBinaries = expBinaries.replace('@LTIME@', ltime).replace('@STIME@', stime)
        actual = file(path).read()
        self.failUnlessEqual(actual, expBinaries.replace("@GUID@", "1"))

        job._isFailed = True
        cb.notify_error(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        self.failUnlessEqual(actual, expBinaries.replace("@GUID@", "2").replace(
            "completed", "failed").replace("success", "error"))

        job = FakeJobNoBinaries()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        stime = notices_callbacks.PackageNoticesCallback.formatRFC822Time(0)
        expNoBinaries = """\
<item><title>Package Build calibre:source=1.2-3 completed</title><description>No packages built</description><date>@STIME@</date><category>success</category><guid>/api/users/JeanValjean/notices/contexts/builder/@GUID@</guid></item>"""
        expNoBinaries = expNoBinaries.replace('@STIME@', stime)
        actual = file(path).read()
        self.failUnlessEqual(actual, expNoBinaries.replace("@GUID@", "3"))

        # Same test, but with an appliance callback
        cb = notices_callbacks.ApplianceNoticesCallback(DummyConfig(self.workDir), self.userId)
        cb.store.userStore._generateString = counter._generateString

        job = FakeJob()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        self.failUnlessEqual(actual, expBinaries.replace("@GUID@", "4").replace(
            "Package Build ", "Build "))

        job._isFailed = True
        cb.notify_error(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        self.failUnlessEqual(actual, expBinaries.replace(
            "@GUID@", "5").replace(
            "Package Build ", "Build ").replace(
            "completed", "failed").replace("success", "error"))

        job = FakeJobNoBinaries()
        cb.notify_committed(tb, job)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        self.failUnlessEqual(actual, expNoBinaries.replace(
            "@GUID@", "6").replace(
            "Package Build ", "Build "))

    def testNoticesImagesCallback(self):
        pName = "Project Foo"
        pVer = "Version 1.0"
        class Counter(object):
            counter = 0
            def _generateString(slf, length):
                slf.__class__.counter += 1
                return str(slf.counter)
        counter = Counter()
        cb = notices_callbacks.ImageNotices(DummyConfig(self.workDir), self.userId)
        cb.store.userStore._generateString = counter._generateString

        tstamp = 1234567890
        files = [
            ('/usr/file1', 'http://host/file1'),
            ('/usr/file2', 'http://host/file2'),
        ]
        cb.notify_built("Build Name", 2, tstamp, pName, pVer, files)
        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()
        tstamp = 1234567890
        ltime = notices_callbacks.PackageNoticesCallback.formatTime(tstamp)
        stime = notices_callbacks.PackageNoticesCallback.formatRFC822Time(tstamp)
        exp = """\
<item><title>Image `Build Name' built (Project Foo version Version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; Project Foo&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; Version 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; 2&lt;br/&gt;&lt;b&gt;File Name:&lt;/b&gt; file1&lt;br/&gt;&lt;b&gt;Download URL:&lt;/b&gt; &lt;a href="http://host/file1"&gt;http://host/file1&lt;/a&gt;&lt;br/&gt;&lt;b&gt;File Name:&lt;/b&gt; file2&lt;br/&gt;&lt;b&gt;Download URL:&lt;/b&gt; &lt;a href="http://host/file2"&gt;http://host/file2&lt;/a&gt;&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @LTIME@</description><date>@STIME@</date><category>success</category><guid>/api/users/JeanValjean/notices/contexts/builder/1</guid></item>"""
        exp = exp.replace('@LTIME@', ltime).replace('@STIME@', stime)
        self.failUnlessEqual(actual, exp)

        cb = notices_callbacks.AMIImageNotices(DummyConfig(self.workDir), self.userId)
        cb.store.userStore._generateString = counter._generateString

        tstamp = 1234567890
        # Add some dummy data to the file list
        cb.notify_built("Build Name", 2, tstamp, pName, pVer,
            [ 'AMI-0', 'AMI-1', ])

        path = os.path.join(self.workDir, "notices", "users", self.userId,
            "notices", "builder", str(counter.counter), "content")
        self.failUnless(os.path.exists(path))
        actual = file(path).read()

        exp = """\
<item><title>Image `Build Name' built (Project Foo version Version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; Project Foo&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; Version 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; 2&lt;br/&gt;&lt;b&gt;AMI:&lt;/b&gt; AMI-0&lt;br/&gt;&lt;b&gt;AMI:&lt;/b&gt; AMI-1&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @LTIME@</description><date>@STIME@</date><category>success</category><guid>/api/users/JeanValjean/notices/contexts/builder/2</guid></item>"""
        exp = exp.replace('@LTIME@', ltime).replace('@STIME@', stime)
        self.failUnlessEqual(actual, exp)


class DummyConfig(object):
    def __init__(self, workDir):
        self.dataPath = workDir
        self.siteHost = "siteproject.com"

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
