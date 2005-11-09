#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

import database
import sqlite3
import time
from deps import deps

import versions
import re
import mint_error
import jobs

class GroupTroveNameError(mint_error.MintError):
    def __str__(self):
        return "Bad name for Group Trove"

class GroupTroveVersionError(mint_error.MintError):
    def __str__(self):
        return "Bad version for Group Trove"

############ Server Side ##############

class GroupTroveTable(database.KeyedTable):
    name = "GroupTroves"
    key = "groupTroveId"

    createSQL = """
        CREATE TABLE GroupTroves(
                                 groupTroveId INTEGER,
                                 projectId INTEGER,
                                 creatorId INTEGER,
                                 recipeName STR,
                                 upstreamVersion STR,
                                 description STR,
                                 timeCreated INTEGER,
                                 timeModified INTEGER,
                                 autoResolve INTEGER,
                                 PRIMARY KEY (groupTroveId)
                                 );
    """
    
    fields = ['groupTroveId', 'projectId', 'creatorId', 'recipeName',
              'upstreamVersion', 'description', 'timeCreated', 'timeModified',
              'autoResolve']

    def listGroupTrovesByProject(self, projectId):
        cu = self.db.cursor()
        r = cu.execute("SELECT groupTroveId, recipeName FROM %s WHERE projectId=?" % self.name, projectId)
        return r.fetchall()

    def setUpstreamVersion(self, groupTroveId, vers):
        try:
            versions.Revision(vers + "-1-1")
        except versions.ParseError:
            raise GroupTroveVersionError
        self.update(groupTroveId, upstreamVersion = vers, timeModified = time.time())

    def createGroupTrove(self, projectId, creatorId, recipeName,
                         upstreamVersion, description, autoResolve):
        if not re.match("group-[a-zA-Z0-9\-_]+$", recipeName):
            raise GroupTroveNameError
        try:
            versions.Revision(upstreamVersion + "-1-1")
        except versions.ParseError:
            raise GroupTroveVersionError
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            r = cu.execute("SELECT IFNULL(MAX(groupTroveId), 0) + 1 AS groupTroveId FROM GroupTroves")
            groupTroveId = r.fetchone()[0]
            timeStamp = time.time()
            self.new(groupTroveId = groupTroveId,
                     projectId = projectId,
                     creatorId = creatorId,
                     recipeName = recipeName,
                     upstreamVersion = upstreamVersion,
                     description = description,
                     timeCreated = timeStamp,
                     timeModified = timeStamp,
                     autoResolve = int(autoResolve))
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return groupTroveId

    def delGroupTrove(self, groupTroveId):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            cu.execute("DELETE FROM GroupTroveItems WHERE groupTroveId=?", groupTroveId)
            cu.execute("DELETE FROM GroupTroves WHERE groupTroveId=?", groupTroveId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def getProjectId(self, groupTroveId):
        return self.get(groupTroveId)['projectId']

    def setAutoResolve(self, groupTroveId, resolve):
        self.update(groupTroveId, autoResolve = int(resolve), timeModified = (time.time()))

    def get(self, groupTroveId):
        ret = database.KeyedTable.get(self, groupTroveId)
        ret['autoResolve'] = bool(ret['autoResolve'])
        return ret

class GroupTroveItemsTable(database.KeyedTable):
    name = "GroupTroveItems"
    key = "groupTroveItemId"

    # unique index to prevent common case of clicking on "add this trove"
    # button twice in a row.
    indexes = {'groupTroveItemIdIdx': "CREATE UNIQUE INDEX groupTroveItemIdIdx ON GroupTroveItems(groupTroveId, trvName, trvVersion, trvFlavor)"}

    createSQL = """
        CREATE TABLE GroupTroveItems(
                                 groupTroveItemId INTEGER,
                                 groupTroveId INTEGER,
                                 creatorId INTEGER,
                                 trvName STR,
                                 trvVersion STR,
                                 trvFlavor STR,
                                 subGroup STR,
                                 versionLock INTEGER,
                                 useLock INTEGER,
                                 instSetLock INTEGER,
                                 PRIMARY KEY (groupTroveItemId)
                                 );
    """

    fields = [ 'groupTroveItemId', 'groupTroveId', 'creatorId', 'trvName',
               'trvVersion', 'trvFlavor', 'subGroup', 'versionLock', 'useLock',
               'instSetLock' ]

    def updateModifiedTime(self, groupTroveItemId):
        cu = self.db.cursor()
        cu.execute("SELECT groupTroveId FROM GroupTroveItems WHERE groupTroveItemId=?", groupTroveItemId)
        cu.execute("UPDATE GroupTroves SET timeModified=? WHERE groupTroveId=?", time.time(), cu.fetchone()[0])

    def setVersionLocked(self, groupTroveItemId, lock):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            cu.execute("UPDATE GroupTroveItems SET versionLock=? WHERE groupTroveItemId=?", lock, groupTroveItemId)
            self.updateModifiedTime(groupTroveItemId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def setUseLocked(self, groupTroveItemId, lock):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            cu.execute("UPDATE GroupTroveItems SET useLock=? WHERE groupTroveItemId=?", lock, groupTroveItemId)
            self.updateModifiedTime(groupTroveItemId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def setInstSetLocked(self, groupTroveItemId, lock):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            cu.execute("UPDATE GroupTroveItems SET instSetLock=? WHERE groupTroveItemId=?", lock, groupTroveItemId)
            self.updateModifiedTime(groupTroveItemId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def addTroveItem(self, groupTroveId, creatorId, trvName, trvVersion, trvFlavor, subGroup, versionLock, useLock, instSetLock):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            cu.execute("SELECT IFNULL(MAX(groupTroveItemId), 0) + 1 as groupTroveItemId FROM GroupTroveItems")

            groupTroveItemId = cu.fetchone()[0]
            self.new(groupTroveItemId = groupTroveItemId,
                     groupTroveId = groupTroveId,
                     creatorId = creatorId,
                     trvName = trvName,
                     trvVersion = trvVersion,
                     trvFlavor = trvFlavor,
                     subGroup = subGroup,
                     versionLock = versionLock,
                     useLock = useLock,
                     instSetLock = instSetLock)
            self.updateModifiedTime(groupTroveItemId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return groupTroveItemId

    def delGroupTroveItem(self, groupTroveItemId):
        cu = self.db.cursor()
        cu.execute("BEGIN")
        try:
            self.updateModifiedTime(groupTroveItemId)
            cu.execute("DELETE FROM GroupTroveItems WHERE groupTroveItemId=?", groupTroveItemId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def listByGroupTroveId(self, groupTroveId):
        cu = self.db.cursor()
        cu.execute("SELECT groupTroveItemId FROM GroupTroveItems WHERE groupTroveId=?", groupTroveId)
        trvIdList = [x[0] for x in cu.fetchall()]
        trvList = []
        for trvId in trvIdList:
            trvList.append(self.get(trvId))
        return trvList

    def get(self, groupTroveItemId):
        ret = database.KeyedTable.get(self, groupTroveItemId)
        ret['versionLock'] = bool(ret['versionLock'])
        ret['useLock'] = bool(ret['useLock'])
        ret['instSetLock'] = bool(ret['instSetLock'])
        parsedVer = versions.VersionFromString(ret['trvVersion'])
        ret['trvLabel'] = str(parsedVer.branch().label())

        flav = deps.ThawDependencySet(ret['trvFlavor'])
        if not (ret['useLock'] or ret['instSetLock']):
            flavStr = ''
        elif (ret['useLock'] and ret['instSetLock']):
            flavStr = str(flav)
        elif ret['useLock']:
            depSet = deps.DependencySet()
            depSet.addDeps(deps.UseDependency,
                           flav.iterDepsByClass(deps.UseDependency))
            flavStr = str(depSet)
        else:
            depSet = deps.DependencySet()
            depSet.addDeps(deps.InstructionSetDependency,
                           flav.iterDepsByClass(deps.InstructionSetDependency))
            flavStr = str(depSet)
        ret['trvFlavor'] = flavStr
        if ret['subGroup'] == '':
            cu = self.db.cursor()
            cu.execute("""SELECT recipeName from GroupTroveItems, GroupTroves 
                            WHERE GroupTroveItems.groupTroveItemId=? AND
                                  GroupTroveItems.groupTroveId=GroupTroves.groupTroveId""", groupTroveItemId)
            ret['subGroup'] = cu.fetchone()[0]
        return ret

    def getProjectId(self, groupTroveItemId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId from GroupTroveItems, GroupTroves
                        WHERE GroupTroveItems.groupTroveItemId=? AND 
                              GroupTroveItems.groupTroveId=GroupTroves.groupTroveId""", groupTroveItemId)
        return cu.fetchone()[0]

############ Client Side ##############

class GroupTrove(database.TableObject):
    __slots__ = [GroupTroveTable.key] + GroupTroveTable.fields

    # don't mistake the name collision! this has nothing to do with
    # group trove items! it's something required from TableObject
    def getItem(self, id):
        return self.server.getGroupTrove(id)

    # what follows is pertinent to group troves
    def delete(self):
        return self.server.deleteGroupTrove(self.groupTroveId)

    def addTrove(self, trvname, trvVersion, trvFlavor, subGroup, versionLock,
                 useLock, InstSetLock):
        return self.server.addGroupTroveItem(self.getId(), trvname, trvVersion,
                                             trvFlavor, subGroup, versionLock,
                                             useLock, InstSetLock)

    def delTrove(self, groupTroveItemId):
        return self.server.delGroupTroveItem(groupTroveItemId)

    def getTrove(self, groupTroveItemId):
        return self.server.getGroupTroveItem(groupTroveItemId)

    def setTroveVersionLocked(self, groupTroveItemId, locked):
        return self.server.setGroupTroveItemVersionLocked(groupTroveItemId, locked)

    def setTroveInstSetLocked(self, groupTroveItemId, locked):
        return self.server.setGroupTroveItemInstSetLocked(groupTroveItemId, locked)

    def setTroveUseLocked(self, groupTroveItemId, locked):
        return self.server.setGroupTroveItemUseLocked(groupTroveItemId, locked)

    def listTroves(self):
        return self.server.listGroupTroveItemsByGroupTrove(self.getId())

    def setDesc(self, description):
        self.server.setGroupTroveDesc(self.getId(), description)

    def setTroveSubGroup(self, trvId, subGroup):
        self.server.setGroupTroveItemSubGroup(trvId, subGroup)

    def setUpstreamVersion(self, vers):
        self.server.setGroupTroveUpstreamVersion(self.getId(), vers)

    def setAutoResolve(self, resolve):
        self.server.setGroupTroveAutoResolve(self.getId(), resolve)

    def getRecipe(self):
        return self.server.getRecipe(self.getId())

    def startCookJob(self):
        return self.server.startCookJob(self.id)

    def getJob(self):
        jobId = self.server.getJobIdForCook(self.id)
        if jobId:
            return jobs.Job(self.server, jobId)
        else:
            return None

    def getLabelPath(self):
        return self.server.getGroupTroveLabelPath(self.getId())
