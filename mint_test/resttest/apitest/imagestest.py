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

from conary.lib import digestlib, util
from mint import buildtypes
from mint import jobstatus
from mint import notices_store
from mint.rest.errors import BuildNotFound, PermissionDeniedError
from mint_test import mint_rephelp
import restbase

class ImagesTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupReleases()

    def setUpNotices(self):
        class Counter(object):
            counter = 0
            def _generateString(slf, length):
                slf.__class__.counter += 1
                return str(slf.counter)
        # Predictable IDs
        self.counter = counter = Counter()
        self.mock(notices_store.DiskStorage, '_generateString',
                  counter._generateString)

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

    def testCreateImage(self):
        hostname = "createdproject"
        productVersion = "10"
        db = self.openRestDatabase()
        client = self.getRestClient(username='adminuser', db=db)

        # Create the project and the project version
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct(hostname, owners=['admin'], db=db)
        self.createProductVersion(db, hostname, productVersion)

        imageXml = """\
<image>
  <architecture>x86</architecture>
  <name>ginkgo-Raw Filesystem (x86)</name>
  <baseFileName>ginkgo-1-x86_64</baseFileName>
  <troveName>blabbedy</troveName>
  <version href="%(productVersion)s"/>
  <stage><href>Development</href></stage>
  <imageType>vmwareEsxImage</imageType>
  <troveFlavor /> <!-- explicitly set it to empty string -->
  <troveVersion /> <!-- explicitly set it to empty string -->
  <buildCount /> <!-- explicitly set it to empty string -->
  <files>
    <file>
      <title>My super-duper file</title>
      <size>123</size>
      <sha1>123</sha1>
      <fileName>ginkgo-1-x86.fs.tar.gz</fileName>
      <url urlType="0">http://reinhold.rdu.rpath.com/~misa/ginkgo-1-x86-ovf.tar.gz</url>
    </file>
  </files>
  <metadata>
    <billingCode>sdfg</billingCode>
    <cost>sdfg</cost>
    <deptCode />
    <owner>sdfg</owner>
  </metadata>
</image>""" % dict(productVersion=productVersion)


        from mint.image_gen.upload import client as rclient
        class MockRClient(rclient.UploadClient):
            calls = []
            def __init__(self, *args, **kwargs):
                pass
            def downloadImages(slf, *args, **kwargs):
                slf.calls.append((args, kwargs))
                return 'uuid', 'job'

        def mockGetUploaderClient():
            return MockRClient()
        self.mock(db.imageMgr, "getUploaderClient", mockGetUploaderClient)

        req, img = client.call('POST', 'products/%s/images' % hostname, imageXml)
        self.failUnlessEqual(img.stage, "Development")
        self.failUnlessEqual(img.version, productVersion)
        self.failUnlessEqual(str(img.troveVersion), '/local@local:COOK/1-1-1')
        self.failUnlessEqual(str(img.troveFlavor), 'is: x86')

        self.failUnlessEqual(len(MockRClient.calls), 1)
        rcargs, rckwargs = MockRClient.calls[0]
        self.failUnlessEqual(rckwargs, {})

        image, baseUrl = rcargs
        self.failUnlessEqual(image.architecture, 'x86')
        self.failUnlessEqual(image.metadata['cost'], 'sdfg')

        self.failUnlessEqual(baseUrl.path,
            '/api/products/createdproject/images/4/')

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
    <imageCount>2</imageCount>
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
  <file title="title1" size="1231" sha1="1231" fileName="aaa1" />
  <file title="title2" size="1232" sha1="1232" fileName="aaa2" />
