#!/usr/bin/python

import StringIO

import testsetup
from mint_test import mint_rephelp

from mint.rest.db import awshandler

class AwsHandlerest(mint_rephelp.MintDatabaseHelper):

    def _mockRequest(self, **kwargs):
        from boto.ec2.connection import EC2Connection
        from boto.s3.connection import S3Connection

        s3kwargs = kwargs.pop('s3kwargs', {})

        reqobj = MockedRequest()
        reqobj.data = MockedRequest.data.copy()
        reqobj.data.update(kwargs)
        self.mock(EC2Connection, 'make_request',
                  reqobj.mockedMakeRequest)
        self.mock(EC2Connection, 'proxy_ssl', mockedProxySsl)

        reqobj = MockedS3Request()
        reqobj.data = MockedS3Request.data.copy()
        reqobj.data.update(s3kwargs)
        self.mock(S3Connection, 'make_request',
                  reqobj.mockedMakeRequest)
        self.mock(S3Connection, 'proxy_ssl', mockedProxySsl)

    def testImageRemoved(self):
        self._mockRequest()
        class Database(object):
            db = self.openRestDatabase()
            db = db.db
        targetData = dict(ec2AccountId = '42',
            ec2PublicKey = 'publicKey',
            ec2PrivateKey = 'privateKey')
        targetId = Database.db.targets.addTarget('ec2', 'aws')
        Database.db.targetData.addTargetData(targetId, targetData)
        handler = awshandler.AWSHandler(self.mintCfg, Database(), None)
        event = 'ImageRemoved'
        handler.notify_ImageRemoved(event, imageId = '1', imageName = 'ami-Foo',
            imageType = awshandler.buildtypes.AMI)

        # Make sure all the removals got called
        from boto.s3.connection import S3Connection
        reqobj = S3Connection.make_request.im_self
        self.failUnlessEqual(reqobj.called, [
            ('GET', 'rbuilder-online', None),
            ('GET', 'rbuilder-online', 'flatpress-2-x86_17185.img.manifest.xml'),
            ('DELETE', 'rbuilder-online', 'part00'),
            ('DELETE', 'rbuilder-online', 'part01'),
            ('DELETE', 'rbuilder-online', 'flatpress-2-x86_17185.img.manifest.xml')])

        from boto.ec2.connection import EC2Connection
        reqobj = EC2Connection.make_request.im_self
        self.failUnlessEqual(reqobj.called, [
            ('DescribeImages', {'ImageId.1': 'ami-Foo'}, '/'),
            ('DeregisterImage', {'ImageId': 'ami-Foo'}, '/')
        ])

        # Reset caller list
        reqobj.called = []
        # aws handler notification should only be called for AMIs
        handler.notify_ImageRemoved(event, imageId = '1', imageName = None,
            imageType = awshandler.buildtypes.INSTALLABLE_ISO)
        self.failUnlessEqual(reqobj.called, [])

    def testImageMissing(self):
        """
        Test that a missing AMI does not prevent the image deletion from
        succeeding. (RBL-4838)
        """
        self._mockRequest()
        class Database(object):
            db = self.openRestDatabase()
            db = db.db
        targetData = dict(ec2AccountId = '42',
            ec2PublicKey = 'publicKey',
            ec2PrivateKey = 'privateKey')
        targetId = Database.db.targets.addTarget('ec2', 'aws')
        Database.db.targetData.addTargetData(targetId, targetData)
        handler = awshandler.AWSHandler(self.mintCfg, Database(), None)
        handler.notify_ImageRemoved('ImageRemoved', imageId='3',
                imageName='ami-BAR', imageType=awshandler.buildtypes.AMI)

xml_DescribeImages1 = """\
<?xml version="1.0"?>
<DescribeImagesResponse xmlns="http://ec2.amazonaws.com/doc/2008-12-01/">
    <requestId>09610634-2a52-4b53-875a-fecc4d2356cb</requestId>
    <imagesSet>
        <item>
            <imageId>ami-fdc12594</imageId>
            <imageLocation>rbuilder-online/flatpress-2-x86_17185.img.manifest.xml</imageLocation>
            <imageState>available</imageState>
            <imageOwnerId>099034111737</imageOwnerId>
            <isPublic>true</isPublic>
            <architecture>i386</architecture>
            <imageType>machine</imageType>
        </item>
    </imagesSet>
</DescribeImagesResponse>
"""

xml_DescribeImages2 = """\
<?xml version="1.0"?>
<DescribeImagesResponse xmlns="http://ec2.amazonaws.com/doc/2008-12-01/">
</DescribeImagesResponse>
"""

xml_DeregisterImage1 = """\
<?xml version="1.0"?>
<DeregisterImageResponse xmlns="http://ec2.amazonaws.com/doc/2008-12-01/">
</DeregisterImageResponse>
"""

xml_ListBucket1 = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>rbuilder-online</Name>
  <Prefix/>
  <Marker/>
  <MaxKeys>1000</MaxKeys>
  <IsTruncated>true</IsTruncated>
  <Contents>
    <Key>agathap-1-x86_17180.img.manifest.xml</Key>
    <LastModified>2008-09-11T15:35:42.000Z</LastModified>
    <ETag>"694ab46ba68bff2292c08aca944f0e97"</ETag>
    <Size>3454</Size>
    <StorageClass>STANDARD</StorageClass>
  </Contents>
