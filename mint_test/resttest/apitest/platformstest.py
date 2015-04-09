#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.db import platformmgr
from mint.rest.modellib import converter
from mint.mint_error import PlatformAlreadyExists

from testutils import mock

import restbase
from platformstestxml import *
from restlib import client as restClient

ResponseError = restClient.ResponseError

class BaseTest(restbase.BaseRestTest):
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

class PlatformsTest(BaseTest):
    def testGetPlatforms(self):
        return self._testGetPlatforms()

    def _toXml(self, model, client, req):
        return converter.toText('xml', model, client.controller, req)

    def _getPlatformModels(self):
        uri = 'platforms'
        kw = {}
        kw['username'] = 'username'
        kw['password'] = 'password'
        client = self.getRestClient(**kw)
        req, platforms = client.call('GET', uri)
        self.client = client
        return req, platforms

    def _getPlatforms(self):
        self._disableAllPlatforms()
        req, platforms = self._getPlatformModels()
        return self._toXml(platforms, self.client, req)

    def _testGetPlatforms(self):
        xml = self._getPlatforms()
        self.assertXMLEquals(platformsXml, xml)

    def _disableAllPlatforms(self):
        restdb = self.openRestDatabase()
        restdb.db.cursor().execute("UPDATE Platforms SET enabled=0")
        restdb.db.commit()

    def testGetPlatform(self):
        self._disableAllPlatforms()
        uri = '/platforms/1'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformXml, xml)

    def testGetImageTypeDefinitions(self):
        uri = '/platforms/1/imageTypeDefinitions'
        client = self.getRestClient()
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformImageDefXml, xml)

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
        self.assertXMLEquals(platformGETXml, xml)


class NewPlatformTest(BaseTest):

    def testCreatePlatform(self):
        # Create a platform from a product
        pdLabel = self.productDefinition.getProductDefinitionLabel()
        uri = "/platforms"
        xml = "<platform><label>%s</label><platformName>ignored</platformName></platform>" % pdLabel
        client = self.getRestClient()
        req, plat = client.call('POST', uri, body=xml)
        self.failUnlessEqual(plat.label, pdLabel)
        self.failUnlessEqual(plat.platformName, 'Project 1')

        # Post again, should produce ConflictError guarding against
        # inadvertent overwrite of existing platform.
        self.assertRaises(PlatformAlreadyExists, client.call, 'POST', uri, body=xml)

    def testCreatePlatform_NoProduct(self):
        # Create a platform when there is no product
        self.setupPlatform3(repositoryOnly=True)
        pdLabel = 'localhost@rpath:plat-3'

        uri = "/platforms"
        xml = "<platform><label>%s</label><platformName>ignored</platformName></platform>" % pdLabel
        client = self.getRestClient()
        req, plat = client.call('POST', uri, body=xml)
        self.failUnlessEqual(plat.label, pdLabel)
        self.failUnlessEqual(plat.platformName, 'Crowbar Linux 3')

    def testCreatePlatform_NoPlatform(self):
        # Create a platform when there is no product or platform
        self.setupPlatform3(repositoryOnly=True)
        pdLabel = 'localhost@rpath:plat-4'

        uri = "/platforms"
        xml = "<platform><label>%s</label><platformName>Platform 4</platformName><abstract>true</abstract><configurable>true</configurable></platform>" % pdLabel
        client = self.getRestClient()
        req, plat = client.call('POST', uri, body=xml)
        self.failUnlessEqual(plat.label, pdLabel)
        self.failUnlessEqual(plat.platformName, 'Platform 4')
        self.failUnlessEqual(plat.abstract, True)
        self.failUnlessEqual(plat.configurable, True)

