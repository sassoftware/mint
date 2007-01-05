#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import md5
import time
import random

from mint import database
from conary import versions
from mint.rmakeconstants import buildjob, buildtrove, currentApi

class rMakeBuildTable(database.KeyedTable):
    name = "rMakeBuild"
    key = "rMakeBuildId"

    createSQL = """CREATE TABLE rMakeBuild(
                                    rMakeBuildId %(PRIMARYKEY)s,
                                    userId INT,
                                    title VARCHAR(128),
                                    UUID CHAR(32),
                                    jobId INT,
                                    status INT DEFAULT 0,
                                    statusMessage TEXT
                                    )"""

    fields = ['rMakeBuildId', 'userId', 'title', 'UUID', 'jobId', 'status',
              'statusMessage']

    indexes = {'rMakeBuildIdx' : \
               "CREATE INDEX rMakeBuildIdx ON rMakeBuild(userId)",
               'rMakeBuildTitleIdx' : \
               "CREATE UNIQUE INDEX rMakeBuildTitleIdx ON rMakeBuild(userId, title)"}

    def listTrovesById(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("""SELECT rMakeBuildItemId
                          FROM rMakeBuildItems
                          WHERE rMakeBuildId=?""", rMakeBuildId)

        return [x[0] for x in cu.fetchall()]

    def delete(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM rMakeBuildItems WHERE rMakeBuildId=?",
                   rMakeBuildId)
        cu.execute("DELETE FROM rMakeBuild WHERE rMakeBuildId=?", rMakeBuildId)
        self.db.commit()

    def randomizeUUID(self, rMakeBuildId):
        m = md5.new()
        cu = self.db.cursor()
        cu.execute('SELECT * FROM rMakeBuild WHERE rMakeBuildId=?',
                   rMakeBuildId)
        m.update(str(cu.fetchall()))
        cu.execute('SELECT * FROM rMakeBuildItems WHERE rMakeBuildId=?',
                   rMakeBuildId)
        m.update(str(cu.fetchall()))
        m.update(str(time.time()))
        m.update(str(random.random()))
        UUID = m.hexdigest()
        cu.execute("UPDATE rMakeBuild SET UUID=? WHERE rMakeBuildId=?",
                   UUID, rMakeBuildId)
        self.db.commit()
        return UUID

    def getUUID(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("SELECT UUID FROM rMakeBuild WHERE rMakeBuildIt=?",
                   rMakeBuildId)
        res = cu.fetchone()
        if not res:
            raise database.ItemNotFound
        return res[0]

    def reset(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("""UPDATE rMakeBuild SET UUID=NULL,
                                            status=0,
                                            statusMessage='',
                                            jobId=NULL
                          WHERE rMakeBuildId=?""", rMakeBuildId)
        cu.execute("""UPDATE rMakeBuildItems SET status=0, statusMessage=''
                          WHERE rMakeBuildId=?""", rMakeBuildId)
        self.db.commit()

    def startBuild(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("""UPDATE rMakeBuild SET status=?,
                                 statusMessage='Waiting for rMake Server'
                          WHERE rMakeBuildId=?""",
                   buildjob.JOB_STATE_QUEUED, rMakeBuildId)
        self.db.commit()

    def commitBuild(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("""UPDATE rMakeBuild SET status=?,
                                 statusMessage='Waiting for rMake Server'
                          WHERE rMakeBuildId=?""",
                   buildjob.JOB_STATE_COMMITTING, rMakeBuildId)
        cu.execute("""UPDATE rMakeBuildItems SET status=?, statusMessage=''
                          WHERE rMakeBuildId=?""",
                   buildtrove.TROVE_STATE_INIT, rMakeBuildId)
        self.db.commit()

    def setStatus(self, UUID, status, statusMessage):
        cu = self.db.cursor()
        cu.execute("""UPDATE rMakeBuild
                          SET status=?, statusMessage=?
                          WHERE UUID=?""", status, statusMessage, UUID)
        self.db.commit()

    def setJobId(self, UUID, jobId):
        cu = self.db.cursor()
        cu.execute("""UPDATE rMakeBuild
                          SET jobId=?
                          WHERE UUID=?""", jobId, UUID)
        self.db.commit()

    def listByUser(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT rMakeBuildId FROM rMakeBuild WHERE userId=?",
                   userId)
        return [x[0] for x in cu.fetchall()]


class rMakeBuildItemsTable(database.KeyedTable):
    name = "rMakeBuildItems"
    key = "rMakeBuildItemId"

    createSQL = """CREATE TABLE rMakeBuildItems(
                       rMakeBuildItemId %(PRIMARYKEY)s,
                       rMakeBuildId INT,
                       trvName VARCHAR(128),
                       trvLabel VARCHAR(128),
                       status INT DEFAULT 0,
                       statusMessage TEXT
                       )"""

    fields = ['rMakeBuildItemId', 'rMakeBuildId', 'trvName', 'trvLabel',
              'status', 'statusMessage']

    indexes = {'rMakeBuildItemIdx' : """CREATE INDEX rMakeBuildItemIdx
                                           ON rMakeBuildItems(rMakeBuildId)""",
               'rMakeBuildItemNameIdx' : \
               """CREATE UNIQUE INDEX rMakeBuildItemNameIdx
               ON rMakeBuildItems(rMakeBuildId, trvName, trvLabel)"""}

    def delete(self, rMakeBuildItemId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM rMakeBuildItems WHERE rMakeBuildItemId=?",
                   rMakeBuildItemId)
        self.db.commit()

    def get(self, rMakeBuildItemId):
        ret = database.KeyedTable.get(self, rMakeBuildItemId)
        ret['shortHost'] = \
                    versions.Label(ret['trvLabel']).getHost().split('.')[0]

         # This is a totally hackerrific. We really need a
         # better way to alias projects to shortnames
         # i.e. rPath Linux = conary.rpath.com, however,
         # its repos is in 'rpath', not 'conary'. [Bug #714]
        if ret['shortHost'] == 'conary':
            ret['shortHost'] = 'rpath'
        return ret

    def new(self, **kwargs):
        if self.troveInBuild(kwargs['rMakeBuildId'], kwargs['trvName'],
                             kwargs['trvLabel']):
            raise database.DuplicateItem
        # ensure we don't save full versions
        kwargs['trvLabel'] = self._getLabel(kwargs['trvLabel'])
        return database.KeyedTable.new(self, **kwargs)

    def setStatus(self, UUID, trvName, trvVersion, status, statusMessage):
        cu = self.db.cursor()
        cu.execute("SELECT rMakeBuildId FROM rMakeBuild WHERE UUID=?", UUID)
        res = cu.fetchone()
        if not res:
                return
        for trvName in (trvName.split(':')[0],
                        trvName.split(':')[0] + ':source'):
            trvLabel = self._getLabel(trvVersion)
            cu.execute("""UPDATE rMakeBuildItems SET status=?, statusMessage=?
                              WHERE trvName=?
                              AND trvLabel=?
                              AND rMakeBuildId=?""",
                       status, statusMessage, trvName, trvLabel, res[0])
        self.db.commit()

    def troveInBuild(self, rMakeBuildId, trvName, trvVersion):
        cu = self.db.cursor()
        trvLabel = self._getLabel(trvVersion)
        pkgName = trvName.split(':')[0]
        cu.execute("""SELECT rMakeBuildItemId
                          FROM rMakeBuildItems
                          WHERE (trvName=? OR trvName=?)
                          AND trvLabel=?
                          AND rMakeBuildId=?""",
                   pkgName, pkgName + ':source', trvLabel, rMakeBuildId)
        return bool(cu.fetchall())

    def _getLabel(self, trvVersion):
        try:
            return str(versions.ThawVersion(trvVersion).branch().label())
        except:
            try:
                return str(versions.VersionFromString( \
                    trvVersion).branch().label())
            except:
                return str(versions.Label(trvVersion))


class rMakeBuild(database.TableObject):
    __slots__ = rMakeBuildTable.fields

    # don't mistake the name collision. this "item" is for tableobjects
    def getItem(self, id):
        return self.server.getrMakeBuild(id)

    def getXML(self, command = 'build', protocolVersion = currentApi):
        return self.server.getrMakeBuildXML(self.id, command, protocolVersion)

    def addTrove(self, trvName, trvLabel):
        return self.server.addrMakeBuildTrove(self.id, trvName, trvLabel)

    def addTroveByProject(self, trvName, projectName):
        return self.server.addrMakeBuildTroveByProject(self.id, trvName,
                                                       projectName)

    def listTroves(self):
        return self.server.listrMakeBuildTroves(self.id)

    def delete(self):
        return self.server.delrMakeBuild(self.id)

    def rename(self, title):
        return self.server.renamerMakeBuild(self.id, title)

    def resetStatus(self):
        return self.server.resetrMakeBuildStatus(self.id)
