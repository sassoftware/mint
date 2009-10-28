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

    def XXXtestGetPlatformSources(self):        
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourcesXml, xml)

    def XXXtestGetPlatformSource(self):        
        # TODO: can be removed once the code is refactored
        # Need to get platforms first to trigger creation in the db
        self.testGetPlatforms()

        uri = '/platforms/1/sources/plat1source'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceXml, xml)

    def testGetContentSourceStatusNoData(self):
        uri = '/contentSources/rhn/instances/plat2source0/status'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusXml, xml)

    def testGetContentSourceStatusData(self):
        source = models.PlatformSource()
        source.sourceUrl = 'https://example.com'
        source.username = 'foousername'
        source.password = 'foopassword'

        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'getSourceInstance', source)
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              '_checkRHNSourceStatus',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/rhn/instances/plat2source0/status'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusDataXml, xml)

        # Now try and trigger a failure.
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'getSourceInstance', source)
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              '_checkRHNSourceStatus',
                              (True, False, 'Validation Failed'))
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusDataFailXml, xml)

    def testGetSourceDescriptor(self):
        uri = '/contentSources/rhn/descriptor'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(sourceDescriptorXml, xml)

    def testGetSources(self):
        uri = '/contentSources'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourcesXml, xml)

    def testGetSource(self):
        uri = '/contentSources/rhn'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceXml, xml)

    def testGetSourceInstances(self):
        uri = '/contentSources/rhn/instances'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceInstancesXml, xml)

    def testGetSourceInstance(self):
        uri = '/contentSources/rhn/instances/plat2source0'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceInstanceXml, xml)

    def XXXtestPutPlatformSource(self):
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

    def XXXtestPutPlatform(self):
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
