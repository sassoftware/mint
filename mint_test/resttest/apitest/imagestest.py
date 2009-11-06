#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import re
import subprocess
import time

from conary.lib import digestlib
from mint import buildtypes
from mint import jobstatus
from mint.rest.errors import BuildNotFound, PermissionDeniedError
from mint_test import mint_rephelp
import restbase

class ImagesTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupReleases()

    def testDeleteImage(self):
        # image 1 is not published yet
        client = self.getRestClient(username='adminuser')
        db = self.openRestDatabase()
        url, = db.cursor().execute('''SELECT url from BuildFiles
                                      JOIN BuildFilesUrlsMap USING (fileId)
                                      JOIN FilesUrls USING(urlId)
                                      WHERE buildId=?
                                   ''', 1).fetchone()
        assert(os.path.exists(url))
        client.call('DELETE', 'products/testproject/images/1')
        assert(not os.path.exists(url))
        open(url, 'w').write('data')

    def testDeleteImageFiles(self):
        class Subscriber(object):
            imageIds = []
            def notify_ImageRemoved(slf, event, imageId, imageName, imageType):
                slf.imageIds.append((imageId, imageName, imageType))
        client = self.getRestClient(username='adminuser',
            subscribers = [Subscriber()])
        # image 1 is not published yet
        db = self.openRestDatabase()
        url, = db.cursor().execute('''SELECT url from BuildFiles
                                      JOIN BuildFilesUrlsMap USING (fileId)
                                      JOIN FilesUrls USING(urlId)
                                      WHERE buildId=?
                                   ''', 1).fetchone()
        assert(os.path.exists(url))
        client.call('DELETE', 'products/testproject/images/1/files')
        assert(not os.path.exists(url))
        # FIXME - changes the actual original version bc
        # we store absolute references.  Lame.
        open(url, 'w').write('data')
        # Make sure the subscriber's method got called
        self.failUnlessEqual(Subscriber.imageIds, [('1', None, 1)])

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
  </release>
