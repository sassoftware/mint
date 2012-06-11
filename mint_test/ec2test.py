#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import time
from conary.lib import util

from testrunner import pathManager


import boto
import boto.s3
import boto.s3.key
from boto.exception import EC2ResponseError

from mint import config
from mint import ec2
from mint import mint_error

from mint.helperfuncs import toDatabaseTimestamp, fromDatabaseTimestamp

import fixtures
from testutils import mock

from mint import buildtypes
from mint import shimclient
from mint import userlevels
from mint.lib.data import RDT_STRING
from mint_rephelp import MINT_PROJECT_DOMAIN

FAKE_PUBLIC_KEY  = '123456789ABCDEFGHIJK'
FAKE_PRIVATE_KEY = '123456789ABCDEFGHIJK123456789ABCDEFGHIJK'

FAKE_PUBLIC_KEY2  = '987654321ABCDEFGHIJK'
FAKE_PRIVATE_KEY2 = '987654321ABCDEFGHIJK123456789ABCDEFGHIJK'

AWS_ERROR_XML_SINGLE = \
    '''<?xml version="1.0"?>\n
       <Response>
           <Errors>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>AWS was not able to validate the provided access credentials</Message>
               </Error>
           </Errors>
           <RequestID>2410d7ed-986c-4e86-a35b-68d4a4062024</RequestID>
       </Response>'''
       
AWS_ERROR_XML_MULTIPLE = \
    '''<?xml version="1.0"?>\n
       <Response>
           <Errors>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>AWS was not able to validate the provided access credentials</Message>
               </Error>
               <Error>
                   <Code>IQTooLow</Code>
                   <Message>You&apos;re an idiot, back off</Message>
               </Error>
           </Errors>
           <RequestID>3410d7ed-986c-4e86-a35b-68d4a4062024</RequestID>
       </Response>'''

AWS_ERROR_XML_DUP_MESSAGES = \
    '''<?xml version="1.0"?>\n
       <Response>
           <Errors>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>AWS was not able to validate the provided access credentials</Message>
               </Error>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>AWS was not able to validate the provided access credentials</Message>
               </Error>
           </Errors>
           <RequestID>3410d7ed-986c-4e86-a35b-68d4a4062024</RequestID>
       </Response>'''
       
AWS_ERROR_XML_DUP_CODES = \
    '''<?xml version="1.0"?>\n
       <Response>
           <Errors>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>Some message</Message>
               </Error>
               <Error>
                   <Code>AuthFailure</Code>
                   <Message>Different message</Message>
               </Error>
           </Errors>
           <RequestID>3410d7ed-986c-4e86-a35b-68d4a4062024</RequestID>
       </Response>'''

AWS_ERROR_XML_UNKNOWN = \
    '''<?xml version="1.0"?>\n
       <Response>
           <Errors>
               <Error>
               </Error>
           </Errors>
           <RequestID>4410d7ed-986c-4e86-a35b-68d4a4062024</RequestID>
       </Response>'''

AMI_MANIFEST_FILE_XML = \
    """<?xml version='1.0'?>
        <manifest>
            <version>2007-10-10</version>
            <bundler>
                <name>ec2-ami-tools</name>
                <version>1.3</version>
                <release>15586</release>
            </bundler>
            <machine_configuration>
                <architecture>i386</architecture>
            </machine_configuration>
            <image>
                <name>teletran1-1-x86_18.img</name>
                <user>941766519978</user>
                <type>machine</type>
                <digest algorithm='SHA1'>283de2b0f2dade4f1322be9ea56f4dc8f1beda15</digest>
                <size>1205432320</size>
                <bundled_size>89887632</bundled_size>
                <ec2_encrypted_key algorithm='AES-128-CBC'>encrypted-key</ec2_encrypted_key>
                <user_encrypted_key algorithm='AES-128-CBC'>user-encrypted-key</user_encrypted_key>
                <ec2_encrypted_iv>ec2-encrypted-iv</ec2_encrypted_iv>
                <user_encrypted_iv>user-encrypted-iv</user_encrypted_iv>
                <parts count='9'>
                    <part index='0'>
                        <filename>teletran1-1-x86_18.img.part.0</filename>
                        <digest algorithm='SHA1'>471c07d6c19a5aca4450474b10422645df8b2c0f</digest>
                    </part>
                    <part index='1'>
                        <filename>teletran1-1-x86_18.img.part.1</filename>
                        <digest algorithm='SHA1'>2b2f48f7f37c82d5dc92c0430206372481593add</digest>
                    </part>
                    <part index='2'>
                        <filename>teletran1-1-x86_18.img.part.2</filename>
                        <digest algorithm='SHA1'>f34334c8b0674877b324a932c72a3851995fcaca</digest>
                    </part>
                    <part index='3'>
                        <filename>teletran1-1-x86_18.img.part.3</filename>
                        <digest algorithm='SHA1'>a81c93f9e07096e411f54b4239a99360da43f2dd</digest>
                    </part>
                </parts>
            </image>
            <signature>signature</signature>
    </manifest>"""

deletedKeys = []

class FakeS3Connection(object):

    def __init__(self, (accountId, accessKey, secretKey), proxyArgs):
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.proxyArgs = proxyArgs

    def get_bucket(self, bucketName):
        return FakeBucket(bucketName)

class FakeBucket(object):
    
    def __init__(self, name=''):
        self.name = name

    def delete_key(self, key):
        global deletedKeys
        deletedKeys.append(key)

class FakeKey(object):

    def __init__(self, bucket=FakeBucket(), name=''):
        self.bucket = bucket
        self.name = name

    def get_contents_as_string(self):
        return AMI_MANIFEST_FILE_XML

