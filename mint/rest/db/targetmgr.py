#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import json
import logging
import subprocess

from mint import mint_error
from mint.lib import data as mintdata
from mint.rest.db import manager

log = logging.getLogger(__name__)

class TargetManager(manager.Manager):
    TargetImportScriptPath = '/usr/share/rbuilder/scripts/target-systems-import'
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

    def _addTarget(self, targetType, targetName):
        cu = self.db.cursor()
        targetId = self.getTargetId(targetType, targetName)
        if targetId:
            raise mint_error.TargetExists( \
                    "Target named '%s' of type '%s' already exists",
                    targetName, targetType)
        cu.execute("INSERT INTO Targets (targetType, targetName) VALUES(?, ?)", targetType, targetName)
        return cu.lastid()

    def _addTargetData(self, targetId, targetData):
        cu = self.db.cursor()
        # perhaps check the id to be certain it's unique
        for name, value in targetData.iteritems():
            value = json.dumps(value)
            cu.execute("INSERT INTO TargetData VALUES(?, ?, ?)",
                    targetId, name, value)

    def getTargetData(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT td.name, td.value
              FROM Targets
              JOIN TargetData AS td USING (targetId)
             WHERE targetType = ? AND targetName = ?
        """, targetType, targetName)
        return dict((k, self._stripUnicode(json.loads(v)))
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
                json.loads(value))
        return ret

    def getTargetsForUser(self, targetType, userName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT Targets.targetName,
                   tc.credentials
              FROM Targets
              JOIN TargetUserCredentials AS tuc USING (targetId)
              JOIN Users USING (userId)
              JOIN TargetCredentials AS tc ON
                  (tuc.targetCredentialsId=tc.targetCredentialsId)
             WHERE Targets.targetType = ?
               AND Users.username = ?
        """, targetType, userName)
        userCreds = {}
        for targetName, creds in cu:
            userCreds[targetName] = mintdata.unmarshalTargetUserCredentials(creds)
        targetConfig = self.getConfiguredTargetsByType(targetType)
        ret = []
        for targetName, cfg in sorted(targetConfig.items()):
            ret.append((targetName, cfg, userCreds.get(targetName, {})))
        return ret

    def getTargetsForUsers(self, targetType):
        targetConfigs = self.getConfiguredTargetsByType(targetType)
        cu = self.db.cursor()
        cu.execute("""
            SELECT Targets.targetName,
                   tc.credentials,
                   tc.targetCredentialsId,
                   Users.username,
                   Users.userId
              FROM Targets
              JOIN TargetUserCredentials AS tuc USING (targetId)
              JOIN Users USING (userId)
              JOIN TargetCredentials AS tc ON
                  (tuc.targetCredentialsId=tc.targetCredentialsId)
             WHERE Targets.targetType = ?
             ORDER BY Users.userId, targetName
        """, targetType)
        ret = []
        for targetName, creds, credsId, userName, userId in cu:
            userCredentials = mintdata.unmarshalTargetUserCredentials(creds)
            targetCfg = targetConfigs.get(targetName)
            if targetCfg is None:
                continue
            ret.append((userId, userName, targetName, credsId, targetCfg,
                userCredentials))
        return ret

    def getUniqueTargetsForUsers(self, targetType):
        """
        From all configured targets (of this type), for all users that have
        added credentials for them, return just one representative user
        Return list of
            (userId, userName, targetName, userCredsId, cfg, userCredentials)
        """
        cmap = {}
        data = self.getTargetsForUsers(targetType)
        for ent in data:
            (uId, uName, tName, uCredsId, cfg, uCredentials) = ent
            cmap[(tName, uCredsId)] = ent
        return sorted(cmap.values())

    def importTargetSystems(self, targetType, targetName):
        log.info('Importing systems for target %s.' % targetName)
        cmd = [ self.TargetImportScriptPath ]
        subprocess.Popen(cmd)

    def linkTargetImageToImage(self, targetType, targetName, fileId,
            targetImageId):
        targetId = self.getTargetId(targetType, targetName)
        if targetId is None:
            raise mint_error.TargetMissing(
                    "Target named '%s' of type '%s' does not exist",
                    targetName, targetType)
        return self._linkTargetImageToImage(targetId, fileId, targetImageId)

    def _linkTargetImageToImage(self, targetId, fileId, targetImageId):
        cu = self.db.cursor()
        # XXX Make sure we don't insert duplicates - but this query angers
        # the postgres bindings
        ("""INSERT INTO TargetImagesDeployed
            (targetId, fileId, targetImageId)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM TargetImagesDeployed
                    WHERE targetId = ? AND fileId = ? AND targetImageId = ?)""",
            targetId, fileId, targetImageId, targetId, fileId, targetImageId)
        cu.execute("""INSERT INTO TargetImagesDeployed
            (targetId, fileId, targetImageId)
            VALUES (?, ?, ?)""", targetId, fileId, targetImageId)

    def setTargetCredentialsForUser(self, targetType, targetName, userName,
                                    credentials):
        userId = self.getUserId(userName)
        if userId is None:
            raise mint_error.IllegalUsername(userName)
        self.setTargetCredentialsForUserId(targetType, targetName,
            userId, credentials)
        if self.db.auth.isAdmin:
            self.importTargetSystems(targetType, targetName)

    def setTargetCredentialsForUserId(self, targetType, targetName, userId,
            credentials):
        targetId = self.getTargetId(targetType, targetName)
        if targetId is None:
            raise mint_error.TargetMissing(
                    "Target named '%s' of type '%s' does not exist",
                    targetName, targetType)
        return self._setTargetCredentialsForUser(targetId, userId, credentials)

    @classmethod
    def _getCredentialsId(cls, cu, credentials):
        cu.execute("""
            SELECT targetCredentialsId
              FROM TargetCredentials
             WHERE credentials = ?""", credentials)
        row = cu.fetchone()
        if row:
            return row[0]
        return None

    @classmethod
    def _pruneTargetCredentials(cls, cu):
        cu.execute("""
            DELETE FROM TargetCredentials
             WHERE targetCredentialsId not in (
                SELECT targetCredentialsId
                  FROM TargetUserCredentials)
        """)

    def _setTargetCredentialsForUser(self, targetId, userId, credentials):
        self._deleteTargetCredentials(targetId, userId)
        cu = self.db.cursor()
        # Newline-separated credential fields
        data = mintdata.marshalTargetUserCredentials(credentials)
        targetCredentialsId = self._getCredentialsId(cu, data)
        if targetCredentialsId is None:
            cu.execute("INSERT INTO TargetCredentials (credentials) VALUES (?)",
                data)
            targetCredentialsId = self._getCredentialsId(cu, data)
        cu.execute("""
            INSERT INTO TargetUserCredentials
                (targetId, userId, targetCredentialsId)
            VALUES (?, ?, ?)""", targetId, userId, targetCredentialsId)
        self._pruneTargetCredentials(cu)

    def getTargetCredentialsForUser(self, targetType, targetName, userName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT creds.credentials
              FROM Users
              JOIN TargetUserCredentials USING (userId)
              JOIN TargetCredentials AS creds USING (targetCredentialsId)
              JOIN Targets ON
                (Targets.targetId=TargetUserCredentials.targetId)
             WHERE Targets.targetType = ?
               AND Targets.targetName = ?
               AND Users.username = ?
        """, targetType, targetName, userName)
        return self._extractUserCredentialsFromCursor(cu)

    def getTargetCredentialsForUserId(self, targetType, targetName, userId):
        cu = self.db.cursor()
        cu.execute("""
            SELECT creds.credentials
              FROM TargetCredentials AS creds
              JOIN TargetUserCredentials AS uc USING (targetCredentialsId)
              JOIN Targets USING (targetId)
             WHERE Targets.targetType = ?
               AND Targets.targetName = ?
               AND uc.userId = ?
        """, targetType, targetName, userId)
        return self._extractUserCredentialsFromCursor(cu)

    def _extractUserCredentialsFromCursor(self, cu):
        row = cu.fetchone()
        if not row:
            return {}
        return mintdata.unmarshalTargetUserCredentials(row[0])

    def _deleteTargetCredentials(self, targetId, userId):
        cu = self.db.cursor()
        cu.execute(
            "DELETE FROM TargetUserCredentials WHERE targetId=? AND userId=?",
            targetId, userId)
        self._pruneTargetCredentials(cu)

    def deleteTargetCredentialsForUserId(self, targetType, targetName, userId):
        targetId = self.getTargetId(targetType, targetName)
        self._deleteTargetCredentials(targetId, userId)

    def getEC2AccountNumbersForProductUsers(self, productId):
        return self.db.db.projectUsers.getEC2AccountNumbersForProjectUsers(productId)
