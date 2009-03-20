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

from conary.lib import util
from mint import buildtypes

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ReposTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testGetRepos(self):
        uriTemplate = 'products/%s/repos'
        uri = uriTemplate % (self.productShortName, )
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
        uri = uriTemplate % (self.productShortName, )

        client = self.getRestClient(uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Label not specified")

        uriTemplate = 'products/%s/repos/search?type=nosuchtype'
        uri = uriTemplate % (self.productShortName, )
        self.newConnection(client, uri)

        response = self.failUnlessRaises(ResponseError, client.request, 'GET')
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.contents, "Invalid search type nosuchtype")

        uriTemplate = 'products/%s/repos/search?type=group'
        uri = uriTemplate % (self.productShortName, )
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
            uri = uriTemplate % (self.productShortName, label.encode('utf-8'))
            self.newConnection(client, uri)

            response = self.failUnlessRaises(ResponseError, client.request, 'GET')
            self.failUnlessEqual(response.status, 400)
            self.failUnlessEqual(response.contents,
                "Error parsing label %s: %s" % (label, errorMessage))

        uriTemplate = 'products/%s/repos/search?type=group&label=%s'
        uri = uriTemplate % (self.productShortName,
            self.productDefinition.getDefaultLabel())
        self.newConnection(client, uri)
        response = client.request('GET')
        # We have no troves right now
        self.failUnlessEqual(response.read(), """\
<?xml version='1.0' encoding='UTF-8'?>
<troves/>
""")

        # So let's add some
        label = self.productDefinition.getDefaultLabel()
        self.addComponent("foo:bin=%s" % label)
        self.addCollection("foo=%s" % label, ['foo:bin'])
        self.addCollection("group-foo=%s" % label, ['foo'])

        response = client.request('GET')
        exp =  """\
<?xml version='1.0' encoding='UTF-8'?>
<troves>
  <trove id="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo=/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1[]">
    <hostname>testproject</hostname>
    <name>group-foo</name>
    <version>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</version>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0-devel</label>
    <trailingVersion>1-1-1</trailingVersion>
    <flavor></flavor>
    <timeStamp>%(timestamp)s</timeStamp>
    <images href="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo=/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1[]/images"/>
  </trove>
</troves>
"""
        resp = response.read()
        resp = re.sub("<timeStamp>.*</timeStamp>", "<timeStamp></timeStamp>",
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server,
                        timestamp = ''))

    def testGetImages(self):
        label = self.productDefinition.getDefaultLabel()
        self.addComponent("foo:bin=%s" % label)
        self.addCollection("foo=%s" % label, ['foo:bin'])
        groupTrv = self.addCollection("group-foo=%s" % label, ['foo'])

        uriTemplate = 'products/%s/repos/items/%s=%s[%s]/images'
        uri = uriTemplate % (self.productShortName, groupTrv.getName(),
            groupTrv.getVersion(), groupTrv.getFlavor())

        client = self.getRestClient(uri)
        response = client.request('GET')
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<images/>
"""
        self.failUnlessEqual(response.read(), exp)

        badVerFlv = [
            ('aaa', '', 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('a:b', '', 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('a:b@', '', 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('/a:b@c', 'blah:blah', 'InvalidTroveSpec: Error parsing trove %(trv)s: Error with spec "%(trv)s": bad flavor spec\n'),
        ]

        for ver, flv, errorMessage in badVerFlv:
            uri = uriTemplate % (self.productShortName, groupTrv.getName(),
                ver, flv)
            self.newConnection(client, uri)

            response = self.failUnlessRaises(ResponseError, client.request, 'GET')
            self.failUnlessEqual(response.status, 400)
            trvSpec = "%s=%s[%s]" % ('group-foo', ver, flv)
            self.failUnlessEqual(response.contents, errorMessage % 
                dict(ver = ver, flv = flv, trv = trvSpec))

        # Let's add some images
        db = self.openRestDatabase()
        images = [
            ('Image 1', buildtypes.INSTALLABLE_ISO),
            ('Image 2', buildtypes.TARBALL),
        ]
        groupName = groupTrv.getName()
        groupVer = groupTrv.getVersion().freeze()
        groupFlv = str(groupTrv.getFlavor())
        for imageName, imageType in images:
            imageId = self.createImage(db, self.productShortName,
                imageType, name = imageName,
                description = "Description for %s" % imageName,
                troveName = groupName,
                troveVersion = groupVer,
                troveFlavor = groupFlv)
            self.setImageFiles(db, self.productShortName, imageId)

        uri = uriTemplate % (self.productShortName, groupTrv.getName(),
            groupTrv.getVersion(), groupTrv.getFlavor())

        self.newConnection(client, uri)
        response = client.request('GET')
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<images>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/1">
    <imageId>1</imageId>
    <hostname>testproject</hostname>
    <release/>
    <imageType>Inst CD/DVD</imageType>
    <name>Image 1</name>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0"/>
    <stage/>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser"/>
    <updater/>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <status>401</status>
    <statusMessage>No job</statusMessage>
    <files>
      <file>
        <fileId>1</fileId>
        <imageId>1</imageId>
        <title>Image File 1</title>
        <size>1024</size>
        <sha1>356a192b7913b04c54574d18c28d46e6395428ab</sha1>
        <url urlType="0">%(data)s/images/testproject/2/imagefile_2.iso</url>
      </file>
    </files>
  </image>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/2">
    <imageId>2</imageId>
    <hostname>testproject</hostname>
    <release/>
    <imageType>Tar</imageType>
    <name>Image 2</name>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0"/>
    <stage/>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser"/>
    <updater/>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <status>401</status>
    <statusMessage>No job</statusMessage>
    <files>
      <file>
        <fileId>2</fileId>
        <imageId>2</imageId>
        <title>Image File 2</title>
        <size>2048</size>
        <sha1>da4b9237bacccdf19c0760cab7aec4a8359010b0</sha1>
        <url urlType="0">%(data)s/images/testproject/2/imagefile_2.iso</url>
      </file>
    </files>
  </image>
</images>
"""
        resp = response.read()
        resp = re.sub("<timeCreated>.*</timeCreated>",
                      "<timeCreated></timeCreated>",
                      resp)

        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server,
                        data = self.mintCfg.dataPath))


if __name__ == "__main__":
        testsetup.main()
