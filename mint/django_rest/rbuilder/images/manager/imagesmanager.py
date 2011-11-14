#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import errno
import logging
import os
from django.core import urlresolvers
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.targets import models as tgtmodels
from mint.django_rest.rbuilder.manager import basemanager
from conary.lib import sha1helper
from mint.lib import data as datatypes
from conary import trovetup
from conary import versions
from conary.deps import deps
import time

log = logging.getLogger(__name__)
exposed = basemanager.exposed

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
            image.image_data.add(models.ImageData(name=bdName, value=bdValue,
                data_type=bdType))

        self.mgr.addToMyQuerySet(image, for_user)
        self.mgr.retagQuerySetsByType('image', for_user)
        return image

    @exposed
    def createImageBuildFile(self, image, **kwargs):
        from mint import urltypes
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
    def updateImageBuild(self, image_id, image):
        image.save()
        return image

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
