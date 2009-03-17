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

    def testGetProductVersion(self):
        uriTemplate = 'products/%s/versions/%s/'
        uri = uriTemplate % (self.shortName, self.productVersion)
        client = self.getRestClient(uri)
        response = client.request('GET')
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<productVersion id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">
  <versionId>1</versionId>
  <hostname>testproject</hostname>
  <name>1.0</name>
  <productUrl href="http://%(server)s:%(port)s/api/products/testproject"/>
  <nameSpace>yournamespace</nameSpace>
  <description>Version description</description>
  <platform href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/platform"/>
  <stages href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/"/>
  <definition href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/definition"/>
  <imageTypeDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions"/>
  <imageDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions"/>
  <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/images"/>
</productVersion>
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

    def testGetProductDefinition(self):
        uriTemplate = 'products/%s/versions/%s/definition'
        uri = uriTemplate % (self.shortName, self.productVersion)
        client = self.getRestClient(uri)
        response = client.request('GET')
        sio = StringIO.StringIO()
        self.productDefinition.serialize(sio)
        self.failUnlessEqual(response.read(), sio.getvalue())

    def testGetStageImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/stages/%s/imageDefinitions'
        uri = uriTemplate % (self.shortName, self.productVersion,
        'Development')

        client = self.getRestClient(uri)
        response = client.request('GET')

        raise testsuite.SkipTestException("out of time, will come back later")
        exp = """\
"""
        self.failUnlessEqual(response.read(),
            exp % dict(server = client.server, port = client.port))

    def testGetImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageDefinitions'
        uri = uriTemplate % (self.shortName, self.productVersion)

        client = self.getRestClient(uri)
        response = client.request('GET')

        raise testsuite.SkipTestException("out of time, will come back later")
        exp = """\
"""
        self.failUnlessEqual(response.read(),
            exp % dict(server = client.server, port = client.port))

    def testGetImageTypeDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageTypeDefinitions'
        uri = uriTemplate % (self.shortName, self.productVersion)

        client = self.getRestClient(uri)
        response = client.request('GET')

        raise testsuite.SkipTestException("out of time, will come back later")
        exp = """\
"""
        self.failUnlessEqual(response.read(),
            exp % dict(server = client.server, port = client.port))

    def testSetImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageDefinitions'
        uri = uriTemplate % (self.shortName, self.productVersion)

        client = self.getRestClient(uri, admin = True)
        response = client.request('PUT', imageSet1)

        raise testsuite.SkipTestException("out of time, will come back later")
        exp = """\
"""
        self.failUnlessEqual(response.read(),
            exp % dict(server = client.server, port = client.port))


imageSet1 = """
<image-definitions>
  <image-definition>
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit Edited for Completeness</displayName>
    <container href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <options autoResolve="false" freespace="6789" natNetworking="false" vmMemory="64" swapSize="512" installLabelPath="" baseFileName=""/>
    </container>
    <architecture href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64"/>
    <flavorSet href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
    </flavorSet>
  </image-definition>
  <image-definition>
    <name>virtual_irony 32-bit</name>
    <displayName>Virtual Irony 32-bit</displayName>
    <container href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="1024"/>
    </container>
    <architecture href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86" />
    <flavorSet href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
    </flavorSet>
  </image-definition>
  <image-definition>
    <name>update iso 64-bit</name>
    <displayName>update iso 64-bit</displayName>
    <container href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="2048"/>
    </container>
    <architecture href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64" />
  </image-definition>
</image-definitions>
"""

if __name__ == "__main__":
        testsetup.main()
