#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import time

import boto
from boto.exception import EC2ResponseError

from mint import ec2
from mint import mint_error

from mint.helperfuncs import toDatabaseTimestamp, fromDatabaseTimestamp, buildEC2AuthToken

import fixtures

from mint import buildtypes
from mint import userlevels
from mint.data import RDT_STRING
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

class FakeEC2Connection(object):

    def __init__(self, (accountId, accessKey, secretKey)):
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey

    def _checkKeys(self):
        if self.accessKey != FAKE_PUBLIC_KEY or \
                self.secretKey != FAKE_PRIVATE_KEY:
            raise EC2ResponseError()

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

    __slots__ = ( 'amiId', 'id', 'state', 'dns_name' )

    def __init__(self, amiId, instanceId, state='pending', dns_name=''):
        self.id = instanceId
        self.state = state
        self.dns_name = dns_name
        self.amiId = amiId

class FakeEC2ResultSet(object):

    __slots__ = ( 'instances', )

    def __init__(self, instances):
        self.instances = instances
        pass

def getFakeEC2Connection(accessKey, secretKey):
    return FakeEC2Connection((None, accessKey, secretKey))

class Ec2Test(fixtures.FixturedUnitTest):

    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.old_connect_ec2 = boto.connect_ec2
        boto.connect_ec2 = getFakeEC2Connection

    def tearDown(self):
        fixtures.FixturedUnitTest.tearDown(self)
        boto.connect_ec2 = self.old_connect_ec2

    @fixtures.fixture("Full")
    def testBlessedAMI_CRUD(self, db, data):
        client = self.getClient("admin")

        ec2AMIId = 'ami-decafbad'
        shortDescription = "This is a blessed AMI. Woot!"
        helptext = \
