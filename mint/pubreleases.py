#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
from mint.db import pubreleases
from mint.lib import database

class PublishedRelease(database.TableObject):

    __slots__ = pubreleases.PublishedReleasesTable.fields

    def getItem(self, id):
        return self.server.getPublishedRelease(id)

    def addBuild(self, buildId):
        return self.server.setBuildPublished(buildId, self.id, True)

    def removeBuild(self, buildId):
        return self.server.setBuildPublished(buildId, self.id, False)

    def getBuilds(self):
        return self.server.getBuildsForPublishedRelease(self.id)

    def getUniqueBuildTypes(self):
        return self.server.getUniqueBuildTypesForPublishedRelease(self.id)

    def isPublished(self):
        return self.server.isPublishedReleasePublished(self.id)

    def save(self):
        valDict = {'name': self.name,
                   'version': self.version,
                   'description': self.description}
        return self.server.updatePublishedRelease(self.pubReleaseId, valDict)

    def publish(self, shouldMirror=False):
        self.server.publishPublishedRelease(self.pubReleaseId, shouldMirror)
        return True

    def unpublish(self):
        self.server.unpublishPublishedRelease(self.pubReleaseId)
        return True
