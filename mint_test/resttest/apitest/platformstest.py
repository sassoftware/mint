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
from conary import errors as conaryErrors
from conary.lib import util
from conary.repository import errors as reposErrors
from mint import buildtypes
from mint.rest.api import models
from mint.rest.db import platformmgr
from mint.rest.db import reposmgr
from mint.rest.db import contentsources
from mint.rest.modellib import converter

from testutils import mock

import restbase
from platformstestxml import *
from restlib import client as restClient

from rpath_proddef import api1 as proddef

ResponseError = restClient.ResponseError

class PlatformsTest(restbase.BaseRestTest):
    architectures = [
           # ('x86', 'x86', 'is:x86 x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)'),
           # ('x86_64', 'x86 (64-bit)', 'is:x86_64 x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)')
    ]
    containerTemplates = [
           # ('vmwareEsxImage', {'autoResolve':'false', 'natNetworking':'true', 'baseFileName':'', 'vmSnapshots':'false', 'swapSize':'512', 'vmMemory':'256', 'installLabelPath':'', 'freespace':'1024'}),
           # ('xenOvaImage', {'autoResolve':'false', 'baseFileName':'', 'swapSize':'512', 'vmMemory':'256', 'installLabelPath':'', 'freespace':'1024'}),
    ]
    flavorSets = [
           # ('xen', 'Xen DomU', '~xen, ~domU, ~!dom0, ~!vmware'),
           # ('vmware','VMware','~vmware, ~!xen, !domU, ~!dom0'),
    ]
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()
        self.setupPlatforms()
        mock.mock(platformmgr.Platforms, '_checkMirrorPermissions',
                        True)

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
        self.assertXMLEquals(platformsXml, xml)

    def testGetPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformXml, xml)

    def testGetImageTypeDefinitions(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()
        uri = '/platforms/1/imageTypeDefinitions'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformImageDefXml, xml)

    def testGetPlatformSourceStatus(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        mock.mockFunctionOnce(reposmgr.RepositoryManager,
            '_getFullRepositoryMap', 
            {'localhost' : 'http://localhost:8000/repos/localhost'})

        client = self.getRestClient(admin=True)

        # Enable the platform
        mock.mockFunctionOnce(platformmgr.Platforms,
                              '_setupPlatform', 1)
        uri2 = '/platforms/1'
        req, platform = client.call('PUT', uri2, body=platformPUTXml)

        uri = '/platforms/1/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml, xml)

        mock.mock(proddef.PlatformDefinition, 'loadFromRepository')
        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            reposErrors.OpenError)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml2, xml)
        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            conaryErrors.ConaryError)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml3, xml)
        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            proddef.ProductDefinitionTroveNotFoundError)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml4, xml)
        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            Exception)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml5, xml)

    def testGetContentSourceStatusNoData(self):
        uri = '/contentSources/RHN/instances/plat2source0/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourceStatusXml, xml)

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
        self.assertXMLEquals(contentSourceStatusDataXml, xml)

        # Now try and trigger a failure.
        mock.mockFunctionOnce(platformmgr.PlatformManager,
                              'getSource', source)
        mock.mockFunctionOnce(contentsources.Rhn,
                              'status',
                              (True, False, 'Validation Failed'))
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourceStatusDataFailXml, xml)

    def testGetSourceTypeStatus(self):
        mock.mockFunctionOnce(contentsources.Rhn,
                              'status',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/RHN/statusTest'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri,
                            body=statusTestPOSTXml)
        xml = self._toXml(platform, client, req)

        self.assertXMLEquals(statusTestPOSTRespXml, xml)

    def testGetSourceDescriptor(self):
        uri = '/contentSources/RHN/descriptor'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(sourceDescriptorXml, xml)

        uri = '/contentSources/satellite/descriptor'
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(sourceDescriptor2Xml, xml)

    def testGetSourceTypes(self):
        uri = '/contentSources'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourceTypesXml, xml)

    def testGetSourceType(self):
        uri = '/contentSources/RHN'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourceTypeXml, xml)

    def testGetSources(self):
        uri = '/contentSources/RHN/instances'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourcesXml, xml)

    def _getSource(self, name):
        uri = '/contentSources/RHN/instances/%s' % name
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        return self._toXml(platform, client, req)

    def testGetSource(self):
        xml = self._getSource('plat2source0')
        self.assertXMLEquals(contentSourceXml, xml)

    def testGetSourcesByPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1/contentSources'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourcesByPlatformXml, xml)
    
    def testGetSourceTypesByPlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        uri = '/platforms/1/contentSourceTypes'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourceTypesByPlatformXml, xml)

    def testUpdateSource(self):
        # GET the source instance first, so it will be created
        self._getSource('plat2source0')

        uri = '/contentSources/RHN/instances/plat2source0'
        client = self.getRestClient(admin=True)
        req, platform = client.call('PUT', uri, body=contentSourcePUTXml)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourcePUTXml, xml)

        # Now that username/password is set in db, PUT again to test an 
        # update.
        req, platform = client.call('PUT', uri, body=contentSourcePUTXml2)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(contentSourcePUTXml2, xml)

    def testCreateSource(self):
        uri = '/contentSources/RHN/instances/'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, 
                            body=sourcePOSTXml)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(sourcePOSTRespXml, xml)

    def testCreateSource2(self):
        uri = '/contentSources/satellite/instances/'
        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, 
                            body=sourcePOST2Xml)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(sourcePOSTResp2Xml, xml)

    def testUpdatePlatform(self):
        # we already have a platform, so we must assume they've already been
        # created in the db.  call getPlatforms to create them for this test.
        self._getPlatforms()

        mock.mockFunctionOnce(platformmgr.Platforms,
                              '_setupPlatform', 1)

        uri = '/platforms/1'
        client = self.getRestClient(admin=True)
        req, platform = client.call('PUT', uri, body=platformPUTXml)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformPUTXml, xml)

    def testGetPlatformStatus(self):
        self._getPlatforms()
        uri = '/platforms/1/status'
        client = self.getRestClient(admin=True)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformStatusXml, xml)

        # Enable the platform
        mock.mockFunctionOnce(platformmgr.Platforms,
                              '_setupPlatform', 1)
        uri2 = '/platforms/1'
        req, platform = client.call('PUT', uri2, body=platformPUTXml)

        # Check the status now
        mock.mockFunctionOnce(proddef.PlatformDefinition,
                              'loadFromRepository', 1)
        mock.mockFunctionOnce(reposmgr.RepositoryManager,
                              '_getFullRepositoryMap', 
                              {'localhost':'http://localhost/conary/'})
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformStatus2Xml, xml)

if __name__ == "__main__":
        testsetup.main()
