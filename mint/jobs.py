#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import database
from mint_error import MintError

class JobMissing(MintError):
    def __str__(self):
        return "the requested job does not exist"

class FileMissing(MintError):
    def __str__(self):
        return "the requested file does not exist"

class DuplicateJob(MintError):
    def __str__(self):
        return "a conflicting job is already in progress"

class JobsTable(database.KeyedTable):
    name = 'Jobs'
    key = 'jobId'
    createSQL = """
                CREATE TABLE Jobs (
                    jobId           %(PRIMARYKEY)s,
                    releaseId       INT,
                    groupTroveId    INT,
                    owner           BIGINT,
                    userId          INT,
                    status          INT,
                    statusMessage   CHAR(255),
                    timeStarted     DOUBLE,
                    timeFinished    DOUBLE
                )"""

    fields = ['jobId', 'releaseId', 'groupTroveId', 'userId', 'status',
              'statusMessage', 'timeStarted', 'timeFinished']

    indexes = {"JobsReleaseIdx": """CREATE INDEX JobsReleaseIdx
                                        ON Jobs(releaseId)""",
               "JobsGroupTroveIdx": """CREATE INDEX JobsGroupTroveIdx
                                           ON Jobs(groupTroveId)""",
               "JobsUserIdx": "CREATE INDEX JobsUserIdx ON Jobs(userId)"}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 5:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN groupTroveId INT")
                return (dbversion + 1) == self.schemaVersion
            if dbversion == 11:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN owner INT")
                return (dbversion + 1) == self.schemaVersion
        return True

    def get(self, id):
        res = database.get(self, id)
        del(res['owner'])

class Job(database.TableObject):
    __slots__ = [JobsTable.key] + JobsTable.fields

    def getItem(self, id):
        return self.server.getJob(id)

    def getId(self):
        return self.id

    def getReleaseId(self):
        return self.releaseId

    def getGroupTroveId(self):
        return self.groupTroveId

    def getUserId(self):
        return self.userId

    def getStatus(self):
        return self.status

    def getStatusMessage(self):
        return self.statusMessage

    def setStatus(self, status, statusMessage):
        return self.server.setJobStatus(self.id, status, statusMessage)

    def getTimeStarted(self):
        return self.timeStarted

    def getTimeFinished(self):
        return self.timeFinished

    def setDataValue(self, name, value, dataType):
        return self.server.setJobDataValue(self.id, name, value, dataType)

    def getDataValue(self, name):
        isPresent, val = self.server.getJobDataValue(self.getId(), name)
        if not isPresent:
            val = None
        return val

class ImageFilesTable(database.KeyedTable):
    name = 'ImageFiles'
    key = 'fileId'
    createSQL = """
                CREATE TABLE ImageFiles (
                    fileId      %(PRIMARYKEY)s,
                    releaseId   INT,
                    idx         INT,
                    filename    CHAR(255),
                    title       CHAR(255) DEFAULT ''
                );"""
    fields = ['fileId', 'releaseId', 'idx', 'filename', 'title']

    indexes = {"ImageFilesReleaseIdx": """CREATE INDEX ImageFilesReleaseIdx
                                              ON ImageFiles(releaseId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 1:
                sql = """ALTER TABLE ImageFiles ADD COLUMN title STR DEFAULT ''"""
                cu = self.db.cursor()
                cu.execute(sql)
                return (dbversion + 1) == self.schemaVersion
        return True
