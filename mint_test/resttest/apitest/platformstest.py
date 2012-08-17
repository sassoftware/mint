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
from mint.mint_error import PlatformAlreadyExists

from testutils import mock

import restbase
from platformstestxml import *
from restlib import client as restClient

from rpath_proddef import api1 as proddef

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

        platLabel = 'localhost@rpath:plat-1'

        platformMgr = self.openRestDatabase().platformMgr
        mock.mock(proddef.PlatformDefinition, 'loadFromRepository')
        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            reposErrors.OpenError)
        # Reset platform cache
        platformMgr.platforms.platformCache._clearStatus(platLabel)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml2, xml)

        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            conaryErrors.ConaryError)
        # Reset platform cache
        platformMgr.platforms.platformCache._clearStatus(platLabel)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml3, xml)

        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            proddef.ProductDefinitionTroveNotFoundError)
        # Reset platform cache
        platformMgr.platforms.platformCache._clearStatus(platLabel)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformSourceStatusXml4, xml)

        proddef.PlatformDefinition.loadFromRepository._mock.raiseErrorOnAccess(
            Exception)
        # Reset platform cache
        platformMgr.platforms.platformCache._clearStatus(platLabel)
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

    def testGetSourceTypeStatusSMT(self):
        mock.mockFunctionOnce(contentsources.Smt,
                              'status',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/SMT/statusTest'
        xmlReq = '<contentSource><contentSourceId>0</contentSourceId><contentSourceStatus><id /><value /></contentSourceStatus><contentSourceType>SMT</contentSourceType><defaultSource>false</defaultSource><enabled>false</enabled><id /><name>Content source 1</name><orderIndex>0</orderIndex><password>bar</password><resourceErrors /><shortname>contentsource1</shortname><sourceUrl>http://example.com</sourceUrl><status>100</status><username>foo</username></contentSource>'

        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, body=xmlReq)
        xmlResp = self._toXml(platform, client, req)

        self.assertXMLEquals(xmlResp, statusTestPOSTRespXml)

    def testGetSourceTypeStatusRepomd(self):
        mock.mockFunctionOnce(contentsources.Repomd,
                              'status',
                              (True, True, 'Validated Successfully'))

        uri = '/contentSources/repomd/statusTest'
        xmlReq = '<contentSource><contentSourceId>0</contentSourceId><contentSourceStatus><id /><value /></contentSourceStatus><contentSourceType>repomd</contentSourceType><defaultSource>false</defaultSource><enabled>false</enabled><id /><name>Content source 1</name><orderIndex>0</orderIndex><password /><resourceErrors /><shortname>contentsource1</shortname><sourceUrl>http://example.com</sourceUrl><status>100</status><username /></contentSource>'

        client = self.getRestClient(admin=True)
        req, platform = client.call('POST', uri, body=xmlReq)
        xmlResp = self._toXml(platform, client, req)

        self.assertXMLEquals(xmlResp, statusTestPOSTRespXml)


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
        self.assertXMLEquals(platformGETXml, xml)

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

        platLabel = 'localhost@rpath:plat-1'
        platformMgr = self.openRestDatabase().platformMgr
        platformMgr.platforms.platformCache._clearStatus(platLabel)
        req, platform = client.call('GET', uri)
        xml = self._toXml(platform, client, req)
        self.assertXMLEquals(platformStatus2Xml, xml)

    def testLoadPlatform(self):
        req, platforms = self._getPlatformModels()
        
        platformLoad = models.PlatformLoad()
        platformLoad.loadUri = "http://no.such.host/1234"
        platformLoad.jobId = "abcd1234"
        platformLoad.platformId = platforms.platforms[0].platformId

        from rpath_job import api1 as rpath_job
        def bRun(self, *args, **kw):
            self.function(*args, **kw)
        oldBackgroundRunner = rpath_job.BackgroundRunner.backgroundRun
        rpath_job.BackgroundRunner.backgroundRun = bRun
        mock.mock(reposmgr, 'RepositoryManager')
        mock.mock(platformmgr.Platforms, '_load')
        from conary.build import lookaside
        lookasideClass = mock.MockObject()
        lookasideObj = mock.MockObject()
        lookasideClass._mock.setDefaultReturn(lookasideObj)
        mock.mock(lookaside, 'FileFinder', lookasideClass)

        client = self.getRestClient(admin=True)
        platformLoadXml = self._toXml(platformLoad, client, req)
        uri = '/platforms/1/load'
        req, platformLoadJob = client.call('POST', uri, body=platformLoadXml)
        self.assertEquals(len(platformmgr.Platforms._load._mock.calls), 1)

        rpath_job.BackgroundRunner.backgroundRun = oldBackgroundRunner
        

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

if __name__ == "__main__":
        testsetup.main()
