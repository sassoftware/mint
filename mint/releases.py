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
from mint import releasetypes
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint.mint_error import MintError, ParameterError
from mint.releasetemplates import dataHeadings, dataTemplates

from conary import versions
from conary.deps import deps


class TroveNotSet(MintError):
    def __str__(self):
        return "this release needs a be associated with a group or fileset trove."

class ReleaseMissing(MintError):
    def __str__(self):
        return "the requested release does not exist."

class ReleaseDataNameError(MintError):
    def __str__(self):
        return self.str

    def __init__(self, reason = None):
        if reason is None:
            self.str = "Named value is not in data template."
        else:
            self.str = reason

class ReleasesTable(database.KeyedTable):
    name = "Releases"
    key = "releaseId"

    createSQL = """
                CREATE TABLE Releases (
                    releaseId            %(PRIMARYKEY)s,
                    projectId            INT,
                    name                 VARCHAR(128),
                    description          TEXT,
                    troveName            VARCHAR(128),
                    troveVersion         VARCHAR(255),
                    troveFlavor	         VARCHAR(4096),
                    troveLastChanged     INT,
                    published            INT DEFAULT 0,
                    downloads            INT DEFAULT 0,
                    timePublished        INT
                )"""

    fields = ['releaseId', 'projectId', 'name', 'description',
              'troveName', 'troveVersion', 'troveFlavor',
              'troveLastChanged', 'published', 'downloads', 'timePublished']
    indexes = {"ReleaseProjectIdIdx": """CREATE INDEX ReleaseProjectIdIdx
                                             ON Releases(projectId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 3 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Releases ADD COLUMN timePublished INT DEFAULT 0")
                cu.execute("UPDATE Releases SET timePublished=0")
            if dbversion == 4 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Releases ADD COLUMN description STR")
                cu.execute("UPDATE Releases SET description=desc")
            if dbversion == 14:
                from mint.distro import jsversion
                cu = self.db.cursor()
                cu.execute("""INSERT INTO ReleaseData
                                  SELECT DISTINCT releaseId, 'jsversion',
                                                  '%s', 0
                                      FROM Releases
                                      WHERE releaseId NOT IN
                                          (SELECT DISTINCT releaseId
                                               FROM ReleaseData
                                               WHERE name='jsversion')""" % \
                           jsversion.getDefaultVersion())
            return dbversion >= 14
        return True

    def new(self, **kwargs):
        projectId = kwargs['projectId']
        cu = self.db.cursor()
        cu.execute("""SELECT releaseId FROM Releases
                          WHERE projectId=?
                          AND troveLastChanged IS NULL""", projectId)
        for releaseId in [x[0] for x in cu.fetchall()]:
            cu.execute("DELETE FROM ReleaseData WHERE releaseId=?", releaseId)
        cu.execute("""DELETE FROM Releases
                        WHERE projectId=?
                        AND troveLastChanged IS NULL""", projectId)
        self.db.commit()
        return database.KeyedTable.new(self, **kwargs)

    def get(self, id):
        cu = self.db.cursor()
        fields = [ self.name + "." + x for x in self.fields ]
        stmt = """
            SELECT %s, ReleaseImageTypes.imageType
            FROM %s LEFT OUTER JOIN ReleaseImageTypes ON Releases.%s=ReleaseImageTypes.%s
            WHERE Releases.%s=?
            """ % (", ".join(fields), self.name, self.key, self.key, self.key)
        cu.execute(stmt, id)

        #The above query returns something like
        # | FOO | BAR | 0 |
        # | FOO | BAR | 1 |
        # | FOO | BAR | 2 |
        # | FOO | BAR | 3 |
        #The following code converts that to
        # [ FOO, BAR, [0, 1, 2, 3]]
        rows = cu.fetchall()
        if not rows:
            raise database.ItemNotFound
        imageTypes = []
        for row in rows:
            if row[-1] is not None:
                imageTypes.append(int(row[-1]))

        row = rows[-1]
        res = {}
        for i, key in enumerate(self.fields):
            if row[i] is not None:
                res[key] = row[i]
            else:
                res[key] = ''

        res['projectId'] = int(res['projectId'])
        res['releaseId'] = int(res['releaseId'])
        res['published'] = bool(res['published'])
        res['imageTypes'] = imageTypes
        return res

    def iterReleasesForProject(self, projectId, showUnpublished = False):
        """ Returns an iterator over the all of the releaseIds in a given
            project with ID projectId. Optionally screens out unpublished
            releases (by default). The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        if showUnpublished:
            published = ""
        else:
            published = " AND published=1"

        cu.execute("""SELECT releaseId FROM Releases
                      WHERE projectId=? AND
                            troveName IS NOT NULL AND
                            troveVersion IS NOT NULL AND
                            troveFlavor IS NOT NULL AND
                            troveLastChanged IS NOT NULL
                            """ + published + """ ORDER BY
                                troveLastChanged DESC, releaseId""",
                   projectId)

        for results in cu.fetchall():
            yield int(results[0])

    def setTrove(self, releaseId, troveName, troveVersion, troveFlavor):
        cu = self.db.cursor()
        cu.execute("""UPDATE Releases SET troveName=?,
                                          troveVersion=?,
                                          troveFlavor=?,
                                          troveLastChanged=?
                      WHERE releaseId=?""",
                   troveName, troveVersion,
                   troveFlavor, time.time(),
                   releaseId)
        self.db.commit()
        return 0

    def getTrove(self, releaseId):
        cu = self.db.cursor()

        cu.execute("""SELECT troveName,
                             troveVersion,
                             troveFlavor
                      FROM Releases
                      WHERE releaseId=?""",
                   releaseId)
        r = cu.fetchone()

        name, version, flavor = r[0], r[1], r[2]
        if not flavor:
            flavor = "none"
        if not name or not version:
            raise TroveNotSet
        else:
            return name, version, flavor

    def getPublished(self, releaseId):
        cu = self.db.cursor()

        cu.execute("SELECT IFNULL((SELECT published FROM Releases WHERE releaseId=?), 0)", releaseId)
        return bool(cu.fetchone()[0])

    def deleteRelease(self, releaseId):
        cu = self.db.transaction()
        try:
            r = cu.execute("DELETE FROM Releases WHERE releaseId=?", releaseId)
            r = cu.execute("DELETE FROM ReleaseData WHERE releaseId=?", releaseId)
            r = cu.execute("DELETE FROM Jobs WHERE releaseId=?", releaseId)
            r = cu.execute("DELETE FROM ImageFiles WHERE releaseId=?", releaseId)
        except:
            self.db.rollback()
        else:
            self.db.commit()

    def releaseExists(self, releaseId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM Releases WHERE releaseId=?", releaseId)
        return cu.fetchone()[0]

class Release(database.TableObject):
    __slots__ = ReleasesTable.fields + ['imageTypes']

    def __eq__(self, val):
        for item in [x for x in self.__slots__ if x not in \
                     ('published', 'releaseId', 'troveLastChanged',
                      'timePublished')]:
            if self.__getattribute__(item) != val.__getattribute__(item):
                return False
        return self.getDataDict() == val.getDataDict()

    def getItem(self, id):
        return self.server.getRelease(id)

    def getId(self):
        return self.releaseId

    def getName(self):
        return self.name

    def setName(self, name):
        return self.server.setReleaseName(self.releaseId, name.strip())

    def getDefaultName(self):
        """ Returns a generated release name based on the group trove
            the release is based upon and its version. This should be
            as a default name if the user doesn't supply one in the UI."""
        return "%s=%s" % (self.getTroveName(),
                self.getTroveVersion().trailingRevision().asString())

    def getDesc(self):
        return self.description

    def setDesc(self, desc):
        return self.server.setReleaseDesc(self.releaseId, desc.strip())

    def getProjectId(self):
        return self.projectId

    def getUserId(self):
        return self.userId

    def getTrove(self):
        return tuple(self.server.getReleaseTrove(self.releaseId))

    def getTroveName(self):
        return self.troveName

    def getTroveVersion(self):
        return versions.ThawVersion(self.troveVersion)

    def getTroveFlavor(self):
        return deps.ThawDependencySet(self.troveFlavor)

    def getChangedTime(self):
        return self.troveLastChanged

    def setTrove(self, troveName, troveVersion, troveFlavor):
        self.server.setReleaseTrove(self.releaseId,
            troveName, troveVersion, troveFlavor)
        self.refresh()

    def setImageTypes(self, imageTypes):
        for imageType in imageTypes:
            assert(imageType in releasetypes.TYPES)
        oldimagetypes = self.imageTypes
        self.imageTypes = imageTypes
        try:
            return self.server.setImageTypes(self.releaseId, imageTypes)
        except:
            self.imageTypes = oldimagetypes
            raise

    def getImageTypes(self):
        if not self.imageTypes:
            self.imageTypes = self.server.getImageTypes(self.releaseId)
        return self.imageTypes

    #This function is not used
    #def getImageTypeName(self, type):
    #    return releasetypes.typeNames[type]

    def getJob(self):
        jobId = self.server.getJobIdForRelease(self.id)
        if jobId:
            return jobs.Job(self.server, jobId)
        else:
            return None

    def getFiles(self):
        return self.server.getImageFilenames(self.releaseId)

    def setFiles(self, filenames):
        return self.server.setImageFilenames(self.releaseId, filenames)

    def getArch(self):
        flavor = deps.ThawDependencySet(self.getTrove()[2])
        if flavor.members:
            return flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        else:
            return "none"

    def getDownloads(self):
        return self.downloads

    def incDownloads(self):
        return self.server.incReleaseDownloads(self.releaseId)

    def getPublished(self):
        return self.published

    def setPublished(self, published):
        return self.server.setReleasePublished(self.releaseId, published)

    def getDataTemplate(self):
        if len(self.imageTypes):
            return dataTemplates[self.imageTypes[0]]
        else:
            return {}

    def getDisplayTemplates(self):
        return [(x, dataHeadings[x], dataTemplates[x]) \
                for x in dataTemplates.keys()]
        # FIXME: use the following code once we revert to new release model
        if len(self.imageTypes):
            return [(dataHeadings[self.imageTypes[0]], \
                     dataTemplates[self.imageTypes[0]])]
        else:
            return 'No Image Selected', {}

    def setDataValue(self, name, value, dataType = None, validate = True):
        template = self.getDataTemplate()
        if (name not in template and validate) or (dataType is None and not validate):
            raise ReleaseDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        if dataType == RDT_ENUM and value not in template[name][3].values():
            raise ParameterError("%s is not a legal enumerated value" % value)
        return self.server.setReleaseDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name):
        template = self.getDataTemplate()
        isPresent, val = self.server.getReleaseDataValue(self.getId(), name)
        if not isPresent and name not in template:
            raise ReleaseDataNameError( "%s not in data template" % name)
        if not isPresent:
            val = template[name][1]
        return val

    def getDataDict(self):
        dataDict = self.server.getReleaseDataDict(self.getId())
        template = self.getDataTemplate()
        for name in list(template):
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict

    def deleteRelease(self):
        return self.server.deleteRelease(self.getId())

    def hasVMwareImage(self):
        """ Returns True if release has a VMware player image. """
        filelist = self.getFiles()
        for file in filelist:
            if file["filename"].endswith(".vmware.zip"):
                return True
        return False

class ReleaseImageTypesTable(database.DatabaseTable):
    name = "ReleaseImageTypes"
    createSQL = """
        CREATE TABLE ReleaseImageTypes (
            releaseId   INT,
            imageType   INT,
            PRIMARY KEY (releaseId, imageType)
        )"""

    indexes = {'ReleaseImageTypesIdx': 'CREATE INDEX ReleaseImageTypesIdx ON ReleaseImageTypes (releaseId, imageType)'
              }

    fields = ['releaseId, imageType']