class FakeEC2Connection(object):

    def __init__(self, (accountId, accessKey, secretKey), proxyArgs):
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.proxyArgs = proxyArgs

    def _checkKeys(self):
        if self.accessKey != FAKE_PUBLIC_KEY or \
                self.secretKey != FAKE_PRIVATE_KEY:
                    # XXX I don't know what to put here but it had no args
            raise EC2ResponseError(401, '', AWS_ERROR_XML_SINGLE)

    def run_instances(self, amiId, user_data=None, addressing_type = 'public'):
        self._checkKeys()
        return FakeEC2Reservation(amiId)

    def get_all_instances(self, instance_ids=[]):
        self._checkKeys()
        return [ FakeEC2ResultSet([ FakeEC2Instance('ami-00000000', instance_ids[0]) ]) ]

    def terminate_instances(self, instance_ids=[]):
        return
    
    def get_all_key_pairs(self, keynames=None):
        if not keynames:
            return KEY_PAIRS
        
        pairs = []
        for name in keynames:
            for keyPair in KEY_PAIRS:
                if keyPair.name == name:
                    pairs.append(keyPair)
            
        return pairs      
    
    def get_key_pair(self, keyname):
        return self.get_all_key_pairs([keyname])

    def reset_image_attribute(self, amiId, attribute):
        return True

    def modify_image_attribute(self, *args, **kw):
        return True

    def deregister_image(self, amiId):
        return True

    def get_all_images(self, image_ids=['ami-id']):
        image = FakeEC2Instance(image_ids[0], 'instance-id')
        return [image]

class FakeEC2KeyPair(object):
    __slots__ = ( 'name', 'fingerprint', 'material')
    
    def __init__(self, name, fingerprint, material):
        self.name = name
        self.fingerprint = fingerprint
        self.material = material
        
KEY_PAIRS = [FakeEC2KeyPair(
                 'key1', 
                 '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f',
                 'some RSA private key'),
             FakeEC2KeyPair(
                 'key2', 
                 '2f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f',
                 'another RSA private key')]     

class FakeEC2Reservation(object):

    __slots__ = ( 'instances', )

    def __init__(self, amiId):
        self.instances = [ FakeEC2Instance(amiId, 'i-00000001') ]

class FakeEC2Instance(object):

    __slots__ = ('amiId', 'id', 'state', 'dns_name', 'location')

    def __init__(self, amiId, instanceId, state='pending', dns_name=''):
        self.id = instanceId
        self.state = state
        self.dns_name = dns_name
        self.amiId = amiId
        self.location = 'bucket-name/manifest-file-name.xml'

class FakeEC2ResultSet(object):

    __slots__ = ( 'instances', )

    def __init__(self, instances):
        self.instances = instances
        pass

def getFakeEC2Connection(accessKey, secretKey, **kwargs):
    return FakeEC2Connection((None, accessKey, secretKey), kwargs)

def getFakeS3Connection(accessKey, secretKey, **kwargs):
    return FakeS3Connection((None, accessKey, secretKey), kwargs)

class BaseEC2Test(fixtures.FixturedUnitTest):
    def setupEC2Credentials(self):
        """
        set up rBuilder to have EC2 credentials.
        """
        amiData = {
                'ec2PublicKey' : '123456789ABCDEFGHIJK',
                'ec2PrivateKey' : '123456789ABCDEFGHIJK123456789ABCDEFGHIJK',
                'ec2AccountId' : '000000000000',
                'ec2S3Bucket' : 'extracrispychicken',
                'ec2LaunchUsers' : ["000000001111", "000000002222"],
                'ec2LaunchGroups' : ["group1", "group2"],
                'ec2Certificate': open(os.path.join( \
                        pathManager.getPath('MINT_ARCHIVE_PATH'), 'ec2.pem')).read(),
                'ec2CertificateKey': open(os.path.join( \
                        pathManager.getPath('MINT_ARCHIVE_PATH'), 'ec2.key')).read()
                }
        adminClient = shimclient.ShimMintClient(self.cfg, ("admin", "adminpass"))
        adminClient.addTarget('ec2', 'aws', amiData)


