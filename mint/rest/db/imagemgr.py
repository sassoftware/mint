#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.deps import deps
from conary import versions

from mint import buildtypes
from mint.rest import errors
from mint.rest.api import models

class ImageManager(object):
    def __init__(self, cfg, db, auth):
        self.cfg = cfg
        self.db = db
        self.auth = auth

    def _getImages(self, fqdn, extraJoin='', extraWhere='',
                   extraArgs=None, getOne=False):
        hostname = fqdn.split('.')[0]
        sql = '''
        SELECT buildId as imageId, hostname,
               pubReleaseId as release,  
               buildType as imageType, Builds.name, Builds.description, 
               troveName, troveVersion, troveFlavor, troveLastChanged,
               Builds.timeCreated, CreateUser.username as creator, 
               Builds.timeUpdated, 
               ProductVersions.name as version, stageName as stage,
               UpdateUser.username as updater, buildCount
            FROM Builds 
            %(join)s
            JOIN Projects USING(projectId)
            LEFT JOIN ProductVersions 
                ON(Builds.productVersionId=ProductVersions.productVersionId)
            JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
            LEFT JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
            WHERE hostname=? AND deleted=0 %(where)s''' 
        sql = sql % dict(where=extraWhere, join=extraJoin)
        args = (hostname,)
        if extraArgs:
            args += tuple(extraArgs)
        cu = self.db.cursor()
        rows = cu.execute(sql, *args)
        if getOne:
            row = self.db._getOne(cu, errors.ImageNotFound, args)
            rows = [row]

        images = []
        for row in rows:
            row = dict(row)
            row['troveFlavor'] = deps.ThawFlavor(row['troveFlavor'])
            row['troveVersion'] = versions.ThawVersion(row['troveVersion'])
            row['trailingVersion'] = str(row['troveVersion'].trailingRevision())
            row['imageType'] = buildtypes.typeNamesShort[row['imageType']]
            image = models.Image(**row)
            image.files = self.listFilesForImage(hostname, image.imageId)
            images.append(image)
        if getOne:
            return images[0]
        return models.ImageList(images)

    def listImagesForProduct(self, fqdn):
        return self._getImages(fqdn)

    def getImageForProduct(self, fqdn, imageId):
        return self._getImages(fqdn, '', 'AND imageId=?', [imageId], getOne=True)

    def listImagesForRelease(self, fqdn, releaseId):
        return self._getImages(fqdn, '', ' AND pubReleaseId=?', 
                               [releaseId])

    def listImagesForProductVersion(self, fqdn, version):
        return self._getImages(fqdn, '',
                               ' AND ProductVersions.name=?', [version])
    
    def listImagesForTrove(self, fqdn, name, version, flavor):
        images =  self._getImages(fqdn, '', 
                                  ' AND troveName=? AND troveFlavor=?',
                                    [name, flavor.freeze()])
        images.images = [ x for x in images.images 
                          if x.troveVersion == version ]
        return images

    def listImagesForProductVersionStage(self, fqdn, version, stageName):
        return self._getImages(fqdn, '',
                              ' AND ProductVersions.name=? AND stageName=?', 
                              [version, stageName])

    def listFilesForImage(self, fqdn, imageId):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        cu.execute('''SELECT fileId, buildId,
                      filename, title, size, sha1
                      FROM BuildFiles
                      JOIN Builds USING(buildId)
                      JOIN Projects USING(projectId)
                      WHERE buildId=? and hostname=?
                      ORDER BY idx''', imageId, hostname)
        imageFiles = []
        for row in cu:
            d = dict(row)
            d['imageId'] = d.pop('buildId')
            file = models.ImageFile(**d)
            imageFiles.append(file)
        for file in imageFiles:
            cu.execute('''SELECT urlType, url
                          FROM BuildFilesUrlsMap 
                          JOIN FilesUrls USING(urlId)
                          WHERE fileId=?''', file.fileId)
            urls = []
            for row in cu:
                d = dict(row)
                urls.append(models.FileUrl(**d))
            file.urls = urls
        return models.ImageFileList(imageFiles)
