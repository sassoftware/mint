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
    def getImageBuild(self, image_id):
        return models.Image.objects.get(pk=image_id)
        
    @exposed
    def getImageBuilds(self):
        Images = models.Images()
        Images.image = models.Image.objects.all()
        return Images

    @exposed
    def createImageBuild(self, image):
        image.save()
        return image
        
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
        build_files = models.BuildFile.objects.filter(build__image_id=image_id)
        BuildFiles.build_file = build_files
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