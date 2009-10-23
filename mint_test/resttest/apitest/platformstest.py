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
    <hostname>localhost@rpath:plat-1</hostname>
    <label>localhost@rpath:plat-1</label>
    <platformName>Crowbar Linux 1</platformName>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost@rpath:plat-1/api"/>
    <sources>
      <platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
        <platformSourceId>1</platformSourceId>
        <name>Platform 1 Source</name>
        <platformId>1</platformId>
        <shortname>plat1source</shortname>
        <sourceUrl>http://plat1source.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
      </platformSource>
    </sources>
    <platformMode>proxied</platformMode>
    <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  </platform>
  <platform id="http://localhost:8000/api/platforms/2">
    <platformId>2</platformId>
    <hostname>localhost@rpath:plat-2</hostname>
    <label>localhost@rpath:plat-2</label>
    <platformName>Crowbar Linux 2</platformName>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost@rpath:plat-2/api"/>
    <sources>
      <platformSource id="http://localhost:8000/api/platforms/2/sources/plat2source0">
        <platformSourceId>2</platformSourceId>
        <name>Platform 2 Source 0</name>
        <platformId>2</platformId>
        <shortname>plat2source0</shortname>
        <sourceUrl>https://plat2source0.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/2/sources/plat2source0/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/2/sources/plat2source0/descriptor"/>
      </platformSource>
      <platformSource id="http://localhost:8000/api/platforms/2/sources/plat2source1">
        <platformSourceId>3</platformSourceId>
        <name>Platform 2 Source 1</name>
        <platformId>2</platformId>
        <shortname>plat2source1</shortname>
        <sourceUrl>https://plat2source1.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/2/sources/plat2source1/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/2/sources/plat2source1/descriptor"/>
      </platformSource>
    </sources>
    <platformMode>proxied</platformMode>
    <platformStatus href="http://localhost:8000/api/platforms/2/status"/>
  </platform>
</platforms>
"""
        xml = self._toXml(platforms, client, req)
        self.assertEquals(exp, xml)

if __name__ == "__main__":
        testsetup.main()
