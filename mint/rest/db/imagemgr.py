#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import logging
import os
import sys
import time

from conary.deps import deps
from conary import versions

from mint import builds
from mint import buildtypes
from mint import jobstatus
from mint import helperfuncs
from mint import mint_error
from mint import notices_callbacks
from mint import urltypes
from mint.lib import data
from mint.rest import errors
from mint.rest.db import manager
from mint.rest.api import models

from conary.lib import cfgtypes

log = logging.getLogger(__name__)


class ImageManager(manager.Manager):
    def __init__(self, cfg, db, auth, publisher=None):
        manager.Manager.__init__(self, cfg, db, auth, publisher)

    def _getImages(self, fqdn, extraJoin='', extraWhere='',
                   extraArgs=None, getOne=False):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()

        # TODO: pull amiId out of here and move into builddata dict ASAP
        sql = '''
            SELECT
                p.hostname,
                pv.name AS version,
                b.buildId AS imageId, b.pubReleaseId AS "releaseId",
                    b.buildType AS imageType, b.name, b.description,
                    b.troveName, b.troveVersion, b.troveFlavor,
                    b.troveLastChanged, b.timeCreated, b.timeUpdated,
                    b.status AS statusCode, b.statusMessage, b.buildCount,
                    b.stageName AS stage,
                pr.timePublished,
                pr.name AS release,
                cr_user.username AS creator, up_user.username AS updater,
                ami_data.value AS amiId

            FROM Builds b
                JOIN Projects p USING ( projectId )
                %(join)s
                -- NB: USING() would be typical but sqlite seems upset?
                LEFT JOIN PublishedReleases pr ON (
                    b.pubReleaseId = pr.pubReleaseId )
                LEFT JOIN ProductVersions pv ON (
                    b.productVersionId = pv.productVersionId )
                LEFT JOIN Users cr_user ON ( b.createdBy = cr_user.userId )
                LEFT JOIN Users up_user ON ( b.updatedBy = up_user.userId )
                LEFT JOIN BuildData ami_data ON (
                    b.buildId = ami_data.buildId AND ami_data.name = 'amiId' )

            WHERE hostname = ? AND troveVersion IS NOT NULL
            %(where)s
            '''
        sql %= dict(where=extraWhere, join=extraJoin)
        args = (hostname,)
        if extraArgs:
            args += tuple(extraArgs)
        cu.execute(sql, *args)
        if getOne:
            row = self.db._getOne(cu, errors.ImageNotFound, args)
            rows = [row]
        else:
            rows = cu

        images = []
        for row in rows:
            imageType = row['imageType']
            row['released'] = bool(row['releaseId'])
            row['published'] = bool(row.pop('timePublished', False))
            if row['troveFlavor'] is not None:
                row['troveFlavor'] = deps.ThawFlavor(row['troveFlavor'])
                row['architecture'] = helperfuncs.getArchFromFlavor(
                        row['troveFlavor'])
            else:
                row['architecture'] = None

            if row['troveVersion'] is not None:
                row['troveVersion'] = helperfuncs.parseVersion(row['troveVersion'])
                row['trailingVersion'] = str(row['troveVersion'].trailingRevision())
            else:
                row['trailingVersion'] = None

            row['imageType'] = buildtypes.imageTypeXmlTagNameMap.get(imageType, 'imageless')
            row['imageTypeName'] = buildtypes.typeNamesMarketing.get(imageType, 'Unknown')

            status = models.ImageStatus()
            status.hostname = row['hostname']
            status.imageId = row['imageId']
            status.set_status(code=row.pop('statusCode'),
                    message=row.pop('statusMessage'))

            image = models.Image(row)
            image.imageStatus = status
            images.append(image)

        imageIds = [ x.imageId for x in images ]
        imagesBaseFileNameMap = self.getImagesBaseFileName(hostname, imageIds)

        imagesFiles = self._getFilesForImages(hostname, imageIds)
        for image, imageFiles in zip(images, imagesFiles):
            image.files = imageFiles
            image.baseFileName = imagesBaseFileNameMap[image.imageId]

        if getOne:
            return images[0]
        return models.ImageList(images)

    def _getFilesForImages(self, hostname, imageIds):
        imageIds = [int(x) for x in imageIds]
        if not imageIds:
            return []

        cu = self.db.cursor()

        cu.execute("DELETE FROM tmpOneVal")
        cu.executemany("INSERT INTO tmpOneVal (id) VALUES (?)",
            [ (x, ) for x in imageIds ])

        # Grab target images
        cu.execute("""
            SELECT DISTINCT t.targetType, t.targetName, tid.fileId, tid.targetImageId
              FROM Targets AS t
              JOIN TargetImagesDeployed AS tid USING (targetId)
              JOIN BuildFiles AS bf USING (fileId)
              JOIN tmpOneVal AS tb ON (bf.buildId = tb.id)
        """)
        targetImages = {}
        for row in cu:
            targetImages.setdefault(row['fileId'], []).append(
                models.TargetImage(targetType=row['targetType'],
                    targetName=row['targetName'],
                    targetImageId=row['targetImageId']))

        sql = '''
            SELECT
                f.fileId, f.buildId AS imageId, f.idx, f.title, f.size, f.sha1,
                u.urlType, u.url
            FROM BuildFiles f
                JOIN BuildFilesUrlsMap USING ( fileId )
                JOIN FilesUrls u USING ( urlId )
                JOIN tmpOneVal AS tb ON (f.buildId = tb.id)
            '''
        cu.execute(sql)

        filesByImageId = dict((imageId, {}) for imageId in imageIds)
        for d in cu:
            imageId, fileId = d['imageId'], d['fileId']
            urlType, url = d.pop('urlType'), d.pop('url')
            imageFiles = filesByImageId[imageId]
            if fileId in imageFiles:
                file = imageFiles[fileId]
            else:
                file = imageFiles[fileId] = models.ImageFile(d)
                file.urls = []
                file.sha1 = d['sha1']
            targetImageIds = sorted(targetImages.get(fileId, []),
                key=lambda x: (x.targetName, x.targetType, x.targetImageId))
            file.targetImages = targetImageIds

            if url:
                file.fileName = os.path.basename(url)
            file.urls.append(models.FileUrl(fileId=fileId, urlType=urlType))

        # Order image files in a list parallel to imageIds
        imageFilesList = [ filesByImageId[x] for x in imageIds ]
        return [models.ImageFileList(hostname=hostname, imageId=imageId,
            files=sorted(imageFiles.values(), key=lambda x: x.idx))
            for (imageId, imageFiles) in zip(imageIds, imageFilesList) ]

    def getImagesBaseFileName(self, hostname, imageIds):
        imageIds = [int(x) for x in imageIds]
        if not imageIds:
            return {}

        cu = self.db.cursor()
        # We join Builds with BuildData in a subquery first, to find out the
        # base file name; the outer join will make sure we get NULL if
        # baseFileName is not set.
        sql = '''
            SELECT b.buildId, b.troveName, b.troveVersion, b.troveFlavor,
                   bd.baseFileName
              FROM Builds AS b
         LEFT JOIN (
                    SELECT buildId, value AS baseFileName
                      FROM Builds
                      JOIN BuildData USING (buildId)
                     WHERE BuildData.name ='baseFileName'
                   ) AS bd USING (buildId)
             WHERE b.buildId IN ( %(images)s )
            '''
        sql %= dict(images=','.join('%d' % x for x in imageIds))
        cu.execute(sql)
        imageTroveMap = dict(
            (r['buildId'],
                (r['troveName'], r['troveVersion'], r['troveFlavor'],
                    r['baseFileName']))
             for r in cu)
        ret = {}
        for imageId in imageIds:
            troveName, troveVersion, troveFlavor, baseFileName = imageTroveMap[imageId]
            baseFileName = self._sanitizeString(baseFileName)
            if not baseFileName:
                troveVersion = helperfuncs.parseVersion(troveVersion)
                troveArch = helperfuncs.getArchFromFlavor(troveFlavor)
                baseFileName = "%(name)s-%(version)s-%(arch)s" % dict(
                    # XXX One would assume hostname == troveName, but that's
                    # how server.py had the code written
                    name = hostname,
                    version = troveVersion.trailingRevision().version,
                    arch = troveArch)
            ret[imageId] = baseFileName
        return ret

    @classmethod
    def _sanitizeString(cls, string):
        if string is None:
            return ''
        # Copied from mint/server.py
        return ''.join(
            [(x.isalnum() or x in ('-', '.')) and x or '_'
            for x in string])

    def listImagesForProduct(self, fqdn):
        return self._getImages(fqdn)

    def getImageForProduct(self, fqdn, imageId):
        return self._getImages(fqdn, '', 'AND b.buildId=?', [imageId],
                                getOne=True)

    def deleteImageForProduct(self, fqdn, imageId):
        self.deleteImageFilesForProduct(fqdn, imageId)
        cu = self.db.cursor()
        cu.execute('''DELETE FROM Builds where buildId=?''', imageId)

    def deleteImageFilesForProduct(self, fqdn, imageId):
        cu = self.db.cursor()
        # Grab the AMI ID, if there is one
        cu.execute("""SELECT value FROM BuildData
                      WHERE buildId=? AND name = 'amiId'""", imageId)
        imageName = cu.fetchone()
        if imageName:
            imageName = imageName[0]
        cu.execute('''SELECT url FROM BuildFiles
                     JOIN BuildFilesUrlsMap USING(fileId)
                     JOIN FilesUrls USING(urlId)
                     WHERE buildId=?''', imageId)
        for url, in cu:
            if os.path.exists(url):
                os.unlink(url)
        cu.execute('''DELETE FROM FilesUrls WHERE urlId IN
                     (SELECT urlId FROM BuildFiles
                      JOIN BuildFilesUrlsMap USING(FileId)
                      WHERE buildId=?)''', imageId)
        cu.execute("""DELETE FROM BuildFilesUrlsMap
            WHERE fileId IN ( SELECT fileId FROM BuildFiles WHERE buildId = ? )
            """, imageId)
        cu.execute('''DELETE FROM BuildFiles WHERE buildId=?''', imageId)
        # Grab the build type
        imageType = self._getImageType(imageId)
        self.publisher.notify('ImageRemoved', imageId, imageName, imageType)

    def _getImageType(self, imageId):
        cu = self.db.cursor()
        cu.execute('''SELECT buildType FROM Builds
                      WHERE buildId = ?''', imageId)
        imageType = cu.fetchone()[0]
        return imageType

    def listImagesForRelease(self, fqdn, releaseId):
        return self._getImages(fqdn, '', ' AND b.pubReleaseId=?',
                               [releaseId])

    def listImagesForProductVersion(self, fqdn, version):
        return self._getImages(fqdn, '',
                               ' AND pv.name=?', [version])

    def listImagesForTrove(self, fqdn, name, version, flavor):
        images =  self._getImages(fqdn, '',
                                  ' AND troveName=? AND troveFlavor=?',
                                    [name, flavor.freeze()])
        images.images = [ x for x in images.images
                          if x.troveVersion == version ]
        return images

    def listImagesForProductVersionStage(self, fqdn, version, stageName):
        return self._getImages(fqdn, '',
                              ' AND pv.name=? AND stageName=?',
                              [version, stageName])

    def listFilesForImage(self, fqdn, imageId):
        hostname = fqdn.split('.')[0]
        return self._getFilesForImages(hostname, [imageId])[0]

    def createImage(self, fqdn, image, buildData):
        buildType = image.imageType
        buildName = image.name
        troveTuple = image.getNameVersionFlavor()

        # Look up the build type by name too - and fall back to what the user
        # specified
        buildType = buildtypes.xmlTagNameImageTypeMap.get(buildType, buildType)
        cu = self.db.db.cursor()
        productId = self.db.getProductId(fqdn)
        troveLabel = troveTuple[1].trailingLabel()
        if image.stage and image.version:
            stage = os.path.basename(image.stage.href)
            version = os.path.basename(image.version.href)
            productVersion = self.db.productMgr.getProductVersion(fqdn, version)
            productVersionId = productVersion.versionId
        else:
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

        # clear out all "important flavors"
        for x in buildtypes.flavorFlags.keys():
            buildDataTable.removeDataValue(buildId, x, commit=False)

        # and set the new ones
        for x in builds.getImportantFlavors(troveTuple[2]):
            buildDataTable.setDataValue(buildId, x, 1, data.RDT_INT, 
                                        commit=False)
        return buildId

    def getRepeaterClient(self):
        try:
            from rpath_repeater import client as repeater_client
        except:
            return None

        return repeater_client.RepeaterClient()

    def uploadImageFiles(self, hostname, image, outputToken=None):
        if not image.files.files:
            return None
        rcli = self.getRepeaterClient()
        if rcli is None:
            return None
        path = "/api/products/%s/images/%s/" % (hostname, image.imageId)
        stPath = path + 'status'
        putFilesPath = path + 'files'
        uploadPath = "/uploadBuild/%s/" % (image.imageId, )
        headers = { 'X-rBuilder-OutputToken' : outputToken }
        fileList = []
        putFilesURL = rcli.URL(scheme="http", host="localhost",
            path=putFilesPath, unparsedPath=putFilesPath,
            headers=headers)
        statusReportURL = rcli.URL(scheme="http", host="localhost",
                path=stPath, unparsedPath=stPath, headers=headers)
        for fileItem in image.files.files:
            if not fileItem.urls:
                continue
            srcurl = fileItem.urls[0].url
            fileName = os.path.basename(fileItem.fileName)
            uPath = uploadPath + fileName
            url = rcli.makeUrl(srcurl)
            destination = rcli.URL(scheme="http", host="localhost",
                path=uPath, unparsedPath=uPath, headers=headers)
            # Convert fields to unicode, we don't want to send xobj strings
            # over the wire
            ifile = rcli.ImageFile(
                title=self._u(fileItem.fileName),
                fileName=self._u(fileItem.fileName),
                url=url, destination=destination)
            fileList.append(ifile)
        if not fileList:
            return None
        meta = rcli.ImageMetadata(**dict(image.metadata.getValues()))
        image = rcli.Image(name=self._u(image.name), metadata=meta,
            architecture=self._u(image.architecture), files=fileList)
        uuid, job = rcli.download_images(image, statusReportURL, putFilesURL)

    @classmethod
    def _u(cls, obj):
        if obj is None:
            return None
        return unicode(obj)

    def stopImageJob(self, imageId):
        raise NotImplementedError

    def getImageStatus(self, imageId):
        cu = self.db.cursor()
        cu.execute("""SELECT hostname, buildId AS imageId,
                    status AS code, statusMessage AS message
                FROM Builds JOIN Projects USING ( projectId )
                WHERE buildId = ?""", imageId)
        row = self.db._getOne(cu, errors.ImageNotFound, imageId)
        return models.ImageStatus(row)

    def setImageStatus(self, imageId, status):
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET status = ?, statusMessage = ?
                WHERE buildId = ?""", status.code, status.message, imageId)
        return self.getImageStatus(imageId)

    def finalImageProcessing(self, imageId, status):
        self._postFinished(imageId, status)
        self._createNotices(imageId, status)

    class UploadCallback(object):
        def __init__(self, manager, imageId):
            self.manager = manager
            self.imageId = imageId

        def callback(self, fileName, fileIdx, fileTotal,
                currentFileBytes, totalFileBytes, sizeCurrent, sizeTotal):
            # Nice percentages
            if sizeTotal == 0:
                sizeTotal = 1024
            pct = sizeCurrent * 100.0 / sizeTotal
            message = "Uploading bundle: %d%%" % (pct, )
            self.manager._setStatus(self.imageId, message = message)
            log.info("Uploading %s (%s/%s): %.1f%%, %s/%s",
                fileName, fileIdx, fileTotal, pct, sizeCurrent, sizeTotal)

    def _setStatus(self, imageId, code = jobstatus.RUNNING, message = ''):
        status = models.ImageStatus()
        status.set_status(code, message)
        self.db.setVisibleImageStatus(imageId, status)

    def _postFinished(self, imageId, status):
        if status.code != jobstatus.FINISHED:
            return
        imageType = self._getImageType(imageId)
        if imageType != buildtypes.AMI:
            # for now we only have to do something special for AMIs
            return
        log.info("Finishing AMI image")
        # Fetch the image path
        cu = self._getImageFiles(imageId)
        uploadCallback = self.UploadCallback(self, imageId)
        for row in cu:
            url = row[0]
            if not os.path.exists(url):
                continue
            log.info("Uploading bundle")
            bucketName, manifestName = self.db.awsMgr.amiPerms.uploadBundle(
                url, callback = uploadCallback.callback)
            self._setStatus(imageId, message = "Registering AMI")
            log.info("Registering AMI for %s/%s", bucketName,
                manifestName)
            projectId = self._getProjectForImage(imageId)
            getEC2AccountNumbersForProjectUsers = self.db.db.projectUsers.getEC2AccountNumbersForProjectUsers
            writers, readers = getEC2AccountNumbersForProjectUsers(projectId)
            amiId, manifestPath = self.db.awsMgr.amiPerms.registerAMI(
                bucketName, manifestName, readers = readers, writers = writers)
            log.info("Registered AMI %s for %s", amiId,
                manifestPath)
            self.db.db.buildData.setDataValue(imageId, 'amiId', amiId,
                data.RDT_STRING)
            self.db.db.buildData.setDataValue(imageId, 'amiManifestName,',
                manifestPath, data.RDT_STRING)
            self.db.commit()

    def _getProjectForImage(self, imageId):
        sql = "SELECT projectId FROM Builds WHERE buildId = ?"
        cu = self.db.cursor()
        cu.execute(sql, imageId)
        row = cu.fetchone()
        return row[0]

    def _createNotices(self, imageId, status):
        sql = """
            SELECT Projects.hostname, ProductVersions.name, Users.username,
                   Builds.name, Builds.buildType, BuildData.value AS amiId
              FROM Builds
              JOIN Projects USING ( projectId )
         LEFT JOIN ProductVersions ON
                (Builds.productVersionId = ProductVersions.productVersionId)
         LEFT JOIN Users ON ( Builds.createdBy = Users.userId )
         LEFT JOIN BuildData ON (Builds.buildId = BuildData.buildId AND
                                 BuildData.name = 'amiId' )
             WHERE Builds.buildId = ?
        """
        cu = self.db.cursor()
        cu.execute(sql, imageId)
        row = cu.fetchone()
        projectName, projectVersion, imageCreator, imageName, imageType, amiId = row
        imageType = buildtypes.typeNamesMarketing.get(imageType)

        failed = (status.code != jobstatus.FINISHED)

        if amiId is not None:
            notices = notices_callbacks.AMIImageNotices(self.cfg, imageCreator)
            imageFiles = [ amiId ]
        else:
            notices = notices_callbacks.ImageNotices(self.cfg, imageCreator)
            imageFiles = [ (x[0], self.getDownloadUrl(x[1]))
                for x in self._getImageFiles(imageId) ]

        method = (failed and notices.notify_error) or notices.notify_built
        method(imageName, imageType, time.time(), projectName, projectVersion,
            imageFiles)

    def getDownloadUrl(self, fileId):
        downloadUrlTemplate = "https://%s%sdownloadImage?fileId=%d"
        return downloadUrlTemplate % (
            self.cfg.siteHost, self.cfg.basePath, fileId)

    def _getImageFiles(self, imageId):
        cu = self.db.cursor()
        cu.execute("""
            SELECT FilesUrls.url, BuildFilesUrlsMap.fileId
              FROM BuildFiles
              JOIN BuildFilesUrlsMap USING (fileId)
              JOIN FilesUrls USING (urlId)
             WHERE BuildFiles.buildId = ?
               AND FilesUrls.urlType = ?
        """, imageId, urltypes.LOCAL)
        return cu

    def _getImageInfoForNotices(self, imageId, status):
        cu = self.db.cursor()
        cu.execute("""
            SELECT Projects.name, Projects.version, Users.username,
                   Builds.buildType,
                   BuildData.value AS amiId,
              FROM Builds
              JOIN Projects USING (projectId)
              JOIN Users ON (Builds.createdBy = Users.userId)
         LEFT JOIN BuildData ON (Builds.buildId = BuildData.buildId AND
                                 BuildData.name = 'amiId' )
             WHERE Builds.buildId = ?
        """, imageId)
        # XXX FIXME: add notices
        return

    def setFilesForImage(self, fqdn, imageId, files):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()

        # Delete existing files attached to the build.
        # NB: currently we just orphan the URL objects, esp. since some may be
        # on S3 and require special cleanup.
        if self.db.db.driver == 'sqlite':
            cu.execute("""DELETE FROM BuildFilesUrlsMap WHERE fileId IN
                (SELECT fileId FROM BuildFiles WHERE buildId=?)""",
                    imageId)
        cu.execute("DELETE FROM BuildFiles WHERE buildId=?", imageId)

        for idx, file in enumerate(files.files):
            # First insert the file ...
            # NOTE: cast file size to long to work around broken python-pgsql
            # behavior with integers too big for a postgres int but small
            # enough to fit in a python int, esp. on 64 bit systems.
            cu.execute("""
                INSERT INTO BuildFiles ( buildId, idx, title, size, sha1 )
                    VALUES ( ?, ?, ?, ?, ? )""",
                imageId, idx, file.title, long(file.size), file.sha1)
            fileId = cu.lastrowid

            # ... then the URL ...
            fileName = os.path.basename(file.fileName)
            filePath = os.path.join(self.cfg.imagesPath, hostname,
                    str(imageId), fileName)
            cu.execute("INSERT INTO FilesUrls ( urlType, url) VALUES ( ?, ? )",
                    urltypes.LOCAL, filePath)
            urlId = cu.lastrowid

            # ... then the mapping between them.
            cu.execute("""INSERT INTO BuildFilesUrlsMap (
                    fileId, urlId) VALUES ( ?, ? )""",
                    fileId, urlId)

        if files.metadata:
            self._addImageToRepository(hostname, imageId, files.metadata)

        return self.listFilesForImage(hostname, imageId)

    def _addImageToRepository(self, hostname, imageId, metadata):
        # Fetch file paths
        cu = self._getImageFiles(imageId)
        filePaths = [ row[0] for row in cu ]
        img = self.getImageForProduct(hostname, imageId)
        productMgr = self.db.productMgr
        # We need the product's fqdn
        product = productMgr.getProduct(hostname)
        fqdn = product.repositoryHostname
        pd = productMgr.getProductVersionDefinition(fqdn, img.version)
        buildLabel = pd.getLabelForStage(img.stage)

        factoryName = "rbuilder-image"
        troveName = "image-%s" % hostname
        troveVersion = "1.0"
        streamMap = dict((os.path.basename(x), file(x)) for x in filePaths)
        try:
            self._setStatus(imageId, message="Committing image to repository")
            productMgr.reposMgr.createSourceTrove(fqdn, troveName, buildLabel,
                troveVersion, streamMap, changeLogMessage="Image imported",
                factoryName=factoryName, admin=True)
        except Exception, e:
            self._setStatus(imageId, message="Commit failed: %s" % (e, ))
            log.error("Error: %s", e)
        else:
            message = "Image committed as %s:source=%s" % (troveName, buildLabel)
            self._setStatus(imageId, message=message)
            log.info(message)

    def getAllImagesByType(self, imageType):
        images = self.db.db.builds.getAllBuildsByType(imageType,
            self.db.auth.userId)
        hostname = None
        imageIds = []
        hostnameToImageIdsMap = {}
        if not images:
            return []
        for imageData in images:
            hostname = imageData.pop('hostname')
            hostnameToImageIdsMap.setdefault(hostname, []).append(
                imageData['buildId'])
        imagesBaseFileNameMap = {}
        imageFileListMap = {}
        for hostname, imageIds in hostnameToImageIdsMap.items():
            imagesBaseFileNameMap.update(
                self.getImagesBaseFileName(hostname, imageIds))
            imageFilesList = self._getFilesForImages(hostname, imageIds)
            imageFileListMap.update(dict((x, y)
                for (x, y) in zip(imageIds, imageFilesList)))

        for imageData in images:
            imageFileList = imageFileListMap[imageData['buildId']]
            imageFileData = [
                dict(fileId = x.fileId, sha1 = x.sha1,
                     fileName = x.fileName,
                     idx = x.idx, size = x.size,
                     downloadUrl = self.getDownloadUrl(x.fileId),
                     targetImages = [
                        (y.targetType, y.targetName, y.targetImageId)
                            for y in x.targetImages ])
                for x in imageFileList.files ]
            imageData['files'] = imageFileData
            imageId = imageData['buildId']
            imageData['baseFileName'] = imagesBaseFileNameMap[imageId]
        return images