"""This is a blessed AMI that can be used for demonstrating the power of EC2
Please log in via raa using the following password. %(raaPassword)s"""

        # create the Blessed AMI
        blessedAMIId = client.createBlessedAMI(ec2AMIId, shortDescription)
        blessedAMI = client.getBlessedAMI(blessedAMIId)

        # check some default properties
        self.failUnlessEqual(blessedAMI.blessedAMIId, blessedAMIId)
        self.failUnlessEqual(blessedAMI.shortDescription, shortDescription)
        self.failUnlessEqual(blessedAMI.ec2AMIId, ec2AMIId)
        self.failUnlessEqual(blessedAMI.instanceTTL, self.cfg.ec2DefaultInstanceTTL)
        self.failUnlessEqual(blessedAMI.mayExtendTTLBy, self.cfg.ec2DefaultMayExtendTTLBy)
        self.failUnless(blessedAMI.isAvailable)
        self.failIf(blessedAMI.buildId)

        # update some things
        blessedAMI.buildId = None
        blessedAMI.helptext = helptext
        blessedAMI.mayExtendTTLBy = 4000
        blessedAMI.save()

        self.failUnlessEqual(blessedAMI.helptext, helptext)
        self.failUnlessEqual(blessedAMI.mayExtendTTLBy, 4000)
        del blessedAMI

        blessedAMI = client.getBlessedAMI(blessedAMIId)
        self.failUnlessEqual(blessedAMI.helptext, helptext)
        self.failUnlessEqual(blessedAMI.mayExtendTTLBy, 4000)

        blessedAMI.isAvailable = False
        blessedAMI.buildId = None
        blessedAMI.save()
        del blessedAMI

        blessedAMI = client.getBlessedAMI(blessedAMIId)
        self.failUnlessEqual(blessedAMI.isAvailable, 0)

        blessedAMI = client.getBlessedAMI(blessedAMIId)
        blessedAMI.userDataTemplate = "This here is my userdata template!"
        # FIXME: client.getBlessedAMI turns buildId from None to ''
        #   database.py:161 KeyedTable.get()
        # so we have to set it back here or we end up with a foreign
        # key constraint failure.
        blessedAMI.buildId = None
        blessedAMI.save()
        del blessedAMI

        blessedAMI = client.getBlessedAMI(blessedAMIId)
        self.failUnlessEqual(blessedAMI.userDataTemplate,
                "This here is my userdata template!")

    @fixtures.fixture("EC2")
    def testGetAvailableBlessedAMIs(self, db, data):

        client = self.getClient("admin")

        # seven blessed AMIs set up by the fixture
        self.failUnlessEqual([1, 2, 3, 4, 5, 6, 7], \
                [x.id for x in client.getAvailableBlessedAMIs()])

        # Now take one out of the pool and make sure it worked
        blessedAMI = client.getBlessedAMI(1)
        blessedAMI.buildId = None
        blessedAMI.isAvailable = False
        blessedAMI.save()

        self.failUnlessEqual([2, 3, 4, 5, 6, 7], \
                [x.id for x in client.getAvailableBlessedAMIs()])

    @fixtures.fixture("Empty")
    def testEmptyBlessedAMIs(self, db, data):
        client = self.getClient("admin")
        self.failUnlessEqual([], \
                [x.id for x in client.getAvailableBlessedAMIs()])

    @fixtures.fixture("Empty")
    def testEmptyActiveLaunchedAMIs(self, db, data):
        client = self.getClient("admin")
        self.failUnlessEqual([],
                [x.id for x in client.getActiveLaunchedAMIs()])

    @fixtures.fixture("Empty")
    def testGetNonexistentBlessedAMI(self, db, data):
        client = self.getClient("admin")
        self.assertRaises(mint_error.ItemNotFound, client.getBlessedAMI, 1)

    @fixtures.fixture("Empty")
    def testGetNonexistentLaunchedAMI(self, db, data):
        client = self.getClient("admin")
        self.assertRaises(mint_error.ItemNotFound, client.getLaunchedAMI, 1)

    @fixtures.fixture("EC2")
    def testLaunchAMIInstance(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg), 
                                              amiIds[0])
        self.failUnlessEqual(1, instanceId)

        instance = client.getLaunchedAMI(instanceId)
        self.failUnlessEqual(1, instance.id)
        self.failUnlessEqual('i-00000001', instance.ec2InstanceId)


    @fixtures.fixture("EC2")
    def testTerminateInstances(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg), 
                                              amiIds[0])
        instanceId2 = client.launchAMIInstance(buildEC2AuthToken(self.cfg), 
                                               amiIds[1])
        instanceId3 = client.launchAMIInstance(buildEC2AuthToken(self.cfg), 
                                               amiIds[2])

        activeAMIs = client.getActiveLaunchedAMIs()
        self.failUnlessEqual([instanceId, instanceId2, instanceId3],
                [x.id for x in activeAMIs])

        instance = client.getLaunchedAMI(instanceId)
        instance.expiresAfter = toDatabaseTimestamp(offset=-900)
        instance.save()

        instance = client.getLaunchedAMI(instanceId3)
        instance.expiresAfter = toDatabaseTimestamp(offset=-20)
        instance.save()

        # kill 'em
        self.failUnlessEqual([instanceId, instanceId3],
                client.terminateExpiredAMIInstances(buildEC2AuthToken(self.cfg)))
        del activeAMIs

        # there better only be one active now
        activeAMIs = client.getActiveLaunchedAMIs()
        self.failUnlessEqual([instanceId2], [x.id for x in activeAMIs])


    @fixtures.fixture("EC2")
    def testLaunchLimitPerIP(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']
        for i in range(0, self.cfg.ec2MaxInstancesPerIP):
            try:
                client.launchAMIInstance(buildEC2AuthToken(self.cfg), 
                                         amiIds[0])
            except mint_error.TooManyAMIInstancesPerIP:
                self.fail()

        # this should not fail
        #try:
        #    client.launchAMIInstance(amiIds[0])
        #except ec2.TooManyAMIInstancesPerIP:
        #    self.fail()

        # but this should
        self.assertRaises(mint_error.TooManyAMIInstancesPerIP,
                client.launchAMIInstance, buildEC2AuthToken(self.cfg), 
                amiIds[0])

        # this should not fail
        #try:
        #    client.launchAMIInstance(amiIds[0])
        #except ec2.TooManyAMIInstancesPerIP:
        #    self.fail()

    @fixtures.fixture("EC2")
    def testGetAMIInstanceStatus(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg),
                                              amiIds[0])

        state, dns_name = client.getLaunchedAMIInstanceStatus(
                              buildEC2AuthToken(self.cfg), instanceId)
        self.failUnlessEqual(state, 'pending')
        self.failIf(dns_name)

    @fixtures.fixture("Empty")
    def testLaunchNonexistentAMIInstance(self, db, data):
        client = self.getClient("admin")

        self.assertRaises(mint_error.FailedToLaunchAMIInstance,
                client.launchAMIInstance, buildEC2AuthToken(self.cfg), 3431)

    @fixtures.fixture("EC2")
    def testExtendInstanceTTL(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg), amiIds[0])

        blessedAMI = client.getBlessedAMI(amiIds[0])
        launchedAMI = client.getLaunchedAMI(instanceId)

        self.assertEqual(toDatabaseTimestamp(fromDatabaseTimestamp(launchedAMI.launchedAt) + blessedAMI.instanceTTL), launchedAMI.expiresAfter, "Failed normal case")

        client.extendLaunchedAMITimeout(instanceId)
        launchedAMI.refresh()

        self.assertEqual(toDatabaseTimestamp(fromDatabaseTimestamp(launchedAMI.launchedAt) + blessedAMI.instanceTTL + blessedAMI.mayExtendTTLBy),
                launchedAMI.expiresAfter, "Failed to extend the timeout")

    @fixtures.fixture("EC2")
    def testUserDataTemplate(self, db, data):
        client = self.getClient("admin")
        amiIds = data['amiIds']

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg), amiIds[0])

        blessedAMI = client.getBlessedAMI(amiIds[0])
        blessedAMIUserDataTemplate = \