class Ec2Test(BaseEC2Test):

    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.old_connect_ec2 = boto.connect_ec2
        boto.connect_ec2 = getFakeEC2Connection
        self.old_connect_s3 = boto.connect_s3
        boto.connect_s3 = getFakeS3Connection
        self.oldKey = boto.s3.key.Key
        boto.s3.key.Key = FakeKey
        
        global deletedKeys
        deletedKeys = []

    def tearDown(self):
        fixtures.FixturedUnitTest.tearDown(self)
        boto.connect_ec2 = self.old_connect_ec2
        boto.connect_s3 = self.old_connect_s3
        boto.s3.key.Key = self.oldKey

    def _buildEC2AuthToken(self, client):
        """
        Convenience function to build the EC2 auth token from the config data
        """
        amiData = client.getTargetData('ec2', 'aws')
        at = ()
        if amiData:
            # make sure all the values are set
            if not (amiData.get('ec2AccountId') and \
                    amiData.get('ec2PublicKey') and\
                    amiData.get('ec2PrivateKey')):
                raise EC2NotConfigured()
            at = (amiData.get('ec2AccountId'),
                    amiData.get('ec2PublicKey'),
                    amiData.get('ec2PrivateKey'))

        if not at:
            raise EC2NotConfigured()

        return at

    def testGetIncompleteEC2Credentials(self):
        self.failUnlessRaises(mint_error.EC2Exception,
                ec2.EC2Wrapper, ('id', '', 'secretKey'), None)
        
    @fixtures.fixture("EC2")
    def testEC2CredentialsForUser(self, db, data):
        """
        This tests getting, setting, and removing credentials
        """
        client = self.getClient("admin")
        
        self.addAllLaunchPermsCalled = False
        self.removeAllLaunchPermsCalled = False

        def addAllEC2LaunchPermissions(userId, awsAccountNumber):
            self.addAllLaunchPermsCalled = True

        def removeAllEC2LaunchPermissions(userId, awsAccountNumber):
            self.removeAllLaunchPermsCalled = True

        def validateEC2Credentials(authToken):
            return True
                
        oldValidateAMICredentials = client.server._server.validateEC2Credentials
        client.server._server.validateEC2Credentials = validateEC2Credentials
        oldAddAllEC2LaunchPermissions = \
            client.server._server.amiPerms._addAMIPermissionsForAccount
        client.server._server.amiPerms._addAMIPermissionsForAccount = \
            addAllEC2LaunchPermissions
        oldRemoveAllEC2LaunchPermissions = \
            client.server._server.amiPerms._removeAMIPermissionsForAccount
        client.server._server.amiPerms._removeAMIPermissionsForAccount = \
            removeAllEC2LaunchPermissions
        
        try:
            # add some credentials and make sure they are saved
            client.setEC2CredentialsForUser(data['adminId'], 'id', 'publicKey',
                                            'secretKey', False)
            self.assertTrue(self.addAllLaunchPermsCalled)
            self.assertFalse(self.removeAllLaunchPermsCalled)
            ec2cred = client.getEC2CredentialsForUser(data['adminId'])
            self.assertTrue(ec2cred == {'awsPublicAccessKeyId': 'publicKey', 
                                        'awsSecretAccessKey': 'secretKey', 
                                        'awsAccountNumber': 'id'})
            
            # now replace the credentials and make sure they are replaced
            self.addAllLaunchPermsCalled = False
            self.removeAllLaunchPermsCalled = False
            client.setEC2CredentialsForUser(data['adminId'], 'newId',
                    'newPublicKey', 'newSecretKey', False)
            self.assertTrue(self.removeAllLaunchPermsCalled)
            self.assertTrue(self.addAllLaunchPermsCalled)
            ec2cred = client.getEC2CredentialsForUser(data['adminId'])
            self.assertTrue(ec2cred == {'awsPublicAccessKeyId': 'newPublicKey', 
                                        'awsSecretAccessKey': 'newSecretKey', 
                                        'awsAccountNumber': 'newId'})

            # now remove the credentials and make sure they are gone
            self.addAllLaunchPermsCalled = False
            self.removeAllLaunchPermsCalled = False
            client.removeEC2CredentialsForUser(data['adminId'])
            self.assertTrue(self.removeAllLaunchPermsCalled)
            self.assertFalse(self.addAllLaunchPermsCalled)
            ec2cred = client.getEC2CredentialsForUser(data['adminId'])
            self.assertTrue(ec2cred == {'awsPublicAccessKeyId': '', 
                                        'awsSecretAccessKey': '', 
                                        'awsAccountNumber': ''})
            
            # add some credentials with a dash and whitespace
            self.addAllLaunchPermsCalled = False
            client.setEC2CredentialsForUser(data['adminId'], 'id-fo o ', 
                                            'publicKey foo',
                                            'secr foo etKey', False)
            self.assertTrue(self.addAllLaunchPermsCalled)
            ec2cred = client.getEC2CredentialsForUser(data['adminId'])
            self.assertTrue(ec2cred == {'awsPublicAccessKeyId': 'publicKeyfoo', 
                                        'awsSecretAccessKey': 'secrfooetKey', 
                                        'awsAccountNumber': 'idfoo'})
            
        finally:
            client.server._server.validateEC2Credentials = \
                oldValidateAMICredentials
            client.server._server.amiPerms._addAMIPermissionsForAccount = \
                oldAddAllEC2LaunchPermissions
            client.server._server.amiPerms._removeAMIPermissionsForAccount = \
                oldRemoveAllEC2LaunchPermissions
                
    @testsuite.tests('RBL-4146')
    @fixtures.fixture("EC2")
    def testEC2CredentialsForUserInvalidAMI(self, db, data):
        """
        This tests setting credentials for a user where we try to set
        permissions on an invalid AMI (i.e. removed from S3).
        """
        client = self.getClient("admin")

        mock.mockMethod(client.server._server.amiPerms._getEC2Client)
        self.addLaunchPermCalled = False
        
        def addLaunchPermission(amiId, awsAccountNumber):
            self.addLaunchPermCalled = True
            ec2ResponseObj = ec2.ErrorResponseObject()
            ec2ResponseObj.addError("InvalidAMIID.Unavailable", 
                "The image ID 'ami-3c1bfe55' is no longer available")

            raise mint_error.EC2Exception(ec2ResponseObj)

        mock.mockMethod(client.server._server.amiPerms._getAMIsForPermChange,
                        ['ami-3c1bfe55'])
        ec2Client = client.server._server.amiPerms._getEC2Client()
        ec2Client._mock.set(addLaunchPermission = addLaunchPermission)

        def validateEC2Credentials(authToken):
            return True
                
        oldValidateAMICredentials = client.server._server.validateEC2Credentials
        client.server._server.validateEC2Credentials = validateEC2Credentials
        
        failed = False
        
        try:
            # try adding the credentials
            client.setEC2CredentialsForUser(data['adminId'], 'id', 'publicKey',
                                            'secretKey', False)
        except Exception, e:
            raise
            failed = True
        assert(self.addLaunchPermCalled)

        client.server._server.validateEC2Credentials = \
            oldValidateAMICredentials
            
        if failed:
            self.fail("Should not fail setting EC2 credentials if AMI is missing!")
            
    @fixtures.fixture("EC2")
    def testAddRemoveEC2LaunchPermissions(self, db, data):
        client = self.getClient("admin")

        launchableAMIIds = []

        def addLaunchPermission(self, ec2AMIId, awsAccountNumber):
            launchableAMIIds.append(ec2AMIId)
        def removeLaunchPermission(self, ec2AMIId, awsAccountNumber):
            spot = launchableAMIIds.index(ec2AMIId)
            launchableAMIIds.pop(spot)

        oldAddLaunchPermission = ec2.EC2Wrapper.addLaunchPermission
        oldRemoveLaunchPermission = ec2.EC2Wrapper.removeLaunchPermission
        ec2.EC2Wrapper.addLaunchPermission = addLaunchPermission
        ec2.EC2Wrapper.removeLaunchPermission = removeLaunchPermission

        try:
            client.setEC2CredentialsForUser(data['developerId'], 'acctnum',
                                            '', '', force=True)
            self.assertEquals(launchableAMIIds,
               ['ami-00000001', 'ami-00000002', 'ami-00000006', 'ami-00000007'])
            client.setEC2CredentialsForUser(data['developerId'], '',
                                            '', '', force=True)
            self.assertEquals(launchableAMIIds, [])

            client.setEC2CredentialsForUser(data['normalUserId'], 'acctnum',
                                            '', '', force=True)
            self.assertEquals(launchableAMIIds, ['ami-00000007'])
            client.setEC2CredentialsForUser(data['normalUserId'], '',
                                            '', '', force=True)
            self.assertEquals(launchableAMIIds, [])
        finally:
            ec2.EC2Wrapper.addLaunchPermission = oldAddLaunchPermission
            ec2.EC2Wrapper.removeLaunchPermission = oldRemoveLaunchPermission
        
    def testErrorResponseObject(self):
        
        # test single error
        errObj = ec2.EC2ResponseError(401, '', AWS_ERROR_XML_SINGLE)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == 401)
        self.assertTrue(ec2error.requestId == u'2410d7ed-986c-4e86-a35b-68d4a4062024')
        self.assertTrue(ec2error.errors == [
             {'message': u'AWS was not able to validate the provided access credentials', 
              'code': u'AuthFailure'}])
        
        # test multiple errors
        errObj = ec2.EC2ResponseError(403, '', AWS_ERROR_XML_MULTIPLE)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == 403)
        self.assertTrue(ec2error.requestId == u'3410d7ed-986c-4e86-a35b-68d4a4062024')
        self.assertTrue(ec2error.errors == [
             {'message': u'AWS was not able to validate the provided access credentials', 
              'code': u'AuthFailure'},
             {'message': u'You\'re an idiot, back off', 
              'code': u'IQTooLow'}])
        
        # test that duplicate error messages are only reported once
        errObj = ec2.EC2ResponseError(403, '', AWS_ERROR_XML_DUP_MESSAGES)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == 403)
        self.assertTrue(ec2error.requestId == u'3410d7ed-986c-4e86-a35b-68d4a4062024')
        self.assertTrue(ec2error.errors == [
             {'message': u'AWS was not able to validate the provided access credentials', 
              'code': u'AuthFailure'}])
        
        # test that duplicate error codes with different messages are reported
        errObj = ec2.EC2ResponseError(403, '', AWS_ERROR_XML_DUP_CODES)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == 403)
        self.assertTrue(ec2error.requestId == u'3410d7ed-986c-4e86-a35b-68d4a4062024')
        self.assertTrue(ec2error.errors == [
             {'message': u'Some message', 
              'code': u'AuthFailure'},
             {'message': u'Different message', 
              'code': u'AuthFailure'}])
        
        # test unknown errors (i.e. no XML for the errors)
        errObj = ec2.EC2ResponseError(400, '', AWS_ERROR_XML_UNKNOWN)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == 400)
        self.assertTrue(ec2error.requestId == u'4410d7ed-986c-4e86-a35b-68d4a4062024')
        self.assertTrue(ec2error.errors == [
             {'message': u'An unknown failure occurred', 
              'code': u'UnknownFailure'}])
        
        # test unknown errors when no response data at all
        errObj = ec2.EC2ResponseError(None, '', "<foo><bar></bar></foo>")
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.status == None)
        self.assertTrue(ec2error.requestId == u'')
        self.assertTrue(ec2error.errors == [
             {'message': u'An unknown failure occurred', 
              'code': u'UnknownFailure'}])
        
        # test freeze (marshal)
        errObj = ec2.EC2ResponseError(401, '', AWS_ERROR_XML_SINGLE)
        ec2error = ec2.ErrorResponseObject(errObj)
        self.assertTrue(ec2error.freeze() == (401, 
            u'2410d7ed-986c-4e86-a35b-68d4a4062024', 
            [{'message': u'AWS was not able to validate the provided access credentials', 
              'code': u'AuthFailure'}]))
        
        # test thaw (unmarshal)
        errObj = ec2.EC2ResponseError(401, '', AWS_ERROR_XML_SINGLE)
        ec2error = ec2.ErrorResponseObject(errObj)
        marshalledData = ec2error.freeze()
        newEc2error = ec2.ErrorResponseObject()
        newEc2error.thaw(marshalledData)
        self.assertTrue(marshalledData == ec2error.freeze())
        
        # test creating standalone
        errRespObj = ec2.ErrorResponseObject()
        errRespObj.addError(u"IncompleteCredentials", 
                            u"Incomplete set of credentials")
        marshalledData = errRespObj.freeze()
        self.assertTrue(errRespObj.freeze() == (0, u'', 
            [{'message': u'Incomplete set of credentials', 
              'code': u'IncompleteCredentials'}]))
        newEc2error = ec2.ErrorResponseObject()
        newEc2error.thaw(marshalledData)
        self.assertTrue(marshalledData == errRespObj.freeze())

    @fixtures.fixture("EC2")
    def testAMIBuildsForUser(self, db, data):
        client = self.getClient('developer')
        AMIbuilds = client.getAMIBuildsForUser(data['developerId'])
        self.failUnlessEqual(set([x['amiId'] for x in AMIbuilds]),
                set(['ami-00000001', 'ami-00000002', 'ami-00000003',
                     'ami-00000006', 'ami-00000007']))

        client = self.getClient('someotherdeveloper')
        otherAMIbuilds = client.getAMIBuildsForUser(data['someOtherDeveloperId'])
        self.failUnlessEqual(len(otherAMIbuilds), 7)

    @fixtures.fixture("EC2")
    def testAMIBuildsForDifferentUser(self, db, data):
        client = self.getClient('developer')
        self.failUnlessRaises(mint_error.PermissionDenied,
                client.getAMIBuildsForUser, data['adminId'])

    @fixtures.fixture("EC2")
    def testAMIBuildsForNonExisistentUser(self, db, data):
        client = self.getClient('admin')
        self.failUnlessRaises(mint_error.ItemNotFound,
                client.getAMIBuildsForUser, 238494)

    @fixtures.fixture("EC2")
    def testAMIBuildsForUserWithNoAMIBuilds(self, db, data):
        client = self.getClient('admin')
        AMIbuilds = client.getAMIBuildsForUser(data['adminId'])
        self.failUnlessEqual(len(AMIbuilds), 0, "Admin user has no" \
                " AMI builds, should have returned empty list")

    @fixtures.fixture("EC2")
    def testAMIBuildsForAdminUser(self, db, data):
        client = self.getClient('admin')
        AMIbuilds = client.getAMIBuildsForUser(data['someOtherDeveloperId'])
        self.failUnlessEqual(len(AMIbuilds), 7,
                "Expected to see seven AMI builds")

    @fixtures.fixture("EC2")
    def testAllAMIBuilds(self, db, data):
        client = self.getClient('admin')
        AMIbuilds = client.getAllBuildsByType('AMI')
        self.failUnlessEqual(len(AMIbuilds), 7,
                "Expected to see seven AMI builds")

        AMIbuilds = dict((x['amiId'], x) for x in AMIbuilds)
        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'Unknown')
        # now add some EC2 credentials to the admin user
        client.setEC2CredentialsForUser(data['adminId'], 'newId',
            'newPublicKey', 'newSecretKey', False)

        AMIbuilds = client.getAllBuildsByType('AMI')
        AMIbuilds = dict((x['amiId'], x) for x in AMIbuilds)
        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'newId')

        self.failUnlessEqual(AMIbuilds['ami-00000006']['role'],
                '')

        # remove EC2 credentials to the admin user
        client.setEC2CredentialsForUser(data['adminId'], 'newId',
            'newPublicKey', 'newSecretKey', False)

        AMIbuilds = client.getAllBuildsByType('AMI')
        AMIbuilds = dict((x['amiId'], x) for x in AMIbuilds)
        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'newId')

        # now add admin as a developer to the build's project
        client.removeEC2CredentialsForUser(data['adminId'])
        bld = client.getBuild(AMIbuilds['ami-00000006']['buildId'])
        prj = client.getProject(bld.getProjectId())
        prj.addMemberById(data['adminId'], userlevels.DEVELOPER)
        AMIbuilds = client.getAllBuildsByType('AMI')
        AMIbuilds = dict((x['amiId'], x) for x in AMIbuilds)
        self.failUnlessEqual(AMIbuilds['ami-00000006']['role'],
                'Product Developer')

    @fixtures.fixture("EC2")
    def testAMIBuildsDataVisibilityDeveloper(self, db, data):
        client = self.getClient('developer')
        amiIds = [x['amiId'] for x in client.getAllBuildsByType('AMI')]
        self.failUnless('ami-00000001' in amiIds,
                "developer should see this unpublished build")
        self.failUnless('ami-00000003' in amiIds,
                "developer should see this published build")
        self.failUnless('ami-00000006' in amiIds,
                "developer should see the unpublished build in the" \
                " hidden project he is a member of")
        self.failUnless('ami-00000007' in amiIds,
                "developer should see the published build in the" \
                " hidden project he is a member of")

    @fixtures.fixture("EC2")
    def testAMIBuildsDataVisibilityNormalUser(self, db, data):
        client = self.getClient('normaluser')
        amiIds = [ x['amiId'] for x in client.getAllBuildsByType('AMI')] 
        self.failIf('ami-00000001' in amiIds,
                "normal user should not see this unpublished build")
        self.failUnless('ami-00000003' in amiIds,
                "normal user should see this published build")
        self.failIf('ami-00000006' in amiIds,
                "normal user should not see the unpublished build in" \
                " the hidden project he is a member of")
        self.failUnless('ami-00000007' in amiIds,
                "normal user should see the published build in the" \
                " hidden project he is a member of")

    @fixtures.fixture("EC2")
    def testAMIBuildsDataVisibilityNobody(self, db, data):
        client = self.getClient('loneuser')
        amiIds = [ x['amiId'] for x in client.getAllBuildsByType('AMI')] 
        self.failIf('ami-00000001' in amiIds,
                "lone user should not see this unpublished build")
        self.failUnless('ami-00000003' in amiIds,
                "lone user should see this published build")
        self.failIf('ami-00000006' in amiIds,
                "lone user should not see unpublished builds " \
                        "in hidden projects")
        self.failIf('ami-00000007' in amiIds,
                "lone user should not see published builds " \
                        "in hidden projects")

    @fixtures.fixture("EC2")
    def testAMIBuildsDataVisibilityAdmin(self, db, data):
        client = self.getClient('admin')
        amiIds = [ x['amiId'] for x in client.getAllBuildsByType('AMI')] 
        self.failUnlessEqual(len(amiIds), 7, 'admin should see everything')

    @fixtures.fixture("Empty")
    def testAMIBuildsData(self, db, data):
        self.setupEC2Credentials()
        client = self.getClient('admin')
        testClient = self.getClient('test')

        # Create a plain ol' project
        hostname = shortname = "project1"
        projectId = testClient.newProject("Project 1",
                                      hostname,
                                      MINT_PROJECT_DOMAIN,
                                      shortname=shortname,
                                      version="1.0",
                                      prodtype="Component")

        # create an AMI build that isn't a part of a release
        build = testClient.newBuild(projectId,
                "Test AMI Build (Unpublished, not in release)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000001', RDT_STRING,
                validate=False)

        # original build created by test user, not seen by admin
        self.failUnlessEqual(client.getAMIBuildsForUser(data['test']),
            [dict(amiId='ami-00000001', isPublished=0,
                 level=0, isPrivate=0, projectId=1)],
            "Expected to see ami-00000001")

        # make sure admin can't see any AMI builds for herself
        self.failUnlessEqual(client.getAMIBuildsForUser(data['admin']), [],
                "Expected to not see any AMI builds as admin doesn't belong to any projects with AMI builds")

        # add admin to project, now admin shows AMI build
        project = client.getProject(projectId)
        project.addMemberById(data['admin'], userlevels.DEVELOPER)
        self.failUnlessEqual(client.getAMIBuildsForUser(data['admin']),
            [dict(amiId='ami-00000001', isPublished=0,
                 level=1, isPrivate=0, projectId=1)],
            "Expected to see ami-00000001")

        # create a published release, but don't publish yet
        pubRelease = client.newPublishedRelease(projectId)
        pubRelease.name = "(Not final) Release"
        pubRelease.version = "1.1"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        self.failUnlessEqual(client.getAMIBuildsForUser(data['admin']),
            [dict(amiId='ami-00000001', isPublished=0,
                 level=1, isPrivate=0, projectId=1)],
            "Expected isPublished to not be set")

        # publish the published release
        pubRelease.publish()
        self.failUnlessEqual(client.getAMIBuildsForUser(data['admin']),
            [dict(amiId='ami-00000001', isPublished=1,
                 level=1, isPrivate=0, projectId=1)],
            "Expected isPublished to be set")

        # hide the project (make private)
        client.hideProject(projectId)
        self.failUnlessEqual(client.getAMIBuildsForUser(data['admin']),
            [dict(amiId='ami-00000001', isPublished=1,
                 level=1, isPrivate=1, projectId=1)],
            "Expected isPrivate to be set")

    @fixtures.fixture("EC2")
    def testPublicProductMemberModification(self, db, data):
        self.setupLaunchPermissionsTest()
        client = self.getClient("developer")
        loneClient = self.getClient("loneuser")

        try:
            # Set some aws creds for the user
            loneClient.setEC2CredentialsForUser(data['loneUserId'], 'id', 
                                                'publicKey',
                                                'secretKey', False)

            project = loneClient.getProject(data['projectId'])

            # Watch Product
            project.addMemberByName("loneuser", userlevels.USER)
            # Users get no explicit launch permissions on public products.
            self.assertEquals(self.launchableAMIIds, [])

            # Promote to Developer
            project.updateUserLevel(data['loneUserId'], userlevels.DEVELOPER)
            # Should now have launch perms on private AMI's.
            self.assertEquals(self.launchableAMIIds, 
                              ['ami-00000001', 'ami-00000002'])

            # Demote to regular user
            project.updateUserLevel(data['loneUserId'], userlevels.USER)
            # Users get no explicit launch permissions on public products.
            self.assertEquals(self.launchableAMIIds, [])
            # Promote to Owner
            project.updateUserLevel(data['loneUserId'], userlevels.DEVELOPER)
            # Should now have launch perms on private AMI's.
            self.assertEquals(self.launchableAMIIds, 
                              ['ami-00000001', 'ami-00000002'])

            # Leave Product
            project.delMemberById(data['loneUserId'])
            # Should have no launch permissions
            self.assertEquals(self.launchableAMIIds, [])
        finally:
            self.tearDownLaunchPermissionsTest()
            
    @fixtures.fixture("EC2")
    def testPrivateProductMemberModification(self, db, data):
        self.setupLaunchPermissionsTest()
        client = self.getClient("developer")
        loneClient = self.getClient("loneuser")

        try:
            # Set some aws creds for the user
            loneClient.setEC2CredentialsForUser(data['loneUserId'], 'id', 
                                                'publicKey',
                                                'secretKey', False)

            project = client.getProject(data['hiddenProjectId'])

            # Add the user as a developer to the product
            project.addMemberById(data['loneUserId'], userlevels.DEVELOPER)
            # Should have launch perms on all AMIs in the product
            self.assertEquals(self.launchableAMIIds, 
                              ['ami-00000006', 'ami-00000007'])

            # Promote to Owner
            project.updateUserLevel(data['loneUserId'], userlevels.OWNER)
            # Should have launch perms on all AMIs in the product
            self.assertEquals(self.launchableAMIIds, 
                              ['ami-00000006', 'ami-00000007'])

            # Leave Product
            project.delMemberById(data['loneUserId'])
            # Should have no launch permissions
            self.assertEquals(self.launchableAMIIds, [])
        finally:
            self.tearDownLaunchPermissionsTest()

    def setupLaunchPermissionsTest(self):
        client = self.getClient("admin")

        launchableAMIIds = []
        self.launchableAMIIds = launchableAMIIds

        def addLaunchPermission(self, ec2AMIId, awsAccountNumber):
            launchableAMIIds.append(ec2AMIId)
        def removeLaunchPermission(self, ec2AMIId, awsAccountNumber):
            try:
                spot = launchableAMIIds.index(ec2AMIId)
                launchableAMIIds.pop(spot)
            except ValueError:
                pass

        self.oldAddLaunchPermission = ec2.EC2Wrapper.addLaunchPermission
        self.oldRemoveLaunchPermission = ec2.EC2Wrapper.removeLaunchPermission
        ec2.EC2Wrapper.addLaunchPermission = addLaunchPermission
        ec2.EC2Wrapper.removeLaunchPermission = removeLaunchPermission

        def validateEC2Credentials(authToken):
            return True
                
        self.oldValidateAMICredentials = \
            client.server._server.validateEC2Credentials
        client.server._server.validateEC2Credentials = validateEC2Credentials

    def tearDownLaunchPermissionsTest(self):
        client = self.getClient("admin")

        ec2.EC2Wrapper.addLaunchPermission = self.oldAddLaunchPermission
        ec2.EC2Wrapper.removeLaunchPermission = self.oldRemoveLaunchPermission

        client.server._server.validateEC2Credentials = \
            self.oldValidateAMICredentials

    @fixtures.fixture("EC2")
    def testPublishPublishedRelease(self, db, data):
        client = self.getClient("admin")
        devclient = self.getClient("developer")
        sodevclient = self.getClient("someotherdeveloper")
        nuclient = self.getClient("normaluser")

        def reset():
            self.resetLaunchPermissionsCalled = False
            self.addPublicLaunchPermissionCalled = False
            self.removePublicLaunchPermissionCalled = False
            self.launchPermissions = []

        reset()
        
        def addPublicLaunchPermission(cls, amiId):
            self.addPublicLaunchPermissionCalled = True
        def removePublicLaunchPermission(cls, amiId):
            self.removePublicLaunchPermissionCalled = True
        def resetLaunchPermissions(cls, amiId):
            self.resetLaunchPermissionsCalled = True
        def addLaunchPermission(cls, amiId, awsAccountNumber):
            self.launchPermissions.append((amiId, awsAccountNumber))
        def removeLaunchPermission(cls, amiId, awsAccountNumber):
            self.launchPermissions.append((amiId, awsAccountNumber))
        def resetLaunchPermissions(cls, amiId):
            self.launchPermissions = []
            self.resetLaunchPermissionsCalled = True
        def isRBO():
            return True

        oldresetLaunchPermissions = ec2.EC2Wrapper.resetLaunchPermissions
        ec2.EC2Wrapper.resetLaunchPermissions = resetLaunchPermissions
        oldaddPublicLaunchPermission = ec2.EC2Wrapper.addPublicLaunchPermission
        ec2.EC2Wrapper.addPublicLaunchPermission = addPublicLaunchPermission
        oldremovePublicLaunchPermission = ec2.EC2Wrapper.removePublicLaunchPermission
        ec2.EC2Wrapper.removePublicLaunchPermission = removePublicLaunchPermission
        oldaddLaunchPermission = ec2.EC2Wrapper.addLaunchPermission
        ec2.EC2Wrapper.addLaunchPermission = addLaunchPermission
        oldremoveLaunchPermission = ec2.EC2Wrapper.removeLaunchPermission
        ec2.EC2Wrapper.removeLaunchPermission = removeLaunchPermission
        oldresetLaunchPermissions = ec2.EC2Wrapper.resetLaunchPermissions
        ec2.EC2Wrapper.resetLaunchPermissions = resetLaunchPermissions
        oldIsRBO = config.isRBO

        try:
            # Set some aws creds for the user
            devclient.setEC2CredentialsForUser(data['developerId'], 'devid',
                                                'devPublicKey',
                                                'secretKey', False)
            # Set some aws creds for the user
            sodevclient.setEC2CredentialsForUser(data['someOtherDeveloperId'], 'sodevid',
                                                'sodevPublicKey',
                                                'secretKey', False)
             
            # Set some aws creds for the user
            nuclient.setEC2CredentialsForUser(data['normalUserId'], 'nuid',
                                                'nuPublicKey',
                                                'secretKey', False)
            reset()

            # Get the published release id that we need.
            pubReleases = client.getPublishedReleaseList()
            for pubRelease in pubReleases:
                if pubRelease[1] == 'testproject':
                    id = pubRelease[2].id

            # Unpublish the release of a public product on rBA
            client.unpublishPublishedRelease(id)
            # Launch perms were reset
            self.assertTrue(self.resetLaunchPermissionsCalled)
            # launch perms were added to the owner and developer in the product
            self.assertEquals(len(self.launchPermissions), 2)
            self.assertTrue(('ami-00000003', 'devid') in self.launchPermissions)
            self.assertTrue(('ami-00000003', 'sodevid') in self.launchPermissions)
            reset()

            # Publish the release of a public product on rBA
            client.publishPublishedRelease(id, False)
            # Public launch perms were not added
            self.assertTrue(not self.addPublicLaunchPermissionCalled)
            # Launch perms for all 3 users were added.
            self.assertEquals(len(self.launchPermissions), 3)
            reset()

            # Unpublish the release of a private product on rBA
            client.unpublishPublishedRelease(data['hiddenProjPubPubReleaseId'])
            # Perms were reset
            self.assertTrue(self.resetLaunchPermissionsCalled)
            # Launch perms were added for owners and developers
            self.assertEquals(2, len(self.launchPermissions))
            self.assertTrue(('ami-00000007', 'devid') in self.launchPermissions)
            self.assertTrue(('ami-00000007', 'sodevid') in self.launchPermissions)
            reset()

            # Publish the release of a private product on rBA
            client.publishPublishedRelease(data['hiddenProjPubPubReleaseId'], False)
            # adding Public launch perms wasn't done
            self.assertFalse(self.addPublicLaunchPermissionCalled)
            # Perms weren't reset
            self.assertFalse(self.resetLaunchPermissionsCalled)
            # Launch perms were added for a normal user
            self.assertEquals(1, len(self.launchPermissions))
            self.assertTrue(('ami-00000007', 'nuid') in self.launchPermissions)
            reset()

            # Publish the release of a public product on rBO
            config.isRBO = isRBO
            # Unpublish the previously published release.
            client.unpublishPublishedRelease(id)
            client.publishPublishedRelease(id, False)
            # Public launch perms were added
            self.assertTrue(self.addPublicLaunchPermissionCalled)
            reset()

            # Unpublish the release of a public product on rBO
            client.unpublishPublishedRelease(id)
            # Launch perms were reset.
            self.assertTrue(self.resetLaunchPermissionsCalled)
            # Launch perms were added for owner and developer.
            self.assertEquals(2, len(self.launchPermissions))
            self.assertTrue(('ami-00000003', 'devid') in self.launchPermissions)
            self.assertTrue(('ami-00000003', 'sodevid') in self.launchPermissions)
            reset()

            # Publish the release of a private product on rBO
            # Unpublish the previously published release first to run this
            # test.
            client.unpublishPublishedRelease(data['hiddenProjPubPubReleaseId'])
            reset()
            client.publishPublishedRelease(data['hiddenProjPubPubReleaseId'], False)
            # Public launch perms were not added.
            self.assertFalse(self.addPublicLaunchPermissionCalled)
            # Launch perms were added for a normal user
            self.assertEquals(1, len(self.launchPermissions))
            self.assertTrue(('ami-00000007', 'nuid') in self.launchPermissions)
            reset()

            # Unpublish the release of a private product on rBO
            client.unpublishPublishedRelease(data['hiddenProjPubPubReleaseId'])
            # Launch perms were reset.
            self.assertTrue(self.resetLaunchPermissionsCalled)
            # Launch perms were added for owner and developer.
            self.assertEquals(2, len(self.launchPermissions))
            self.assertTrue(('ami-00000007', 'devid') in self.launchPermissions)
            self.assertTrue(('ami-00000007', 'sodevid') in self.launchPermissions)
            reset()

            config.isRBO = oldIsRBO
        finally:
            ec2.EC2Wrapper.resetLaunchPermissions = oldresetLaunchPermissions
            ec2.EC2Wrapper.addPublicLaunchPermission = oldaddPublicLaunchPermission
            ec2.EC2Wrapper.removePublicLaunchPermission = oldremovePublicLaunchPermission
            ec2.EC2Wrapper.addLaunchPermission = oldaddLaunchPermission
            ec2.EC2Wrapper.removeLaunchPermission = oldremoveLaunchPermission
            ec2.EC2Wrapper.resetLaunchPermissions = oldresetLaunchPermissions
            config.isRBO = oldIsRBO
          
    @fixtures.fixture('EC2')
    def testCancelUserAccountEC2(self, db, data):
        """
        Test canceling user account with EC2 credentials and permissions.
        """
        adminClient = self.getClient('admin')
        client = self.getClient('developer')
        user = client.getUser(data['developerId'])
        
        self.addLaunchPermsCalled = False
        self.removeLaunchPermsCalled = False
        self.removeUserAccountCalled = False

        def addAllEC2LaunchPermissions(userId, awsAccountNumber):
            self.addLaunchPermsCalled = True
            return True

        def removeAllEC2LaunchPermissions(userId, awsAccountNumber):
            self.removeLaunchPermsCalled = True
            return True

        def validateEC2Credentials(authToken):
            return True
        
        def ensureNoOrphans(userId):
            return True
        
        def removeUserAccount(userId):
            self.removeUserAccountCalled = True
            oldRemoveUserAccount(userId)
            return True
                
        oldValidateAMICredentials = client.server._server.validateEC2Credentials
        client.server._server.validateEC2Credentials = validateEC2Credentials
        oldAddAllEC2LaunchPermissions = \
            client.server._server.amiPerms._addAMIPermissionsForAccount
        client.server._server.amiPerms._addAMIPermissionsForAccount = \
            addAllEC2LaunchPermissions
        oldRemoveAllEC2LaunchPermissions = \
            client.server._server.amiPerms._removeAMIPermissionsForAccount
        client.server._server.amiPerms._removeAMIPermissionsForAccount = \
            removeAllEC2LaunchPermissions
        oldEnsureNoOrphans = client.server._server._ensureNoOrphans
        client.server._server._ensureNoOrphans = ensureNoOrphans
        oldRemoveUserAccount = client.server._server.removeUserAccount
        client.server._server.removeUserAccount = removeUserAccount
        
        try:
            # set some EC2 credentials
            client.setEC2CredentialsForUser(user.id, '012345678901',
                'awsPublicAccessKeyId', 'awsSecretAccessKey', force=True)
            self.assertTrue(client.getEC2CredentialsForUser(user.id) ==\
                {'awsPublicAccessKeyId': 'awsPublicAccessKeyId', 
                 'awsSecretAccessKey': 'awsSecretAccessKey', 
                 'awsAccountNumber': '012345678901'})
            
            # add some launch permissions
            client.setEC2CredentialsForUser(user.id, '012345678901', '', '',
                                            force=False)
            self.assertTrue(self.addLaunchPermsCalled)
            
            # cancel the account
            user.cancelUserAccount()
            
            # make sure no launch permissions are present
            self.assertTrue(self.removeLaunchPermsCalled)
            
            # make sure credentials are gone
            self.assertTrue(adminClient.getEC2CredentialsForUser(user.id) ==\
                {'awsPublicAccessKeyId': '', 
                 'awsSecretAccessKey': '', 
                 'awsAccountNumber': ''})
            
            # make sure account is gone
            self.assertTrue(self.removeUserAccountCalled)
        finally:
            client.server._server.validateEC2Credentials = \
                oldValidateAMICredentials
            client.server._server.amiPerms._addAMIPermissionsForAccount = \
                oldAddAllEC2LaunchPermissions
            client.server._server.amiPerms._removeAMIPermissionsForAccount = \
                oldRemoveAllEC2LaunchPermissions
            client.server._server._ensureNoOrphans = oldEnsureNoOrphans
            client.server._server.removeUserAccount = oldRemoveUserAccount


    @fixtures.fixture('EC2')
    def testDeleteAMI(self, db, data):
        """
        Test deleting an AMI from s3.
        """
        client = self.getClient("admin")

        build1 = client.getBuild(data['buildId1'])
        build1.deleteBuild()

        global deletedKeys
        self.assertEquals(deletedKeys, 
            ['teletran1-1-x86_18.img.part.0',
             'teletran1-1-x86_18.img.part.1',
             'teletran1-1-x86_18.img.part.2',
             'teletran1-1-x86_18.img.part.3',
             'manifest-file-name.xml'
            ])


