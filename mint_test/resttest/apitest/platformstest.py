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
from mint.rest.modellib import converter

import restbase
from restlib import client as restClient

from rpath_proddef import api1 as proddef

ResponseError = restClient.ResponseError

class PlatformTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()
        self.setupPlatforms()

    def testGetPlatforms(self):
        return self._testGetPlatforms()

    def testGetPlatformsNotLoggedIn(self):
        return self._testGetPlatforms(notLoggedIn = True)

    def _toXml(self, model, client, req):
        return converter.toText('xml', model, client.controller, req)

    def _testGetPlatforms(self, notLoggedIn = False):
        uri = 'platforms'
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        client = self.getRestClient(**kw)
        req, platforms = client.call('GET', uri)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/platforms/1">
    <platformId>1</platformId>
    <hostname>localhost@rpl:plat-1</hostname>
    <label>localhost@rpl:plat-1</label>
    <platformName>Wunderbar Linux</platformName>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost@rpl:plat-1/api"/>
    <sources/>
    <platformMode>proxied</platformMode>
    <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  </platform>
</platforms>
"""
        xml = self._toXml(platforms, client, req)
        self.assertEquals(exp, xml)

if __name__ == "__main__":
        testsetup.main()
