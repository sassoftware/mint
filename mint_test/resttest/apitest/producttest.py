#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import re
import StringIO
import time
import base64

from conary.lib import util

import restbase
from mint.rest import errors as resterrors
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ProductTest(restbase.BaseRestTest):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]

    def testCreateProductErrors(self):
        errors = [
            (dict(shortname = "", hostname = "", name = ""),
                "Product name must be specified"),
            (dict(shortname = "a_b", hostname = "a", name = "a"),
                "Invalid short name: must start with a letter and contain only letters, numbers, and hyphens."),
            (dict(shortname = "-a", hostname = "a", name = "a"),
                "Invalid short name: must start with a letter and contain only letters, numbers, and hyphens."),
            (dict(shortname = "a", hostname = "a_b", name = "a"),
                "Invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."),
            (dict(shortname = "a", hostname = "-a", name = "a"),
                "Invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."),
            (dict(shortname = "a", hostname = "a", name = ""),
                "Product name must be specified"),
        ]
        client = self.getRestClient()
        for uhash, errmsg in errors:
            err = self.assertRaises(resterrors.InvalidItem, 
                                    client.call,'POST', 'products', 
                                    body=newProduct1 % uhash)
            self.failUnlessEqual(str(err), errmsg)

    def testProductLatestReleases(self):
        # test where we actually have a published release
        self.setupReleases()
        client = self.getRestClient()
        req, prd = client.call('GET', '/products/%s' % self.productShortName)
        assert(prd.latestRelease == 2)

    def testUpdateProduct(self):
        # test where we actually have a published release
        self.setupReleases()
        client = self.getRestClient(username='adminuser')
        req, prd = client.call('PUT', '/products/%s' % self.productShortName,
                               body = '''
<product><description>Foo</description>
<commitEmail>foo@rpath.com</commitEmail>
<projecturl>projecturl</projecturl>
<name>new product name</name>
</product>
''')
        assert(prd.description == 'Foo')
        assert(prd.commitEmail == 'foo@rpath.com')
        assert(prd.name == 'new product name')

    def testCreateProduct(self):
        productShortName = "foobar"
        uriTemplate = 'products'
        uri = uriTemplate
        db = self.openMintDatabase(createRepos=False)
        client = self.getRestClient(username='foouser', db=db)
        data = newProduct1 % dict(shortname = "foobar",
            hostname = "foobar", name = "foobar appliance")
        req, response = client.call('POST', uri, data)
        resp = client.convert('xml', req, response)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<product id="http://%(server)s:%(port)s/api/products/foobar">
  <productId>1</productId>
  <hostname>foobar</hostname>
  <name>foobar appliance</name>
  <nameSpace>yournamespace</nameSpace>
  <domainname>rpath.local2</domainname>
  <shortname>foobar</shortname>
  <projecturl></projecturl>
  <repositoryHostname>foobar.rpath.local2</repositoryHostname>
  <repositoryUrl href="http://%(server)s:%(port)s/repos/foobar/api"/>
  <repositoryBrowserUrl href="http://%(server)s:%(port)s/repos/foobar/browse"/>
  <description></description>
  <commitEmail></commitEmail>
  <backupExternal>false</backupExternal>
  <timeCreated>WHITEOUT</timeCreated>
  <timeModified>WHITEOUT</timeModified>
  <hidden>false</hidden>
  <role>Owner</role>
  <versions href="http://%(server)s:%(port)s/api/products/foobar/versions/"/>
  <members href="http://%(server)s:%(port)s/api/products/foobar/members/"/>
  <creator href="http://%(server)s:%(port)s/api/users/foouser">foouser</creator>
  <releases href="http://%(server)s:%(port)s/api/products/foobar/releases/"/>
  <images href="http://%(server)s:%(port)s/api/products/foobar/images/"/>
</product>
"""
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s>WHITEOUT</%s>" % (pat, pat),
            resp)

        self.assertBlobEquals(resp,
             exp % dict(port = 8000, server = 'localhost'))

    def testCreateProduct(self):
        productShortName = "foobar"
        uriTemplate = 'products'
        uri = uriTemplate
        db = self.openMintDatabase(createRepos=False)
        client = self.getRestClient(username=None)
        data = newProduct1 % dict(shortname = "foobar",
            hostname = "foobar", name = "foobar appliance")
        req, response = client.call('POST', uri, data)
        self.failUnlessEqual(response.status, 401)

        req, response = client.call('POST', uri, data,
                headers={'HTTP_X_FLASH_VERSION': '1'})
        self.failUnlessEqual(response.status, 403)


    def testAuthPacket(self):
        username = 'foo'
        password = 'bar'
        productShortName = "foobar"
        uriTemplate = 'products'
        uri = uriTemplate
        db = self.openMintDatabase(createRepos=False)
        client = self.getRestClient(username=None)
        
        msg = "Your authentication header could not be decoded"
        data = newProduct1 % dict(shortname = "foobar",
            hostname = "foobar", name = "foobar appliance")
        auth = 'Basic ' + base64.b64encode(
                    username + ':' + password)[1:]
                    
        err = self.assertRaises(resterrors.AuthHeaderError, 
                                    client.call,'POST', 'products', 
                                    data, headers={'Authorization': auth})
        self.failUnlessEqual(str(err), msg)

newProduct1 = """
<product>
  <shortname>%(shortname)s</shortname>
  <hostname>%(hostname)s</hostname>
  <name>%(name)s</name>
</product>
"""



if __name__ == "__main__":
        testsetup.main()