"""[amiconfig]
plugins = rapadminpassword conaryproxy

[rpath]
rapadminpassword = @RAPAPASSWORD@
conaryproxy = http://proxy.hostname.com/proxy/
"""

        # FIXME: client.getBlessedAMI turns buildId from None to ''
        #   database.py:161 KeyedTable.get()
        # so we have to set it back here or we end up with a foreign
        # key constraint failure.
        blessedAMI.buildId = None
        blessedAMI.userDataTemplate = blessedAMIUserDataTemplate
        blessedAMI.save()

        instanceId = client.launchAMIInstance(buildEC2AuthToken(self.cfg),
                                              amiIds[0])
        launchedAMIInstance = client.getLaunchedAMI(instanceId)

        self.failUnless('rapadminpassword = password' in
                launchedAMIInstance.userData)

    def testGetIncompleteEC2Credentials(self):
        self.failUnlessRaises(mint_error.EC2Exception,
                ec2.EC2Wrapper, ('id', '', 'secretKey'))
        
    @fixtures.fixture("EC2")
    def testGetEC2KeyPairs(self, db, data):
        client = self.getClient("admin")

        # test getting all
        pairs = client.getEC2KeyPairs(buildEC2AuthToken(self.cfg), [])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key'), 
            ('key2', '2f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'another RSA private key')])
        
        # test getting 1
        pairs = client.getEC2KeyPairs(buildEC2AuthToken(self.cfg), ['key1'])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key')])
        
        # test getting multiple
        pairs = client.getEC2KeyPairs(buildEC2AuthToken(self.cfg), ['key1', 'key2'])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key'), 
            ('key2', '2f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'another RSA private key')])
        
    @fixtures.fixture("EC2")
    def testGetEC2KeyPair(self, db, data):
        client = self.getClient("admin")

        # test getting all
        pair = client.getEC2KeyPair(buildEC2AuthToken(self.cfg), 'key1')
        self.assertTrue(pair == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key')])
                
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
            client.server._server.addAllEC2LaunchPermissions
        client.server._server.addAllEC2LaunchPermissions = \
            addAllEC2LaunchPermissions
        oldRemoveAllEC2LaunchPermissions = \
            client.server._server.removeAllEC2LaunchPermissions
        client.server._server.removeAllEC2LaunchPermissions = \
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
        finally:
            client.server._server.validateEC2Credentials = \
                oldValidateAMICredentials
            client.server._server.addAllEC2LaunchPermissions = \
                oldAddAllEC2LaunchPermissions
            client.server._server.removeAllEC2LaunchPermissions = \
                oldRemoveAllEC2LaunchPermissions
            
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
            client.addAllEC2LaunchPermissions(data['developerId'], 'acctnum')
            self.assertEquals(launchableAMIIds,
               ['ami-00000001', 'ami-00000002', 'ami-00000006', 'ami-00000007'])
            client.removeAllEC2LaunchPermissions(data['developerId'], 'acctnum')
            self.assertEquals(launchableAMIIds, [])

            client.addAllEC2LaunchPermissions(data['normalUserId'], 'acctnum')
            self.assertEquals(launchableAMIIds, ['ami-00000007'])
            client.removeAllEC2LaunchPermissions(data['normalUserId'], 'acctnum')
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
        AMIbuilds = client.getAllAMIBuilds()
        self.failUnlessEqual(len(AMIbuilds), 7,
                "Expected to see seven AMI builds")

        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'Unknown')
        # now add some EC2 credentials to the admin user
        client.setEC2CredentialsForUser(data['adminId'], 'newId',
            'newPublicKey', 'newSecretKey', False)

        AMIbuilds = client.getAllAMIBuilds()
        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'newId')

        self.failUnlessEqual(AMIbuilds['ami-00000006']['role'],
                '')

        # remove EC2 credentials to the admin user
        client.setEC2CredentialsForUser(data['adminId'], 'newId',
            'newPublicKey', 'newSecretKey', False)

        AMIbuilds = client.getAllAMIBuilds()
        self.failUnlessEqual(AMIbuilds['ami-00000006']['awsAccountNumber'],
                'newId')

        # now add admin as a developer to the build's project
        client.removeEC2CredentialsForUser(data['adminId'])
        bld = client.getBuild(AMIbuilds['ami-00000006']['buildId'])
        prj = client.getProject(bld.getProjectId())
        prj.addMemberById(data['adminId'], userlevels.DEVELOPER)
        AMIbuilds = client.getAllAMIBuilds()
        self.failUnlessEqual(AMIbuilds['ami-00000006']['role'],
                'Product Developer')

    @fixtures.fixture("EC2")
    def testAMIBuildsDataVisibilityDeveloper(self, db, data):
        client = self.getClient('developer')
        amiIds = client.getAllAMIBuilds().keys()
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
        amiIds = client.getAllAMIBuilds().keys()
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
        amiIds = client.getAllAMIBuilds().keys()
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
        amiIds = client.getAllAMIBuilds()
        self.failUnlessEqual(len(amiIds), 7, 'admin should see everything')

    @fixtures.fixture("Empty")
    def testAMIBuildsData(self, db, data):
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
        client = self.getClient("admin")
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
        client = self.getClient("admin")
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

        oldresetLaunchPermissions = ec2.EC2Wrapper.resetLaunchPermissions
        ec2.EC2Wrapper.resetLaunchPermissions = resetLaunchPermissions
        oldaddPublicLaunchPermission = ec2.EC2Wrapper.addPublicLaunchPermission
        ec2.EC2Wrapper.addPublicLaunchPermission = addPublicLaunchPermission
        oldremovePublicLaunchPermission = ec2.EC2Wrapper.removePublicLaunchPermission
        ec2.EC2Wrapper.removePublicLaunchPermission = removePublicLaunchPermission
        oldaddLaunchPermission = ec2.EC2Wrapper.addLaunchPermission
        ec2.EC2Wrapper.addLaunchPermission = addLaunchPermission

        try:
            # Set some aws creds for the user
            devclient.setEC2CredentialsForUser(data['developerId'], 'devid',
                                                'devPublicKey',
                                                'secretKey', False)
            # Set some aws creds for the user
            sodevclient.setEC2CredentialsForUser(data['someOtherDeveloperId'], 'sodevid',
                                                'sodevPublicKey',
                                                'secretKey', False)
             
            reset()
            pubReleases = client.getPublishedReleaseList()
            for pubRelease in pubReleases:
                if pubRelease[1] == 'testproject':
                    id = pubRelease[2].id
            client.unpublishPublishedRelease(id)
            self.assertTrue(self.removePublicLaunchPermissionCalled)
            self.assertEquals(2, len(self.launchPermissions))
            self.assertTrue(('ami-00000003', 'devid') in self.launchPermissions)
            self.assertTrue(('ami-00000003', 'sodevid') in self.launchPermissions)
            reset()

        finally:
            ec2.EC2Wrapper.resetLaunchPermissions = oldresetLaunchPermissions
            ec2.EC2Wrapper.addPublicLaunchPermission = oldaddPublicLaunchPermission
            ec2.EC2Wrapper.removePublicLaunchPermission = oldremovePublicLaunchPermission
            ec2.EC2Wrapper.addLaunchPermission = oldaddLaunchPermission
          

if __name__ == '__main__':
    testsuite.main()
