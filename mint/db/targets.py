#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

from mint import mint_error
from mint.lib import database
import simplejson

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
        cu = cu.execute("INSERT INTO Targets (targetType, targetName) VALUES(?, ?)", targetType, targetName)
        self.db.commit()
        return cu.lastid()

    def getTargetId(self, targetType, targetName, default = -1):
        cu = self.db.cursor()
        cu.execute("""SELECT targetId FROM Targets WHERE targetType=?
                AND targetName=?""", targetType, targetName)
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
            value = simplejson.dumps(value)
            cu.execute("INSERT INTO TargetData VALUES(?, ?, ?)",
                    targetId, name, value)
        self.db.commit()

    def getTargetData(self, targetId):
        cu = self.db.cursor()
        cu.execute("SELECT name, value FROM TargetData WHERE targetId=?",
                targetId)
        res = {}
        for name, value in cu.fetchall():
            res[name] = simplejson.loads(value)
        return res

    def deleteTargetData(self, targetId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM TargetData WHERE targetId=?", targetId)
        self.db.commit()
