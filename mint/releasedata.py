#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

import database

(RDT_STRING,
     RDT_BOOL,
     RDT_INT)= range(3)

class ReleaseDataTable(database.DatabaseTable):
    name = "ReleaseData"

    createSQL = """
        CREATE TABLE ReleaseData(
                                 releaseId INTEGER,
                                 name STR,
                                 value TEXT,
                                 dataType INTEGER,
                                 PRIMARY KEY(releaseId, name)
                                 );
    """
    
    fields = ['releaseId', 'name', 'value', 'dataType']

    def setReleaseDataValue(self, releaseId, name, value, dataType):
        cu = self.db.cursor()

        if self.db.type == "native_sqlite":
            cu.execute("BEGIN")
        else:
            self.db.transaction(None)

        # do any data conversions necessary to safely store value as a string
        if dataType == RDT_BOOL:
            value=str(int(value))
        elif dataType == RDT_INT:
            value=str(value)

        cu.execute("DELETE FROM ReleaseData WHERE releaseId=? AND name=?", releaseId, name)
        cu.execute("INSERT INTO ReleaseData (releaseId, name, value, dataType) VALUES(?, ?, ?, ?)",
                   (releaseId, name, value, dataType))
        self.db.commit()
        return True

    def getReleaseDataValue(self, releaseId, name):
        cu = self.db.cursor()
        cu.execute("SELECT value, dataType FROM ReleaseData WHERE releaseId=? AND name=?", (releaseId, name))
        res = cu.fetchall()
        if len(res) != 1:
            return None
        value, dataType = res[0]
        if dataType == RDT_BOOL:
            value=bool(int(value))
        elif dataType == RDT_INT:
            value=int(value)
        return value

    def getReleaseDataDict(self, releaseId):
        cu = self.db.cursor()
        cu.execute("SELECT name, value, dataType FROM ReleaseData WHERE releaseId=?", releaseId)
        dataDict = {}
        for name, value, dataType in cu.fetchall():
            if dataType == RDT_BOOL:
                value=bool(int(value))
            elif dataType == RDT_INT:
                value=int(value)
            dataDict[name] = value
        return dataDict
