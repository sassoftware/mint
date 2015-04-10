#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
import exceptions

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.platforms import models as platform_models

IMAGE_TYPE_DESCRIPTORS="mint.django_rest.rbuilder.platforms.image_type_descriptors"
exposed = basemanager.exposed


class PlatformManager(basemanager.BaseManager):
    @exposed
    def getPlatform(self, platform_id):
        return platform_models.Platform.objects.get(platform_id=platform_id)

    @exposed
    def getPlatforms(self):
        Platforms = platform_models.Platforms()
        Platforms.platform = platform_models.Platform.objects.order_by('platform_id')
        return Platforms

    @exposed
    def createPlatform(self, platform):
        platform.save()
        return platform

    @exposed
    def updatePlatform(self, platform_id, platform):
        platform.save()
        return platform

    @exposed
    def getImageTypeDefinitionDescriptor(self, name):
        '''
        An image type definition descriptor contains the smartform
        XML needed to define an image type, for example,
        a vmwareImage type will need virtualized RAM and disk
        parameters.
        '''
        modname = "%s.%s" % (IMAGE_TYPE_DESCRIPTORS, name)
        try:
             __import__(modname)
        except exceptions.ImportError:
             return None
        mod = sys.modules[modname]
        return mod.XML.strip()


class PlatformImageTypeManager(basemanager.BaseManager):
    @exposed
    def getPlatformImageTypeDefs(self, request, platform_id):
        pass
        

class PlatformVersionManager(basemanager.BaseManager):
    @exposed
    def getPlatformVersion(self, platform_id, platform_version_id):
        return platform_models.PlatformVersion.objects.get(pk=platform_version_id)
    
    @exposed
    def getPlatformVersions(self, platform_id):
        PlatformVersions = platform_models.PlatformVersions()
        PlatformVersions.platform_version = \
            platform_models.PlatformVersion.objects.all().filter(platform_id=platform_id)
        return PlatformVersions
