#
# Copyright (c) 2005 Specifix, Inc.
#
# All rights reserved
#

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

class JobsTable:
    def __init__(self, db):
        self.db = db

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
        tables = [ x[0] for x in cu ]
        if 'Jobs' not in tables:
            cu.execute("""
                CREATE TABLE Jobs (
                    jobId           INTEGER PRIMARY KEY,
                    releaseId       INT,
                    userId          INT,
                    status          INT,
                    statusMessage   STR,
                    timeStarted     INT,
                    timeFinished    INT
                )""")
        if 'ImageFiles' not in tables:
            cu.execute("""
                CREATE TABLE ImageFiles (
                    fileId      INTEGER PRIMARY KEY,
                    releaseId   INT,
                    idx         INT,
                    filename    STR 
                );""")
        self.db.commit()

class Job(object):
    jobId = None
    release = None
    userId = None
    status = None
    statusMessage = None
    timeStarted = None
    timeFinished = None

    _itserver = None

    def __init__(self, server, jobId):
        self.jobId = jobId
        self._itserver = server
        self._refresh()

    def _refresh(self):
        jobData = self._itserver.getJob(self.jobId)
        self.__dict__.update(jobData)

    # static members: no need to call _refresh
    def getId(self):
        return self.jobId

    def getReleaseId(self):
        return self.releaseId

    def getUserId(self):
        return self.userId

    # non-static members
    def getStatus(self):
        self._refresh()
        return self.status

    def getStatusMessage(self):
        self._refresh()
        return self.statusMessage

    def setStatus(self, status, statusMessage):
        return self._itserver.setJobStatus(self.jobId, status, statusMessage)

    def getTimeStarted(self):
        self._refresh()
        return self.timeStarted

    def getTimeFinished(self):
        self._refresh()
        return self.timeFinished
