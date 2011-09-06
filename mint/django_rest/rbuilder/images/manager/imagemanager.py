#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
#from mint.django_rest.rbuilder.images import models
import exceptions
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.images import models

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class ImageManager(basemanager.BaseManager):
    pass

    @exposed
    def getImageDefinitionDescriptors(self):
        outer = models.ImageDefinitionDescriptors()
        outer.image_definition_descriptor = [
            models.ImageDefinitionDescriptor(
               name = 'vmware',
            )
        ]
        return outer

    @exposed
    def getImageDefinitionDescriptor(self):
       raise exceptions.NotImplementedError


