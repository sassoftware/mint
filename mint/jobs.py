#
# Copyright (c) 2005 rPath, Inc.
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
        return "the request file does not exist"

class DuplicateJob(MintError):
    def __str__(self):
        return "a conflicting job is already in progress"

class JobsTable(database.KeyedTable):
    name = 'Jobs'
    key = 'jobId'
    createSQL = """
                CREATE TABLE Jobs (
                    jobId           INTEGER PRIMARY KEY,
                    releaseId       INT,
                    userId          INT,
                    status          INT,
                    statusMessage   STR,
                    timeStarted     INT,
                    timeFinished    INT
                )"""
    fields = ['jobId', 'releaseId', 'userId', 'status',
              'statusMessage', 'timeStarted', 'timeFinished']

class Job(database.TableObject):
    __slots__ = [JobsTable.key] + JobsTable.fields
    
    def getItem(self, id):
        return self.server.getJob(id)
    
    def getId(self):
        return self.jobId

    def getReleaseId(self):
        return self.releaseId

    def getUserId(self):
        return self.userId

    def getStatus(self):
        return self.status

    def getStatusMessage(self):
        return self.statusMessage

    def setStatus(self, status, statusMessage):
        return self.server.setJobStatus(self.jobId, status, statusMessage)

    def getTimeStarted(self):
        return self.timeStarted

    def getTimeFinished(self):
        return self.timeFinished

class ImageFilesTable(database.KeyedTable):
    name = 'ImageFiles'
    key = 'fileId'
    createSQL = """
                CREATE TABLE ImageFiles (
                    fileId      INTEGER PRIMARY KEY,
                    releaseId   INT,
                    idx         INT,
                    filename    STR
                );"""
    fields = ['fileId', 'releaseId', 'idx', 'filename']
