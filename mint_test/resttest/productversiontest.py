#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup
import testsuite
testsuite.setup()

import os
import StringIO
import time

from mint import helperfuncs
from mint import notices_store
from conary.lib import util

from rpath_common.proddef import api1 as proddef

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class WebPageTest(restbase.BaseRestTest):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]

    def setUp(self):
        restbase.BaseRestTest.setUp(self)

        version = self.productVersion = '1.0'
        projectName = self.productName = 'Project 1'
        shortName = self.shortName = 'testproject'
        domainName = 'rpath.local2'
        description = "Version description"
        self.hostName = "%s.%s" % (shortName, domainName)

        ownerClient = self.openMintClient()
        projectId = self.projectId = self.newProject(ownerClient, projectName)
        versionId = self.versionId = ownerClient.addProductVersion(projectId,
            self.mintCfg.namespace, version, description=description)
        pd = helperfuncs.sanitizeProductDefinition(
            projectName, '', shortName, domainName,
            shortName, version, '', self.mintCfg.namespace)
        stageRefs = [ x.name for x in pd.getStages() ]
        for buildName, flavorSetRef, archRef, containerTemplateRef in \
                    self.buildDefs:
            pd.addBuildDefinition(name = buildName,
                flavorSetRef = flavorSetRef,
                architectureRef = archRef,
                containerTemplateRef = containerTemplateRef,
                stages = stageRefs)

        ret = ownerClient.setProductDefinitionForVersion(versionId, pd)
        # Make sure we get something back
        self.productDefinition = ownerClient.getProductDefinitionForVersion(versionId)

    def testGetProductDefinition(self):
        uriTemplate = 'products/%s/versions/%s/definition'
        uri = uriTemplate % (self.shortName, self.productVersion)
        client = self.getRestClient(uri)
        response = client.request('GET')
        sio = StringIO.StringIO()
        self.productDefinition.serialize(sio)
        self.failUnlessEqual(response.read(), sio.getvalue())

    def testGetProductDefinitionBuilds(self):
        uriTemplate = 'products/%s/versions/%s/stages/%s/definition/builds'
        uri = uriTemplate % (self.shortName, self.productVersion,
        'Development')

        client = self.getRestClient(uri)
        response = client.request('GET')
        # XXX do something meaningful with this data
        raise testsuite.SkipTestException("out of time, will come back later")
        print response.read()

    def testGetProductDefinitionImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/definition/images'
        uri = uriTemplate % (self.shortName, self.productVersion)

        client = self.getRestClient(uri)
        response = client.request('GET')
        # XXX do something meaningful with this data
        raise testsuite.SkipTestException("out of time, will come back later")
        print response.read()


if __name__ == "__main__":
        testsetup.main()
