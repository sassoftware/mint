#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import time

from mint import notices_store
from conary.lib import util

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class NoticesTest(restbase.BaseRestTest):

    def getStore(self, userId = None):
        if not self.mintCfg:
            self.openRestDatabase()
        return notices_store.createStore(
            os.path.join(self.mintCfg.dataPath, "notices"), userId = userId)

    def testGlobalNoticesAggregation(self):
        store = self.getStore()

        now = time.time()
        store.storeGlobal("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeGlobal("default", "<three />", modified = now - 3)

        uri = 'notices/aggregation'

        client = self.getRestClient()
        req, response = client.call('GET', 'notices/aggregation')

        self.assertXMLEquals(response.get(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global Notices"><one /><two /><three /></channel></rss>""")

    def testGlobalNoticesDefaultContext(self):
        store = self.getStore()

        now = time.time()
        store.storeGlobal("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeGlobal("default", "<three />", modified = now - 3)

        uri = 'notices/contexts/default'

        client = self.getRestClient(username = None)
        req, response = client.call('GET', uri)
        self.assertXMLEquals(response.get(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global notices for context default"><one /><two /><three /></channel></rss>""")

        # Try a non-public context
        uri = 'notices/contexts/aaa'
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 403)

    def testGlobalNoticesAddNoCreds(self):
        store = self.getStore()

        uri = 'notices/contexts/default'

        client = self.getRestClient()
        client.call('POST', uri)

        reqData = '<four />'
        req, response = client.call('POST', uri, body = reqData)
        self.failUnlessEqual(response.status, 403)

    def testGlobalNoticesAdd(self):

        store = self.getStore()

        uri = 'notices/contexts/default'

        client = self.getRestClient(username='user', admin = True)

        reqData = '<four><guid>upstream-guid</guid></four>'

        req, response = client.call('POST', uri, body = reqData)
        data = response.get()

        notice = [ x for x in store.enumerateStoreGlobal("default") ][0]
        guid = 'http://localhost:8000/api/notices/contexts/%s' % notice.id
        source = 'http://localhost:8000/api/notices/contexts/default'

        self.failUnlessEqual(data,
            '<four><guid-upstream>upstream-guid</guid-upstream><guid>%s</guid><source url="%s"/></four>' % (guid, source))

        # Individually fetch the notice
        req, response = client.call('GET', 'notices/contexts/%s' % notice.id)
        self.failUnlessEqual(response.get(), data)

        # Check 404
        req, response = client.call('GET',
                                    'notices/contexts/%sadefadf' % notice.id)
        self.failUnlessEqual(response.status, 404)

        req, response = client.call('DELETE', 'notices/contexts/%s' % notice.id)
        self.failUnlessEqual(response.get(), data)

        # resource should no longer be available
        req, response = client.call('GET', 'notices/contexts/%s' % notice.id)
        self.failUnlessEqual(response.status, 404)

        # You should not be able to delete a context
        req, response = client.call('DELETE', 'notices/contexts/default')
        self.failUnlessEqual(response.status, 403)

    def testUserNoticesAggregation(self):
        store = self.getStore(userId = 'JeanValjean')

        now = time.time()
        store.storeUser("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeUser("default", "<three />", modified = now - 3)
        store.storeGlobal("default", "<four />", modified = now - 2)
        store.storeUser("default", "<five />", modified = now - 1)

        username = 'JeanValjean'
        uri = 'users/%s/notices/aggregation' % username

        client = self.getRestClient(username = username)
        req, response = client.call('GET', uri)
        self.assertXMLEquals(response.get(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Notices for user JeanValjean"><one /><two /><three /><four /><five /></channel></rss>""")

    def testUserNoticesAddNoCreds(self):
        store = self.getStore()

        username = 'JeanValjean'
        uri = 'users/%(username)s/notices/contexts/default' % dict(username=username)

        client = self.getRestClient()

        reqData = '<four />'
        req, response = client.call('POST', uri, body = reqData)
        self.failUnlessEqual(response.status, 403)

    def testUserNoticesAdd(self):
        store = self.getStore(userId = 'JeanValjean')

        uri = 'users/JeanValjean/notices/contexts/default'

        client = self.getRestClient(username = 'JeanValjean',
                                    admin = True)

        reqData = '<four />'

        req, response = client.call('POST', uri, body = reqData)
        data = response.get()

        notice = [ x for x in store.enumerateStoreUser("default") ][0]
        guid = 'http://localhost:8000/api/users/%(username)s/notices/contexts/' + notice.id
        source = 'http://localhost:8000/api/users/%(username)s/notices/contexts/default'
        subs = dict(username='JeanValjean')
        guid = guid % subs
        source = source % subs

        self.failUnlessEqual(data,
            '<four><guid>%s</guid><source url="%s"/></four>' % (guid, source))

        # Individually fetch the notice
        uri = 'users/%(username)s/notices/contexts/' % subs + notice.id
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.get(), data)

        # Check 404
        req, response = client.call('GET', uri + 'adefadf')
        self.failUnlessEqual(response.status, 404)

        req, response = client.call('DELETE', uri)
        self.failUnlessEqual(response.get(), data)

        # resource should no longer be available
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 404)

        # You should not be able to delete a context
        uri = 'notices/contexts/default'
        req, response = client.call('DELETE', uri)
        self.failUnlessEqual(response.status, 403)

    def testNoCrossoverUsers(self):
        # Create notice for our user
        subs = dict(username='JeanValjean')
        store = self.getStore(userId = "JeanValjean")
        notice = store.storeUser("default", "<one />")

        uri = 'users/%(username)s/notices/contexts/' % subs + notice.id
        client = self.getRestClient(username = "JeanValjean")

        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.get(), notice.content)

        # Delete the notice, make sure it's gone
        self.failUnless(store.userStore.exists(notice.id))
        store.userStore.delete(notice.id)
        self.failIf(store.userStore.exists(notice.id))

        # Now create the data for a different user
        store = self.getStore(userId = "blip")
        notice = store.storeUser("default", "<one />")

        # We should not have access to it
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 404)

        # Nothing in the enumeration either
        uri = 'users/%(username)s/notices/contexts/default' % subs
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.get(), """\
<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global notices for context default"></channel></rss>""")

if __name__ == "__main__":
        testsetup.main()
