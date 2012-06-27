#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
import errno
import logging
import os
import os.path
import hashlib
import json
from django.core import urlresolvers
from mcp import client as mcp_client
from mint import buildtypes
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
from conary import trovetup
from conary import versions
from conary.deps import deps
from conary.lib import util
from smartform import descriptor
import time

log = logging.getLogger(__name__)
exposed = basemanager.exposed
autocommit = basemanager.autocommit

class ImagesManager(basemanager.BaseManager):
 
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
            image.trove_version = str(versions.VersionFromString(
                '/local@local:COOK/1-1-1', timeStamps = [ 0.1 ]))

        if not image.trove_flavor and image.architecture:
            image.trove_flavor = "is: %s" % image.architecture

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
    def _getOutputTrove(self, image):
        if image.output_trove is None:
            return None
        name, version, flavor = trovetup.TroveSpec.fromString(image.output_trove)
        version = versions.VersionFromString(version)
        if flavor is None:
            flavor = deps.Flavor()
        return trovetup.TroveTuple(name, version, flavor)

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
        self.finishImageBuild(image.image_id)

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
        self._uploadAMI(image)

    def _getImageFiles(self, imageId):
        filePaths = []
        for path, in models.FileUrl.objects.filter(
                urls_map__file__image__image_id=imageId,
                url_type=urltypes.LOCAL).values_list('url'):
            if isinstance(path, unicode):
                path = path.encode('utf8')
            filePaths.append(path)
        return filePaths

    def _uploadAMI(self, image):
        if image._image_type != buildtypes.AMI:
            # for now we only have to do something special for AMIs
            return
        imageId = image.image_id
        # Do all the read operations before we commit
        # Get all builds for this image
        filePaths = self._getImageFiles(imageId)
        readers, writers = self.getEC2AccountNumbersForProjectUsers(
            image.project.project_id)
        # Move to autocommit mode. This will flush the existing
        # transaction, and the decorated commitImageStatus will do its
        # own commits. We need to restore transaction management when
        # we're done.
        self.mgr.prepareAutocommit()
        uploadCallback = self.UploadCallback(self, imageId)
        amiPerms = self.mgr.restDb.awsMgr.amiPerms
        for filePath in filePaths:
            if not os.path.exists(filePath):
                continue
            log.info("Uploading bundle")
            bucketName, manifestName = amiPerms.uploadBundle(
                filePath, callback=uploadCallback.callback)
            message = "Registering AMI for %s/%s" % (bucketName, manifestName)
            self.commitImageStatus(imageId, statusMessage=message)
            log.info(message)
            amiId, manifestPath = amiPerms.registerAMI(
                bucketName, manifestName, readers=readers, writers=writers)
            message = "Registered AMI %s for %s" % (amiId, manifestPath)
            self.commitImageStatus(imageId, statusMessage=message)
            log.info(message)
            self._setImageDataValue(imageId, 'amiId', amiId)
            self._setImageDataValue(imageId, 'amiManifestName', manifestPath)
        self.mgr.commit()
        # Restore transaction management
        self.mgr.enterTransactionManagement()

    def _setImageDataValue(self, imageId, name, value, dataType=datatypes.RDT_STRING):
        models.ImageData.objects.create(image_id=imageId,
            name=name, value=value, data_type=dataType)

    def getEC2AccountNumbersForProjectUsers(self, projectId):
        writers = set()
        readers = set()
        vals = projmodels.Member.objects.filter(
            project__project_id = projectId,
            user__target_user_credentials__target__target_type__name = 'ec2',
            user__target_user_credentials__target__name = 'aws').values_list('level', 'user__target_user_credentials__target_credentials__credentials')
        for level, creds in vals:
            val = datatypes.unmarshalTargetUserCredentials(creds).get('accountId')
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

        # see if any images have this image as a baseimage, and if so, refuse to delete
        layered_images = models.Image.objects.filter(base_image = image)
        if len(layered_images) > 0:
            raise errors.PermissionDenied(msg="Image is in use as a layered base image and cannot be deleted")

        log.info("Deleting image %s from project %s" % (image_id,
            image.project.short_name))
        # Delete image files from finished-images
        for imageFile in models.BuildFile.objects.filter(image=image_id):
            for urlMap in models.BuildFilesUrlsMap.objects.filter(
                    file=imageFile):
                fileUrl = urlMap.url
                path = fileUrl.url
                if path.startswith('/') and os.path.exists(path):
                    os.unlink(path)
                fileUrl.delete()
        imageDir = os.path.join(self.cfg.imagesPath, image.project.short_name,
                str(image_id))
        for name in ['build.log', 'trace.txt']:
            path = os.path.join(imageDir, name)
            if os.path.exists(path):
                os.unlink(path)
        # Delete the parent directory, if it's empty.
        try:
            os.rmdir(imageDir)
        except OSError, err:
            if err.args[0] not in (errno.ENOENT, errno.ENOTEMPTY):
                raise
        image.delete()
        # Delete the image trove from the repository if it is not referenced by
        # any other image.
        if image.output_trove:
            others = models.Image.objects.filter(output_trove=image.output_trove)
            if others:
                log.info("Keeping image trove %s because it is claimed by "
                        "other images", image.output_trove)
            else:
                log.info("Deleting image trove %s", image.output_trove)
                reposMgr = self.mgr._restDb.productMgr.reposMgr
                tup = trovetup.TroveSpec.fromString(image.output_trove)
                reposMgr.deleteTroves([tup])

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
        targetImages = getattr(targetImages, 'target_image', None)
        if targetImages is None:
            return
        if not isinstance(targetImages, list):
            targetImages = [ targetImages ]
        for targetImage in targetImages:
            targetId = targetImage.target.id
            match = urlresolvers.resolve(targetId)
            if not match:
                continue
            targetId = match.kwargs['target_id']
            target = tgtmodels.Target.objects.get(target_id=targetId)
            img = targetImage.image
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
            url = models.FileUrl.objects.create(url_type=urltypes.LOCAL,
                url=filePath)
            models.BuildFilesUrlsMap.objects.create(file=fobj, url=url)

        if files.metadata is not None:
            self._addImageToRepository(imageId, files.metadata)

        return self.getImageBuildFiles(imageId)

    def _addImageToRepository(self, imageId, metadata):
        metadataDict = self.mgr.restDb.imageMgr.getMetadataDict(metadata)
        # Find the stage for this image, we need the label to commit to
        buildLabels = projmodels.Stage.objects.filter(
                images__image_id=imageId).values_list(
                    'label', 'project__short_name', 'project__repository_hostname')
        if not buildLabels:
            raise Exception("Stage for image does not exist")
        buildLabel, shortName, repositoryHostname = buildLabels[0]
        factoryName = "rbuilder-image"
        troveName = "image-%s" % shortName
        troveVersion = imageId

        filePaths = self._getImageFiles(imageId)

        streamMap = dict((os.path.basename(x),
            self.mgr.reposMgr.RegularFile(contents=file(x), config=False))
                for x in filePaths)

        try:
            nvf = self.mgr.reposMgr.createSourceTrove(
                repositoryHostname,
                troveName,
                buildLabel,
                troveVersion, streamMap, changeLogMessage="Image imported",
                factoryName=factoryName, admin=True,
                metadata=metadataDict)
        except Exception, e:
            self.setImageStatus(imageId, code=jobstatus.FAILED,
                message="Commit failed: %s" % (e, ))
            log.error("Error: %s", e)
            raise
        else:
            models.Image.objects.filter(image_id=imageId).update(
                output_trove = nvf.asString())
            msg = "Image committed as %s=%s/%s" % (nvf.name,
                    nvf.version.trailingLabel(),
                    nvf.version.trailingRevision())
            log.info(msg)
            #self._getImageLogger(hostname, imageId).info(msg)

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

    @exposed
    def getImageUploadStatus(self, image_id, basename):
        filename = self._getUploadFilename(image_id, basename) # FIXME pass an image instead of image_id
        handler = MultiRequestUploadHandler()
        status = handler.getStatus(filename)
        return status

    @exposed
    def processImageUpload(self, image_id, uploaded_file, basename, chunk_id,
                           num_chunks, checksum):
        # FIXME don't process the upload if the image is "complete"
        filename = self._getUploadFilename(image_id, basename) # FIXME pass an image instead of image_id
        handler = MultiRequestUploadHandler()
        upload = handler.handle(uploaded_file, filename, chunk_id, num_chunks, checksum)
        # if upload.isComplete():
            # do useful stuff
            # pass

    def _getUploadFilename(self, image_id, basename):
        # FIXME put UPLOAD_DIR somewhere sane
        # FIXME put project name in path
        UPLOAD_DIR = '/srv/rbuilder/incoming-images'
        # return os.path.join(UPLOAD_DIR, image.projectname, image.image_id)
        return os.path.join(UPLOAD_DIR, os.path.basename(basename))