class EC2SitewideTest(BaseEC2Test):
    def setUp(self):
        self.mockEC2Connect = mock.MockObject()
        self.mock(boto, 'connect_ec2', self.mockEC2Connect)
        fixtures.FixturedUnitTest.setUp(self)

    @fixtures.fixture('Empty')
    @testsuite.context('RBL-3757')
    def testSetSitewideEC2Data(self, db, data):
        client = self.getClient("admin")
        refData = {'key': 'value'}
        targetId = client.addTarget('ec2', 'aws', refData)

        res = client.getTargetData('ec2', 'aws')
        self.assertEquals(res, refData)

        client.deleteTarget('ec2', 'aws')
        err = self.assertRaises(mint_error.TargetMissing,
                client.getTargetData, 'ec2', 'aws')
        self.assertEquals(str(err), "No target named 'aws' of type 'ec2'")

    @fixtures.fixture('Empty')
    @testsuite.context('RBL-3757')
    def testSetDuplicateEC2Data(self, db, data):
        client = self.getClient("admin")
        refData = {'key': 'value'}
        targetId = client.addTarget('ec2', 'aws', refData)
        err = self.assertRaises(mint_error.TargetExists,
                client.addTarget, 'ec2', 'aws', refData)
        self.assertEquals(str(err),
                "Target named 'aws' of type 'ec2' already exists")

        targetId = client.deleteTarget('ec2', 'aws')
        err = self.assertRaises(mint_error.TargetMissing,
                client.deleteTarget, 'ec2', 'aws')
        self.assertEquals(str(err), "No target named 'aws' of type 'ec2'")

    @fixtures.fixture('Empty')
    @testsuite.context('RBL-3757')
    def testSetSitewideEC2DataPermissions(self, db, data):
        client = self.getClient("loneUserId")
        refData = {'key': 'value'}
        self.assertRaises(mint_error.PermissionDenied,
                client.addTarget, 'ec2', 'aws', refData)

        self.assertRaises(mint_error.PermissionDenied,
                client.getTargetData, 'ec2', 'aws')

        self.assertRaises(mint_error.PermissionDenied,
                client.deleteTarget, 'ec2', 'aws')


if __name__ == '__main__':
    testsuite.main()
