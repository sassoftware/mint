#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import database
import re
import time

from mint import jobs
from mint import mint_error

from conary import versions
from conary.deps import deps

PROTOCOL_VERSION = 1

class GroupTroveNameError(mint_error.MintError):
    def __str__(self):
        return "Invalid name for group: letters, numbers, hyphens allowed."

class GroupTroveVersionError(mint_error.MintError):
    def __str__(self):
        return "Invalid version for group: letters, numbers, periods allowed."

############ Server Side ##############

class GroupTroveTable(database.KeyedTable):
    name = "GroupTroves"
    key = "groupTroveId"

    fields = ['groupTroveId', 'projectId', 'creatorId', 'recipeName',
              'upstreamVersion', 'description', 'timeCreated', 'timeModified',
              'autoResolve', 'cookCount']

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)

    def listGroupTrovesByProject(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT groupTroveId, recipeName
                          FROM GroupTroves WHERE projectId=?""", projectId)
        return [(int(x[0]), x[1]) for x in cu.fetchall()]

    def setUpstreamVersion(self, groupTroveId, vers):
        try:
            versions.Revision(vers + "-1-1")
        except versions.ParseError:
            raise GroupTroveVersionError
        self.update(groupTroveId, upstreamVersion = vers,
                    timeModified = time.time())

    def createGroupTrove(self, projectId, creatorId, recipeName,
                         upstreamVersion, description, autoResolve):
        if not re.match("group-[a-zA-Z0-9\-_]+$", recipeName):
            raise GroupTroveNameError
        try:
            versions.Revision(upstreamVersion + "-1-1")
        except versions.ParseError:
            raise GroupTroveVersionError

        cu = self.db.cursor()
        cu.execute("SELECT IFNULL(MAX(groupTroveId), 0) + 1 AS groupTroveId FROM GroupTroves")
        groupTroveId = cu.fetchone()[0]
        timeStamp = time.time()
        self.new(groupTroveId = groupTroveId,
                 projectId = projectId,
                 creatorId = creatorId,
                 recipeName = recipeName,
                 upstreamVersion = upstreamVersion,
                 description = description,
                 timeCreated = timeStamp,
                 timeModified = timeStamp,
                 autoResolve = int(autoResolve),
                 cookCount = 0)
        return groupTroveId

    def delGroupTrove(self, groupTroveId):
        cu = self.db.transaction()
        try:
            cu.execute("DELETE FROM GroupTroveItems WHERE groupTroveId=?",
                       groupTroveId)
            cu.execute("DELETE FROM GroupTroves WHERE groupTroveId=?",
                       groupTroveId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
            return groupTroveId

    def getProjectId(self, groupTroveId):
        return self.get(groupTroveId)['projectId']

    def setAutoResolve(self, groupTroveId, resolve):
        self.update(groupTroveId, autoResolve = int(resolve),
                    timeModified = (time.time()))

    def get(self, groupTroveId):
        ret = database.KeyedTable.get(self, groupTroveId)
        ret['autoResolve'] = bool(ret['autoResolve'])
        cu = self.db.cursor()
        cu.execute("SELECT hostname from Projects where projectId=?",
                   ret['projectId'])
        r = cu.fetchone()
        if not r:
            ret['projectName'] = '(none)'
        else:
            ret['projectName'] = r[0]
        return ret

    def bumpCookCount(self, groupTroveId):
        # this function will save the current value, increment it, then return
        # the value the table had before the function was called.
        # basically a post-increment function.
        cu = self.db.cursor()
        cu.execute("SELECT cookCount FROM GroupTroves WHERE groupTroveId=?",
                   groupTroveId)
        res = cu.fetchall()
        if res:
            count = res[0][0] + 1
            cu.execute("""UPDATE GroupTroves
                              SET cookCount=?
                              WHERE groupTroveId=?""", count, groupTroveId)
            self.db.commit()
            return count
        else:
            return None

    def cleanup(self):
        cu = self.db.cursor()
        cu.execute("""DELETE FROM GroupTroves WHERE projectId=0
                         AND timeModified<?""", time.time() - 86400)
        self.db.commit()

class GroupTroveItemsTable(database.KeyedTable):
    name = "GroupTroveItems"
    key = "groupTroveItemId"

    fields = [ 'groupTroveItemId', 'groupTroveId', 'creatorId', 'trvName',
               'trvVersion', 'trvFlavor', 'subGroup', 'versionLock', 'useLock',
               'instSetLock' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)

    def updateModifiedTime(self, groupTroveItemId):
        cu = self.db.cursor()
        cu.execute("SELECT groupTroveId FROM GroupTroveItems WHERE groupTroveItemId=?", groupTroveItemId)
        cu.execute("UPDATE GroupTroves SET timeModified=? WHERE groupTroveId=?", time.time(), cu.fetchone()[0])
        self.db.commit()

    def setVersionLock(self, groupTroveItemId, lock):
        self.update(groupTroveItemId, versionLock = lock)
        self.updateModifiedTime(groupTroveItemId)

    def setUseLock(self, groupTroveItemId, lock):
        self.update(groupTroveItemId, useLock = lock)
        self.updateModifiedTime(groupTroveItemId)

    def setInstSetLock(self, groupTroveItemId, lock):
        self.update(groupTroveItemId, instSetLock = lock)
        self.updateModifiedTime(groupTroveItemId)

    def addTroveItem(self, groupTroveId, creatorId, trvName, trvVersion, trvFlavor, subGroup, versionLock, useLock, instSetLock):
        if ":source" in trvName:
            raise GroupTroveNameError("Can't add source components")
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(groupTroveId)
                        FROM GroupTroveItems
                        WHERE trvName=? AND trvVersion=? AND trvFlavor=?
                            AND groupTroveId=?""",
            trvName, trvVersion, trvFlavor, groupTroveId)
        if cu.fetchone()[0] > 0:
            raise database.DuplicateItem

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
        return groupTroveItemId

    def delGroupTroveItem(self, groupTroveItemId):
        cu = self.db.cursor()
        self.updateModifiedTime(groupTroveItemId)
        cu.execute("DELETE FROM GroupTroveItems WHERE groupTroveItemId=?", groupTroveItemId)
        self.db.commit()
        return groupTroveItemId

    def listByGroupTroveId(self, groupTroveId):
        cu = self.db.cursor()
        cu.execute("SELECT groupTroveItemId FROM GroupTroveItems WHERE groupTroveId=?", groupTroveId)
        trvIdList = [x[0] for x in cu.fetchall()]
        trvList = []
        for trvId in trvIdList:
            trvList.append(self.get(trvId))
        return trvList

    def troveInGroupTroveItems(self, groupTroveId, name, version, flavor):
        trvDicts = self.listByGroupTroveId(groupTroveId)
        trvDicts = [x for x in trvDicts if x['trvName'] == name]
        if not trvDicts:
            return False
        for trvDict in trvDicts:
            flav = deps.ThawFlavor(flavor)
            if not (trvDict['useLock'] or trvDict['instSetLock']):
                flavor = ''
            elif (trvDict['useLock'] and trvDict['instSetLock']):
                flavor = str(flav)
            elif trvDict['useLock']:
                depSet = deps.Flavor()
                depSet.addDeps(deps.UseDependency,
                               flav.iterDepsByClass(deps.UseDependency))
                flavor = str(depSet)
            else:
                depSet = deps.Flavor()
                depSet.addDeps(deps.InstructionSetDependency,
                               flav.iterDepsByClass(deps.InstructionSetDependency))
                flavor = str(depSet)
            if flavor:
                flavorMatch = trvDict['trvFlavor'] == flavor
            else:
                # short circuit degenerate flavors
                flavorMatch = True
            if version == '':
                # short circuit degenerate versions
                return flavorMatch
            parsedVer = versions.VersionFromString(version)
            label = str(parsedVer.branch().label())
            if trvDict['trvFlavor'] == flavor and \
               (trvDict['versionLock'] and  \
               version == trvDict['trvVersion'] or \
                (not trvDict['versionLock'] and
                    trvDict['trvLabel'] == label)):
                return True
        return False

    def get(self, groupTroveItemId):
        ret = database.KeyedTable.get(self, groupTroveItemId)
        ret['versionLock'] = bool(ret['versionLock'])
        ret['useLock'] = bool(ret['useLock'])
        ret['instSetLock'] = bool(ret['instSetLock'])
        parsedVer = versions.VersionFromString(ret['trvVersion'])
        ret['trvLabel'] = str(parsedVer.branch().label())
        ret['shortHost'] = parsedVer.branch().label().getHost().split('.')[0]

         # This is a totally hackerrific. We really need a
         # better way to alias projects to shortnames
         # i.e. rPath Linux = conary.rpath.com, however,
         # its repos is in 'rpath', not 'conary'. [Bug #714]
        if ret['shortHost'] == 'conary':
            ret['shortHost'] = 'rpath'

        ret['baseUrl'] = self.cfg.basePath + 'repos/' + ret['shortHost'] + '/'

        flav = deps.ThawFlavor(ret['trvFlavor'])
        if not (ret['useLock'] or ret['instSetLock']):
            flavStr = ''
        elif (ret['useLock'] and ret['instSetLock']):
            flavStr = str(flav)
        elif ret['useLock']:
            depSet = deps.Flavor()
            depSet.addDeps(deps.UseDependency,
                           flav.iterDepsByClass(deps.UseDependency))
            flavStr = str(depSet)
        else:
            depSet = deps.Flavor()
            depSet.addDeps(deps.InstructionSetDependency,
                           flav.iterDepsByClass(deps.InstructionSetDependency))
            flavStr = str(depSet)
        ret['trvFlavor'] = flavStr
        if ret['subGroup'] == '':
            cu = self.db.cursor()
            cu.execute("""SELECT recipeName from GroupTroveItems, GroupTroves
                            WHERE GroupTroveItems.groupTroveItemId=? AND
                                  GroupTroveItems.groupTroveId=
                                          GroupTroves.groupTroveId""",
                       groupTroveItemId)
            ret['subGroup'] = cu.fetchone()[0]
        return ret

    def getProjectId(self, groupTroveItemId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId from GroupTroveItems, GroupTroves
                        WHERE GroupTroveItems.groupTroveItemId=? AND
                              GroupTroveItems.groupTroveId=
                                      GroupTroves.groupTroveId""",
                   groupTroveItemId)
        return cu.fetchone()[0]

KNOWN_COMPONENTS = {'build-tree' : "Kernel build environment",
                    'config' : "Configuration-related files",
                    'configs' : "Kernel build configuration files",
                    'data' : "Data files",
                    'devel' : "Developer-related support files",
                    'devellib' : "Developer-related libraries",
                    'doc' : "Documentation-related files",
                    'emacs': "Emacs-related extensions",
                    'lib': "Libraries",
                    'locale' : "Localization-related files",
                    'perl' : "Perl-related files",
                    'python' : "Python-related files",
                    'runtime' : "Files required for runtime environment",
                    'tcl' : "Tcl-related support files",
                    'tk' : "Tk-related support files"}

class ConaryComponentsTable(database.KeyedTable):
    name = "ConaryComponents"
    key = "componentId"

    fields = [ 'componentId', 'component']

class GroupTroveRemovedComponentsTable(database.DatabaseTable):
    name = "GroupTroveRemovedComponents"

    fields = [ 'groupTroveId', 'componentId']

    def list(self, groupTroveId):
        cu = self.db.cursor()
        cu.execute("""SELECT component
                          FROM GroupTroveRemovedComponents
                          LEFT JOIN ConaryComponents
                              ON GroupTroveRemovedComponents.componentId =
                                     ConaryComponents.componentId
                          WHERE groupTroveId=?""", groupTroveId)
        return [x[0] for x in cu.fetchall()]

    def setRemovedComponents(self, groupTroveId, components):
        cu = self.db.cursor()
        cu.execute("""DELETE FROM GroupTroveRemovedComponents
                          WHERE groupTroveId=?""", groupTroveId)
        self.removeComponents(groupTroveId, components)
        self.db.commit()

    def removeComponents(self, groupTroveId, components):
        cu = self.db.cursor()
        for comp in components:
            if comp not in KNOWN_COMPONENTS:
                raise mint_error.ParameterError( \
                    "Unkown component specified: %s" % comp)

            cu.execute("""SELECT componentId
                              FROM ConaryComponents
                              WHERE component=?""", comp)
            res = cu.fetchone()
            if not res:
                cu.execute("""INSERT INTO ConaryComponents (component)
                                  VALUES(?)""",
                           comp)
                compId = cu.lastid()
            else:
                compId = res[0]
            cu.execute("""SELECT COUNT(*)
                              FROM GroupTroveRemovedComponents
                              WHERE groupTroveId=? AND componentId=?""",
                       groupTroveId, compId)
            if not cu.fetchone()[0]:
                # only add component if it wasn't already there
                cu.execute("""INSERT INTO GroupTroveRemovedComponents
                                  (groupTroveId, componentId) VALUES(?, ?)""",
                           groupTroveId, compId)
        self.db.commit()

    def allowComponents(self, groupTroveId, components):
        cu = self.db.cursor()
        for comp in components:
            cu.execute("""SELECT componentId
                              FROM ConaryComponents
                              WHERE component=?""", comp)
            res = cu.fetchone()
            if not res:
                continue
            cu.execute("""DELETE FROM GroupTroveRemovedComponents
                              WHERE groupTroveId=? AND componentId=?""",
                       groupTroveId, res[0])
        self.db.commit()

############ Client Side ##############

class GroupTrove(database.TableObject):
    __slots__ = [GroupTroveTable.key, 'projectName'] + GroupTroveTable.fields

    # don't mistake the name collision! this has nothing to do with
    # group trove items! it's something required from TableObject
    def getItem(self, id):
        return self.server.getGroupTrove(id)

    # what follows is pertinent to group troves
    def delete(self):
        return self.server.deleteGroupTrove(self.groupTroveId)

    def addTroveByProject(self, trvname, projectName, trvFlavor, subGroup,
                          versionLock, useLock, InstSetLock):
        return self.server.addGroupTroveItemByProject(self.getId(), trvname,
                                                      projectName, trvFlavor,
                                                      subGroup, versionLock,
                                                      useLock, InstSetLock)

    def addTrove(self, trvname, trvVersion, trvFlavor, subGroup, versionLock,
                 useLock, InstSetLock):
        return self.server.addGroupTroveItem(self.getId(), trvname, trvVersion,
                                             trvFlavor, subGroup, versionLock,
                                             useLock, InstSetLock)

    def delTrove(self, groupTroveItemId):
        return self.server.delGroupTroveItem(groupTroveItemId)

    def getTrove(self, groupTroveItemId):
        return self.server.getGroupTroveItem(groupTroveItemId)

    def setTroveVersionLock(self, groupTroveItemId, lock):
        return self.server.setGroupTroveItemVersionLock(groupTroveItemId, lock)

    def setTroveInstSetLock(self, groupTroveItemId, lock):
        return self.server.setGroupTroveItemInstSetLock(groupTroveItemId, lock)

    def setTroveUseLock(self, groupTroveItemId, lock):
        return self.server.setGroupTroveItemUseLock(groupTroveItemId, lock)

    def listTroves(self):
        return self.server.listGroupTroveItemsByGroupTrove(self.getId())

    def troveInGroup(self, name, version = '', flavor = ''):
        return self.server.troveInGroupTroveItems(self.getId(), name, version,
                                                  flavor)

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

    def startCookJob(self, arch):
        return self.server.startCookJob(self.id, arch)

    def getJob(self):
        jobId = self.server.getJobIdForCook(self.id)
        if jobId:
            return jobs.Job(self.server, jobId)
        else:
            return None

    def getLabelPath(self):
        return self.server.getGroupTroveLabelPath(self.id)

    def listRemovedComponents(self):
        return self.server.listGroupTroveRemovedComponents(self.id)

    def removeComponents(self, components):
        return self.server.removeGroupTroveComponents(self.id, components)

    def allowComponents(self, components):
        return self.server.allowGroupTroveComponents(self.id, components)

    def setRemovedComponents(self, components):
        return self.server.setGroupTroveRemovedComponents(self.id, components)

    def serialize(self, arch):
        return self.server.serializeGroupTrove(self.id, arch)
