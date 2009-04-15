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
from conary.lib import util
from mint import buildtypes

import mint_rephelp
import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ImagesTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupReleases()

    @mint_rephelp.restFixturize('apitest.setupReleases')
    def setupReleases(self):
        self.setupProduct()
        # Add a group
        label = self.productDefinition.getDefaultLabel()
        db = self.openRestDatabase()
        self.setDbUser(db, 'adminuser')
        client = db.productMgr.reposMgr.getConaryClientForProduct(self.productShortName)
        repos = client.getRepos()
        self.addComponent("foo:bin=%s" % label, repos=repos)
        self.addCollection("foo=%s" % label, ['foo:bin'], repos=repos)
        groupTrv = self.addCollection("group-foo=%s" % label, ['foo'],
                                      repos=repos)

        # Let's add some images
        images = [
            ('Image 1', buildtypes.INSTALLABLE_ISO),
            ('Image 2', buildtypes.TARBALL),
        ]
        groupName = groupTrv.getName()
        groupVer = groupTrv.getVersion().freeze()
        groupFlv = str(groupTrv.getFlavor())
        imageIds = []
        for imageName, imageType in images:
            imageId = self.createImage(db, self.productShortName,
                imageType, name = imageName,
                description = "Description for %s" % imageName,
                troveName = groupName,
                troveVersion = groupVer,
                troveFlavor = groupFlv)
            self.setImageFiles(db, self.productShortName, imageId)
            imageIds.append(imageId)

        releaseId = db.createRelease(self.productShortName, 'Release Name', '',
                'v1', imageIds)

    def testGetReleases(self):
        return self._testGetReleases()

    def testGetReleasesNotLoggedIn(self):
        return self._testGetReleases(notLoggedIn = True)

    def _testGetReleases(self, notLoggedIn = False):
        client = self.getRestClient()
        req, results = client.call('GET', 'products/testproject/releases')
        txt = client.convert('xml', req, results)

        # We have not added releases, we're mainly testing auth vs. nonauth
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<releases>
  <release id="http://localhost:8000/api/products/testproject/releases/1">
    <releaseId>1</releaseId>
    <hostname>testproject</hostname>
    <name>Release Name</name>
    <version>v1</version>
    <description></description>
    <published>false</published>
    <images href="http://localhost:8000/api/products/testproject/releases/1/images"/>
    <creator href="http://localhost:8000/api/users/adminuser">adminuser</creator>
    <updater/>
    <publisher/>
    <timeCreated></timeCreated>
    <shouldMirror>false</shouldMirror>
  </release>
</releases>
"""
        for pat in [ "timeCreated", "timeModified" ]:
            txt = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            txt)
        self.failUnlessEqual(txt, 
            exp % dict(server = 'localhost', port = '8000'))

        # These tests are very expensive, so cram the image test here as well
        req, results = client.call('GET',
                'products/testproject/releases/1/images')
        resp = client.convert('xml', req, results)
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            resp)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<images>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/1">
    <imageId>1</imageId>
    <hostname>testproject</hostname>
    <release href="http://%(server)s:%(port)s/api/products/testproject/releases/1">1</release>
    <imageType>installableIsoImage</imageType>
    <imageTypeName>Installable CD/DVD</imageTypeName>
    <name>Image 1</name>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">1.0</version>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development">Development</stage>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
    <updater/>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <status>-1</status>
    <statusMessage>Unknown</statusMessage>
    <files>
      <file>
        <fileId>1</fileId>
        <imageId>1</imageId>
        <title>Image File 1</title>
        <size>1024</size>
        <sha1>356a192b7913b04c54574d18c28d46e6395428ab</sha1>
        <url urlType="0">/downloadImage?fileId=1</url>
      </file>
    </files>
  </image>
  <image id="http://%(server)s:%(port)s/api/products/testproject/images/2">
    <imageId>2</imageId>
    <hostname>testproject</hostname>
    <release href="http://%(server)s:%(port)s/api/products/testproject/releases/1">1</release>
    <imageType>tarballImage</imageType>
    <imageTypeName>TAR File</imageTypeName>
    <name>Image 2</name>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <version href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">1.0</version>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development">Development</stage>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
    <updater/>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <status>-1</status>
    <statusMessage>Unknown</statusMessage>
    <files>
      <file>
        <fileId>2</fileId>
        <imageId>2</imageId>
        <title>Image File 2</title>
        <size>2048</size>
        <sha1>da4b9237bacccdf19c0760cab7aec4a8359010b0</sha1>
        <url urlType="0">/downloadImage?fileId=2</url>
      </file>
    </files>
  </image>
</images>
"""

        self.failUnlessEqual(resp,
            exp % dict(server = 'localhost', port = '8000'))

if __name__ == "__main__":
        testsetup.main()
