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
from conary import dbstore
from conary.lib import util
from mint import buildtypes
from mint.rest.api import models
from mint.rest.db import platformmgr
from mint.rest.modellib import converter

from mint_test import mock

import restbase
from platformstestxml import *
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

        xml = self._toXml(platforms, client, req)
        self.assertEquals(platformsXml, xml)

    def testGetPlatform(self):
        uri = '/platforms/1'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformXml, xml)

    def testGetPlatformSources(self):        
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourcesXml, xml)

    def testGetPlatformSource(self):        
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources/plat1source'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceXml, xml)

    def testGetPlatformSourceStatusNoData(self):
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources/plat1source/status'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceStatusXml, xml)

    def testGetPlatformSourceStatusData(self):
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        source = models.PlatformSource()
        source.sourceUrl = 'https://example.com'
        source.username = 'foousername'
        source.password = 'foopassword'

        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'listPlatformSources', source)
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              '_checkRHNSourceStatus',
                              (True, True, 'Validated Successfully'))

        uri = '/platforms/1/sources/plat1source/status'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceStatusDataXml, xml)

        # Now try and trigger a failure.
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'listPlatformSources', source)
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              '_checkRHNSourceStatus',
                              (True, False, 'Validation Failed'))
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceStatusDataFailXml, xml)

    def testGetPlatformSourceDescriptor(self):
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources/plat1source/descriptor'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceDescriptorXml, xml)
        
    def testPutPlatformSource(self):
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources/plat1source'
        client = self.getRestClient()
        req, platform = client.call('PUT', uri, body=platformSourcePUTXml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourcePUTXml, xml)

        # Now that username/password is set in db, PUT again to test an 
        # update.
        req, platform = client.call('PUT', uri, body=platformSourcePUTXml2)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourcePUTXml2, xml)

    def testPutPlatform(self):
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1'
        client = self.getRestClient()
        req, platform = client.call('PUT', uri, body=platformPUTXml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformPUTXml, xml)

if __name__ == "__main__":
        testsetup.main()
