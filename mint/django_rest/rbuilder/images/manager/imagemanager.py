#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint.django_rest.rbuilder.images import models
from datetime import datetime
import exceptions
from mint.django_rest.rbuilder.manager import basemanager

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class ImageManager(basemanager.BaseManager):
    pass

    @exposed
    def getImageDescriptors(self):
        raise exceptions.NotImplementedError

    @exposed
    def getImageDescriptor(self):
       raise exceptions.NotImplementedError


