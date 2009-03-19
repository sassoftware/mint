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

class ReleaseManager(object):
    def __init__(self, cfg, db, auth):
        self.cfg = cfg
        self.db = db
        self.auth = auth

    def listReleasesForProduct(self, fqdn):
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
        JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
        JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
        LEFT JOIN Users as PublishUser ON (publishedBy=PublishUser.userId)
        WHERE hostname=?'''
        cu.execute(sql, hostname)
        releases = models.ReleaseList()
        for row in cu:
            row = dict(row)
            row['published'] = bool(row['timePublished'])
            releases.releases.append(models.Release(**row))
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
        JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
        JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
        LEFT JOIN Users as PublishUser ON (publishedBy=PublishUser.userId)
        WHERE hostname=? and releaseId=?'''
        cu.execute(sql, hostname, releaseId)
        row = dict(self.db._getOne(cu, errors.ReleaseNotFound, 
                                   (hostname, releaseId)))
        return models.Release(**row)

    def createRelease(self, fqdn, buildIds):
        hostname = fqdn.split('.')[0]
        sql = '''
        INSERT INTO PublishedReleases 
            (projectId, timeCreated, createdBy)
            SELECT projectId, ?, ? FROM Projects WHERE hostname=?
        '''
        cu = self.db.cursor()
        cu.execute(sql, time.time(), self.auth.userId, hostname)
        releaseId = cu.lastrowid
        for buildId in buildIds:
            self._addBuildToRelease(hostname, releaseId, buildId)
        return releaseId

    def _addBuildToRelease(self, hostname, releaseId, imageId):
        image = self.db.getImageForProduct(hostname, imageId)
        if image.release and releaseId != image.release:
            raise mint_error.BuildPublished()
        if (image.imageType not in (buildtypes.AMI, buildtypes.IMAGELESS)
                and not image.files.files):
            raise mint_error.BuildEmpty()
        cu = self.db.cursor()
        cu.execute('''UPDATE Builds SET pubReleaseId=?
                      WHERE buildId=?''', releaseId, imageId)
