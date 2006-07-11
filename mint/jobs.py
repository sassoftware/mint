#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
from mint import database
from mint.mint_error import MintError

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
                    buildId         INT,
                    groupTroveId    INT,
                    owner           BIGINT,
                    userId          INT,
                    status          INT,
                    statusMessage   TEXT,
                    timeSubmitted   DOUBLE,
                    timeStarted     DOUBLE,
                    timeFinished    DOUBLE)"""

    fields = ['jobId', 'buildId', 'groupTroveId', 'owner', 'userId',
              'status', 'statusMessage', 'timeSubmitted',
              'timeStarted', 'timeFinished']

    indexes = {"JobsBuildIdx": """CREATE INDEX JobsBuildIdx
                                        ON Jobs(buildId)""",
               "JobsGroupTroveIdx": """CREATE INDEX JobsGroupTroveIdx
                                           ON Jobs(groupTroveId)""",
               "JobsUserIdx": "CREATE INDEX JobsUserIdx ON Jobs(userId)"}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 5 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN groupTroveId INT")
            if dbversion == 11 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN owner BIGINT")
            if dbversion == 12 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN timeSubmitted DOUBLE")
            if dbversion == 19:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Jobs ADD COLUMN buildId INT")
                cu.execute('UPDATE Jobs SET buildId = releaseId')
                if self.db.driver == 'mysql':
                    cu.execute("ALTER TABLE Jobs DROP COLUMN releaseId")
                else:
                    cu.execute("DROP TABLE Jobs")
                    cu.execute(self.createSQL % self.db.keywords)
                    cu.execute('DELETE FROM JobData')
            return dbversion >= 19
        return True

    def get(self, id):
        res = database.KeyedTable.get(self, id)
        del res['owner']
        res['status'] = int(res['status'])
        return res

class Job(database.TableObject):
    __slots__ = [JobsTable.key] + JobsTable.fields

    def getItem(self, id):
        return self.server.getJob(id)

    def getId(self):
        return self.id

    def getBuildId(self):
        return self.buildId

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

    def getTimeSubmitted(self):
        return self.timeSubmitted

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

class BuildFilesTable(database.KeyedTable):
    name = 'BuildFiles'
    key = 'fileId'
    createSQL = """
                CREATE TABLE BuildFiles (
                    fileId      %(PRIMARYKEY)s,
                    buildId   INT,
                    idx         INT,
                    filename    CHAR(255),
                    title       CHAR(255) DEFAULT ''
                );"""
    fields = ['fileId', 'buildId', 'idx', 'filename', 'title']

    indexes = {"BuildFilesBuildIdx": """CREATE INDEX BuildFilesBuildIdx
                                              ON BuildFiles(buildId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 1 and not self.initialCreation:
                sql = """ALTER TABLE BuildFiles ADD COLUMN title STR DEFAULT ''"""
                cu = self.db.cursor()
                cu.execute(sql)
            return dbversion >= 1
        return True
