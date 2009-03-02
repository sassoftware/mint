#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import os
import time

from mint import notices_store
from conary.lib import util

import mint_rephelp
from restlib import client as restClient
ResponseError = restClient.ResponseError

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def tearDown(self):
        mint_rephelp.WebRepositoryHelper.tearDown(self)
        util.rmtree(os.path.join(self.mintCfg.dataPath, 'notices'),
                    ignore_errors = True)

    def getRestClient(self, uri, username = 'foouser', password = 'foopass',
                      admin = False, **kwargs):
        # Launch a mint server
        defUser = username or 'foouser'
        defPass = password or 'foopass'
        if admin:
            client, userId = self.quickMintAdmin(defUser, defPass)
        else:
            client, userId = self.quickMintUser(defUser, defPass)
        page = self.webLogin(defUser, defPass)
        if username is not None:
            pysid = page.headers['Set-Cookie'].split(';', 1)[0]
            headers = { 'Cookie' : page.headers['Set-Cookie'] }
        else:
            headers = {}
            # Unauthenticated request
        baseUrl = "http://%s:%s/api/v1" % (page.server, page.port)
        client = Client(baseUrl, headers)
        client.server = page.server
        client.port = page.port
        client.baseUrl = baseUrl
        client.username = username
        client.password = password

        # Hack. Do the macro expansion in the URI - so we call __init__ again
        uri = self.makeUri(client, uri)
        client.__init__(uri, headers)
        client.connect()
        return client

    def newConnection(self, client, uri):
        uri = self.makeUri(client, uri)
        client.__init__(uri, client.headers)
        client.connect()
        return client

    def makeUri(self, client, uri):
        if uri.startswith('http://') or uri.startswith('https://'):
            return uri
        replDict = dict(username = client.username, password =
            client.password, port = client.port, server = client.server)

        return ("%s/%s" % (client.baseUrl, uri)) % replDict

    def getStore(self, userId = None):
        return notices_store.createStore(
            os.path.join(self.mintCfg.dataPath, "notices"), userId = userId)

    def testGlobalNoticesAggregation(self):
        store = self.getStore()

        now = time.time()
        store.storeGlobal("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeGlobal("default", "<three />", modified = now - 3)

        uri = 'notices/aggregation'

        client = self.getRestClient(uri, username = None)
        response = client.request('GET')
        self.assertXMLEquals(response.read(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global Notices"><one /><two /><three /></channel></rss>""")

    def testGlobalNoticesDefaultContext(self):
        store = self.getStore()

        now = time.time()
        store.storeGlobal("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeGlobal("default", "<three />", modified = now - 3)

        uri = 'notices/contexts/default'

        client = self.getRestClient(uri, username = None)
        response = client.request('GET')
        self.assertXMLEquals(response.read(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global notices for context default"><one /><two /><three /></channel></rss>""")

        # Try a non-public context
        uri = 'notices/contexts/aaa'
        self.newConnection(client, uri)
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 403)

    def testGlobalNoticesAddNoCreds(self):
        store = self.getStore()

        uri = 'notices/contexts/default'

        client = self.getRestClient(uri)

        reqData = '<four />'
        response = self.failUnlessRaises(ResponseError, client.request, 'POST', body = reqData)
        self.failUnlessEqual(response.status, 403)

    def testGlobalNoticesAdd(self):

        store = self.getStore()

        uri = 'notices/contexts/default'

        client = self.getRestClient(uri, admin = True)

        reqData = '<four />'

        response = client.request('POST', body = reqData)
        data = response.read()

        notice = [ x for x in store.enumerateStoreGlobal("default") ][0]
        guid = self.makeUri(client, 'notices/contexts/%s' % notice.id)
        source = self.makeUri(client, 'notices/contexts/default')

        self.failUnlessEqual(data,
            '<four><guid>%s</guid><source url="%s"/></four>' % (guid, source))

        # Individually fetch the notice
        uri = 'notices/contexts/%s' % notice.id
        self.newConnection(client, uri)
        response = client.request('GET')
        self.failUnlessEqual(response.read(), data)

        # Check 404
        self.newConnection(client, uri + "adefadf")
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 404)

        self.newConnection(client, uri)
        response = client.request('DELETE')
        self.failUnlessEqual(response.read(), data)

        # resource should no longer be available
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 404)

        # You should not be able to delete a context
        uri = 'notices/contexts/default'
        self.newConnection(client, uri)
        response = self.failUnlessRaises(ResponseError, client.request, 'DELETE')
        self.failUnlessEqual(response.status, 403)

    def testUserNoticesAggregation(self):
        store = self.getStore(userId = 'JeanValjean')

        now = time.time()
        store.storeUser("default", "<one />", modified = now - 5)
        store.storeGlobal("default", "<two />", modified = now - 4)
        store.storeUser("default", "<three />", modified = now - 3)
        store.storeGlobal("default", "<four />", modified = now - 2)
        store.storeUser("default", "<five />", modified = now - 1)

        uri = 'users/%(username)s/notices/aggregation'

        client = self.getRestClient(uri, username = 'JeanValjean')
        response = client.request('GET')
        self.assertXMLEquals(response.read(), """<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Notices for user JeanValjean"><one /><two /><three /><four /><five /></channel></rss>""")

    def testUserNoticesAddNoCreds(self):
        store = self.getStore()

        uri = 'users/%(username)s/notices/contexts/default'

        client = self.getRestClient(uri)

        reqData = '<four />'
        response = self.failUnlessRaises(ResponseError, client.request, 'POST', body = reqData)
        self.failUnlessEqual(response.status, 403)

    def testUserNoticesAdd(self):
        store = self.getStore(userId = 'JeanValjean')

        uri = 'users/%(username)s/notices/contexts/default'

        client = self.getRestClient(uri, username = 'JeanValjean',
            admin = True)

        reqData = '<four />'

        response = client.request('POST', body = reqData)
        data = response.read()

        notice = [ x for x in store.enumerateStoreUser("default") ][0]
        guid = self.makeUri(client, 'users/%(username)s/notices/contexts/'
            + notice.id)
        source = self.makeUri(client, 'users/%(username)s/notices/contexts/default')

        self.failUnlessEqual(data,
            '<four><guid>%s</guid><source url="%s"/></four>' % (guid, source))

        # Individually fetch the notice
        uri = 'users/%(username)s/notices/contexts/' + notice.id
        self.newConnection(client, uri)
        response = client.request('GET')
        self.failUnlessEqual(response.read(), data)

        # Check 404
        self.newConnection(client, uri + 'adefadf')
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 404)

        self.newConnection(client, uri)
        response = client.request('DELETE')
        self.failUnlessEqual(response.read(), data)

        # resource should no longer be available
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 404)

        # You should not be able to delete a context
        uri = 'notices/contexts/default'
        self.newConnection(client, uri)
        response = self.failUnlessRaises(ResponseError, client.request, 'DELETE')
        self.failUnlessEqual(response.status, 403)


    def testNoCrossoverUsers(self):
        # Create notice for our user
        store = self.getStore(userId = "JeanValjean")
        notice = store.storeUser("default", "<one />")

        uri = 'users/%(username)s/notices/contexts/' + notice.id
        client = self.getRestClient(uri, username = "JeanValjean")

        response = client.request('GET')
        self.failUnlessEqual(response.read(), notice.content)

        # Delete the notice, make sure it's gone
        self.failUnless(store.userStore.exists(notice.id))
        store.userStore.delete(notice.id)
        self.failIf(store.userStore.exists(notice.id))

        # Now create the data for a different user
        store = self.getStore(userId = "blip")
        notice = store.storeUser("default", "<one />")

        # We should not have access to it
        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 404)

        # Nothing in the enumeration either
        uri = 'users/%(username)s/notices/contexts/default'
        self.newConnection(client, uri)

        response = client.request('GET')
        self.failUnlessEqual(response.read(), """\
<?xml version='1.0' encoding='UTF-8'?>
<rss version="2.0"><channel title="Global notices for context default"></channel></rss>""")


class Client(restClient.Client):
    pass

if __name__ == "__main__":
        testsuite.main()
