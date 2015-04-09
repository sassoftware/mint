#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
import exceptions
import StringIO

import smartform.descriptor

from conary.deps import deps

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.platforms import models as platform_models
from mint.django_rest.rbuilder.images import models as imagemodels

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
        parameters.   (These are served from templates unless
        the type is deferred, in which case it is generated
        dynamically.  More types may be dynamic later.)
        '''
        if name == 'deferredImage':
            return self._getDeferredImageTypeDescriptor()

        modname = "%s.%s" % (IMAGE_TYPE_DESCRIPTORS, name)
        try:
             __import__(modname)
        except exceptions.ImportError:
             return None
        mod = sys.modules[modname]
        return mod.XML.strip()

    def _getDeferredImageTypeDescriptor(self):
        '''
        A deferred image is a base image + an appliance
        group to install on it. Here we only need to prompt
        for the base image as the appliance group is defined
        based on the project name.
        '''
        desc = smartform.descriptor.ConfigurationDescriptor()
        desc.setRootElement('descriptor_data')
        desc.setDisplayName("Layered Image Configuration")
        desc.addDescription("Layered Image Configuration")

        # TODO: this might be filtered more aggressively later
        # right now the image list could get very large

        deployable_images = imagemodels.Image.objects.filter(
            output_trove__isnull=False
        )

        smartform_values = []
        
        noImages=False
        if not deployable_images:
            val = desc.ValueWithDescription('nobaseimagesavailable',
                    descriptions='No base images available')
            smartform_values.append(val)
            noImages=True
        else:
            for img in deployable_images:
                val = desc.ValueWithDescription(img.output_trove,
                    descriptions=img.name)
    
                flv = deps.ThawFlavor(str(img.trove_flavor))
                if flv.stronglySatisfies(deps.parseFlavor('is: x86_64')):
                    arch = 'x86_64'
                else:
                    arch = 'x86'
    
                val.architecture = arch
                smartform_values.append(val)
        
        desc.addDataField('displayName',
            required = True,
            multiple = False,
            type = 'str',
            descriptions = ['Image Name', ],
        )

        desc.addDataField("options.baseImageTrove",
            required = True,
            multiple = False,
            readonly = noImages,
            default = noImages and 'nobaseimagesavailable' or None,
            type = desc.EnumeratedType(smartform_values)
        )

        sio = StringIO.StringIO()
        desc.serialize(sio)
        result = sio.getvalue()
        return result

        
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
