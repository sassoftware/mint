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

