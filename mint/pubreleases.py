#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

VISIBILITY_PUBLIC = 1
VISIBILITY_PROJECT_ONLY = 0

class PublishedReleasesTable(database.KeyedTable):

    name = "PublishedReleases"
    key  = "pubReleaseId"

    createSQL = """
                CREATE TABLE PublishedReleases (
                    pubReleaseId        %(PRIMARYKEY)s,
                    projectId           INTEGER,
                    name                VARCHAR(255),
                    description         TEXT,
                    visibility          SMALLINT,
                    timeCreated         DOUBLE,
                    createdBy           INTEGER,
                    timeUpdated         DOUBLE,
                    updatedBy           INTEGER
                )"""

    fields = [ 'pubReleaseId', 'projectId', 'name', 'description',
               'visibility', 'timeCreated', 'createdBy', 'timeUpdated',
               'updatedBy' ]

    indexes = { "PubReleasesProjectIdIdx": \
                   """CREATE INDEX PubReleasesProjectIdIdx
                          ON PublishedReleases(projectId)""" }

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

    def isPublicallyVisible(self):
        return self.visibility == VISIBILITY_PUBLIC

    def save(self):
        valDict = {'name': self.name,
                   'description': self.description,
                   'visibility': self.visibility}
        return self.server.updatePublishedRelease(self.pubReleaseId, valDict)


