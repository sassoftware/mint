#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

import sys
import time
import urlparse

from mint import database
from mint import jobs
from mint import buildtypes
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint.mint_error import MintError, ParameterError
from mint.buildtemplates import dataHeadings, dataTemplates

from conary import versions
from conary.deps import deps

class TroveNotSet(MintError):
    def __str__(self):
        return "this build needs a be associated with a group or fileset trove."

class BuildMissing(MintError):
    def __str__(self):
        return "the requested build does not exist."

class BuildDataNameError(MintError):
    def __str__(self):
        return self.str

    def __init__(self, reason = None):
        if reason is None:
            self.str = "Named value is not in data template."
        else:
            self.str = reason

class BuildsTable(database.KeyedTable):
    name = "Builds"
    key  = "buildId"

    createSQL = """
                CREATE TABLE Builds (
                    buildId            %(PRIMARYKEY)s,
                    projectId            INTEGER NOT NULL,
                    pubReleaseId         INTEGER,
                    buildType          INTEGER,
                    name                 VARCHAR(255),
                    description          TEXT,
                    troveName            VARCHAR(128),
                    troveVersion         VARCHAR(255),
                    troveFlavor          VARCHAR(4096),
                    troveLastChanged     INTEGER,
                    timeCreated          DOUBLE,
                    createdBy            INTEGER,
                    timeUpdated          DOUBLE,
                    updatedBy            INTEGER
                )"""

    fields = ['buildId', 'projectId', 'pubReleaseId', 
              'buildType', 'name', 'description',
              'troveName', 'troveVersion', 'troveFlavor', 'troveLastChanged',
              'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy']

    indexes = {"BuildProjectIdIdx":\
                 """CREATE INDEX BuildProjectIdIdx
                        ON Builds(projectId)""",
               "BuildPubReleaseIdIdx":\
                 """CREATE INDEX BuildPubReleaseIdIdx
                        ON Builds(pubReleaseId)"""}


    def new(self, **kwargs):
        projectId = kwargs['projectId']
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM Builds
                          WHERE projectId=?
                          AND troveLastChanged IS NULL""", projectId)
        for buildId in [x[0] for x in cu.fetchall()]:
            cu.execute("DELETE FROM BuildData WHERE buildId=?", buildId)
        cu.execute("""DELETE FROM Builds
                        WHERE projectId=?
                        AND troveLastChanged IS NULL""", projectId)
        self.db.commit()
        return database.KeyedTable.new(self, **kwargs)

    def iterBuildsForProject(self, projectId):
        """ Returns an iterator over the all of the buildIds in a given
            project with ID projectId. The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        cu.execute("""SELECT buildId FROM Builds
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
                      FROM Builds
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
        cu.execute("SELECT IFNULL((SELECT pubReleaseId FROM Builds WHERE buildId=?), 0)", buildId)
        pubReleaseId = cu.fetchone()[0]
        if bool(pubReleaseId):
            cu.execute("SELECT IFNULL(timePublished, 0) FROM PublishedReleases WHERE pubReleaseId = ?", pubReleaseId)
            return bool(cu.fetchone()[0])
        return False

    def getUnpublishedBuilds(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM Builds
                      WHERE projectId = ? AND pubReleaseId IS NULL""",
                      projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def deleteBuild(self, buildId):
        cu = self.db.transaction()
        try:
            r = cu.execute("DELETE FROM Builds WHERE buildId=?", buildId)
            r = cu.execute("DELETE FROM BuildData WHERE buildId=?", buildId)
            r = cu.execute("DELETE FROM Jobs WHERE buildId=?", buildId)
            r = cu.execute("DELETE FROM BuildFiles WHERE buildId=?", buildId)
        except:
            self.db.rollback()
        else:
            self.db.commit()

    def buildExists(self, buildId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM Builds WHERE buildId=?", buildId)
        return cu.fetchone()[0]

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

    def getJob(self):
        jobId = self.server.getJobIdForBuild(self.id)
        if jobId:
            return jobs.Job(self.server, jobId)
        else:
            return None

    def getFiles(self):
        return self.server.getBuildFilenames(self.buildId)

    def setFiles(self, filenames):
        return self.server.setBuildFilenames(self.buildId, filenames)

    def getArch(self):
        flavor = deps.ThawFlavor(self.getTrove()[2])
        if flavor.members:
            return flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        else:
            return "none"

    def setPublished(self, pubReleaseId, published):
        return self.server.setBuildPublished(self.buildId,
                pubReleaseId, published)

    def getPublished(self):
        return bool(self.pubReleaseId)

    def getDataTemplate(self):
        if self.buildType:
            return dataTemplates[self.buildType]
        else:
            return {}

    def getDisplayTemplates(self):
        return [(x, dataHeadings[x], dataTemplates[x]) \
                for x in dataTemplates.keys()]
        # FIXME: use the following code once we revert to new build model
        if self.buildType:
            return [(dataHeadings[self.buildType], \
                     dataTemplates[self.buildType])]
        else:
            return 'No Image Selected', {}

    def setDataValue(self, name, value, dataType = None, validate = True):
        template = self.getDataTemplate()
        if (name not in template and validate) or (dataType is None and not validate):
            raise BuildDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        if dataType == RDT_ENUM and value not in template[name][3].values():
            raise ParameterError("%s is not a legal enumerated value" % value)
        return self.server.setBuildDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name):
        template = self.getDataTemplate()
        isPresent, val = self.server.getBuildDataValue(self.getId(), name)
        if not isPresent and name not in template:
            raise BuildDataNameError( "%s not in data template" % name)
        if not isPresent:
            val = template[name][1]
        return val

    def getDataDict(self):
        dataDict = self.server.getBuildDataDict(self.getId())
        template = self.getDataTemplate()
        for name in list(template):
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict

    def deleteBuild(self):
        return self.server.deleteBuild(self.getId())

    def hasVMwareImage(self):
        """ Returns True if build has a VMware player image. """
        filelist = self.getFiles()
        for file in filelist:
            if file["filename"].endswith(".vmware.zip"):
                return True
        return False

