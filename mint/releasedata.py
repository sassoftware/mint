#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

import database
import sqlite3

(RDT_STRING,
     RDT_BOOL,
     RDT_INT)= range(3)

class ReleaseDataTable(database.DatabaseTable):
    name = "ReleaseData"

    createSQL = """
        CREATE TABLE ReleaseData(
                                 releaseId INTEGER,
                                 name TEXT,
                                 value TEXT,
                                 dataType INTEGER,
                                 PRIMARY KEY(releaseId, name)
                                 );
    """
    
    fields = ['releaseId', 'name', 'value', 'dataType']

    def setReleaseDataValue(self, releaseId, name, value, dataType):
        cu = self.db.cursor()
        self.db._begin()

        #do any data conversions necessary to safely store value as a string
        if dataType == RDT_BOOL:
            value=str(int(value))
        elif dataType == RDT_INT:
            value=str(value)

        cu.execute("INSERT OR REPLACE INTO ReleaseData (releaseId, name, value, dataType) VALUES(?, ?, ?, ?)",
                   (releaseId, name, value, dataType))
        self.db.commit()
        return True

    def getReleaseDataValue(self, releaseId, name):
        cu = self.db.cursor()
        r = cu.execute("SELECT value, dataType FROM ReleaseData WHERE releaseId=? AND name=?", (releaseId, name))
        res = r.fetchall()
        if len(res) != 1:
            if len(res) == 0:
                raise NotFoundError
            else:
                raise MultipleFoundError
        value, dataType = res[0]
        if dataType == RDT_BOOL:
            value=bool(int(value))
        elif dataType == RDT_INT:
            value=int(value)
        return value

    def getReleaseDataDict(self, releaseId):
        cu = self.db.cursor()
        r = cu.execute("SELECT name, value, dataType FROM ReleaseData WHERE releaseId=?", releaseId)
        dataDict = {}
        for name, value, dataType in r.fetchall():
            if dataType == RDT_BOOL:
                value=bool(int(value))
            elif dataType == RDT_INT:
                value=int(value)
            dataDict[name] = value
        return dataDict
