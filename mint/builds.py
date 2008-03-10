#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import sys
import time
import urlparse

from mint import buildtemplates
from mint import buildtypes
from mint import database
from mint import flavors
from mint import helperfuncs
from mint import jobs

from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint.mint_error import *

from conary import versions
from conary.deps import deps

PROTOCOL_VERSION = 1

class UrlDownloadsTable(database.DatabaseTable):
    name = "UrlDownloads"
    fields = ['urlId', 'timeDownloaded', 'ip']

    def add(self, urlId, ip):
        t = helperfuncs.toDatabaseTimestamp()
        cu = self.db.cursor()
        cu.execute("""INSERT INTO UrlDownloads (urlId, timeDownloaded, ip)
            VALUES (?, ?, ?)""",
            urlId, t, ip)
        self.db.commit()


class BuildsTable(database.KeyedTable):
    name = "Builds"
    key  = "buildId"

    fields = ['buildId', 'projectId', 'pubReleaseId',
              'buildType', 'name', 'description',
              'troveName', 'troveVersion', 'troveFlavor', 'troveLastChanged',
              'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy',
              'deleted', 'buildCount']

    def iterBuildsForProject(self, projectId):
        """ Returns an iterator over the all of the buildIds in a given
            project with ID projectId. The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        cu.execute("""SELECT buildId FROM BuildsView
                      WHERE projectId=? AND
                            troveName IS NOT NULL AND
                            troveVersion IS NOT NULL AND
                            troveFlavor IS NOT NULL AND
                            troveLastChanged IS NOT NULL
                            ORDER BY troveLastChanged DESC, buildId""",
                   projectId)

        for results in cu.fetchall():
            yield int(results[0])

    def setTrove(self, buildId, troveName, troveVersion, troveFlavor):
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET troveName=?,
                                          troveVersion=?,
                                          troveFlavor=?,
                                          troveLastChanged=?
                      WHERE buildId=?""",
                   troveName, troveVersion,
                   troveFlavor, time.time(),
                   buildId)
        self.db.commit()
        return 0

    def getTrove(self, buildId):
        cu = self.db.cursor()

        cu.execute("""SELECT troveName,
                             troveVersion,
                             troveFlavor
                      FROM BuildsView
                      WHERE buildId=?""",
                   buildId)
        r = cu.fetchone()

        name, version, flavor = r[0], r[1], r[2]
        if not flavor:
            flavor = "none"
        if not name or not version:
            raise TroveNotSet
        else:
            return name, version, flavor

    def getPublished(self, buildId):
        cu = self.db.cursor()
        cu.execute("SELECT IFNULL((SELECT pubReleaseId FROM BuildsView WHERE buildId=?), 0)", buildId)
        pubReleaseId = cu.fetchone()[0]
        if pubReleaseId:
            cu.execute("SELECT timePublished FROM PublishedReleases WHERE pubReleaseId = ?", pubReleaseId)
            res = cu.fetchone()
            if res:
                return bool(res[0])
        return False

    def getUnpublishedBuilds(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM BuildsView
                      WHERE projectId = ? AND pubReleaseId IS NULL""",
                      projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def deleteBuild(self, buildId):
        try:
            cu = self.db.cursor()
            cu.execute("UPDATE Builds SET deleted=1 WHERE buildId=?", buildId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def buildExists(self, buildId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM BuildsView WHERE buildId=?", buildId)
        return cu.fetchone()[0]

    def bumpBuildCount(self, buildId):
        # This is a post-increment, unlike bumpCookCount, since we always want
        # to look at the last build.
        cu = self.db.cursor()
        cu.execute("SELECT buildCount FROM Builds WHERE buildId=?",
                   buildId)
        res = cu.fetchall()
        if res:
            count = res[0][0] + 1
            cu.execute("""UPDATE Builds
                              SET buildCount=?
                              WHERE buildId=?""", count, buildId)
            return count
        else:
            return None


def getExtraFlags(buildFlavor):
    """Return a list of human-readable strings describing various
       characteristics that a flavor may have, defined by the
       flavorFlags dictionary in buildtypes.py.
    """
    if type(buildFlavor) == str:
        buildFlavor = deps.ThawFlavor(buildFlavor)

    extraFlags = []
    for flag, flavor in buildtypes.flavorFlagFlavors.items():
        if buildFlavor.stronglySatisfies(deps.parseFlavor(flavor)):
            extraFlags.append(buildtypes.flavorFlagNames[flag])

    return extraFlags


def getImportantFlavors(buildFlavor):
    """Return a list of machine-readable string suitable for storage
       in a database, to store various 'important' pieces of information about
       a flavor for quick retrieval and search.
    """
    if type(buildFlavor) == str:
        buildFlavor = deps.ThawFlavor(buildFlavor)

    flavors = []
    for id, flavor in buildtypes.flavorFlagFlavors.items():
        if buildFlavor is not None and buildFlavor.stronglySatisfies(deps.parseFlavor(flavor)):
            flavors.append(buildtypes.flavorFlagsFromId[id])

    return flavors


class Build(database.TableObject):
    __slots__ = BuildsTable.fields

    def __eq__(self, val):
        for item in [x for x in self.__slots__ if x not in \
                     ('buildId', 'troveLastChanged', 'timeCreated')]:
            if self.__getattribute__(item) != val.__getattribute__(item):
                return False
        return self.getDataDict() == val.getDataDict()

    def getItem(self, id):
        return self.server.getBuild(id)

    def getId(self):
        return self.buildId

    def getName(self):
        return self.name

    def setName(self, name):
        return self.server.setBuildName(self.buildId, name.strip())

    def getDefaultName(self):
        """ Returns a generated build name based on the group trove
            the build is based upon and its version. This should be
            as a default name if the user doesn't supply one in the UI."""
        return "%s=%s" % (self.getTroveName(),
                self.getTroveVersion().trailingRevision().asString())

    def getDesc(self):
        return self.description

    def setDesc(self, desc):
        return self.server.setBuildDesc(self.buildId, desc.strip())

    def getProjectId(self):
        return self.projectId

    def getUserId(self):
        return self.userId

    def getTrove(self):
        return tuple(self.server.getBuildTrove(self.buildId))

    def getTroveName(self):
        return self.troveName

    def getTroveVersion(self):
        return versions.ThawVersion(self.troveVersion)

    def getTroveFlavor(self):
        return deps.ThawFlavor(self.troveFlavor)

    def getChangedTime(self):
        return self.troveLastChanged

    def setTrove(self, troveName, troveVersion, troveFlavor):
        self.server.setBuildTrove(self.buildId,
            troveName, troveVersion, troveFlavor)
        self.refresh()

    def setBuildType(self, buildType):
        assert(buildType in buildtypes.TYPES)
        self.buildType = buildType
        return self.server.setBuildType(self.buildId, buildType)

    def getBuildType(self):
        if not self.buildType:
            self.buildType = self.server.getBuildType(self.buildId)
        return self.buildType

    def getStatus(self):
        return self.server.getBuildStatus(self.id)

    def getFiles(self):
        return self.server.getBuildFilenames(self.buildId)

    def setFiles(self, filenames):
        return self.server.setBuildFilenames(self.buildId, filenames)

    def getArch(self):
        """Return a printable representation of the build's architecture."""
        return helperfuncs.getArchFromFlavor(self.getTrove()[2])

    def getArchFlavor(self):
        """Return a conary.deps.Flavor object representing the build's architecture."""
        f = deps.ThawFlavor(self.getTrove()[2])

        if f.members and deps.DEP_CLASS_IS in f.members:
            # search through our pathSearchOrder and find the
            # best single architecture flavor for this build
            for x in [deps.ThawFlavor(y) for y in flavors.pathSearchOrder]:
                if f.satisfies(x):
                    return x
        return deps.Flavor()

    def setPublished(self, pubReleaseId, published):
        return self.server.setBuildPublished(self.buildId,
                pubReleaseId, published)

    def getPublished(self):
        return self.server.getBuildPublished(self.buildId)

    def getDataTemplate(self):
        return buildtemplates.getDataTemplate(self.buildType)

    def setDataValue(self, name, value, dataType = None, validate = True):
        template = self.getDataTemplate()
        if (name not in template and validate) or (dataType is None and not validate):
            raise BuildDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        if dataType == RDT_ENUM and value not in template[name][3].values():
            raise ParameterError("%s is not a legal enumerated value" % value)
        return self.server.setBuildDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name, validate = True):
        template = self.getDataTemplate()
        isPresent, val = self.server.getBuildDataValue(self.getId(), name)
        if (not isPresent and name not in template) and validate:
            raise BuildDataNameError( "%s not in data template" % name)
        if not isPresent and name in template:
            val = template[name][1]
        return val

    def getDataDict(self):
        dataDict = self.server.getBuildDataDict(self.getId())
        template = self.getDataTemplate()
        for name in list(template):
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict

    def serialize(self):
        return self.server.serializeBuild(self.buildId)

    def addFileUrl(self, fileId, urlType, url):
        return self.server.addFileUrl(self.getId(), fileId, urlType, url)

    def removeFileUrl(self, fileId, urlId):
        return self.server.removeFileUrl(self.getId(), fileId, urlId)

    def deleteBuild(self):
        return self.server.deleteBuild(self.getId())

    def resolveExtraTrove(self, trvName, trvVersion = '', trvFlavor = '', searchPath = []):
        return self.server.resolveExtraBuildTrove(self.id, trvName, trvVersion, trvFlavor, searchPath)
