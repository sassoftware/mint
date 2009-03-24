#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import time

from restlib import client as restClient
from mint import helperfuncs

import mint_rephelp

class BaseRestTest(mint_rephelp.WebRepositoryHelper):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]
    productVersion = '1.0'
    productName = 'Project 1'
    productShortName = 'testproject'
    productDomainName = mint_rephelp.MINT_PROJECT_DOMAIN
    productVersionDescription = 'Version description'
    productHostname = "%s.%s" % (productShortName, productDomainName)

    def setupProduct(self):
        version = self.productVersion
        projectName = self.productName
        shortName = self.productShortName
        domainName = self.productDomainName
        description = self.productVersionDescription

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

    def getRestClient(self, uri, username = 'foouser', password = 'foopass',
                      admin = False, **kwargs):
        # Launch a mint server
        defUser = username or 'foouser'
        defPass = password or 'foopass'
        if admin:
            client, userId = self.quickMintAdmin(defUser, defPass)
        else:
            client, userId = self.quickMintUser(defUser, defPass)
        page = self.webLogin(defUser, defPass)
        if username is not None:
            pysid = page.headers['Set-Cookie'].split(';', 1)[0]
            headers = { 'Cookie' : page.headers['Set-Cookie'] }
        else:
            headers = {}
            # Unauthenticated request
        baseUrl = "http://%s:%s/api" % (page.server, page.port)
        client = Client(baseUrl, headers)
        client.server = page.server
        client.port = page.port
        client.baseUrl = baseUrl
        client.username = username
        client.password = password

        # Hack. Do the macro expansion in the URI - so we call __init__ again
        uri = self.makeUri(client, uri)
        client.__init__(uri, headers)
        client.connect()
        return client

    def newConnection(self, client, uri):
        uri = self.makeUri(client, uri)
        client.__init__(uri, client.headers)
        client.connect()
        return client

    def makeUri(self, client, uri):
        if uri.startswith('http://') or uri.startswith('https://'):
            return uri
        replDict = dict(username = client.username, password =
            client.password, port = client.port, server = client.server)

        return ("%s/%s" % (client.baseUrl, uri)) % replDict

class Client(restClient.Client):
    pass