class MultiRequestUploadHandler(object):
    def handle(self, uploaded_file, filename, chunk_id, num_chunks, checksum):
        if uploaded_file is None:
            raise Exception("No file uploaded")

        if chunk_id is None:
            chunk_id = 0
        chunk_id = int(chunk_id)

        if num_chunks is None:
            num_chunks = 1
        num_chunks = int(num_chunks)

        complete_file = filename
        incomplete_file = filename + '.incomplete'
        status_file = filename + '.status'

        if checksum is not None:
            md5_verify = hashlib.md5()
            for buf in uploaded_file.chunks():
                md5_verify.update(buf)

            if md5_verify.hexdigest() != checksum:
                raise Exception("Checksum error")

        # If this is the first chunk, start from clean slate
        if chunk_id == 0:
            try:
                os.remove(complete_file)
            except:
                pass
            try:
                os.remove(status_file)
            except:
                pass
            # recursively create dest_dir
            dir = os.path.dirname(filename)
            if not os.path.isdir(dir):
                os.path.makedirs(dir)

        # Append uploaded bytes to .incomplete file
        mode = 'wb' if chunk_id == 0 else 'ab'
        with open(incomplete_file, mode) as f:
            for buf in uploaded_file.chunks():
                f.write(buf)
        uploaded_file.close() # delete the tmp file

        # If this is the last chunk, finish up
        if chunk_id == num_chunks - 1:
            os.rename(incomplete_file, complete_file)
            try:
                os.remove(status_file)
            except:
                pass # it's not a big deal if we can't delete the status file
            current_file = complete_file

        else:
            status = {'status': 'uploading',
                      'chunk': chunk_id,
                      'chunks': num_chunks}

            with open(status_file, 'w') as f:
                json.dump(status, f)
            current_file = incomplete_file

        return MultiRequestUploadFile(current_file)

    def getStatus(self, filename):
        '''Returns a dict containing status info, used primarily by Plupload'''
        status = {'status': 'unknown'}
        if os.path.isfile(filename):
            status = {'status': 'finished'}
        elif os.path.isfile(filename + '.status'):
            with open(filename + '.status', 'r') as f:
                status = json.load(f)
        return status


class MultiRequestUploadFile(object):
    def __init__(self, filename):
        self.filename = filename

    def isComplete(self):
        return not self.filename.endswith('.incomplete')
