#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
from mint import database
from mint import urltypes
from mint.mint_error import MintError

class FileMissing(MintError):
    def __str__(self):
        return "The requested file does not exist"

class DuplicateJob(MintError):
    def __str__(self):
        return "A conflicting job is already in progress"

class JobsTable(database.KeyedTable):
    name = 'Jobs'
    key = 'jobId'

    fields = ['jobId', 'buildId', 'groupTroveId', 'owner', 'userId',
              'status', 'statusMessage', 'timeSubmitted',
              'timeStarted', 'timeFinished']

    def get(self, id):
        res = database.KeyedTable.get(self, id)
        del res['owner']
        res['status'] = int(res['status'])
        return res

class Job(database.TableObject):
    __slots__ = JobsTable.fields

    # alias for releaseId
    releaseId = property(lambda self: self.buildId)

    def getItem(self, id):
        # newer clients must call getJob2 to maintain backwards
        # compatibility with older jobservers
        return self.server.getJob2(id)

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
    fields = ['fileId', 'buildId', 'idx', 'title', 'size', 'sha1' ]

class BuildFilesUrlsMapTable(database.KeyedTable):
    name = 'BuildFilesUrlsMap'
    key = 'fileId'
    fields = ['fileId', 'urlId']

class FilesUrlsTable(database.KeyedTable):
    name = 'FilesUrls'
    key = 'urlId'
    fields = ['urlId', 'urlType', 'url']
