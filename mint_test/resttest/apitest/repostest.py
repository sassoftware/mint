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

class ReposTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)

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


if __name__ == "__main__":
        testsetup.main()
