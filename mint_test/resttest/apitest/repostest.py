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
import urllib

from conary.lib import util
from mint import buildtypes
from mint.rest import errors

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ReposTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testReposSearch(self):
        uriTemplate = 'products/%s/repos/search'
        uri = uriTemplate % (self.productShortName, )

        self.createUser('foo')
        client = self.getRestClient(username='foo')

        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.get(), "Label not specified")

        uriTemplate = 'products/%s/repos/search?type=nosuchtype'
        uri = uriTemplate % (self.productShortName, )

        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.get(), "Invalid search type nosuchtype")

        uriTemplate = 'products/%s/repos/search?type=group'
        uri = uriTemplate % (self.productShortName, )
        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 400)
        self.failUnlessEqual(response.get(), "Label not specified")

        badLabels = [ '/aaa', 'aaa', 'a:b', 'a:b@', 'a:b@c',
                      'a:b@c:', 'a:b@c:\u0163' ]

        for label in badLabels:
            uriTemplate = 'products/%s/repos/search?type=group&label=%s'
            uri = uriTemplate % (self.productShortName,
                    urllib.quote(label.encode('utf-8')))
            req, response = client.call('GET', uri)
            self.failUnlessEqual(response.status, 400)
            self.failUnless('Error parsing label' in response.get())

        uriTemplate = 'products/%s/repos/search?type=group&label=%s'
        uri = uriTemplate % (self.productShortName,
            urllib.quote(self.productDefinition.getDefaultLabel()))
        req, response = client.call('GET', uri, convert=True)
        # We have no troves right now
        self.failUnlessEqual(response, """\
<?xml version='1.0' encoding='UTF-8'?>
<troves/>
""")

        # So let's add some
        label = self.productDefinition.getDefaultLabel()
        repos = self.getTestProjectRepos()
        self.addComponent("foo:bin=%s" % label, repos=repos) 
        self.addCollection("foo=%s" % label, ['foo:bin'], repos=repos)
        self.addCollection("group-foo=%s" % label, ['foo'], repos=repos)

        req, response = client.call('GET', uri, convert=True)
        exp =  """\
<?xml version='1.0' encoding='UTF-8'?>
<troves>
  <trove id="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo%3D/testproject.rpath.local2%40yournamespace%3Atestproject-1.0-devel/1-1-1%5B%5D">
    <hostname>testproject</hostname>
    <name>group-foo</name>
    <version>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</version>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0-devel</label>
    <trailingVersion>1-1-1</trailingVersion>
    <flavor></flavor>
    <timeStamp>%(timestamp)s</timeStamp>
    <images href="http://%(server)s:%(port)s/api/products/testproject/repos/items/group-foo%3D/testproject.rpath.local2%40yournamespace%3Atestproject-1.0-devel/1-1-1%5B%5D/images"/>
    <imageCount>0</imageCount>
    <configuration_descriptor></configuration_descriptor>
  </trove>
</troves>
"""
        exp = self.escapeURLQuotes(exp)
        resp = response
        resp = re.sub("<timeStamp>.*</timeStamp>", "<timeStamp></timeStamp>",
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server,
                        timestamp = ''))

    def testGetImages(self):
        label = self.productDefinition.getDefaultLabel()
        repos = self.getTestProjectRepos()
        self.addComponent("foo:bin=%s" % label, repos=repos)
        self.addCollection("foo=%s" % label, ['foo:bin'], repos=repos)
        groupTrv = self.addCollection("group-foo=%s" % label, ['foo'],
                                      repos=repos)

        uriTemplate = 'products/%s/repos/items/%s=%s[%s]/images'
        uri = uriTemplate % (self.productShortName, groupTrv.getName(),
            groupTrv.getVersion(), groupTrv.getFlavor())

        client = self.getRestClient()
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<images/>
"""
        self.failUnlessEqual(response, exp)

        badVerFlv = [
            ('aaa', '', errors.InvalidVersion, 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('a:b', '', errors.InvalidVersion, 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('a:b@', '', errors.InvalidVersion, 'InvalidVersion: Error parsing version %(ver)s: Expected full version, got "%(ver)s"\n'),
            ('/a:b@c', 'blah:blah', errors.InvalidTroveSpec, 'InvalidTroveSpec: Error parsing trove %(trv)s: Error with spec "%(trv)s": bad flavor spec\n'),
        ]

        for ver, flv, cls, errorMessage in badVerFlv:
            uri = uriTemplate % (self.productShortName, groupTrv.getName(),
                ver, flv)

            err = self.assertRaises(cls, client.call,'GET', uri)
            trvSpec = "%s=%s[%s]" % ('group-foo', ver, flv)
            self.failUnlessEqual(cls.__name__ + ': ' + str(err) + '\n',
                errorMessage % dict(ver = ver, flv = flv, trv = trvSpec))

        # Let's add some images
        db = self.openRestDatabase()
        images = [
            ('Image 1', buildtypes.INSTALLABLE_ISO),
            ('Image 2', buildtypes.TARBALL),
        ]
        groupName = groupTrv.getName()
        groupVer = groupTrv.getVersion().freeze()
        groupFlv = str(groupTrv.getFlavor())
        self.setDbUser(db, 'adminuser')
        for imageName, imageType in images:
            imageId = self.createImage(db, self.productShortName,
                imageType, name = imageName,
                description = "Description for %s" % imageName,
                troveName = groupName,
                troveVersion = groupVer,
                troveFlavor = groupFlv)
            self.setImageFiles(db, self.productShortName, imageId)
        db.commit()

        uri = uriTemplate % (self.productShortName, groupTrv.getName(),
            groupTrv.getVersion(), groupTrv.getFlavor())

        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<images>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/1">
    <imageId>1</imageId>
    <hostname>testproject</hostname>
    <imageType>installableIsoImage</imageType>
    <imageTypeName>Legacy Installable CD/DVD</imageTypeName>
    <name>Image 1</name>
    <architecture></architecture>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <released>false</released>
    <published>false</published>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">1.0</version>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development">Development</stage>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <buildLog href="http://%(server)s:%(port)s/api/products/testproject/images/1/buildLog"/>
    <imageStatus id="http://%(server)s:%(port)s/api/products/testproject/images/1/status">
      <code>-1</code>
      <message></message>
      <isFinal>false</isFinal>
    </imageStatus>
    <files id="http://%(server)s:%(port)s/api/products/testproject/images/1/files">
      <file>
        <fileId>1</fileId>
        <title>Image File 1</title>
        <size>1024</size>
        <sha1>356a192b7913b04c54574d18c28d46e6395428ab</sha1>
        <fileName>imagefile_1.iso</fileName>
        <url urlType="0">http://localhost:8000/downloadImage?fileId=1&amp;urlType=0</url>
      </file>
    </files>
    <baseFileName>testproject-1-</baseFileName>
  </image>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/2">
    <imageId>2</imageId>
    <hostname>testproject</hostname>
    <imageType>tarballImage</imageType>
    <imageTypeName>TAR File</imageTypeName>
    <name>Image 2</name>
    <architecture></architecture>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <released>false</released>
    <published>false</published>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">1.0</version>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development">Development</stage>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <buildLog href="http://%(server)s:%(port)s/api/products/testproject/images/2/buildLog"/>
    <imageStatus id="http://%(server)s:%(port)s/api/products/testproject/images/2/status">
      <code>-1</code>
      <message></message>
      <isFinal>false</isFinal>
    </imageStatus>
    <files id="http://%(server)s:%(port)s/api/products/testproject/images/2/files">
      <file>
        <fileId>2</fileId>
        <title>Image File 2</title>
        <size>2048</size>
        <sha1>da4b9237bacccdf19c0760cab7aec4a8359010b0</sha1>
        <fileName>imagefile_2.iso</fileName>
        <url urlType="0">http://localhost:8000/downloadImage?fileId=2&amp;urlType=0</url>
      </file>
    </files>
    <baseFileName>testproject-1-</baseFileName>
  </image>
</images>
"""
        resp = response
        resp = re.sub("<timeCreated>.*?</timeCreated>",
                      "<timeCreated></timeCreated>",
                      resp)

        self.assertBlobEquals(
                actual=resp,
                expected=exp % dict(port = client.port, server = client.server,
                    data = self.mintCfg.dataPath))


if __name__ == "__main__":
        testsetup.main()
