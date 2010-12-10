#
# Copyright (c) 2010 rPath, Inc.
#

import os
import json
import time

from conary.lib import util
from mint import mint_error
from mint.lib import data as mintdata
from catalogService import storage

class TargetConversion(object):
    TargetTypes = [ 'ec2', 'vmware', 'vws', 'xen-enterprise' ]

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

        storagePath = os.path.join(self.cfg.dataPath, 'catalog')
        configStoragePath = os.path.join(storagePath, 'configuration')
        credsStoragePath = os.path.join(storagePath, 'credentials')

        self.cfgStore = storage.DiskStorage(
            storage.StorageConfig(storagePath = configStoragePath))
        self.credsStore = storage.DiskStorage(
            storage.StorageConfig(storagePath = credsStoragePath))

        # Back up the data stores
        backupDir = os.path.join(self.cfg.dataPath,
            time.strftime('catalog-migrate-backup-%Y%m%d%H%M%S'))
        if os.path.exists(storagePath):
            util.mkdirChain(backupDir)
            util.copytree(storagePath, backupDir, dirmode = 0700)

    def convertNonEC2(self):
        for targetType in self.TargetTypes:
            if not self.cfgStore.exists(targetType):
                continue
            cfgMap = {}
            credsMap = {}
            for target in self.cfgStore.enumerate(keyPrefix=targetType):
                cfg = dict((x.split(os.sep)[-1], self.cfgStore.get(x))
                    for x in self.cfgStore.enumerate(keyPrefix=target))
                if target == 'ec2/aws' and cfg.pop('enabled', '0') != '1':
                    self.cfgStore.delete(target)
                    continue
                # Add alias/description to EC2 targets
                if target == 'ec2/aws':
                    cfg.setdefault('alias', "ec2")
                    cfg.setdefault('description', "Amazon Elastic Compute Cloud")
                if not cfg:
                    self.cfgStore.delete(target)
                    continue
                # drop target name from list, it's the same as the key
                cfg.pop('name', None)
                # Extract target name
                targetName = target.split(os.sep)[-1]
                cfgMap[targetName] = cfg

                # Get user credentials from credentials store
                for userKey in self.credsStore.enumerate(keyPrefix=targetType):
                    # Extract user name
                    userName = userKey.split(os.sep)[-1]
                    for targetNameKey in self.credsStore.enumerate(keyPrefix=userKey):
                        # Extract target name
                        targetName = targetNameKey.split(os.sep)[-1]
                        creds = dict((x.split(os.sep)[-1], self.credsStore.get(x))
                            for x in self.credsStore.enumerate(keyPrefix=targetNameKey))
                        credsMap.setdefault(targetName, []).append((userName, creds))
                    self.credsStore.delete(userKey)

                # Clean up
                self.cfgStore.delete(target)

            for targetName, targetData in cfgMap.iteritems():
                print "Target type %s, target %s:" % (targetType, targetName)
                self.addTarget(targetType, targetName, targetData)
                for userName, userCreds in credsMap.get(targetName, []):
                    print "    User %s" % userName
                    userId = self.getUserId(userName)
                    if userId is None:
                        continue
                    self.setTargetCredentialsForUserId(
                        targetType, targetName, userId, userCreds)

    def convertEC2(self):
        q = """
            SELECT ud.userId, ud.name, ud.value
              FROM UserData AS ud
             WHERE ud.name IN
                ('awsAccountNumber', 'awsPublicAccessKeyId', 'awsSecretAccessKey')
        """
        cu = self.db.cursor()
        cu.execute(q)
        remap = [
            ('accountId', 'awsAccountNumber'),
            ('publicAccessKeyId', 'awsPublicAccessKeyId'),
            ('secretAccessKey', 'awsSecretAccessKey') ]
        remap = dict((y, x) for (x, y) in remap)
        usersCreds = {}
        dataToDelete = []
        for row in cu:
            userId = row[0]
            nkey = remap[row[1]]
            val = row[2]
            usersCreds.setdefault(userId, {})[nkey] = val
            #dataToDelete.append(dict(userId=row[0], name=row[1], value=row[2]))
            dataToDelete.append((row[0], row[1], row[2]))
        for userId, userCreds in usersCreds.items():
            print "Adding credentials for user ID", userId
            self.setTargetCredentialsForUserId('ec2', 'aws', userId, userCreds)
        # Clean up old data
        q = """DELETE FROM UserData WHERE userId = ? AND name = ? AND VALUE = ?
        """
        if dataToDelete:
            cu.executemany(q, dataToDelete)

    def run(self):
        self.convertNonEC2()
        self.convertEC2()

    def commit(self):
        return self.db.commit()

    def rollback(self):
        return self.db.rollback()

    # This is duplicated code, but we need a snapshot of it
    def getUserId(self, username):
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM Users WHERE username=? AND active=1",
            username)
        for row in cu:
            return row[0]

    def getTargetId(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT targetId FROM Targets
            WHERE targetType = ? AND targetName = ?""", targetType, targetName)
        for row in cu:
            return row[0]

    def addTarget(self, targetType, targetName, targetData):
        targetId = self._addTarget(targetType, targetName)
        self._addTargetData(targetId, targetData)

    def setTargetCredentialsForUserId(self, targetType, targetName, userId,
            credentials):
        targetId = self.getTargetId(targetType, targetName)
        if targetId is None:
            raise mint_error.TargetMissing(
                    "Target named '%s' of type '%s' does not exist",
                    targetName, targetType)
        return self._setTargetCredentialsForUser(targetId, userId, credentials)

    def _setTargetCredentialsForUser(self, targetId, userId, credentials):
        self._deleteTargetCredentials(targetId, userId)
        cu = self.db.cursor()
        data = mintdata.marshalTargetUserCredentials(credentials)
        cu.execute("""
            INSERT INTO TargetUserCredentials (targetId, userId, credentials)
            VALUES (?, ?, ?)""", targetId, userId, data)

    def _addTarget(self, targetType, targetName):
        cu = self.db.cursor()
        targetId = self.getTargetId(targetType, targetName)
        if targetId:
            return targetId
        cu.execute("INSERT INTO Targets (targetType, targetName) VALUES(?, ?)", targetType, targetName)
        return cu.lastid()

    def _addTargetData(self, targetId, targetData):
        cu = self.db.cursor()
        cu.execute("SELECT name FROM TargetData WHERE targetId = ?",
            targetId)
        existingSet = set(x[0] for x in cu)
        # perhaps check the id to be certain it's unique
        for name, value in targetData.iteritems():
            if name in existingSet:
                continue
            value = json.dumps(value)
            cu.execute("INSERT INTO TargetData VALUES(?, ?, ?)",
                    targetId, name, value)

    def _deleteTargetCredentials(self, targetId, userId):
        cu = self.db.cursor()
        cu.execute(
            "DELETE FROM TargetUserCredentials WHERE targetId=? AND userId=?",
            targetId, userId)

if __name__ == '__main__':
    from mint.db import database as mintdb
    from mint import config
    cfg = config.getConfig()
    mintdb = mintdb.Database(cfg)

    conv = TargetConversion(cfg, mintdb.db)
    conv.run()
    conv.rollback()
