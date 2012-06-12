#
# Copyright (c) 2008-2010 rPath, Inc.
#
# All Rights Reserved
#

import json

from mint import mint_error
from mint.lib import database

class TargetsTable(database.KeyedTable):
    name = 'Targets'
    key = 'targetId'

    fields = ('targetId', 'targetType', 'targetName')

    def addTarget(self, targetType, targetName):
        cu = self.db.cursor()
        targetId = self.getTargetId(targetType, targetName, None)
        if targetId:
            raise mint_error.TargetExists( \
                    "Target named '%s' of type '%s' already exists",
                    targetName, targetType)
        targetTypeId = self.getTargetTypeId(targetType)
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

    def getTargetTypeId(self, targetType):
        cu = self.db.cursor()
        cu.execute("SELECT target_type_id FROM target_types WHERE name=?",
            targetType)
        row = cu.fetchone()
        if row:
            return row[0]
        raise mint_error.TargetMissing(
                "Target type '%s' does not exist", targetType)

    def getTargetId(self, targetType, targetName, default = -1):
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
        if default == -1:
            raise mint_error.TargetMissing("No target named '%s' of type '%s'",
                    targetName, targetType)
        return default

    def deleteTarget(self, targetId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Targets WHERE targetId=?", targetId)
        self.db.commit()

class TargetDataTable(database.DatabaseTable):
    name = 'TargetData'

    fields = ('targetId', 'name', 'value')

    def addTargetData(self, targetId, targetData):
        cu = self.db.cursor()
        # perhaps check the id to be certain it's unique
        for name, value in targetData.iteritems():
            value = json.dumps(value)
            cu.execute("INSERT INTO TargetData (targetId, name, value) VALUES(?, ?, ?)",
                    targetId, name, value)
        self.db.commit()

    def getTargetData(self, targetId):
        cu = self.db.cursor()
        cu.execute("SELECT name, value FROM TargetData WHERE targetId=?",
                targetId)
        res = {}
        for name, value in cu.fetchall():
            v = json.loads(value)
            if isinstance(v, unicode):
                v = v.encode("ascii")
            res[name] = v
        return res

    def deleteTargetData(self, targetId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM TargetData WHERE targetId=?", targetId)
        self.db.commit()
