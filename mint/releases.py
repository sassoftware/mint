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

import versions
from deps import deps

class TroveNotSet(MintError):
    def __str__(self):
        return "this release needs a be associated with a group or fileset trove."
        
class ReleaseMissing(MintError):
    def __str__(self):
        return "the requested release does not exist"

class Release(object):
    releaseId = None
    name = None
    projectId = None
    userId = None
    desc = None
    trove = (None, None, None)
    imageType = None
    downloads = 0
    published = False

    server = None
    
    def __init__(self, server, releaseId):
        self.releaseId = releaseId
        self.server = server
        self._refresh()

    def _refresh(self):
        data = self.server.getRelease(self.releaseId)
        self.__dict__.update(data)
        self.trove = (self.troveName, self.troveVersion, self.troveFlavor)

    def getId(self):
        return self.releaseId

    def getName(self):
        return self.name

    def getDesc(self):
        self._refresh()
        return self.desc

    def setDesc(self, desc):
        return self.server.setReleaseDesc(self.releaseId, desc)

    def getProjectId(self):
        return self.projectId

    def getUserId(self):
        return self.userId

    def getTrove(self):
        return tuple(self.server.getReleaseTrove(self.releaseId))

    def getTroveName(self):
        return self.trove[0]

    def getTroveVersion(self):
        return versions.ThawVersion(self.trove[1])

    def getTroveFlavor(self):
        return deps.ThawDependencySet(self.trove[2])

    def getChangedTime(self):
        return self.troveLastChanged

    def setTrove(self, troveName, troveVersion, troveFlavor):
        return self.server.setReleaseTrove(self.releaseId,
            troveName, troveVersion, troveFlavor)

    def setImageType(self, imageType):
        assert(imageType in releasetypes.TYPES)

        return self.server.setImageType(self.releaseId, imageType)

    def getImageType(self):
        self._refresh()
        return self.imageType

    def getImageTypeName(self):
        return releasetypes.typeNames[self.getImageType()]

    def getJob(self):
        jobIds = self.server.getJobIds(self.releaseId)
        if len(jobIds) > 0:
            job = jobs.Job(self.server, jobIds[0])
        else:
            job = None
        return job

    def getFiles(self):
        return [(x[0], x[1]) for x in self.server.getImageFilenames(self.releaseId)]

    def setFiles(self, filenames):
        return self.server.setImageFilenames(self.releaseId, filenames)
        
    def getArch(self):
        flavor = deps.ThawDependencySet(self.getTrove()[2])
        if flavor.members:
            return flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        else:
            return "none" 

    def getDownloads(self):
        self._refresh()
        return self.downloads

    def getPublished(self):
        return self.published

    def setPublished(self, published):
        return self.server.setReleasePublished(self.releaseId, published)

class ReleasesTable(database.KeyedTable):
    name = "Releases"
    key = "releaseId"

    createSQL = """
                CREATE TABLE Releases (
                    releaseId            INTEGER PRIMARY KEY,
                    projectId            INT,
                    name                 STR,
                    desc                 STR,
                    imageType            INT,
                    troveName            STR,
                    troveVersion         STR,
                    troveFlavor	         STR,
                    troveLastChanged     INT,
                    published            INT,
                    downloads            INT
                )"""

    fields = ['releaseId', 'projectId', 'name', 'desc', 'imageType',
              'troveName', 'troveVersion', 'troveFlavor',
              'troveLastChanged', 'published', 'downloads']
    indexes = {"ReleaseProjectIdIdx": "CREATE INDEX ReleaseProjectIdIdx ON Releases(projectId)"}

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
                            troveFlavor IS NOT NULL""" + published, projectId)
        for results in cu:
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
