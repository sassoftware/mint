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

    def getTargetTypeId(self, targetType):
        cu = self.db.cursor()
        cu.execute("SELECT target_type_id FROM target_types WHERE name=?",
            targetType)
        row = cu.fetchone()
        if row:
            return row[0]

    def getTargetId(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT targetId
              FROM Targets AS t
              JOIN target_types AS tt USING (target_type_id)
             WHERE tt.name = ?
               AND t.name=?""", targetType, targetName)
        res = cu.fetchone()
        if res:
            return res[0]

    def addTarget(self, targetType, targetName, targetData):
        targetId = self._addTarget(targetType, targetName)
        self._addTargetData(targetId, targetData)
        self._addTargetQuerySet(targetId, targetName, targetType)

    def deleteTarget(self, targetType, targetName):
        targetTypeId = self.getTargetTypeId(targetType)
        if targetTypeId is None:
            return
        cu = self.db.cursor()
        cu.execute("DELETE FROM Targets WHERE target_type_id=? AND name=?",
            targetTypeId, targetName)

    def _addTarget(self, targetType, targetName):
        cu = self.db.cursor()
        targetTypeId = self.getTargetTypeId(targetType)
        if targetTypeId is None:
            raise mint_error.TargetMissing(
                    "Target type '%s' does not exist", targetType)
        targetId = self.getTargetId(targetType, targetName)
        if targetId:
            raise mint_error.TargetExists( \
                    "Target named '%s' of type '%s' already exists",
                    targetName, targetType)
        zoneId = self.getLocalZone()
        cu.execute("INSERT INTO Targets (target_type_id, name, description, zone_id) VALUES(?, ?, ?, ?)",
            targetTypeId, targetName, targetName, zoneId)
        self.db.commit()
        return cu.lastid()

    def getLocalZone(self):
        cu = self.db.cursor()
        cu.execute("SELECT zone_id FROM inventory_zone WHERE name = ?",
            "Local rBuilder")
        row = cu.fetchone()
        if row:
            return row[0]
        raise mint_error.ServerError("Local zone not found")

    def _addTargetData(self, targetId, targetData):
        cu = self.db.cursor()
        # perhaps check the id to be certain it's unique
        for name, value in targetData.iteritems():
            value = json.dumps(value)
            cu.execute("INSERT INTO TargetData (targetId, name, value) VALUES(?, ?, ?)",
                    targetId, name, value)

    def _addTargetQuerySet(self, targetId, targetName, targetType):
        # Ideally we would like to handle this from django, but once we
        # add the target in restlib, the db is locked, so django can't
        # do anything

        querySetName = "All %s systems (%s)" % (targetName, targetType)

        cu = self.db.cursor()

        cu.execute("SELECT query_set_id FROM querysets_queryset WHERE name=?",
            querySetName)
        rows = cu.fetchall()
        if not rows:
            log.info("Creating a new query set for target %s." % targetName)
            cu.execute("""
                INSERT INTO querysets_queryset
                (name, description, resource_type, created_date, modified_date)
                VALUES (?, ?, ?, current_timestamp, current_timestamp)""",
                querySetName, querySetName, 'system')
            querySetId = cu.lastrowid
        else:
            log.info("Already a query set named %s, not creating a new one." %
                querySetName)
            querySetId = rows[0][0]

        feField = 'target.target_id'
        feOperator = 'EQUAL'
        feValue = str(targetId)
        cu.execute("""SELECT filter_entry_id FROM querysets_filterentry
            WHERE field=? AND operator=? AND value=?""",
            feField, feOperator, feValue)
        rows = cu.fetchall()
        if not rows:
            cu.execute("""
                INSERT INTO querysets_filterentry (field, operator, value)
                VALUES (?, ?, ?)""",
                feField, feOperator, feValue)
            filterEntryId = cu.lastrowid
        else:
            filterEntryId = rows[0][0]

        cu.execute("""SELECT * FROM querysets_queryset_filter_entries
            WHERE queryset_id = ? AND filterentry_id = ?""",
            querySetId, filterEntryId)
        if not cu.fetchall():
            cu.execute("""
                INSERT INTO querysets_queryset_filter_entries
                    (queryset_id, filterentry_id)
                VALUES (?, ?)""",
                querySetId, filterEntryId)

    def getTargetData(self, targetType, targetName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT td.name, td.value
              FROM Targets AS t
              JOIN target_types USING (target_type_id)
              JOIN TargetData AS td ON td.targetId = t.targetId
             WHERE target_types.name = ? AND t.name = ?
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
            SELECT t.name AS targetName, t.description AS targetDescription, td.name, td.value
              FROM Targets AS t
              JOIN target_types USING (target_type_id)
              JOIN TargetData AS td ON td.targetId = t.targetId
             WHERE target_types.name = ?
        """, targetType)
        ret = {}
        for targetName, targetDescription, key, value in cu:
            targetConfig = ret.setdefault(targetName, {})
            targetConfig['description'] = targetDescription
            targetConfig[key] = self._stripUnicode(json.loads(value))
        return ret

    def getTargetsForUser(self, targetType, userName):
        cu = self.db.cursor()
        cu.execute("""
            SELECT t.name AS targetName, tc.credentials
              FROM Targets t
              JOIN target_types USING (target_type_id)
              JOIN TargetUserCredentials AS tuc ON tuc.targetId = t.targetId
              JOIN Users USING (userId)
              JOIN TargetCredentials AS tc ON
                  (tuc.targetCredentialsId=tc.targetCredentialsId)
             WHERE target_types.name = ?
               AND Users.username = ?
        """, targetType, userName)
        userCreds = {}
        for targetName, creds in cu:
            userCreds[targetName] = mintdata.unmarshalTargetUserCredentials(
                    self.cfg, creds)
        targetConfig = self.getConfiguredTargetsByType(targetType)
        ret = []
        for targetName, cfg in sorted(targetConfig.items()):
            ret.append((targetName, cfg, userCreds.get(targetName, {})))
        return ret

    def getTargetsForUsers(self, targetType):
        targetConfigs = self.getConfiguredTargetsByType(targetType)
        cu = self.db.cursor()
        cu.execute("""
            SELECT t.name AS targetName,
                   tc.credentials,
                   tc.targetCredentialsId,
                   Users.username,
                   Users.userId
              FROM Targets t
              JOIN target_types USING (target_type_id)
              JOIN TargetUserCredentials AS tuc ON tuc.targetId = t.targetId
              JOIN Users USING (userId)
              JOIN TargetCredentials AS tc ON
                  (tuc.targetCredentialsId=tc.targetCredentialsId)
             WHERE target_types.name = ?
             ORDER BY Users.userId, t.name
        """, targetType)
        ret = []
        for targetName, creds, credsId, userName, userId in cu:
            userCredentials = mintdata.unmarshalTargetUserCredentials(self.cfg,
                    creds)
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
        data = mintdata.marshalTargetUserCredentials(self.cfg, credentials)
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
              JOIN target_types USING (target_type_id)
             WHERE target_types.name = ?
               AND Targets.name = ?
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
              JOIN target_types USING (target_type_id)
             WHERE target_types.name = ?
               AND Targets.name = ?
               AND uc.userId = ?
        """, targetType, targetName, userId)
        return self._extractUserCredentialsFromCursor(cu)

    def _extractUserCredentialsFromCursor(self, cu):
        row = cu.fetchone()
        if not row:
            return {}
        return mintdata.unmarshalTargetUserCredentials(self.cfg, row[0])

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
