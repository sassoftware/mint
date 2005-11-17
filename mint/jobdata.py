#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import database

class JobDataTable(database.DatabaseTable):
    name = "JobData"

    createSQL = """
        CREATE TABLE JobData (
            jobId   INTEGER,
            name    CHAR(64),
            value   TEXT,
            PRIMARY KEY(jobId, name)
        );
    """
    
    fields = ['jobId', 'name', 'value']

    def setJobDataValue(self, jobId, name, value):
        cu = self.db.cursor()
        self.db.transaction(None)
        try:
            cu.execute("DELETE FROM JobData WHERE jobId=? AND name=?", jobId, name)
            cu.execute("INSERT INTO JobData (jobId, name, value) VALUES(?, ?, ?)", jobId, name, value)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    def getJobDataValue(self, jobId, name):
        cu = self.db.cursor()
        cu.execute("SELECT value FROM JobData WHERE jobId=? AND name=?", jobId, name)
        res = cu.fetchone()
        if not res:
            return None
        return res[0]

    def getJobDataDict(self, jobId):
        cu = self.db.cursor()
        cu.execute("SELECT name, value FROM JobData WHERE jobId=?", jobId)
        dataDict = {}
        for name, value in cu.fetchall():
            dataDict[name] = value
        return dataDict
