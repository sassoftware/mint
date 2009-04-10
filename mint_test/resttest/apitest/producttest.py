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

from conary.lib import util

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ProductVersionTest(restbase.BaseRestTest):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]

    def setUp(self):
        restbase.BaseRestTest.setUp(self)

    def testCreateProductErrors(self):
        errors = [
            (dict(shortname = "", hostname = "", name = ""),
                "InvalidItem: Product name must be specified\n"),
            (dict(shortname = "a_b", hostname = "a", name = "a"),
                "InvalidItem: Invalid short name: must start with a letter and contain only letters, numbers, and hyphens.\n"),
            (dict(shortname = "-a", hostname = "a", name = "a"),
                "InvalidItem: Invalid short name: must start with a letter and contain only letters, numbers, and hyphens.\n"),
            (dict(shortname = "a", hostname = "a_b", name = "a"),
                "InvalidItem: Invalid hostname: must start with a letter and contain only letters, numbers, and hyphens.\n"),
            (dict(shortname = "a", hostname = "-a", name = "a"),
                "InvalidItem: Invalid hostname: must start with a letter and contain only letters, numbers, and hyphens.\n"),
            (dict(shortname = "a", hostname = "a", name = ""),
                "InvalidItem: Product name must be specified\n"),
        ]
        uriTemplate = 'products'
        uri = uriTemplate
        client = self.getRestClient(uri)
        for uhash, errmsg in errors:
            resp = self.failUnlessRaises(ResponseError,
                client.request, 'POST', newProduct1 % uhash)
            self.failUnlessEqual(resp.status, 400)
            self.failUnlessEqual(resp.contents, errmsg)

    def testCreateProduct(self):
        productShortName = "foobar"
        uriTemplate = 'products'
        uri = uriTemplate
        client = self.getRestClient(uri)
        data = newProduct1 % dict(shortname = "foobar",
            hostname = "foobar", name = "foobar appliance")
        response = client.request('POST', data)
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
  <isAppliance>false</isAppliance>
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
        resp = response.read()
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s>WHITEOUT</%s>" % (pat, pat),
            resp)

        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server))

newProduct1 = """
<product>
  <shortname>%(shortname)s</shortname>
  <hostname>%(hostname)s</hostname>
  <name>%(name)s</name>
</product>
"""


if __name__ == "__main__":
        testsetup.main()
