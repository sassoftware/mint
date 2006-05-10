#
# Copyright (c) 2005-2006 rPath, Inc.
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
                                 groupTroveId %(PRIMARYKEY)s,
                                 projectId INT,
                                 creatorId INT,
                                 recipeName CHAR(200),
                                 upstreamVersion CHAR(128),
                                 description TEXT,
                                 timeCreated INT,
                                 timeModified INT,
                                 autoResolve INT
                                 )
    """

    fields = ['groupTroveId', 'projectId', 'creatorId', 'recipeName',
              'upstreamVersion', 'description', 'timeCreated', 'timeModified',
              'autoResolve']

    indexes = {"GroupTrovesProjectIdx": """CREATE INDEX GroupTrovesProjectIdx
                                               ON GroupTroves(projectId)""",
               "GroupTrovesUserIdx": """CREATE INDEX GroupTrovesUserIdx
                                            ON GroupTroves(creatorId)"""}

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 16:
                cu = self.db.cursor()
                if self.cfg.dbDriver == 'sqlite':
                    cu.execute("""CREATE TABLE %s_backup AS
                                      SELECT * FROM %s""" % \
                               (self.name, self.name))
                    cu.execute('DROP TABLE %s' % self.name)
                    cu.execute(self.createSQL % self.db.keywords)
                    cu.execute("""INSERT INTO GroupTroves
                                      SELECT * FROM %s_backup""" % self.name)
                else:
                    cu.execute("""ALTER TABLE GroupTroves
                                      MODIFY COLUMN recipeName CHAR(200)""")
                return (dbversion + 1) == self.schemaVersion
        return True

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
                 autoResolve = int(autoResolve))
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

    def cleanup(self):
        cu = self.db.cursor()
        cu.execute("""DELETE FROM GroupTroves WHERE projectId=0
                         AND timeModified<?""", time.time() - 86400)
        self.db.commit()

class GroupTroveItemsTable(database.KeyedTable):
    name = "GroupTroveItems"
    key = "groupTroveItemId"

    createSQL = """
        CREATE TABLE GroupTroveItems(
             groupTroveItemId %(PRIMARYKEY)s,
             groupTroveId INT,
             creatorId INT,
             trvName CHAR(128),
             trvVersion TEXT,
             trvFlavor TEXT,
             subGroup CHAR(128),
             versionLock INT,
             useLock INT,
             instSetLock INT
         )"""

    fields = [ 'groupTroveItemId', 'groupTroveId', 'creatorId', 'trvName',
               'trvVersion', 'trvFlavor', 'subGroup', 'versionLock', 'useLock',
               'instSetLock' ]

    indexes = {"GroupTroveItemsUserIdx": """CREATE INDEX GroupTroveItemsUserIdx
                                              ON GroupTroveItems(creatorId)"""}

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
            flav = deps.ThawDependencySet(flavor)
            if not (trvDict['useLock'] or trvDict['instSetLock']):
                flavor = ''
            elif (trvDict['useLock'] and trvDict['instSetLock']):
                flavor = str(flav)
            elif trvDict['useLock']:
                depSet = deps.DependencySet()
                depSet.addDeps(deps.UseDependency,
                               flav.iterDepsByClass(deps.UseDependency))
                flavor = str(depSet)
            else:
                depSet = deps.DependencySet()
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
                    'config' : "Package-specific configuration files",
                    'configs' : "Kernel build configuration files",
                    'data' : "Package-specific data",
                    'devel' : "Developer-specific support",
                    'devellib' : "Developer-specific libraries",
                    'doc' : "Package-specific documentation",
                    'emacs': "Package-specific extensions for Emacs",
                    'lib': "Libraries",
                    'locale' : "Package-specific localization",
                    'perl' : "Package-specific Perl modules",
                    'python' : "Package-specific Python code",
                    'runtime' : "Package-specific runtime environment",
                    'tcl' : "Package-specific Tcl support",
                    'tk' : "Package-specific Tk support"}

class ConaryComponentsTable(database.KeyedTable):
    name = "ConaryComponents"
    key = "componentId"

    createSQL = """
        CREATE TABLE ConaryComponents(
             componentId %(PRIMARYKEY)s,
             component CHAR(128)
         )"""

    fields = [ 'componentId', 'component']

    indexes = {'ConaryComponentsIdx': """CREATE UNIQUE INDEX
                                             ConaryComponentsIdx
                                             ON ConaryComponents(component)"""}

class GroupTroveRemovedComponentsTable(database.DatabaseTable):
    name = "GroupTroveRemovedComponents"

    createSQL = """
        CREATE TABLE GroupTroveRemovedComponents(
             groupTroveId INT,
             componentId INT
         )"""

    fields = [ 'groupTroveId', 'componentId']

    indexes = {'GroupTroveRemovedComponentIdx':
               """CREATE UNIQUE INDEX GroupTroveRemovedComponentIdx
                      ON GroupTroveRemovedComponents
                          (groupTroveId, componentId)"""}

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
