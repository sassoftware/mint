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

from conary import conaryclient
from conary.lib import util
from mint import buildtypes

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class PlatformTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testGetReleases(self):
        return self._testGetReleases()

    def testGetReleasesNotLoggedIn(self):
        return self._testGetReleases(notLoggedIn = True)

    def _testGetReleases(self, notLoggedIn = False):
        uriTemplate = 'products/testproject/releases'
        uri = uriTemplate
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        client = self.getRestClient(uri, **kw)
        response = client.request('GET')
        # We have not added releases, we're mainly testing auth vs. nonauth
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<releases/>
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

if __name__ == "__main__":
        testsetup.main()
