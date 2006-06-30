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
        cu.execute("""UPDATE Products SET pubReleaseId = NULL
                      WHERE pubReleaseId = ?""", id)
        self.db.commit()
        database.KeyedTable.delete(self, id)

    def publishedReleaseExists(self, pubReleaseId):
        try:
            pubRelease = self.get(pubReleaseId, fields=['pubReleaseId'])
        except ItemNotFound:
            return False
        return True

    def isPublishedReleaseFinalized(self, pubReleaseId):
        pubRelease = self.get(pubReleaseId, fields=['timePublished'])
        return bool(pubRelease['timePublished'])

    def getProducts(self, pubReleaseId):
        cu = self.db.cursor()
        cu.execute("""SELECT productId FROM Products
                      WHERE pubReleaseId = ?""", pubReleaseId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def getPublishedReleases(self, projectId, finalizedOnly=False):
        sql = """SELECT pubReleaseId FROM PublishedReleases
                 WHERE projectId = ?"""

        if finalizedOnly:
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

    def addProduct(self, productId):
        return self.server.setProductPublished(productId, self.id, True)

    def removeProduct(self, productId):
        return self.server.setProductPublished(productId, self.id, False)

    def getProducts(self):
        return self.server.getProductsForPublishedRelease(self.id)

    def isFinalized(self):
        return self.server.isPublishedReleaseFinalized(self.id)

    def save(self):
        valDict = {'name': self.name,
                   'version': self.version,
                   'description': self.description}
        return self.server.updatePublishedRelease(self.pubReleaseId, valDict)

    def finalize(self):
        return self.server.finalizePublishedRelease(self.pubReleaseId)


