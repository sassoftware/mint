#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint.django_rest.rbuilder.images import models 
from mint.django_rest.rbuilder.manager import basemanager

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class ImagesManager(basemanager.BaseManager):

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
    def getUnifiedImage(self, permission_type):
        # FIXME: placeholder
        return models.Image(id=1, name='placeholder')

    @exposed
    def updateUnifiedImage(self, image_id, image):
        image.save()
        return image
        
    @exposed
    def createUnifiedImage(self, image):
        image.save()
        return image
        
    @exposed
    def getImageBuild(self, build_id):
        return models.Build.objects.get(pk=build_id)
        
    @exposed
    def getImageBuilds(self):
        Builds = models.Builds()
        Builds.build = models.Build.objects.all()
        return Builds

    @exposed
    def createImageBuild(self, build):
        build.save()
        return build
        
    @exposed
    def updateImageBuild(self, build):
        build.save()
        return build
        
    @exposed
    def deleteImageBuild(self, build_id):
        models.Build.objects.get(pk=build_id).delete()

    @exposed
    def getImageBuildFile(self, build_id, file_id):
        build_file = models.BuildFile.objects.get(file_id=file_id)
        return build_file
        
    @exposed
    def getImageBuildFiles(build_id):
        BuildFiles = models.BuildFiles()
        build_files = models.BuildFile.objects.filter(build__build_id=build_id)
        BuildFiles.build_file = build_files
        return BuildFiles