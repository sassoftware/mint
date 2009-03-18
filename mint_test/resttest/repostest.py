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

        self.quickMintAdmin('adminuser', 'adminpass')
        ownerClient = self.openMintClient(authToken = ('adminuser', 'adminpass'))
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

    def testGetRepos(self):
        uriTemplate = 'products/%s/repos'
        uri = uriTemplate % (self.shortName, )
        client = self.getRestClient(uri)
        response = client.request('GET')
        # This is less than helpful.
        exp = """\
Index.
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

    def testReposSearch(self):
        uriTemplate = 'products/%s/repos/search'
        uri = uriTemplate % (self.shortName, )

        client = self.getRestClient(uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Label not specified")

        uriTemplate = 'products/%s/repos/search?type=nosuchtype'
        uri = uriTemplate % (self.shortName, )
        self.newConnection(client, uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Invalid search type nosuchtype")

        uriTemplate = 'products/%s/repos/search?type=group'
        uri = uriTemplate % (self.shortName, )
        self.newConnection(client, uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Label not specified")

        badLabels = [
            ('/aaa', '/ should not appear in a label'),
            ('aaa', 'colon expected before branch name'),
            ('a:b', '@ expected before label namespace'),
            ('a:b@', '@ sign must occur before a colon'),
            ('a:b@c', '@ sign must occur before a colon'),
            ('a:b@c:', 'unexpected colon'),
            ('a:b@c:\u0163', 'unexpected colon'),
        ]

        for label, errorMessage in badLabels:
            uriTemplate = 'products/%s/repos/search?type=group&label=%s'
            uri = uriTemplate % (self.shortName, label.encode('utf-8'))
            self.newConnection(client, uri)

            response = self.failUnlessRaises(ResponseError, client.request, 'GET')
            self.failUnlessEqual(response.status, 400)
            self.failUnlessEqual(response.contents,
                "Error parsing label %s: %s" % (label, errorMessage))


if __name__ == "__main__":
        testsetup.main()
