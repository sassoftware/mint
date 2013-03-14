#
# Copyright (c) SAS Institute Inc.
#

import re

import restbase

class ImagesTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupReleases()

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
  <release id="http://localhost:8000/api/products/testproject/releases/2">
    <releaseId>2</releaseId>
    <hostname>testproject</hostname>
    <name>Release Name</name>
    <version>v1</version>
    <description></description>
    <published>true</published>
    <images href="http://localhost:8000/api/products/testproject/releases/2/images"/>
    <creator href="http://localhost:8000/api/users/adminuser">adminuser</creator>
    <publisher href="http://localhost:8000/api/users/adminuser">adminuser</publisher>
    <timeCreated></timeCreated>
    <timePublished></timePublished>
    <shouldMirror>true</shouldMirror>
    <imageCount>1</imageCount>
  </release>
  <release id="http://localhost:8000/api/products/testproject/releases/1">
    <releaseId>1</releaseId>
    <hostname>testproject</hostname>
    <name>Release Name</name>
    <version>v1</version>
    <description></description>
    <published>false</published>
    <images href="http://localhost:8000/api/products/testproject/releases/1/images"/>
    <creator href="http://localhost:8000/api/users/adminuser">adminuser</creator>
    <timeCreated></timeCreated>
    <shouldMirror>false</shouldMirror>
    <imageCount>3</imageCount>
  </release>
</releases>
"""
        for pat in [ "timeCreated", "timeModified", "timePublished" ]:
            txt = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            txt)
        self.assertXMLEquals(txt,
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
    <release href="http://%(server)s:%(port)s/api/products/testproject/releases/1">Release Name</release>
    <imageType>installableIsoImage</imageType>
    <imageTypeName>Legacy Installable CD/DVD</imageTypeName>
    <name>Image 1</name>
    <architecture></architecture>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <released>true</released>
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
    <release href="http://%(server)s:%(port)s/api/products/testproject/releases/1">Release Name</release>
    <imageType>tarballImage</imageType>
    <imageTypeName>TAR File</imageTypeName>
    <name>Image 2</name>
    <architecture></architecture>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <released>true</released>
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
  <image id="http://localhost:8000/api/products/testproject/images/3">
    <imageId>3</imageId>
    <hostname>testproject</hostname>
    <release href="http://localhost:8000/api/products/testproject/releases/1">Release Name</release>
    <imageType>vmwareEsxImage</imageType>
    <imageTypeName>VMware(R) ESX/VCD Virtual Appliance</imageTypeName>
    <name>Image 3 vmware esx</name>
    <architecture></architecture>
    <troveName>group-foo</troveName>
    <troveVersion>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1-1</troveVersion>
    <trailingVersion>1-1-1</trailingVersion>
    <troveFlavor></troveFlavor>
    <released>true</released>
    <published>false</published>
    <version href="http://localhost:8000/api/products/testproject/versions/1.0">1.0</version>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/Development">Development</stage>
    <creator href="http://localhost:8000/api/users/adminuser">adminuser</creator>
    <timeCreated></timeCreated>
    <buildCount>0</buildCount>
    <buildLog href="http://localhost:8000/api/products/testproject/images/3/buildLog"/>
    <imageStatus id="http://localhost:8000/api/products/testproject/images/3/status">
      <code>-1</code>
      <message></message>
      <isFinal>false</isFinal>
    </imageStatus>
    <files id="http://localhost:8000/api/products/testproject/images/3/files">
      <file>
        <fileId>3</fileId>
        <title>Image File 3</title>
        <size>3072</size>
        <sha1>77de68daecd823babbb58edb1c8e14d7106e83bb</sha1>
        <fileName>imagefile_3.iso</fileName>
        <url urlType="0">http://localhost:8000/downloadImage?fileId=3&amp;urlType=0</url>
      </file>
    </files>
    <baseFileName>testproject-1-</baseFileName>
  </image>
</images>
"""

        self.assertBlobEquals(resp,
            exp % dict(server = 'localhost', port = '8000'))
