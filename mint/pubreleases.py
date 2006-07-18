#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

class PublishedReleasesTable(database.KeyedTable):

    name = "PublishedReleases"
    key  = "pubReleaseId"

    createSQL = """
                CREATE TABLE PublishedReleases (
                    pubReleaseId        %(PRIMARYKEY)s,
                    projectId           INTEGER,
                    name                VARCHAR(255),
                    version             VARCHAR(32),
                    description         TEXT,
                    timeCreated         DOUBLE,
                    createdBy           INTEGER,
                    timeUpdated         DOUBLE,
                    updatedBy           INTEGER,
                    timePublished       DOUBLE,
                    publishedBy         INTEGER
                )"""

    fields = [ 'pubReleaseId', 'projectId', 'name', 'version', 'description',
               'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy',
               'timePublished', 'publishedBy' ]

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
                      WHERE Proj.hidden = 0
                         AND PubRel.timePublished IS NOT NULL
                      ORDER BY PubRel.timePublished DESC LIMIT ? OFFSET ?""",
                      limit, offset)
        return [(x[0], x[1], int(x[2])) for x in cu.fetchall()]

    def getPublishedReleasesByProject(self, projectId, publishedOnly=False):
        sql = """SELECT pubReleaseId FROM PublishedReleases
                 WHERE projectId = ?"""

        if publishedOnly:
            sql += " AND timePublished IS NOT NULL"

        cu = self.db.cursor()
        cu.execute(sql, projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def getProject(self, pubReleaseId):
        data = self.get(pubReleaseId, ['projectId'])
        return data['projectId']

class PublishedRelease(database.TableObject):

    __slots__ = PublishedReleasesTable.fields

    def getItem(self, id):
        return self.server.getPublishedRelease(id)

    def addBuild(self, buildId):
        return self.server.setBuildPublished(buildId, self.id, True)

    def removeBuild(self, buildId):
        return self.server.setBuildPublished(buildId, self.id, False)

    def getBuilds(self):
        return self.server.getBuildsForPublishedRelease(self.id)

    def isPublished(self):
        return self.server.isPublishedReleasePublished(self.id)

    def save(self):
        valDict = {'name': self.name,
                   'version': self.version,
                   'description': self.description}
        return self.server.updatePublishedRelease(self.pubReleaseId, valDict)

    def publish(self):
        return self.server.publishPublishedRelease(self.pubReleaseId)

    def unpublish(self):
        return self.server.unpublishPublishedRelease(self.pubReleaseId)


