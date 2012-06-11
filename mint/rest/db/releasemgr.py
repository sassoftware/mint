#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import time

from mint import buildtypes
from mint import mint_error
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager

class ReleaseManager(manager.Manager):

    def listReleasesForProduct(self, fqdn, limit=None):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        sql = '''
        SELECT pubReleaseId as releaseId, Projects.hostname,
            PR.name, PR.version, PR.description, PR.timeCreated,  
            PR.timeUpdated, timePublished, 
            CreateUser.username as creator,
            UpdateUser.username as updater, 
            PublishUser.username as publisher, 
            shouldMirror, timeMirrored
        FROM  PublishedReleases as PR
        JOIN Projects USING(projectId)
        LEFT JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
        LEFT JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
        LEFT JOIN Users as PublishUser ON (publishedBy=PublishUser.userId)
        WHERE hostname=?
        ORDER BY COALESCE(timePublished,0) DESC'''
        args = [hostname]
        if limit is not None:
            sql += ' LIMIT ?'
            args.append(limit)
        cu.execute(sql, *args)
        releases = models.ReleaseList()
        for row in cu:
            row['published'] = bool(row['timePublished'])
            release = models.Release(row)
            release.imageCount = self._getBuildCount(row['releaseId'])
            releases.releases.append(release)
        return releases

    def getReleaseForProduct(self, fqdn, releaseId):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        sql = '''
        SELECT pubReleaseId as releaseId, Projects.hostname,
            PR.name, PR.version, PR.description, PR.timeCreated,  
            PR.timeUpdated, timePublished, 
            CreateUser.username as creator,
            UpdateUser.username as updater, 
            PublishUser.username as publisher, 
            shouldMirror, timeMirrored
        FROM  PublishedReleases as PR
        JOIN Projects USING(projectId)
        LEFT JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
        LEFT JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
        LEFT JOIN Users as PublishUser ON (publishedBy=PublishUser.userId)
        WHERE hostname=? and pubReleaseId=?'''
        cu.execute(sql, hostname, releaseId)
        row = self.db._getOne(cu, errors.ReleaseNotFound,
                (hostname, releaseId))
        return models.Release(row)

    def createRelease(self, fqdn, name, description, version, imageIds):
        hostname = fqdn.split('.')[0]
        sql = '''
        INSERT INTO PublishedReleases 
            (projectId, name, description, version, timeCreated, createdBy)
            SELECT projectId, ?, ?, ?, ?, ? FROM Projects WHERE hostname=?
        '''
        cu = self.db.cursor()
        cu.execute(sql, name, description, version, time.time(), 
                   self.auth.userId, hostname)
        releaseId = cu.lastrowid
        for buildId in imageIds:
            self._addBuildToRelease(hostname, releaseId, buildId)
        return releaseId

    def updateImagesForRelease(self, fqdn, releaseId, imageIds):
	cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET pubReleaseId = NULL
                          WHERE pubReleaseId = ?""", releaseId)
        if self._isPublished(releaseId):
            raise mint_error.PublishedReleasePublished
        for imageId in imageIds:
            self._addBuildToRelease(fqdn, releaseId, imageId)

    def updateRelease(self, fqdn, releaseId, name, description, version,
                      published, shouldMirror, imageIds):
        if self._isPublished(releaseId) and published:
            # if we're not switching back to unpublished,
            # then we can't modify a published release.
            raise mint_error.PublishedReleasePublished
        cu = self.db.cursor()
        sql = '''
        UPDATE PublishedReleases SET
            name=?, description=?, version=?, timeUpdated=?, updatedBy=?
            WHERE pubReleaseId=?'''
        cu.execute(sql, name, description, version, time.time(),
                   self.auth.userId, releaseId)
        if imageIds is not None:
            self.updateImagesForRelease(fqdn, releaseId, imageIds)
        if published is not None:
            isPublished, = cu.execute(
                        '''SELECT timePublished from PublishedReleases
                          WHERE pubReleaseId=?''', releaseId).fetchone()
            isPublished = bool(isPublished)
            if bool(isPublished) != bool(published):
                if published:
                    self.publishRelease(releaseId, shouldMirror)
                else:
                    self.unpublishRelease(releaseId)

    def addImageToRelease(self, fqdn, releaseId, imageId):
        self._addBuildToRelease(fqdn, releaseId, imageId)

    def _addBuildToRelease(self, hostname, releaseId, imageId):
        image = self.db.getImageForProduct(hostname, imageId)
        if image.release and releaseId != image.release:
            raise mint_error.BuildPublished()
        if (image.imageType not in ('amiImage', 'imageless')
                and not image.files.files):
            raise mint_error.BuildEmpty()
        cu = self.db.cursor()
        cu.execute('''UPDATE Builds SET pubReleaseId=?
                      WHERE buildId=?''', releaseId, imageId)

    def publishRelease(self, releaseId, shouldMirror):
        if not self._getBuildCount(releaseId):
            raise mint_error.PublishedReleaseEmpty

        if self._isPublished(releaseId):
            raise mint_error.PublishedReleasePublished

        cu = self.db.cursor()
        cu.execute('''UPDATE PublishedReleases 
                      SET timePublished=?, publishedBy=?, 
                      shouldMirror=? WHERE pubReleaseId=?''', 
                      time.time(), self.auth.userId, 
                      int(shouldMirror), releaseId)
        self.publisher.notify('ReleasePublished', releaseId)

    def deleteRelease(self, releaseId):
        if self._isPublished(releaseId):
            raise mint_error.PublishedReleasePublished
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET pubReleaseId = NULL
                      WHERE pubReleaseId = ?""", releaseId)
        cu.execute("""DELETE FROM PublishedReleases WHERE pubReleaseId = ?""",
                   releaseId)

    def _isPublished(self, releaseId):
        cu = self.db.cursor()
        published, = cu.execute('''SELECT timePublished FROM PublishedReleases 
                                   WHERE pubReleaseId=?''', releaseId).next()
        return bool(published)

    def _getBuildCount(self, releaseId):
        cu = self.db.cursor()
        buildCount, = cu.execute(
                    'SELECT COUNT(*) from Builds WHERE pubReleaseId=?',
                    releaseId).next()
        return buildCount

    def unpublishRelease(self, releaseId):
        if not self._isPublished(releaseId):
            raise mint_error.PublishedReleaseNotPublished

        cu = self.db.cursor()
        cu.execute('''UPDATE PublishedReleases 
                      SET timePublished=?, publishedBy=?, 
                      shouldMirror=? WHERE pubReleaseId=?''', 
                      None, None, 0, releaseId)
        self.publisher.notify('ReleaseUnpublished', releaseId)
