#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import time

from conary.deps import deps
from conary import versions

from mint import builds
from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint import urltypes
from mint.lib import data
from mint.rest import errors
from mint.rest.api import models

from mcp import client as mcpclient
from mcp import mcp_error
from conary.lib import cfgtypes

class ImageManager(object):
    def __init__(self, cfg, db, auth):
        self.cfg = cfg
        self.db = db
        self.auth = auth
        self.mcpClient = None

    def __del__(self):
        if self.mcpClient:
            self.mcpClient.disconnect()

    def _getImages(self, fqdn, extraJoin='', extraWhere='',
                   extraArgs=None, getOne=False, update=False):
        hostname = fqdn.split('.')[0]
        # TODO: pull amiId out of here and move into builddata dict ASAP
        sql = '''SELECT Builds.buildId as imageId, hostname,
               pubReleaseId as "release",
               buildType as imageType, Builds.name, Builds.description, 
               troveName, troveVersion, troveFlavor, troveLastChanged,
               Builds.timeCreated, CreateUser.username as creator, 
               Builds.timeUpdated, Builds.status, Builds.statusMessage,
               ProductVersions.name as version, stageName as stage,
               UpdateUser.username as updater, buildCount, 
               BuildData.value as amiId
            FROM Builds
            JOIN Projects USING(projectId)
            %(join)s
            LEFT JOIN ProductVersions 
                ON(Builds.productVersionId=ProductVersions.productVersionId)
            LEFT JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
            LEFT JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
            LEFT JOIN BuildData ON (BuildData.buildId=Builds.buildId 
                                    AND BuildData.name='amiId')
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
            imageType = row['imageType']
            row['troveFlavor'] = deps.ThawFlavor(row['troveFlavor'])
            row['troveVersion'] = versions.ThawVersion(row['troveVersion'])
            row['trailingVersion'] = str(row['troveVersion'].trailingRevision())
            row['imageType'] = buildtypes.imageTypeXmlTagNameMap.get(imageType, 'imageless')
            row['imageTypeName'] = buildtypes.typeNamesMarketing.get(imageType, 'Unknown')
            image = models.Image(row)
            image.statusMessage = jobstatus.statusNames[image.status]
            images.append(image)

        # Now add files for the images.
        filesById = {}
        filesByImageId = {}
        sql = '''SELECT fileId, Builds.buildId, title, size, sha1, urlType, url
               FROM Builds
               JOIN Projects USING(projectId)
               JOIN BuildFiles ON(Builds.buildId = BuildFiles.buildId)
            %(join)s
            JOIN BuildFilesUrlsMap USING(fileId)
            JOIN FilesUrls USING(urlId)
            LEFT JOIN ProductVersions
                ON(Builds.productVersionId=ProductVersions.productVersionId)
            WHERE hostname=? AND deleted=0 %(where)s'''
        sql = sql % dict(where=extraWhere, join=extraJoin)
        args = (hostname,)
        if extraArgs:
            args += tuple(extraArgs)
        rows = self.db.cursor().execute(sql, *args)
        for d in rows:
            urlType = d.pop('urlType')
            url = d.pop('url')
            if d['fileId'] not in filesById:
                d['imageId'] = d.pop('buildId')
                file = models.ImageFile(d)
                filesById[file] = file
                file.urls = []
                filesByImageId.setdefault(file.imageId, []).append(file)
            else:
                file = filesById[d['fileId']]
            url = self.cfg.basePath + 'downloadImage?fileId=%d' % (file.fileId)
            if urlType not in (urltypes.LOCAL, self.cfg.redirectUrlType):
                url += '&urlType=%d' % urlType
            file.urls.append(models.FileUrl(url=url, urlType=urlType))

        imagesById = dict((x.imageId, x) for x in images)
        for image in images:
            files = filesByImageId.get(image.imageId, [])
            image.files = models.ImageFileList(files)
        if update:
            self._updateStatusForImageList(images)
        if getOne:
            return images[0]
        return models.ImageList(images)


    def _updateStatusForImageList(self, imageList):
        changed = []
        for image in imageList:
            if image.status in jobstatus.stoppedStatuses:
                continue
            oldStatus = image.status
            oldMessage = image.statusMessage

            if image.hasBuild():
                uuid = '%s.%s-build-%d-%d' % (self.cfg.hostName,
                                  self.cfg.externalDomainName, image.imageId, 
                                  image.buildCount)
                try:
                    mc = self._getMcpClient()
                    status = mc.jobStatus(uuid)
                except (mcp_error.UnknownJob, mcp_error.NetworkError):
                    image.status = jobstatus.NO_JOB
                    image.statusMessage = jobstatus.statusNames[jobstatus.NO_JOB]
                else:
                    image.status, image.statusMessage = status
            else:
                image.status = jobstatus.FINISHED
                image.statusMessage = jobstatus.statusNames[jobstatus.FINISHED]
            if (oldStatus, oldMessage) != (image.status, image.statusMessage):
                changed.append(image)
        if changed:
            cu = self.db.cursor()
            for image in changed:
                cu.execute('UPDATE Builds SET status=?, statusMessage=?'
                           ' WHERE buildId=?',
                           image.status, image.statusMessage, image.imageId)

    def listImagesForProduct(self, fqdn, update=False):
        return self._getImages(fqdn, update=update)

    def getImageForProduct(self, fqdn, imageId, update=False):
        return self._getImages(fqdn, '', 'AND Builds.buildId=?', [imageId],
                                getOne=True, update=update)

    def listImagesForRelease(self, fqdn, releaseId, update=False):
        return self._getImages(fqdn, '', ' AND pubReleaseId=?',
                               [releaseId], update=update)

    def listImagesForProductVersion(self, fqdn, version, update=False):
        return self._getImages(fqdn, '',
                               ' AND ProductVersions.name=?', [version],
                               update=update)

    def listImagesForTrove(self, fqdn, name, version, flavor, update=False):
        images =  self._getImages(fqdn, '',
                                  ' AND troveName=? AND troveFlavor=?',
                                    [name, flavor.freeze()],
                                    update=False)
        images.images = [ x for x in images.images
                          if x.troveVersion == version ]
        if update:
            self._updateStatusForImageList(images.images)
        return images

    def listImagesForProductVersionStage(self, fqdn, version, stageName):
        return self._getImages(fqdn, '',
                              ' AND ProductVersions.name=? AND stageName=?',
                              [version, stageName])

    def listFilesForImage(self, fqdn, imageId):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        cu.execute('''SELECT fileId, buildId,
                      title, size, sha1
                      FROM BuildFiles
                      JOIN Builds USING(buildId)
                      JOIN Projects USING(projectId)
                      WHERE buildId=? and hostname=?
                      ORDER BY idx''', imageId, hostname)
        imageFiles = []
        for d in cu:
            d['imageId'] = d.pop('buildId')
            file = models.ImageFile(d)
            imageFiles.append(file)
        for file in imageFiles:
            cu.execute('''SELECT urlType, url
                          FROM BuildFilesUrlsMap 
                          JOIN FilesUrls USING(urlId)
                          WHERE fileId=?''', file.fileId)
            urls = []
            for d in cu:
                d['url'] = self.cfg.basePath + 'downloadImage?fileId=%d' % (
                                                                file.fileId)
                if d['urlType'] not in (urltypes.LOCAL, 
                                        self.cfg.redirectUrlType):
                    d['url'] += '&urlType=%d' % d['urlType']
                urls.append(models.FileUrl(d))
            file.urls = urls
        return models.ImageFileList(imageFiles)

    def _getMcpClient(self):
        if not self.mcpClient:
            mcpClientCfg = mcpclient.MCPClientConfig()

            try:
                mcpClientCfg.read(os.path.join(self.cfg.dataPath,
                                               'mcp', 'client-config'))
            except cfgtypes.CfgEnvironmentError:
                # If there is no client-config, default to localhost
                pass

            self.mcpClient = mcpclient.MCPClient(mcpClientCfg)
        return self.mcpClient

    def _getJobServerVersion(self):
        try:
            mc = self._getMcpClient()
            return str(mc.getJSVersion())
        except mcp_error.NotEntitledError:
            raise mint_error.NotEntitledError
        except mcp_error.NetworkError:
            raise mint_error.BuildSystemDown

    def createImage(self, fqdn, buildType, buildName, troveTuple, buildData):
        cu = self.db.db.cursor()
        productId = self.db.getProductId(fqdn)
        troveLabel = troveTuple[1].trailingLabel()
        productVersionId, stage = self.db.productMgr.getProductVersionForLabel(
                                                fqdn, troveLabel)
        sql = '''INSERT INTO Builds (projectId, name, buildType, timeCreated, 
                                     buildCount, createdBy, troveName, 
                                     troveVersion, troveFlavor, stageName, 
                                     productVersionId) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        assert buildType is not None
        cu.execute(sql, productId, buildName, buildType,    
                   time.time(), 0, self.auth.userId,
                   troveTuple[0], troveTuple[1].freeze(),
                   troveTuple[2].freeze(),
                   stage, productVersionId)
        buildId = cu.lastrowid

        buildDataTable = self.db.db.buildData
        if buildData:
            for name, value, dataType in buildData:
                buildDataTable.setDataValue(buildId, name, value, dataType, 
                                            commit=False)

        jsversion = self._getJobServerVersion()
        buildDataTable.setDataValue(buildId, 'jsversion',
                               jsversion, data.RDT_STRING, commit=False)
        # clear out all "important flavors"
        for x in buildtypes.flavorFlags.keys():
            buildDataTable.removeDataValue(buildId, x, commit=False)

        # and set the new ones
        for x in builds.getImportantFlavors(troveTuple[2]):
            buildDataTable.setDataValue(buildId, x, 1, data.RDT_INT, 
                                        commit=False)
        return buildId

    def setImageFiles(self, hostname, imageId, imageFiles):
        cu = self.db.cursor()
        if self.db.db.driver == 'sqlite':
            cu.execute("""DELETE FROM BuildFilesUrlsMap WHERE fileId IN
                (SELECT fileId FROM BuildFiles WHERE buildId=?)""",
                    imageId)
        cu.execute("DELETE FROM BuildFiles WHERE buildId=?", imageId)
        for idx, item in enumerate(imageFiles):
            if len(item) == 2:
                fileName, title = item
                sha1 = ''
                size = 0
            elif len(item) == 4:
                fileName, title, size, sha1 = item

                # Newer jobslaves will send this as a string; convert
                # to a long for the database's sake (RBL-2789)
                size = long(size)

                # sanitize filename based on configuration
                fileName = os.path.join(self.cfg.imagesPath, 
                                        hostname,
                                str(imageId), os.path.basename(fileName))
            else:
                raise ValueError
            cu.execute("""INSERT INTO BuildFiles ( buildId, idx, title,
                    size, sha1) VALUES (?, ?, ?, ?, ?)""",
                    imageId, idx, title, size, sha1)
            fileId = cu.lastrowid
            cu.execute("""INSERT INTO FilesUrls ( urlType, url )
                    VALUES (?, ?)""", urltypes.LOCAL, fileName)
            urlId = cu.lastrowid
            cu.execute("""INSERT INTO BuildFilesUrlsMap ( fileId, urlId )
                    VALUES(?, ?)""", fileId, urlId)

    def stopImageJob(self, imageId):
        mcpClient = self._getMcpClient()
        try:
            mcpClient.stopJob(imageId)
        except Exception, e:
            raise StopJobFailed(imageId, e)
