#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import time

from conary.lib import util

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

import rpath_capsule_indexer
from capsule_indexertest import base

class CapsulesTest(restbase.BaseRestTest, base.IndexerTestMixIn):
    # This controller should mock access from localhost
    class ControllerFactory(restbase.Controller):
        class RequestFactory(restbase.MockRequest):
            def _setProperties(self):
                restbase.MockRequest._setProperties(self)
                self.remote = ('127.0.0.1', 12345)

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        base.IndexerTestMixIn.setUp(self)

    def setUpIndexerCfg(self):
        db = self.openRestDatabase()
        self._addPlatformSources(db)
        self.cfg = db.capsuleMgr.getIndexerConfig()

    def _addPlatformSources(self, db):
        # XXX nasty hacks to produce some data in the hopefully proper format
        sql = """
            INSERT INTO Platforms (label, mode)
            VALUES (?, ?)
        """
        platformLabel = 'myPlatform'
        mode = 'mirrored'
        cu = db.cursor()
        cu.execute(sql, platformLabel, mode)

        platformId = cu.execute("SELECT platformId FROM Platforms "
            "WHERE label = ?", platformLabel).fetchone()[0]
        class Source(object):
            name = 'sourceName'
            shortName = 'sourceShortName'
            defaultSource = 1
            orderIndex = 1
            username = 'JeanValjean'
            password = 'SuperSikrit'
            sourceUrl = 'ignoremereally'
        db.platformMgr.createPlatformSource(platformId, Source())
        db.commit()

    def indexer(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        # Populate the indexer
        indexer.refresh()
        return indexer

    def testGetContent(self):
        # Make sure we populate the indexer's db
        indexer = self.indexer()
        # We test that we're unquoting the file part too
        uri = 'capsules/rpm/content/with-config-speci%61l-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54'

        client = self.getRestClient()
        req, response = client.call('GET', uri)

        self.failUnlessEqual(response.status, 200)
        self.failUnlessEqual(response.getLength(), 3159)
        self.failUnlessEqual(response.headers['content-type'],
            'application/octet-stream')

        errorUris = [
            'capsules/rpm/content/badcontainername/sha1',
            'capsules/rpm/content/badargcount',
            'capsules/rpm/content/badargcount/sha1/badargcount',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/badsha1',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/nosuchfile/sha1',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/%252Fetc%252Fwith-config-special.cfg/badsha1',
        ]
        for uri in errorUris:
            req, response = client.call('GET', uri)
            self.failUnlessEqual(response.status, 404)

        # Fetch file
        uri = 'capsules/rpm/content/with-config-speci%61l-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/%252Fetc%252Fwith-config-special.cfg/337c9fbf3f208f0856c21301abaa370ccc1d14f7'

        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 200)
        self.failUnlessEqual(response.getLength(), 38)
        self.failUnlessEqual(response.headers['content-type'],
            'application/octet-stream')
        self.failUnlessEqual(''.join(x for x in response.get()),
            'config option\nand another config line\n')

    def testRefresh(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        channelLabel = 'rhel-x86_64-server-5'
        # Make sure we don't have any content in the channels
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(channels, [])
        uri = 'capsules/rpm/content'
        client = self.getRestClient()
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 204)
        channel = indexer.model.getChannel(channelLabel)
        self.failUnlessEqual(channel.last_modified, '20091020041355')
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(len(channels), 4)

class CapsulesTestRemote(restbase.BaseRestTest):
    # This controller should mock access from non-localhost
    class ControllerFactory(restbase.Controller):
        class RequestFactory(restbase.MockRequest):
            def _setProperties(self):
                restbase.MockRequest._setProperties(self)
                self.remote = ('1.2.3.4', 12345)

    def testAccess(self):
        uri = 'capsules/rpm/content/aaabbb/sha1sum'

        client = self.getRestClient()
        req, response = client.call('GET', uri)

        self.failUnlessEqual(response.status, 404)

        uri = 'capsules/rpm/content'
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 404)

if __name__ == "__main__":
        testsetup.main()

