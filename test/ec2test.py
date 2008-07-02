#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time
import tempfile

import boto
import boto.ec2
from boto.exception import EC2ResponseError

from mint import ec2
from mint.mint_error import *

from mint.helperfuncs import toDatabaseTimestamp, fromDatabaseTimestamp, buildEC2AuthToken
from conary.lib import util

import fixtures

FAKE_PUBLIC_KEY  = '123456789ABCDEFGHIJK'
FAKE_PRIVATE_KEY = '123456789ABCDEFGHIJK123456789ABCDEFGHIJK'

FAKE_PUBLIC_KEY2  = '987654321ABCDEFGHIJK'
FAKE_PRIVATE_KEY2 = '987654321ABCDEFGHIJK123456789ABCDEFGHIJK'

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

        # five blessed AMIs set up by the fixture
        self.failUnlessEqual([1, 2, 3, 4, 5], \
                [x.id for x in client.getAvailableBlessedAMIs()])

        # Now take one out of the pool and make sure it worked
        blessedAMI = client.getBlessedAMI(1)
        blessedAMI.buildId = None
        blessedAMI.isAvailable = False
        blessedAMI.save()

        self.failUnlessEqual([2, 3, 4, 5], \
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
        self.assertRaises(ItemNotFound, client.getBlessedAMI, 1)

    @fixtures.fixture("Empty")
    def testGetNonexistentLaunchedAMI(self, db, data):
        client = self.getClient("admin")
        self.assertRaises(ItemNotFound, client.getLaunchedAMI, 1)

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
            except ec2.TooManyAMIInstancesPerIP:
                self.fail()

        # this should not fail
        #try:
        #    client.launchAMIInstance(amiIds[0])
        #except ec2.TooManyAMIInstancesPerIP:
        #    self.fail()

        # but this should
        self.assertRaises(ec2.TooManyAMIInstancesPerIP,
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

        self.assertRaises(ec2.FailedToLaunchAMIInstance,
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
        
    @fixtures.fixture("EC2")
    def testGetAMIKeyPairs(self, db, data):
        client = self.getClient("admin")

        # test getting all
        pairs = client.getAMIKeyPairs(buildEC2AuthToken(self.cfg), [])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key'), 
            ('key2', '2f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'another RSA private key')])
        
        # test getting 1
        pairs = client.getAMIKeyPairs(buildEC2AuthToken(self.cfg), ['key1'])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key')])
        
        # test getting multiple
        pairs = client.getAMIKeyPairs(buildEC2AuthToken(self.cfg), ['key1', 'key2'])
        self.assertTrue(pairs == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key'), 
            ('key2', '2f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'another RSA private key')])
        
    @fixtures.fixture("EC2")
    def testGetAMIKeyPair(self, db, data):
        client = self.getClient("admin")

        # test getting all
        pair = client.getAMIKeyPair(buildEC2AuthToken(self.cfg), 'key1')
        self.assertTrue(pair == [
            ('key1', '1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f', 
             'some RSA private key')])

if __name__ == '__main__':
    testsuite.main()
