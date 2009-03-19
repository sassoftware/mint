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

from conary.lib import util

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ReposTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testGetRepos(self):
        uriTemplate = 'products/%s/repos'
        uri = uriTemplate % (self.productShortName, )
        client = self.getRestClient(uri)
        response = client.request('GET')
        # This is less than helpful.
        exp = """\
Index.
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

    def testReposSearch(self):
        uriTemplate = 'products/%s/repos/search'
        uri = uriTemplate % (self.productShortName, )

        client = self.getRestClient(uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Label not specified")

        uriTemplate = 'products/%s/repos/search?type=nosuchtype'
        uri = uriTemplate % (self.productShortName, )
        self.newConnection(client, uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Invalid search type nosuchtype")

        uriTemplate = 'products/%s/repos/search?type=group'
        uri = uriTemplate % (self.productShortName, )
        self.newConnection(client, uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Label not specified")

        badLabels = [
            ('/aaa', '/ should not appear in a label'),
            ('aaa', 'colon expected before branch name'),
            ('a:b', '@ expected before label namespace'),
            ('a:b@', '@ sign must occur before a colon'),
            ('a:b@c', '@ sign must occur before a colon'),
            ('a:b@c:', 'unexpected colon'),
            ('a:b@c:\u0163', 'unexpected colon'),
        ]

        for label, errorMessage in badLabels:
            uriTemplate = 'products/%s/repos/search?type=group&label=%s'
            uri = uriTemplate % (self.productShortName, label.encode('utf-8'))
            self.newConnection(client, uri)

            response = self.failUnlessRaises(ResponseError, client.request, 'GET')
            self.failUnlessEqual(response.status, 400)
            self.failUnlessEqual(response.contents,
                "Error parsing label %s: %s" % (label, errorMessage))

        uriTemplate = 'products/%s/repos/search?type=group&label=%s'
        uri = uriTemplate % (self.productShortName,
            self.productDefinition.getDefaultLabel())
        self.newConnection(client, uri)
        response = client.request('GET')
        # We have no troves right now
        self.failUnlessEqual(response.read(), """\
<?xml version='1.0' encoding='UTF-8'?>
<troves/>
""")

        # So let's add some
        label = self.productDefinition.getDefaultLabel()
        self.addComponent("foo:bin=%s" % label)
        self.addCollection("foo=%s" % label, ['foo:bin'])
        self.addCollection("group-foo=%s" % label, ['foo'])

        response = client.request('GET')
        exp =  """\
<?xml version='1.0' encoding='UTF-8'?>
<troves>
  <trove id="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo=/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1[]">
    <hostname>testproject</hostname>
    <name>group-foo</name>
    <version>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</version>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0-devel</label>
    <trailingVersion>1-1-1</trailingVersion>
    <flavor></flavor>
    <timeStamp>%(timestamp)s</timeStamp>
    <images href="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo=/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1[]/images"/>
  </trove>
</troves>
"""
        resp = response.read()
        resp = re.sub("<timeStamp>.*</timeStamp>", "<timeStamp></timeStamp>",
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server,
                        timestamp = ''))


if __name__ == "__main__":
        testsetup.main()
