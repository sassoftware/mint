#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import connection
import logging
from mint.django_rest.rbuilder.images import models 
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.manager import basemanager
from conary.lib import sha1helper
from mint.lib import data as datatypes
from mint import buildtypes
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
    def createImageBuild(self, image):
        outputToken = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        buildData = [('outputToken', outputToken, datatypes.RDT_STRING)]

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
                self.project_branch_stage_id = pbs.stage_id

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

        return image

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
        models.Image.objects.get(pk=image_id).delete()

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
    def getReleases(self):
        Releases = projectsmodels.Releases()
        Releases.release = projectsmodels.Release.objects.all()
        return Releases
        
    @exposed
    def getReleaseById(self, release_id):
        return projectsmodels.Release.objects.get(pk=release_id)
        
    @exposed
    def createRelease(self, release):
        release.save()
        return release
        
    @exposed
    def updateRelease(self, release_id, release):
        release.save()
        return release
        
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
