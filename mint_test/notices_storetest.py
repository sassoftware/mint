#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.  All Rights Reserved.
#

import testsuite
testsuite.setup()

import os
import time

import testbase
from catalogService import notices_store

class StorageConfig(object):
    __slots__ = [ 'storagePath' ]

class StorageTest(testbase.TestCase):
    def setUp(self):
        testbase.TestCase.setUp(self)
        self.globalStorePath = os.path.join(self.workDir, "global")
        self.userStorePath = os.path.join(self.workDir, "user")
        self.dismissalsPath = os.path.join(self.workDir, "dismissals")
        self.storage = notices_store.Storage(self.globalStorePath,
            self.userStorePath, self.dismissalsPath)

    def testStorageKeys(self):
        stg = self.storage

        k1 = stg.storeGlobal("a", "somedata")
        self.failUnless(os.path.exists(
            os.path.join(self.globalStorePath, "a", os.path.basename(k1.id))))
        self.failUnlessEqual(k1.content, "somedata")

        k2 = stg.storeUser("b", "moredata")
        self.failUnlessEqual(k2.content, "moredata")
        self.failUnless(os.path.exists(
            os.path.join(self.userStorePath, "b", os.path.basename(k2.id))))

        self.failUnlessEqual(
            [ x.id for x in stg.enumerateStoreGlobal("a") ],
            [ x.id for x in [ k1 ] ])
        self.failUnlessEqual(
            [ x.id for x in stg.enumerateStoreUser("b") ],
            [ x.id for x in [ k2 ] ])

        # Change k2, make sure we can pass the whole notice as an argument
        k2.content = "other data"
        k3 = stg.storeUser(None, k2)
        self.failUnlessEqual(k2.id, k3.id)
        self.failUnlessEqual(k2.content, k3.content)
        self.failUnlessEqual(k2.modified, k3.modified)

    def testDismissal(self):
        stg = self.storage
        now = time.time()

        # Add some content first
        k0 = stg.storeUser("a", "content1", modified = now - 3)
        self.failUnlessEqual(k0.modified, now - 3)

        k1 = stg.storeUser("a", "content1", modified = now - 2)
        self.failUnlessEqual(k1.modified, now - 2)

        k2 = stg.storeUser("a", "content2", modified = now - 1)
        self.failUnlessEqual(k2.modified, now - 1)

        k3 = stg.storeUser("a", "content3", modified = now)
        self.failUnlessEqual(k3.modified, now)

        k = stg.retrieveUser(k0.id)
        self.failUnlessEqual(k0.content, k.content)
        k = stg.retrieveUser(os.path.basename(k0.id), context = "a")
        self.failUnlessEqual(k0.content, k.content)

        # Add dismissals for k0, k1 and k3
        stg.storeUserDismissal(k0)
        stg.storeUserDismissal(k1)
        stg.storeUserDismissal(k3)

        self.failUnlessEqual([ x.id for x in stg.enumerateStoreUser('a') ],
            [ k2.id ])

        # Add some context first
        g0 = stg.storeGlobal("a", "content1", modified = now - 6)
        self.failUnlessEqual(g0.modified, now - 6)

        g1 = stg.storeGlobal("a", "content1", modified = now - 5)
        self.failUnlessEqual(g1.modified, now - 5)

        g2 = stg.storeGlobal("a", "content2", modified = now - 4)
        self.failUnlessEqual(g2.modified, now - 4)

        g3 = stg.storeGlobal("a", "content3", modified = now)
        self.failUnlessEqual(g3.modified, now)

        k = stg.retrieveGlobal(g0.id)
        self.failUnlessEqual(g0.content, k.content)
        k = stg.retrieveGlobal(os.path.basename(g0.id), context = "a")
        self.failUnlessEqual(g0.content, k.content)

        # Add dismissals for k0, k1 and k3
        stg.storeGlobalDismissal(g0)
        stg.storeGlobalDismissal(g1)
        stg.storeGlobalDismissal(g3)

        self.failUnlessEqual([ x.id for x in stg.enumerateStoreGlobal('a') ],
            [ g2.id ])

        self.failUnlessEqual([ x.id for x in stg.enumerateAllUserStore() ],
            [ k2.id ])

        self.failUnlessEqual([ x.id for x in stg.enumerateAllGlobalStore() ],
            [ g2.id ])

        self.failUnlessEqual([ x.id for x in stg.enumerateAllStore() ],
            [ g2.id, k2.id ])

    def testMerge(self):
        l0 = range(0, 15, 3)
        l1 = range(1, 15, 3)
        l2 = range(2, 15, 3)

        self.failUnlessEqual(
            [ x for x in notices_store.mergeIterables([l0, l1, l2]) ],
            range(15))

if __name__ == "__main__":
    testsuite.main()

