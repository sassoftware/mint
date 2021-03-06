#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import sys
import errno
import logging
import os
from django.core import urlresolvers
from mcp import client as mcp_client
from mint import jobstatus
from mint import urltypes
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.projects import models as projmodels
from mint.django_rest.rbuilder.targets import models as tgtmodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder import errors
from conary.lib import sha1helper
from mint.lib import data as datatypes
from conary import versions
from conary.deps import deps
from conary.lib import util
from smartform import descriptor
import time

log = logging.getLogger(__name__)
exposed = basemanager.exposed
autocommit = basemanager.autocommit

class ImagesManager(basemanager.BaseManager):
    ImageDataFilteredFields = set(['outputToken', 'baseFileName', ])

    @exposed
    def getImageById(self, image_id):
        return models.Image.objects.get(pk=image_id)

    @exposed
    def getImageBuild(self, image_id):
        return models.Image.objects.get(pk=image_id)
        
    @exposed
    def getImageBuilds(self):
        Images = models.Images()
        Images.image = models.Image.objects.all()
        return Images

    @exposed
    def createImage(self, **kwargs):
        """
        Image factory. Useful so we don't have to access the model directly.
        """
        image = models.Image(**kwargs)
        return image

    @exposed
    def createImageBuild(self, image, buildData=None, for_user=None):
        outputToken = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        if buildData is None:
            buildData = []
        buildData.append(('outputToken', outputToken, datatypes.RDT_STRING))

        image.time_created = image.time_updated = time.time()
        if self.user is not None:
            image.created_by_id = self.user.user_id
        image.image_count = 0
        if image.project_branch_stage_id:
            image.stage_name = image.project_branch_stage.name

        if (image.trove_version and image.project_branch_stage_id is None
                and image.project_branch_id is None):
            # Try to determine the PBS from the trove version
            troveLabel = versions.ThawVersion(image.trove_version).trailingLabel()
            pbId, stage = self.restDb.productMgr.getProductVersionForLabel(
                image.project.repository_hostname, troveLabel)
            pbs = self.mgr.getStageByProjectBranchAndStageName(pbId, stage)
            if pbs:
                image.project_branch_stage_id = pbs.stage_id

        if image.trove_version is None:
            image.trove_version = '/%s/0.1:1-1-1' % versions.CookLabel()

        if not image.trove_flavor and image.architecture:
            flavor = deps.parseFlavor(str('is: ' + image.architecture))
            image.trove_flavor = flavor.freeze()

        # Fill in the redundant information starting with the most
        # specific part
        if image.project_branch_stage_id:
            image.project_branch_id = image.project_branch_stage.project_branch_id
            image.project_id = image.project_branch_stage.project_id
        elif image.project_branch_id:
            image.project_id = image.project_branch.project_id

        image.save()

        for bdName, bdValue, bdType in buildData:
            self._setImageDataValue(image.image_id, bdName, bdValue, dataType=bdType)

        self.mgr.addToMyQuerySet(image, for_user)
        self.mgr.retagQuerySetsByType('image', for_user)
        return image

    @exposed
    def createImageBuildFile(self, image, **kwargs):
        url = kwargs.pop('url')
        urlType = kwargs.pop('urlType', urltypes.LOCAL)
        urlobj = models.FileUrl(url=url, url_type=urlType)
        urlobj.save()
        bf = models.BuildFile(image=image, **kwargs)
        bf.save()
        bfum = models.BuildFilesUrlsMap(file=bf, url=urlobj)
        bfum.save()
        return bf

    def recordTargetInternalId(self, buildFile, target, targetInternalId):
        m = tgtmodels.TargetImagesDeployed(build_file=buildFile,
            target=target, target_image_id=targetInternalId)
        m.save() 

    @exposed
    def setImageBuildStatus(self, image):
        self._postFinished(image)
        self.setImageStatus(image.image_id, image.status, image.status_message)

    @autocommit
    def commitImageStatus(self, imageId, status=None, statusMessage=None):
        if status is None:
            status = jobstatus.RUNNING
        self.setImageStatus(imageId, status, statusMessage)

    def _postFinished(self, image):
        if image.status != jobstatus.FINISHED:
            return
        # We're not done just yet
        self.setImageStatus(image.image_id, code=jobstatus.RUNNING,
            message="Finalizing image build")
        # Remove auth tokens associated with this image
        models.AuthTokens.objects.filter(image=image).delete()
        self._handlePostImageBuildOperations(image)
        # tag image, etc.
        self.finishImageBuild(image)

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
            self.manager.commitImageStatus(self.imageId, statusMessage=message)
            log.info("Uploading %s (%s/%s): %.1f%%, %s/%s",
                fileName, fileIdx, fileTotal, pct, sizeCurrent, sizeTotal)


    def _handlePostImageBuildOperations(self, image):
        pass

    def _getImageFiles(self, imageId):
        filePaths = []
        for path, in models.FileUrl.objects.filter(
                urls_map__file__image__image_id=imageId,
                url_type=urltypes.LOCAL).values_list('url'):
            if isinstance(path, unicode):
                path = path.encode('utf8')
            filePaths.append(path)
        return filePaths

    def _setImageDataValue(self, imageId, name, value, dataType=datatypes.RDT_STRING):
        # Handles the case where the image data entry already exists
        defaults = dict(value=value, data_type=dataType)
        iD, created = models.ImageData.objects.get_or_create(image_id=imageId,
            name=name, defaults=defaults)
        if not created:
            iD.update(**defaults)

    def _deleteImageData(self, imageId, name):
        models.ImageData.objects.filter(image__image_id=imageId,
                name=name).delete()

    def getEC2AccountNumbersForProjectUsers(self, projectId):
        writers = set()
        readers = set()
        vals = projmodels.Member.objects.filter(
            project__project_id = projectId,
            user__target_user_credentials__target__target_type__name = 'ec2',
            user__target_user_credentials__target__name = 'aws').values_list('level', 'user__target_user_credentials__target_credentials__credentials')
        for level, creds in vals:
            val = datatypes.unmarshalTargetUserCredentials(self.cfg, creds
                    ).get('accountId')
            if val is None:
                continue
            if level <= 1:
                writers.add(val)
            else:
                readers.add(val)
        return sorted(writers), sorted(readers)

    @exposed
    def deleteImageBuild(self, image_id):
        image = models.Image.objects.get(pk=image_id)

        log.info("Deleting image %s from project %s" % (image_id,
            image.project.short_name))
        # Delete image files from finished-images
        for imageFile in models.BuildFile.objects.filter(image=image_id):
            for urlMap in models.BuildFilesUrlsMap.objects.filter(
                    file=imageFile):
                fileUrl = urlMap.url
                path = fileUrl.url
                if path.startswith('/'):
                    try:
                        os.unlink(path)
                    except OSError, err:
                        if err.args[0] != errno.ENOENT:
                            log.exception("Failed to delete image %s", path)
                fileUrl.delete()
        imageDir = os.path.join(self.cfg.imagesPath, image.project.short_name,
                str(image_id))
        if os.path.isdir(imageDir):
            for name in os.listdir(imageDir):
                path = os.path.join(imageDir, name)
                if name in ('build.log', 'trace.txt') or name.endswith('.sha1'):
                    try:
                        os.unlink(path)
                    except OSError, err:
                        if err.args[0] != errno.ENOENT:
                            log.exception("Failed to delete image %s", path)
        # Delete the parent directory, if it's empty.
        try:
            os.rmdir(imageDir)
        except OSError, err:
            if err.args[0] not in (errno.ENOENT, errno.ENOTEMPTY):
                log.exception("Failed to delete image directory %s", imageDir)
        image.delete()

    @exposed
    def getImageBuildFile(self, image_id, file_id):
        build_file = models.BuildFile.objects.get(file_id=file_id)
        return build_file

    @exposed
    def getImageBuildFiles(self, image_id):
        BuildFiles = models.BuildFiles()
        build_files = models.BuildFile.objects.filter(image=image_id)
        BuildFiles.file = build_files
        return BuildFiles
    
    @exposed
    def getUnifiedImages(self):
        ''' 
        Return all images available on both the targets & rbuilder...
        once RBAC capable, this should be a queryset redirect instead, 
        but this method should be kept around for CLI usage.

        We may also have some variations that filter it in a more fine
        grained way, like images a user can actually deploy, etc.
        '''

        # FIXME: placeholder
        images = models.Images()
        images.image = [
            models.Image(id=1, name='placeholder'),
            models.Image(id=2, name='placeholder')
        ]
        return images
        
    @exposed
    def getBuildLog(self, image_id):
        image = models.Image.objects.get(pk=image_id)
        hostname = image.project.hostname
        return self.restDb.getImageFile(hostname, image_id, 'build.log')

    @exposed
    def appendToBuildLog(self, imageId, buildLog):
        hostname = self._getImageHostname(imageId)
        filePath = self._getImageFilePath(hostname, imageId, 'build.log',
            create=True)
        file(filePath, "a").write(buildLog)

    @exposed
    def getImageType(self, image_type_id):
        return models.ImageType.objects.get(image_type_id=image_type_id)

    @exposed
    def getImageTypes(self):
        return models.ImageType.objects.all()

    @exposed
    def getJobsByImageId(self, imageId):
        jobs = jobsmodels.Job.objects.filter(images__image__image_id=imageId).order_by("-job_id")
        Jobs = jobsmodels.Jobs()
        Jobs.job = jobs
        return Jobs

    @exposed
    def addTargetImagesForFile(self, obj):
        targetImages = getattr(obj, 'target_images', None)
        if targetImages is None:
            return
        for targetImage in targetImages.iterchildren('target_image'):
            targetIds = targetImage.xpath('target/@id')
            if not targetIds:
                continue
            targetId = targetIds[0]
            match = urlresolvers.resolve(targetId)
            if not match:
                continue
            targetId = match.kwargs['target_id']
            target = tgtmodels.Target.objects.get(target_id=targetId)
            img = targetImage.find('image')
            if img is None:
                continue
            timgModel = self.mgr.addTargetImage(target, img)
            tgtmodels.TargetImagesDeployed.objects.create(target=target,
                target_image_id=timgModel.target_internal_id,
                build_file=obj)
        self.mgr.recomputeTargetDeployableImages()

    @exposed
    def finishImageBuild(self, image, imageStatus="Image built"):
        if isinstance(image, (int, basestring)):
            image = models.Image.objects.get(image_id=image)

        self.setImageStatus(image.image_id, code=jobstatus.FINISHED,
            message=imageStatus)

        self.mgr.addToMyQuerySet(image, image.created_by)
        self.mgr.recomputeTargetDeployableImages()

    def _getImageFilePath(self, hostname, imageId, fileName, create=False):
        filePath = os.path.join(self.cfg.imagesPath, hostname, str(imageId),
            os.path.basename(fileName))
        if create:
            util.mkdirChain(os.path.dirname(filePath))
        return filePath

    def _getImageHostname(self, imageId):
        hostnames = projmodels.Project.objects.filter(
            images__image_id=imageId).values_list('short_name')
        if not hostnames:
            raise Exception("No project associated with the image")
        hostname = hostnames[0][0]
        return hostname

    @exposed
    def updateImageBuildFiles(self, imageId, files):
        fileList = files.file
        # Purge files attached to this build
        models.BuildFile.objects.filter(image__image_id=imageId).delete()
        hostname = self._getImageHostname(imageId)
        # Add files
        for idx, fobj in enumerate(fileList):
            fobj.image_id = imageId
            fobj.idx = idx
            fobj.save()

            filePath = self._getImageFilePath(hostname, imageId, fobj.file_name)
            with open(filePath + '.sha1') as sha1file:
                sha1sum = sha1file.readline().split()[0]
            if sha1sum != fobj.sha1:
                raise RuntimeError("Image file was corrupted during "
                        "upload, check build log")
            url = models.FileUrl.objects.create(url_type=urltypes.LOCAL,
                url=filePath)
            models.BuildFilesUrlsMap.objects.create(file=fobj, url=url)

        attrTypes = dict(installed_size=datatypes.RDT_INT,
                uncompressed_size=datatypes.RDT_INT)
        Etree = models.modellib.Etree
        if files.attributes is not None:
            attributes = dict(
                    ('attributes.' + x.tag, (x.text, attrTypes.get(x.tag,
                        datatypes.RDT_STRING)))
                    for x in files.attributes.iterchildren())
            for attrName, (attrValue, attrType) in attributes.items():
                self._setImageDataValue(imageId, attrName, attrValue,
                        dataType=attrType)

        return self.getImageBuildFiles(imageId)

    def setImageStatus(self, imageId, code=jobstatus.RUNNING, message=''):
        models.Image.objects.filter(image_id=imageId).update(status=code,
            status_message=message)

    @exposed
    def getImageDescriptor(self, imageId, descriptorType):
        supportedDescriptors = dict(cancel_build=self.getImageDescriptorCancelBuild)
        method = supportedDescriptors.get(descriptorType)
        if method is None:
            raise errors.ResourceNotFound()
        return method(imageId)

    def getImageData(self, image):
        ret = {}
        for data in image.image_data.all():
            if data.name in self.ImageDataFilteredFields:
                continue
            ret[data.name] = datatypes.Data.thaw(data.value, data.data_type)
        return ret

    def getImageDescriptorCancelBuild(self, imageId):
        descr = descriptor.ConfigurationDescriptor()
        descr.setDisplayName('Cancel Image Build')
        descr.addDescription('Cancel Image Build')
        descr.setRootElement("descriptor_data")
        return descr

    @exposed
    def cancelImageBuild(self, image, job):
        try:
            self._cancelImageBuild(image, job)
        except:
            exc = sys.exc_info()
            stream = util.BoundedStringIO()
            util.formatTrace(*exc, stream=stream, withLocals=False)
            stream.seek(0)

            job.job_state = self.mgr.getJobStateByName(jobsmodels.JobState.FAILED)
            job.status_code = 500
            job.status_text = "Failed"
            job.status_detail = stream.read()
        else:
            job.job_state = self.mgr.getJobStateByName(jobsmodels.JobState.COMPLETED)
            job.status_code = 200
            job.status_text = "Done"
        job.save()

    def _cancelImageBuild(self, image, job=None):
        mcpJobUUID = image.image_data.filter(name='uuid')
        if not mcpJobUUID:
            raise Exception("Image without a build task")
        mcpJobUUID = mcpJobUUID[0].value
        mcpClient = self._getMcpClient()
        mcpClient.stop_job(mcpJobUUID)

        if job and job.created_by:
            msg = "User %s requested stopping of image build with job %s" % (
                job.created_by.user_name, mcpJobUUID, )
        else:
            msg = "User requested stopping of image build with job %s" % (
                mcpJobUUID, )

        sio = util.BoundedStringIO()
        lhandler = logging.StreamHandler(sio)
        lhandler.setFormatter(util.log._getFormatter('file'))
        oldLevel = log.level
        try:
            # Capture log
            log.setLevel(logging.DEBUG)
            log.addHandler(lhandler)
            log.info(msg)
            sio.seek(0)
            self.appendToBuildLog(image.image_id, sio.read())
        finally:
            log.removeHandler(lhandler)
            log.setLevel(oldLevel)

    def _getMcpClient(self):
        return mcp_client.Client(self.cfg.queueHost, self.cfg.queuePort)
