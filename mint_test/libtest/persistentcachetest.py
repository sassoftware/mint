#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from testrunner import testcase

from mint.lib import persistentcache

class MyCacheTest(persistentcache.PersistentCache):
    _serial = 0
    def _refresh(self, key):
        MyCacheTest._serial += 1
        return MyCacheTest._serial
    def getCurrentTime(self):
        if self.nextTime:
            return self.nextTime.popleft()
        return persistentcache.PersistentCache.getCurrentTime(self)

class TestPersistentCache(testcase.TestCaseWithWorkDir):
    def setUp(self):
        testcase.TestCaseWithWorkDir.setUp(self)
        self.cacheFile = os.path.join(self.workDir, "cache")
        MyCacheTest._serial = 0

    def testBasic(self):
        key = 'a'
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 1)
        self.failUnlessEqual(cache.get(key), 1)
        cache.clear()
        self.failUnlessEqual(cache.get(key), 2)

        cache.clearKey(key)
        cache.clearKey(key) # intentional, should not fail
        self.failUnlessEqual(cache.get(key), 3)

        # Make sure removals are persisted
        cache.clearKey(key)
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 4)

        # Clear everything
        cache.clear()
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache._data.keys(), [])

    def testInvalidation(self):
        key = 'a'
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 1)

        now = time.time()
        expired = now - cache._expiration - 1
        cache._update('a', -2, timestamp=expired)

        self.failUnlessEqual(cache.get(key), 2)

    def testOldEntry(self):
        # Old caches did not have a timestamp. Make sure the timestamp gets
        # added
        key = 'a'
        value = -2
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 1)

        cache._data[key] = value
        self.failUnlessEqual(cache._data[key], value)

        self.failUnlessEqual(cache.get(key), value)
        self.failUnless(isinstance(cache._data[key], tuple))

    def testPersisted(self):
        key1 = 'a'
        key2 = 'b'
        key3 = 'c'
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key1), 1)

        cache2 = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache2.get(key1), 1)

        # Do not commit. Other caches will not see this change
        cache._updateMany([(key1, -1), (key2, -2)], commit=False)

        self.failUnlessEqual(cache2.get(key1), 1)

        # Implicit commit
        cache._updateMany([(key3, -3), (key2, -6)])

        self.failUnlessEqual(cache2.get(key1), -1)
        self.failUnlessEqual(cache2.get(key2), -6)
        self.failUnlessEqual(cache2.get(key3), -3)

    def testGetAfterFileGoesAway(self):
        key = 'a'
        cache = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 1)

        # Remove the file. We should get a new value
        os.unlink(self.cacheFile)
        self.failUnlessEqual(cache.get(key), 2)

    def testConcurrency(self):
        key1 = 'a'
        key2 = 'b'
        key3 = 'c'
        cache1 = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache1.get(key1), 1)

        cache2 = MyCacheTest(self.cacheFile)
        self.failUnlessEqual(cache2.get(key1), 1)

        # Do not commit. Other caches will not see this change
        cache1._updateMany([(key1, -1)], commit=False)

        self.failUnlessEqual(cache2.get(key1), 1)

        # cache2 creates key3. It also writes to disk
        self.failUnlessEqual(cache2.get(key3), 2)

        # cache1 creates key2. It also writes to disk
        self.failUnlessEqual(cache1.get(key2), 3)

        # cache2 should now see both key2 and key3
        self.failUnlessEqual(cache2.get(key1), -1)
        self.failUnlessEqual(cache2.get(key2), 3)
        self.failUnlessEqual(cache2.get(key3), 2)

        self.failUnlessEqual(cache1.get(key1), -1)
        self.failUnlessEqual(cache1.get(key2), 3)
        self.failUnlessEqual(cache1.get(key3), 2)
