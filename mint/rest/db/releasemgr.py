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