</files>
"""
        resp = client.call('PUT', 'products/testproject/images/1/files',
                data, headers=headers)[1]

        exp = [
            ('title1', 1231, '1231', 'aaa1'),
            ('title2', 1232, '1232', 'aaa2'),
        ]
        self.failUnlessEqual(
            [ (x.title, x.size, x.sha1, x.fileName)
                for x in resp.files ],
            exp)

    def testSetFilesRecomputeTargetDeployableImages(self):
        userName = 'JeanValjean'
        self.createUser(userName, admin = False)

        targetType = 'vmware'
        targetName = 'mytarget'
        targetData = dict(alias='my target alias')

        db = self.openMintDatabase(createRepos=False)
        tmgr = db.targetMgr
        tmgr.addTarget(targetType, targetName, targetData)

        credentials = dict(username = 'aaa', password='bbb')
        # No need to run the target import script
        tmgr.auth.isAdmin = False
        tmgr.setTargetCredentialsForUser(targetType, targetName, userName,
            credentials)
        db.commit()

        client = self.getRestClient(username='adminuser')
        token = self._setOutputToken(3)

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        from rmake3.lib import uuid
        sha1 = str(uuid.uuid4())
        data = """\
<files>
  <file title="title1" size="10" sha1="%s" fileName="imagefile_1.ova" />
</files>
""" % sha1
        resp = client.call('PUT', 'products/testproject/images/3/files',
                data, headers=headers)[1]

        exp = [ ('title1', 10, sha1, 'imagefile_1.ova') ]
        self.failUnlessEqual(
            [ (x.title, x.size, x.sha1, x.fileName)
                for x in resp.files ],
            exp)

        # Make sure we have something in the db
        cu = db.cursor()
        cu.execute("""
            SELECT t.name
              FROM targets AS t
              JOIN target_deployable_image AS tdi ON (t.targetid = tdi.target_id)
              JOIN buildfiles AS bf ON (tdi.file_id = bf.fileid)
             WHERE bf.buildid = ?
               AND bf.sha1 = ?""", 3, sha1)
        row = cu.fetchone()
        self.failUnlessEqual(row[0], 'mytarget')

    def testSetFilesForImagePushToRepo(self):
        client = self.getRestClient(username='adminuser')
        token = self._setOutputToken(1)

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        data = """\
<files>
  <file title="title1" size="10" sha1="d68146c2e5fe437a9f2c7a8affb88271cff46182" fileName="imagefile_1.iso" />
  <metadata>
    <owner>JeanValjean</owner>
  </metadata>
</files>
"""
        resp = client.call('PUT', 'products/testproject/images/1/files',
                data, headers=headers)[1]

        exp = [ ('title1', 10,
            'd68146c2e5fe437a9f2c7a8affb88271cff46182', 'imagefile_1.iso')]
        self.failUnlessEqual(
            [ (x.title, x.size, x.sha1, x.fileName)
                for x in resp.files ],
            exp)
        fqdn = 'testproject.rpath.local2'
        db = self.openRestDatabase()
        cli = db.productMgr.reposMgr.getConaryClientForProduct(fqdn,
            admin=True)
        repos = cli.getRepos()
        from conary import versions
        label = versions.Label('%s@yournamespace:testproject-1.0-devel' %
            fqdn)
        trvTup = repos.findTrove(label, ("image-testproject:source", None, None))[0]
        self.failUnlessEqual(str(trvTup[1]),
            '/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-1')
        trv = repos.getTrove(*trvTup)
        self.failUnlessEqual(dict(trv.troveInfo.metadata.flatten()[0].keyValue),
            dict(owner="JeanValjean"))

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

    def testSetImageStatus(self):
        self.setUpNotices()

        username = 'adminuser'
        client = self.getRestClient(username=username)
        db = self.openRestDatabase()
        token = self._setOutputToken(1)

        # Build 1 becomes vmware
        db.cursor().execute("UPDATE Builds SET buildType = ? WHERE buildId = ?",
            buildtypes.VMWARE_IMAGE, 1)
        db.commit()

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }
        fileList = [
            ("file1.txt", "content file 1"),
            ("file2.txt", "content file 2"),
        ]
        imagesPath = os.path.join(self.mintCfg.imagesPath, "testproject", "1")
        util.mkdirChain(imagesPath)
        dataTempl = """<file title="title1" size="%d" sha1="%s" fileName="%s" />"""
        url = 'products/testproject/images/1/files'
        fileXmlData = []
        for fileName, fileContents in fileList:
            destFile = os.path.join(imagesPath, fileName)
            file(destFile, "w").write(fileContents)
            sha1sum = digestlib.sha1(fileContents).hexdigest()
            fileSize = len(fileContents)
            fileXmlData.append(dataTempl % (fileSize, sha1sum, destFile))
        xml = "<files>%s</files>" % '\n'.join(fileXmlData)
        resp = client.call('PUT', url, xml, headers = headers)[1]
        from mint.rest.api.models.images import ImageFileList
        self.failUnlessEqual(resp.__class__, ImageFileList)

        # Update status
        data = """\
