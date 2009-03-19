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
                   extraArgs=None, getOne=False):
        hostname = fqdn.split('.')[0]
        sql = '''SELECT buildId as imageId, hostname,
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
            self._addImageStatus(image)
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

    def _addImageStatus(self, image):
        if image.hasBuild():
            uuid = '%s.%s-build-%d-%d' % (self.cfg.hostName,
                              self.cfg.externalDomainName, image.imageId, 
                              image.buildCount)
            try:
                mc = self._getMcpClient()
                image.status, image.statusMessage = mc.jobStatus(uuid)
            except (mcp_error.UnknownJob, mcp_error.NetworkError):
                image.status = jobstatus.NO_JOB
                image.statusMessage = jobstatus.statusNames[jobstatus.NO_JOB]
        else:
            image.status = jobstatus.FINISHED
            image.statusMessage = jobstatus.statusNames[jobstatus.FINISHED]

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
            cu.execute("INSERT INTO BuildFiles "
                        "VALUES(NULL, ?, ?, NULL, ?, ?, ?)", 
                        imageId, idx, title, size, sha1)
            fileId = cu.lastrowid
            cu.execute("INSERT INTO FilesUrls VALUES(NULL, ?, ?)",
                urltypes.LOCAL, fileName)
            urlId = cu.lastrowid
            cu.execute("INSERT INTO BuildFilesUrlsMap VALUES(?, ?)",
                       fileId, urlId)
