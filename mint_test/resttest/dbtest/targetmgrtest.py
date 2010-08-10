#!/usr/bin/python
import testsetup
from testutils import mock

from conary.lib import cfgtypes

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint.lib import data

from mint.rest import errors
from mint.rest.db import targetmgr

from mint_test import mint_rephelp

class TargetManagerTest(mint_rephelp.MintDatabaseHelper):
    def _newTarget(self, targetType=None, targetName=None, targetData=None):
        targetType = targetType or 'ec2'
        targetName = targetName or 'eww-west-1'
        ntargetData = dict(
            ec2AccountId = '1234',
            ec2PublicKey = 'Public Key',
            ec2PrivateKey = 'Private Key',
            ec2LaunchUsers = ['admin', 'JeanValjean'],
            ec2S3Bucket = 'bukit',
        )
        if targetData:
            ntargetData.update(targetData)

        db = self.openMintDatabase(createRepos=False)
        db.targetMgr.addTarget(targetType, targetName, ntargetData)
        db.commit()
        return targetType, targetName, ntargetData

    def _newUserCredentials(self):
        credentials = dict(accountId = '314159',
            publicAccessKeyId = 'public access key id',
            secretAccessKey = 'secret access key',)
        return credentials

    def testGetTargetData(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)

        targetType, targetName, targetData = self._newTarget()

        targetType2, targetName2, targetData2 = self._newTarget("vmware", "eeeek")

        self.failUnlessEqual(
            db.targetMgr.getTargetData(targetType, targetName),
            targetData)

        # Make sure you can't add a target twice
        e = self.failUnlessRaises(errors.mint_error.TargetExists,
            db.targetMgr.addTarget, targetType, targetName, targetData)
        self.failUnlessEqual(str(e),
            "Target named 'eww-west-1' of type 'ec2' already exists")

        db.targetMgr.deleteTarget(targetType, targetName)
        self.failUnlessEqual(
            db.targetMgr.getTargetData(targetType, targetName), {})

        # Make sure that the second target is still accessible
        self.failUnlessEqual(
            db.targetMgr.getTargetData(targetType2, targetName2),
            targetData2)

    def testGetTargetCredentialsForUser(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        userName = 'JeanValjean'
        self.createUser(userName, admin = False)
        self.createProduct('foo', owners=['admin'], db=db)

        tmgr = db.targetMgr

        targetType, targetName, targetData = self._newTarget()
        credentials = self._newUserCredentials()
        tmgr.setTargetCredentialsForUser(targetType, targetName, userName,
            credentials)

        self.failUnlessEqual(
            tmgr.getTargetCredentialsForUser(targetType, targetName, userName),
            credentials)

        userId = db.userMgr.getUserId(userName)

        self.failUnlessEqual(
            tmgr.getTargetCredentialsForUserId(targetType, targetName, userId),
            credentials)

        tmgr.deleteTargetCredentialsForUserId(targetType, targetName, userId)
        self.failUnlessEqual(
            tmgr.getTargetCredentialsForUser(targetType, targetName, userName),
            {})

        e = self.failUnlessRaises(errors.mint_error.IllegalUsername,
            tmgr.setTargetCredentialsForUser, targetType, targetName,
            "nosuchuser", credentials)
        self.failUnlessEqual(str(e), "nosuchuser")

        e = self.failUnlessRaises(errors.mint_error.TargetMissing,
            tmgr.setTargetCredentialsForUser, targetType, targetName + "-blah",
            userName, credentials)
        self.failUnlessEqual(str(e),
            "Target named 'eww-west-1-blah' of type 'ec2' does not exist")


    def testGetEC2AccountNumbersForProductUsers(self):
        userName1 = 'JeanValjean'
        userName2 = 'Cosette'
        userName3 = 'Javert'

        userMap = [
            (userName1, '31415'),
            (userName2, '8675309'),
            (userName3, '5551234'),
        ]

        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        for userName, accountId in userMap:
            self.createUser(userName, admin = False)
        prodId = self.createProduct('foo', owners=['admin'],
            developers = [userName1], users=[userName2], db=db)

        tmgr = db.targetMgr

        targetType, targetName, targetData = self._newTarget(
            targetName = 'aws')
        credentials = self._newUserCredentials()
        for userName, accountId in userMap:
            credentials['accountId'] = accountId
            tmgr.setTargetCredentialsForUser(targetType, targetName, userName,
                credentials)

        ret = tmgr.getEC2AccountNumbersForProductUsers(prodId)

        self.failUnlessEqual(ret, (['31415'], ['8675309']))

    def testGetConfiguredTargetsByType(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        userName = 'JeanValjean'
        self.createUser(userName, admin = False)
        self.createProduct('foo', owners=['admin'], db=db)

        targets = [
            ('type1', 'name1', dict(data = '11')),
            ('type1', 'name2', dict(data = '12')),
            ('type2', 'nameXXX', dict(data = '21')),
        ]
        tmgr = db.targetMgr
        for targetType, targetName, targetData in targets:
            tmgr.addTarget(targetType, targetName, targetData)
        self.failUnlessEqual(db.targetMgr.getConfiguredTargetsByType('type1'),
            dict((x[1], x[2]) for x in targets if x[0] == 'type1'))
        self.failUnlessEqual(db.targetMgr.getConfiguredTargetsByType('type2'),
            dict((x[1], x[2]) for x in targets if x[0] == 'type2'))

    def testGetTargetsForUser(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        userName = 'JeanValjean'
        self.createUser(userName, admin = False)
        self.createProduct('foo', owners=['admin'], db=db)

        # XXX Replace nameXXX with name1 when RBL-5898 is fixed
        targets = [
            ('type1', 'name1', dict(data = '11')),
            ('type1', 'name2', dict(data = '12')),
            ('type2', 'nameXXX', dict(data = '21')),
        ]
        userCreds = {
            ('type1', 'name1') : dict(userdata = '11'),
            ('type1', 'name2') : dict(userdata = '12'),
        }

        tmgr = db.targetMgr
        for targetType, targetName, targetData in targets:
            tmgr.addTarget(targetType, targetName, targetData)
            if (targetType, targetName) in userCreds:
                tmgr.setTargetCredentialsForUser(targetType, targetName,
                    userName, userCreds[(targetType, targetName)])

        self.failUnlessEqual(tmgr.getTargetsForUser('type2', userName),
            [('nameXXX', dict(data = '21'), {})])

        self.failUnlessEqual(tmgr.getTargetsForUser('type1', userName),
            [ ('name1', dict(data = '11'), userCreds[('type1', 'name1')]),
              ('name2', dict(data = '12'), userCreds[('type1', 'name2')])])

        self.failUnlessEqual(tmgr.getTargetsForUsers('type1'), [
            (2, userName, 'name1', dict(data = '11'),
                userCreds[('type1', 'name1')]),
            (2, userName, 'name2', dict(data = '12'),
                userCreds[('type1', 'name2')]),
        ])

testsetup.main()