<imageStatus code="%d" message="%s" />
""" % (jobstatus.FINISHED, jobstatus.statusNames[jobstatus.FINISHED])
        url = 'products/testproject/images/1/status'
        resp = client.call('PUT', url, data, headers=headers)[1]

        # Now fetch the image
        resp = client.call('GET', 'products/testproject/images/1',
                data, headers=headers)[1]

        self.failUnlessEqual(
            sorted(x.fileName for x in resp.files.files),
            ['file1.txt', 'file2.txt'])
        self.failUnlessEqual(resp.baseFileName, 'testproject-1-')

        store = notices_store.createStore(
            os.path.join(self.mintCfg.dataPath, 'notices'), username)
        notice = [ x for x in store.enumerateStoreUser('builder') ][0]
        contents = notice.content
        contents = re.sub('Created On:&lt;/b&gt; .*</desc',
            'Created On:&lt;/b&gt; @CREATED-ON@</desc', contents)
        contents = re.sub('<date>.*</date>',
            '<date>@DATE@</date>', contents)
        self.failUnlessEqual(contents, """\
<item><title>Image `Image 1' built (testproject version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; testproject&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; VMware(R) Workstation/Fusion Virtual Appliance&lt;br/&gt;&lt;b&gt;File Name:&lt;/b&gt; file1.txt&lt;br/&gt;&lt;b&gt;Download URL:&lt;/b&gt; &lt;a href="https://test.rpath.local/downloadImage?fileId=4"&gt;https://test.rpath.local/downloadImage?fileId=4&lt;/a&gt;&lt;br/&gt;&lt;b&gt;File Name:&lt;/b&gt; file2.txt&lt;br/&gt;&lt;b&gt;Download URL:&lt;/b&gt; &lt;a href="https://test.rpath.local/downloadImage?fileId=5"&gt;https://test.rpath.local/downloadImage?fileId=5&lt;/a&gt;&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @CREATED-ON@</description><date>@DATE@</date><category>success</category><guid>/api/users/adminuser/notices/contexts/builder/1</guid></item>""")


    def testSetImageStatusAMI(self):
        self.setUpNotices()
        # Mock uploadBundle
        from mint import ec2
        self.mock(ec2.S3Wrapper, 'createBucket',
            lambda *args, **kwargs: self.MockBucket())

        statusFile = os.path.join(self.workDir, "registerAMI.status")
        def mockedRegisterAMI(slf, bucketName, manifestName, *args, **kwargs):
            f = file(statusFile, "a")
            f.write("ec2LaunchUsers: %s\n" % kwargs.get('ec2LaunchUsers'))
            f.write("ec2LaunchGroups: %s\n" % kwargs.get('ec2LaunchGroups'))
            f.close()
            return ('ami-01234', '%s/%s' % (bucketName, manifestName))
        self.mock(ec2.EC2Wrapper, 'registerAMI', mockedRegisterAMI)

        username = 'adminuser'
        # Specifically test AMI uploads here
        client = self.getRestClient(username=username)
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
        users = [ 'testUser1', 'testUser2' ]
        for i, uname in enumerate(users):
            params = dict(username = uname,
                password = "password",
                email = "%s@rpath.com" % uname,
                fullName = "",
                displayEmail = "",
                blurb = "")
            userId = db.userMgr.createUser(**params)
            db.setMemberLevel(self.productShortName, uname, 'user')
            userData = [ ('accountId', "%010d" % i),
                         ('publicAccessKeyId', "Public Key Id %d" % i),
                         ('secretAccessKey', "Secret Key %d" % i), ]
            db.targetMgr.setTargetCredentialsForUserId(
                db.db.EC2TargetType, db.db.EC2TargetName, userId, dict(userData))

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
  <file title="title1" size="%d" sha1="%s" fileName="%s" />
</files>
""" % (fileSize, sha1sum, destFile)
        resp = client.call('PUT', 'products/testproject/images/1/files',
                data, headers=headers)[1]
        from mint.rest.api.models.images import ImageFileList
        self.failUnlessEqual(resp.__class__, ImageFileList)

        # Update status
        data = """\
<imageStatus code="%d" message="%s" />
""" % (jobstatus.FINISHED, jobstatus.statusNames[jobstatus.FINISHED])
        resp = client.call('PUT', 'products/testproject/images/1/status',
                data, headers=headers)[1]

        # Check that we passed in additional launch users
        rows = [ x.strip() for x in file(statusFile) ]
        self.failUnlessEqual(rows, [
            "ec2LaunchUsers: ['0000000000', '0000000001']",
            "ec2LaunchGroups: []",
        ])

        # Now fetch the image
        resp = client.call('GET', 'products/testproject/images/1',
                data, headers=headers)[1]

        self.failUnlessEqual(resp.amiId, 'ami-01234')

        store = notices_store.createStore(
            os.path.join(self.mintCfg.dataPath, 'notices'), username)
        notice = [ x for x in store.enumerateStoreUser('builder') ][0]
        contents = notice.content
        contents = re.sub('Created On:&lt;/b&gt; .*</desc',
            'Created On:&lt;/b&gt; @CREATED-ON@</desc', contents)
        contents = re.sub('<date>.*</date>',
            '<date>@DATE@</date>', contents)
        self.failUnlessEqual(contents, """\
<item><title>Image `Image 1' built (testproject version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; testproject&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; Amazon Machine Image (EC2)&lt;br/&gt;&lt;b&gt;AMI:&lt;/b&gt; ami-01234&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @CREATED-ON@</description><date>@DATE@</date><category>success</category><guid>/api/users/adminuser/notices/contexts/builder/1</guid></item>""")

    def testSetImageStatusFailed(self):
        self.setUpNotices()

        username = 'adminuser'
        client = self.getRestClient(username=username)
        db = self.openRestDatabase()
        token = self._setOutputToken(1)

        # Build 1 becomes vmware
        db.cursor().execute("UPDATE Builds SET buildType = ? WHERE buildId = ?",
            buildtypes.VMWARE_IMAGE, 1)
        db.commit()

        headers = {
                'content-type': 'text/plain',
                'x-rbuilder-outputtoken': token,
                }

        # Update status
        data = """\
<imageStatus code="%d" message="%s" />
""" % (jobstatus.FAILED, jobstatus.statusNames[jobstatus.FAILED])
        url = 'products/testproject/images/1/status'
        resp = client.call('PUT', url, data, headers=headers)[1]

        store = notices_store.createStore(
            os.path.join(self.mintCfg.dataPath, 'notices'), username)
        notice = [ x for x in store.enumerateStoreUser('builder') ][0]
        contents = notice.content
        contents = re.sub('Created On:&lt;/b&gt; .*</desc',
            'Created On:&lt;/b&gt; @CREATED-ON@</desc', contents)
        contents = re.sub('<date>.*</date>',
            '<date>@DATE@</date>', contents)
        self.failUnlessEqual(contents, """\
<item><title>Image `Image 1' failed to build (testproject version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; testproject&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; VMware(R) Workstation/Fusion Virtual Appliance&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @CREATED-ON@</description><date>@DATE@</date><category>error</category><guid>/api/users/adminuser/notices/contexts/builder/1</guid></item>""")

testsetup.main()
