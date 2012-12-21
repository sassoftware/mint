#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

from mint import builds
from mint import helperfuncs
from mint.lib import database
from mint.mint_error import ItemNotFound

class PublishedReleasesTable(database.KeyedTable):

    name = "PublishedReleases"
    key  = "pubReleaseId"

    fields = [ 'pubReleaseId', 'projectId', 'name', 'version', 'description',
               'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy',
               'timePublished', 'publishedBy', 'shouldMirror', 'timeMirrored' ]

    indexes = { "PubReleasesProjectIdIdx": \
                   """CREATE INDEX PubReleasesProjectIdIdx
                          ON PublishedReleases(projectId)""" }

    def delete(self, id):
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET pubReleaseId = NULL
                      WHERE pubReleaseId = ?""", id)
        self.db.commit()
        database.KeyedTable.delete(self, id)

    def publishedReleaseExists(self, pubReleaseId):
        try:
            pubRelease = self.get(pubReleaseId, fields=['pubReleaseId'])
        except ItemNotFound:
            return False
        return True

    def isPublishedReleasePublished(self, pubReleaseId):
        pubRelease = self.get(pubReleaseId, fields=['timePublished'])
        return bool(pubRelease['timePublished'])

    def getBuilds(self, pubReleaseId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM Builds
                      WHERE pubReleaseId = ?""", pubReleaseId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def getPublishedReleaseList(self, limit = 10, offset = 0):
        cu = self.db.cursor()
        cu.execute("""SELECT Proj.name, Proj.hostname, PubRel.pubReleaseId
                      FROM Projects Proj LEFT JOIN PublishedReleases PubRel
                         ON Proj.projectId = PubRel.projectId
                      WHERE NOT Proj.hidden
                         AND PubRel.timePublished IS NOT NULL
                      ORDER BY PubRel.timePublished DESC LIMIT ? OFFSET ?""",
                      limit, offset)
        return [(x[0], x[1], int(x[2])) for x in cu.fetchall()]

    def getPublishedReleasesByProject(self, projectId, publishedOnly=False):
        sql = """SELECT pubReleaseId FROM PublishedReleases
                 WHERE projectId = ? %s
                 ORDER BY timePublished DESC, timeUpdated DESC""" % \
                        (publishedOnly and " AND timePublished IS NOT NULL" or "")

        cu = self.db.cursor()
        cu.execute(sql, projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def getProject(self, pubReleaseId):
        data = self.get(pubReleaseId, ['projectId'])
        return data['projectId']

    def getUniqueBuildTypes(self, pubReleaseId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildType, troveFlavor
                      FROM Builds WHERE pubReleaseId = ?
                      ORDER BY buildType, troveFlavor""", pubReleaseId)
        uniqueBuildTypes = []
        for row in cu.fetchall():
            buildType, arch = row[0], helperfuncs.getArchFromFlavor(row[1])
            extraFlags = builds.getExtraFlags(row[1])

            if (buildType, arch) not in uniqueBuildTypes:
                uniqueBuildTypes.append((buildType, arch, extraFlags))

        return uniqueBuildTypes

    def getMirrorableReleasesByProject(self, projectId):
        cu = self.db.cursor()
        cu.execute("""
            SELECT pubReleaseId FROM PublishedReleases
                WHERE projectId = ?
                    AND timePublished IS NOT NULL
                    AND shouldMirror = 1
                ORDER BY timePublished ASC
            """, projectId)
        return [x[0] for x in cu.fetchall()]

    def getAMIBuildsForPublishedRelease(self, pubReleaseId):
        cu = self.db.cursor()
        cu.execute("""
            SELECT pr.pubReleaseId,
                   COALESCE(pr.timePublished,0) != 0 as isPublished,
                   p.hidden as isPrivate,
                   bd.value as amiId,
                   p.projectId as projectId
            FROM PublishedReleases pr
                 JOIN Projects p
                 ON p.projectId = pr.projectId
                 JOIN Builds b
                 ON b.pubReleaseId = pr.pubReleaseId
                 JOIN BuildData bd
                 ON bd.buildId = b.buildId
            WHERE bd.name = 'amiId'
              AND pr.pubReleaseId = ?
            """, pubReleaseId)
        return cu.fetchall()