</ListBucketResult>
"""

xml_manifest1 = """\
<?xml version="1.0"?>
<manifest>
  <version>3</version>
  <bundler>
    <name>ec2-ami-tools</name>
    <version>1.2</version>
    <release>7221</release>
  </bundler>
  <image>
    <name>bioinformatics-0.0.1-x86_15351.img</name>
    <user>099034111737</user>
    <digest algorithm="SHA1">4e6500b699bf71063f4e1b0b95815452e41e274d</digest>
    <size>2212962304</size>
    <bundled_size>334302128</bundled_size>
    <ec2_encrypted_key algorithm="AES-128-CBC">bb80bc8139b275439d6600c0e835259eafbbaac466148be638fedce6167615aca99f14f6c3a086e1e3a64f4ac5aa7ef644b6b2d10fe499a36c904882deecc196f10dc40874a8941386d18862f548eeedca5d70c363a48ac56b269839ff871411fc4b7bca783dac61539d142dc5ccdb77cbc82c2332aaa7292bb23a940ed71746</ec2_encrypted_key>
    <user_encrypted_key algorithm="AES-128-CBC">1d43d570f5773b32cf62c65a7f721503eeb62b3788ad018ccba573b1d249703139503878d4e7f8b5fe6db4aba1b1444f983f3c1c670b92fa129e5c7263776817d6ef3883a563172d6aae6a782ff6db5f23a0d363f9105f1dbbe4ecaa56bef8b8</user_encrypted_key>
    <ec2_encrypted_iv>5ebb99e1d53044dc7d34cfd396c7b4aa195a86c17685f538f2fe254bfea01c75fe3c8fa673f130c6c777752bafe259d83b7fc992dc062d52be099f430f2a507fdc1d9885c5d910681966ee3077b78a9026c7bc5a15cbecb444de7268d0edaa7e2620dcf0b70735d3f9b90437123c7645f3f18ef79dcdf8816d1935214652f793</ec2_encrypted_iv>
    <user_encrypted_iv>4339fadfe33581546afa55ab37425b854c8cbbeb7ff533dc96700886154c7e9cd0ae96d6302daa0a15ac58f1e973a46d845b51cda9aa9175d69761c4132acc7069f5f018c54c186ee3f78fbfc2b5d09d10a1fbad29ed1f9d4b08caaf4b05c310</user_encrypted_iv>
    <parts count="2">
      <part index="0">
        <filename>part00</filename>
        <digest algorithm="SHA1">f929d836dcb700665705210053f74458df3d9c81</digest>
      </part>
      <part index="1">
        <filename>part01</filename>
        <digest algorithm="SHA1">f929d836dcb700665705210053f74458df3d9c81</digest>
      </part>
    </parts>
  </image>
  <signature>51e67f28427715aa9ac6c3577e22524285856cf28665613e94823b225fd2675f9eba6d4ebd77264001c84a5cfa2502fc315d6b2467c3bd1a3b7708c952f171112328da85048922863d68c7ffe270e3095f359f5f92f819bdc29f7e4a0921d540</signature>
</manifest>
"""

class MockedRequest(object):
    data = {
            ('DescribeImages', (('ImageId.1', 'ami-Foo'),)): xml_DescribeImages1,
            ('DescribeImages', (('ImageId.1', 'ami-BAR'),)): xml_DescribeImages2,
            ('DeregisterImage', (('ImageId', 'ami-Foo'),)): xml_DeregisterImage1,
            }

    def _get_response(self, action, params, path, args, kwargs):
        key = (action, tuple(sorted(params.items())))
        if key not in self.data:
            raise Exception("Shouldn't have tried this method", key)
        data = self.data[key]
        if isinstance(data, tuple):
            status, data = data
        else:
            status = 200
        return status, data

    def mockedMakeRequest(self, action, params=None, path=None, *args, **kwargs):
        if not hasattr(self, 'called'):
            self.called = []
        self.called.append((action, params, path))
        status, data = self._get_response(action, params, path, args, kwargs)
        resp = MockedResponse(data)
        resp.status = status
        resp.reason = "Foo"
        return resp

class MockedS3Request(MockedRequest):
    data = dict(
        GET = {
                ('rbuilder-online', None) : xml_ListBucket1,
                ('rbuilder-online', 'flatpress-2-x86_17185.img.manifest.xml') : xml_manifest1,
         },
        DELETE = {
                ('rbuilder-online', 'part00') : (204, ''),
                ('rbuilder-online', 'part01') : (204, ''),
                ('rbuilder-online', 'flatpress-2-x86_17185.img.manifest.xml') : (204, ''),
        }
    )

    def _get_response(self, action, params, path, args, kwargs):
        if action not in self.data or (params, path) not in self.data[action]:
            raise Exception("Shouldn't have tried this method", action)
        data = self.data[action][(params, path)]
        if isinstance(data, tuple):
            status, data = data
        else:
            status = 200
        if status >= 300 and 'sender' in kwargs:
            # Pushing a file
            from boto.exception import S3ResponseError
            raise S3ResponseError(status, 'Foo', data)
        return status, data

class MockedResponse(object):
    "A response that returns canned data"
    def __init__(self, data):
        self.data = StringIO.StringIO(data)
        self.status = 200
        self.msg = {}

    def read(self, amt = None):
        return self.data.read(amt)
    def getheader(self, name, default=None):
        return default
    def close(self):
        pass

class MockedHttpConnection(object):
    def set_debuglevel(self, level):
        pass

def mockedProxySsl(slf):
    return MockedHttpConnection()

testsetup.main()
