#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import base64
import simplejson
import logging

from mint import mint_error
from mint.rest.db import manager

log = logging.getLogger(__name__)

class TargetManager(manager.Manager):
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

    def deleteTarget(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Targets WHERE targetType=? AND targetName=?",
            targetType, targetName)
        self.db.commit()

    def _addTarget(self, targetType, targetName):
        cu = self.db.cursor()
        targetId = self.getTargetId(targetType, targetName)
        if targetId:
            raise mint_error.TargetExists( \
                    "Target named '%s' of type '%s' already exists",
                    targetName, targetType)
        cu.execute("INSERT INTO Targets (targetType, targetName) VALUES(?, ?)", targetType, targetName)
        self.db.commit()
        return cu.lastid()

    def _addTargetData(self, targetId, targetData):
        cu = self.db.cursor()
        # perhaps check the id to be certain it's unique
        for name, value in targetData.iteritems():
            value = simplejson.dumps(value)
            cu.execute("INSERT INTO TargetData VALUES(?, ?, ?)",
                    targetId, name, value)
        self.db.commit()

    def getTargetData(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT td.name, td.value
              FROM Targets
              JOIN TargetData AS td USING (targetId)
             WHERE targetType = ? AND targetName = ?
        """, targetType, targetName)
        res = {}
        return dict((k, self._stripUnicode(simplejson.loads(v)))
            for (k, v) in cu)

    @classmethod
    def _stripUnicode(cls, value):
        if hasattr(value, 'encode'):
            return value.encode('ascii')
        return value

    def getConfiguredTargetsByType(self, targetType):
        cu = self.db.cursor()
        cu.execute("""
            SELECT Targets.targetName, TargetData.name, TargetData.value
              FROM Targets
              JOIN TargetData USING (targetId)
             WHERE Targets.targetType = ?
        """, targetType)
        ret = {}
        for targetName, key, value in cu:
            ret.setdefault(targetName, {})[key] = self._stripUnicode(
                simplejson.loads(value))
        return ret

    def getTargetsForUser(self, targetType, userName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT Targets.targetName,
                   TargetUserCredentials.name, TargetUserCredentials.value
              FROM Targets
         LEFT JOIN TargetUserCredentials USING (targetId)
              JOIN Users USING (userId)
             WHERE Targets.targetType = ?
               AND Users.username = ?
        """, targetType, userName)
        userCreds = {}
        for targetName, key, value in cu:
            d = userCreds.setdefault(targetName, {})
            if key is not None:
                d[key] = base64.b64decode(value)
        targetConfig = self.getConfiguredTargetsByType(targetType)
        ret = []
        for targetName, cfg in sorted(targetConfig.items()):
            ret.append((targetName, cfg, userCreds.get(targetName, {})))
        return ret

    def setTargetCredentialsForUser(self, targetType, targetName, userName,
                                    credentials):
        userId = self.getUserId(userName)
        if userId is None:
            raise mint_error.IllegalUsername(userName)
        return self.setTargetCredentialsForUserId(targetType, targetName,
            userId, credentials)

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
        data = [ (targetId, userId, k, base64.b64encode(v))
            for (k, v) in credentials.items() ]
        cu.executemany("""
            INSERT INTO TargetUserCredentials (targetId, userId, name, value)
            VALUES (?, ?, ?, ?)""", data)
        self.db.commit()

    def getTargetCredentialsForUser(self, targetType, targetName, userName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT creds.name, creds.value
              FROM Users
              JOIN TargetUserCredentials AS creds USING (userId)
              JOIN Targets USING (targetId)
             WHERE Targets.targetType = ?
               AND Targets.targetName = ?
               AND Users.username = ?
        """, targetType, targetName, userName)
        return self._extractUserCredentials(cu)

    def getTargetCredentialsForUserId(self, targetType, targetName, userId):
        cu = self.db.cursor()
        cu.execute("""
            SELECT creds.name, creds.value
              FROM TargetUserCredentials AS creds
              JOIN Targets USING (targetId)
             WHERE Targets.targetType = ?
               AND Targets.targetName = ?
               AND creds.userId = ?
        """, targetType, targetName, userId)
        return self._extractUserCredentials(cu)

    def _extractUserCredentials(self, cu):
        ret = {}
        for name, value in cu:
            ret[name] = base64.b64decode(value)
        return ret

    def _deleteTargetCredentials(self, targetId, userId):
        cu = self.db.cursor()
        cu.execute(
            "DELETE FROM TargetUserCredentials WHERE targetId=? AND userId=?",
            targetId, userId)

    def deleteTargetCredentialsForUserId(self, targetType, targetName, userId):
        targetId = self.getTargetId(targetType, targetName)
        self._deleteTargetCredentials(targetId, userId)

    def getEC2AccountNumbersForProductUsers(self, productId):
        return self.db.db.projectUsers.getEC2AccountNumbersForProjectUsers(productId)