</releases>
"""
        for pat in [ "timeCreated", "timeModified", "timePublished" ]:
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
        <baseFileName>imagefile_1.iso</baseFileName>
        <url urlType="0">http://localhost:8000/downloadImage?fileId=1&amp;urlType=0</url>
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
        <baseFileName>imagefile_2.iso</baseFileName>
        <url urlType="0">http://localhost:8000/downloadImage?fileId=2&amp;urlType=0</url>
      </file>
    </files>
  </image>
</images>
"""

        self.assertBlobEquals(resp,
            exp % dict(server = 'localhost', port = '8000'))

    def _setOutputToken(self, buildId, token='abcdef'):
        db = self.openRestDatabase()
        cu = db.db.transaction()
        cu.execute("DELETE FROM BuildData WHERE buildId = ? AND name = 'outputToken'", buildId)
        cu.execute("""
            INSERT INTO BuildData ( buildId, name, value, dataType )
            VALUES ( ?, 'outputToken', ?, 0 )
            """, buildId, token)
        db.commit()
        return token

    def testBuildLog(self):
        client = self.getRestClient(username='adminuser')
        token = self._setOutputToken(1)

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        data = 'some\nlogging\nstuff\n'

        resp = client.call('POST', 'products/testproject/images/1/buildLog',
                data, headers=headers)[1]
        self.failUnlessEqual(resp.status, 204)
        self.failUnlessEqual(resp.content, '')

        resp = client.call('POST', 'products/testproject/images/1/buildLog',
                data, headers=headers)[1]
        self.failUnlessEqual(resp.status, 204)
        self.failUnlessEqual(resp.content, '')

        resp = client.call('GET', 'products/testproject/images/1/buildLog')[1]
        self.failUnlessEqual(resp.status, 200)
        self.failUnlessEqual(open(resp.path).read(), data + data)

        headers['x-rbuilder-outputtoken'] = 'dsfargeg'
        self.assertRaises(BuildNotFound, client.call, 'POST',
                'products/testproject/images/1/buildLog', data,
                headers=headers)

        del headers['x-rbuilder-outputtoken']
        resp = client.call('POST', 'products/testproject/images/1/buildLog',
                data, headers=headers)[1]
        self.failUnlessEqual(resp.status, 403)

    def testSetFilesForImage(self):
        client = self.getRestClient(username='adminuser')
        token = self._setOutputToken(1)

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        data = """\
<files>
  <file title="title1" size="1231" sha1="1231" baseFileName="aaa1" />
  <file title="title2" size="1232" sha1="1232" baseFileName="aaa2" />
</files>
"""
        resp = client.call('PUT', 'products/testproject/images/1/files',
                data, headers=headers)[1]

        exp = [
            ('title1', 1231, '1231', 'aaa1'),
            ('title2', 1232, '1232', 'aaa2'),
        ]
        self.failUnlessEqual(
            [ (x.title, x.size, x.sha1, x.baseFileName) for x in resp.files ],
            exp)


    class MockKey(object):
        class MockPolicy(object):
            class MockACL(object):
                def add_user_grant(self, permission, user_id):
                    pass

            def __init__(self):
                self.acl = self.MockACL()

        def set_contents_from_file(self, fp, cb = None, policy = None):
            if cb:
                cb(10, 16)

        def get_acl(self):
            return self.MockPolicy()

        def set_acl(self, acl):
            pass

    class MockBucket(object):
        def __init__(self):
            pass

        def new_key(self, name):
            return self.MockKey()

        def get_key(self, name):
            return self.MockKey()
    MockBucket.MockKey = MockKey

    def testSetImageStatusAMI(self):
        # Mock uploadBundle
        from mint import ec2
        self.mock(ec2.S3Wrapper, 'createBucket',
            lambda *args, **kwargs: self.MockBucket())
        self.mock(ec2.EC2Wrapper, 'registerAMI',
            lambda slf, bucketName, manifestName, *args, **kwargs:
                ('ami-01234', '%s/%s' % (bucketName, manifestName)))

        # Specifically test AMI uploads here
        client = self.getRestClient(username='adminuser')
        db = self.openRestDatabase()
        token = self._setOutputToken(1)

        # Build 1 becomes AMI
        db.cursor().execute("UPDATE Builds SET buildType = ? WHERE buildId = ?",
            buildtypes.AMI, 1)

        # Need to configure EC2
        targetId = db.db.targets.addTarget('ec2', 'aws')
        targetData = dict(ec2AccountId = '1234567890',
            ec2PublicKey = 'ec2PublicKey',
            ec2PrivateKey = 'ec2PrivateKey',
            ec2S3Bucket = 's3Bucket',
        )
        db.db.targetData.addTargetData(targetId, targetData)
        db.commit()

        # Create a tarball with stuff in it
        file(os.path.join(self.workDir, "file.manifest.xml"), "w").write(
            "<manifest />")
        for i in range(3):
            file(os.path.join(self.workDir, "file-%d" % i), "w").write(
                "Contents for file %d\n" % i)
        destFile = os.path.join(self.mintCfg.imagesPath, "testproject", "1",
            "ami-bundle.tar.gz")
        cmd = ["tar", "zcf", destFile,
            "-C", self.workDir,
            "file-0", "file-1", "file-2", "file.manifest.xml",
            ]
        retcode = subprocess.call(cmd)
        self.failUnlessEqual(retcode, 0)

        sha1sum = digestlib.sha1(file(destFile).read()).hexdigest()
        fileSize = os.stat(destFile).st_size

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        data = """\
<files>
  <file title="title1" size="%d" sha1="%s" baseFileName="%s" />
</files>
""" % (fileSize, sha1sum, destFile)
        resp = client.call('PUT', 'products/testproject/images/1/files',
                data, headers=headers)[1]

        # Update status
        data = """\
<imageStatus code="%d" message="%s" />
""" % (jobstatus.FINISHED, jobstatus.statusNames[jobstatus.FINISHED])
        resp = client.call('PUT', 'products/testproject/images/1/status',
                data, headers=headers)[1]

        # Now fetch the image
        resp = client.call('GET', 'products/testproject/images/1',
                data, headers=headers)[1]

        self.failUnlessEqual(resp.amiId, 'ami-01234')

testsetup.main()
