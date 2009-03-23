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

    def testGetPlatforms(self):
        return self._testGetPlatforms()

    def testGetPlatformsNotLoggedIn(self):
        return self._testGetPlatforms(notLoggedIn = True)

    def _testGetPlatforms(self, notLoggedIn = False):
        platformLabel = self.mintCfg.availablePlatforms[1]

        # Add a platform definition
        pl = self.productDefinition.toPlatformDefinition()
        pl.setPlatformName('Wunderbar Linux')
        cclient = self.getConaryClient()
        pl.saveToRepository(cclient, platformLabel)

        uriTemplate = 'platforms'
        uri = uriTemplate
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        client = self.getRestClient(uri, **kw)
        response = client.request('GET')
        # This is less than helpful.
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform>
    <label>localhost@rpl:plat</label>
    <platformName>My Spiffy Platform</platformName>
    <enabled>false</enabled>
  </platform>
  <platform>
    <label>testproject.rpath.local2@platform:1</label>
    <platformName>Wunderbar Linux</platformName>
    <enabled>true</enabled>
  </platform>
</platforms>
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

    def getConaryClient(self):
        return conaryclient.ConaryClient(self.cfg)

if __name__ == "__main__":
        testsetup.main()
