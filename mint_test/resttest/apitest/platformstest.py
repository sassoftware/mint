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
from mint.rest.db import contentsources
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

    def _toXml(self, model, client, req):
        return converter.toText('xml', model, client.controller, req)

    def _getPlatforms(self):
        uri = 'platforms'
        kw = {}
        kw['username'] = 'username'
        kw['password'] = 'password'
        client = self.getRestClient(**kw)
        req, platforms = client.call('GET', uri)
        return self._toXml(platforms, client, req)

    def _testGetPlatforms(self):
        xml = self._getPlatforms()
        self.assertEquals(platformsXml, xml)

    def testGetPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformXml, xml)

    def testGetPlatformSourceStatus(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformSourceStatusXml, xml)

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
        uri = '/contentSources/RHN/instances/plat2source0/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusXml, xml)

    def testGetContentSourceStatusData(self):
        source = models.RhnSource()
        source.sourceUrl = 'https://example.com'
        source.username = 'foousername'
        source.password = 'foopassword'
        source.name = 'RHN'
        source.contentSourceType = 'RHN'

        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'getSource', source)
        mock.mockFunctionOnce(contentsources.Rhn,
                              'status',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/RHN/instances/plat2source0/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusDataXml, xml)

        # Now try and trigger a failure.
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'getSource', source)
        mock.mockFunctionOnce(contentsources.Rhn,
                              'status',
                              (True, False, 'Validation Failed'))
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceStatusDataFailXml, xml)

    def testGetSourceTypeStatus(self):
        mock.mockFunctionOnce(contentsources.Rhn,
                              'status',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/RHN/statusTest'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri,
                            body=statusTestPOSTXml)
        xml = self._toXml(platform, client, req)

        self.assertEquals(statusTestPOSTRespXml, xml)

    def testGetSourceDescriptor(self):
        uri = '/contentSources/RHN/descriptor'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(sourceDescriptorXml, xml)

        uri = '/contentSources/satellite/descriptor'
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(sourceDescriptor2Xml, xml)

    def testGetSourceTypes(self):
        uri = '/contentSources'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceTypesXml, xml)

    def testGetSourceType(self):
        uri = '/contentSources/RHN'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceTypeXml, xml)

    def testGetSources(self):
        uri = '/contentSources/RHN/instances'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourcesXml, xml)

    def _getSource(self, name):
        uri = '/contentSources/RHN/instances/%s' % name
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        return self._toXml(platform, client, req)

    def testGetSource(self):
        xml = self._getSource('plat2source0')
        self.assertEquals(contentSourceXml, xml)

    def testGetSourcesByPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1/contentSources'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourcesByPlatformXml, xml)
    
    def testGetSourceTypesByPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1/contentSourceTypes'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourceTypesByPlatformXml, xml)

    def testUpdateSource(self):
        # GET the source instance first, so it will be created
        self._getSource('plat2source0')

        uri = '/contentSources/RHN/instances/plat2source0'
        client = self.getRestClient(admin=True)
        req, platform = client.call('PUT', uri, body=contentSourcePUTXml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourcePUTXml, xml)

        # Now that username/password is set in db, PUT again to test an 
        # update.
        req, platform = client.call('PUT', uri, body=contentSourcePUTXml2)
        xml = self._toXml(platform, client, req)
        self.assertEquals(contentSourcePUTXml2, xml)

    def testCreateSource(self):
        uri = '/contentSources/RHN/instances/'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, 
                            body=sourcePOSTXml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(sourcePOSTRespXml, xml)

    def testCreateSource2(self):
        uri = '/contentSources/satellite/instances/'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, 
                            body=sourcePOST2Xml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(sourcePOSTResp2Xml, xml)

    def testUpdatePlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1'
        client = self.getRestClient(admin=True)
        req, platform = client.call('PUT', uri, body=platformPUTXml)
        xml = self._toXml(platform, client, req)
        self.assertEquals(platformPUTXml, xml)

if __name__ == "__main__":
        testsetup.main()
