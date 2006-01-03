#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#
import urlparse
import time
import sys

import database
import jobs
import releasetypes
from mint_error import MintError 
from data import RDT_STRING, RDT_BOOL, RDT_INT

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

installableIsoTemplate = {
    'installLabelPath': (RDT_STRING, '',  'Default Conary installLabelPath setting'),
    'autoResolve':      (RDT_BOOL, False, "Add 'autoResolve True' to default /etc/conaryrc"),
    'skipMediaCheck':   (RDT_BOOL, False, 'Skip prompt for ISO media check'),
    'betaNag':          (RDT_BOOL, False, 'Show a "beta nag" screen before installation'),
    'bugsUrl':          (RDT_STRING, 'http://bugs.rpath.com/', 'Bug report URL advertised in installer')
}

stubImageTemplate = {
    'boolArg'   : (RDT_BOOL, False, 'Garbage Boolean'),
    'stringArg' : (RDT_STRING, '', 'Garbage String'),
    'intArg'    : (RDT_INT, 0, 'Garbage Integer'),
}

# It is not necessary to define templates for image types with no settings
dataTemplates = {
    releasetypes.INSTALLABLE_ISO : installableIsoTemplate,
    releasetypes.STUB_IMAGE      : stubImageTemplate,
}

class ReleasesTable(database.KeyedTable):
    name = "Releases"
    key = "releaseId"

    createSQL = """
                CREATE TABLE Releases (
                    releaseId            INTEGER PRIMARY KEY,
                    projectId            INT,
                    name                 STR,
                    description          STR,
                    imageType            INT,
                    troveName            STR,
                    troveVersion         STR,
                    troveFlavor	         STR,
                    troveLastChanged     INT,
                    published            INT DEFAULT 0,
                    downloads            INT DEFAULT 0,
                    timePublished        INT
                )"""
    createSQL_mysql = """
                CREATE TABLE Releases (
                    releaseId            INT PRIMARY KEY AUTO_INCREMENT,
                    projectId            INT,
                    name                 VARCHAR(128),
                    description          VARCHAR(255),
                    imageType            INT,
                    troveName            VARCHAR(128),
                    troveVersion         VARCHAR(255),
                    troveFlavor	         VARCHAR(4096),
                    troveLastChanged     INT,
                    published            INT DEFAULT 0,
                    downloads            INT DEFAULT 0,
                    timePublished        INT
                )"""

    fields = ['releaseId', 'projectId', 'name', 'description', 'imageType',
              'troveName', 'troveVersion', 'troveFlavor',
              'troveLastChanged', 'published', 'downloads', 'timePublished']
    indexes = {"ReleaseProjectIdIdx": """CREATE INDEX ReleaseProjectIdIdx
                                             ON Releases(projectId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 3:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Releases ADD COLUMN timePublished INT DEFAULT 0")
                cu.execute("UPDATE Releases SET timePublished=0")
                return (dbversion + 1) == self.schemaVersion
            if dbversion == 4:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE Releases ADD COLUMN description STR")
                cu.execute("UPDATE Releases SET description=desc")
                return (dbversion + 1) == self.schemaVersion
        return True
    
    def new(self, **kwargs):
        projectId = kwargs['projectId']
        cu = self.db.cursor()
        cu.execute("DELETE FROM Releases WHERE projectId=? AND troveLastChanged IS NULL", projectId)
        self.db.commit()
        return database.KeyedTable.new(self, **kwargs)

    def get(self, id):
        res = database.KeyedTable.get(self, id)
        res['published'] = bool(res['published'])
        return res

    def iterReleasesForProject(self, projectId, showUnpublished = False):
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
                            """ + published + " ORDER BY releaseId DESC",
                   projectId)
        for results in cu.fetchall():
            yield results[0]

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
    __slots__ = [ReleasesTable.key] + ReleasesTable.fields

    def getItem(self, id):
        return self.server.getRelease(id)

    def getId(self):
        return self.releaseId

    def getName(self):
        return self.name

    def getDesc(self):
        return self.description

    def setDesc(self, desc):
        return self.server.setReleaseDesc(self.releaseId, desc)

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

    def setImageType(self, imageType):
        assert(imageType in releasetypes.TYPES)
        
        return self.server.setImageType(self.releaseId, imageType)

    def getImageType(self):
        return self.imageType

    def getImageTypeName(self):
        return releasetypes.typeNames[self.getImageType()]

    def getJob(self):
        jobId = self.server.getJobIdsForRelease(self.id)
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
        self.refresh()
        try:
            return dataTemplates[self.getImageType()]
        except KeyError:
            return {}

    def setDataValue(self, name, value, dataType = None):
        template = self.getDataTemplate()
        if name not in template:
            raise ReleaseDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        return self.server.setReleaseDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name):
        template = self.getDataTemplate()
        if name not in template:
            raise ReleaseDataNameError("Named value not in data template: %s" %name)
        isPresent, val = self.server.getReleaseDataValue(self.getId(), name)
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
