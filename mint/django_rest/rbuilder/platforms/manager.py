#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
import exceptions
import StringIO

import smartform.descriptor

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.platforms import models as platformModels

IMAGE_TYPE_DESCRIPTORS="mint.django_rest.rbuilder.platforms.image_type_descriptors"
exposed = basemanager.exposed

class SourceTypeManager(basemanager.BaseManager):
    @exposed
    def getSourceType(self, source_type):
        ContentSourceTypes = platformModels.ContentSourceTypes()
        cst = platformModels.ContentSourceType.objects.all().filter(content_source_type=source_type)
        ContentSourceTypes.content_source_type = cst
        return ContentSourceTypes
        
    @exposed
    def getSourceTypes(self):
        ContentSourceTypes = platformModels.ContentSourceTypes()
        ContentSourceTypes.content_source_type = platformModels.ContentSourceType.objects.all()
        return ContentSourceTypes
    
    @exposed
    def getSourceTypeById(self, content_source_type_id):
        ContentSourceType = platformModels.ContentSourceType.objects.get(pk=content_source_type_id)
        return ContentSourceType
    
    @exposed
    def createSourceType(self, content_source_type):
        content_source_type.save()
        return content_source_type
        
    @exposed
    def updateSourceType(self, content_source_type):
        content_source_type.save()
        return content_source_type


class PlatformManager(basemanager.BaseManager):
    @exposed
    def getPlatform(self, platform_id):
        return platformModels.Platform.objects.get(platform_id=platform_id)

    @exposed
    def getPlatforms(self):
        Platforms = platformModels.Platforms()
        Platforms.platform = platformModels.Platform.objects.all()
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
        if name == 'deferred':
            return self._getDeferredImageTypeDescriptor()

        modname = "%s.%s" % (IMAGE_TYPE_DESCRIPTORS, name)
        # TODO: if the IT is 'deferrred', generate dynamically
        # TODO: add IT type 'deferred'
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
        desc.setRootElement("createApplianceDescriptor")
        desc.setDisplayName("Deferred Image Configuration")
        desc.addDescription("Deferred Image Configuration")

        # TODO: maybe not all images are deployable, if so call something else
        deployable_images = self.mgr.getUnifiedImages()
        image_codes = [ x.name for x in deployable_images.image ]
        # TODO: we might want a description other than just the name
        # this is just stub data for now
        smartform_values = [ desc.ValueWithDescription(x, descriptions=x) for x in image_codes ] 

        desc.addDataField("base-image",
            required = True,
            multiple = False,
            type = desc.EnumeratedType(smartform_values)
        )
        sio = StringIO.StringIO()
        desc.serialize(sio)
        result = sio.getvalue()

        # FIXME -- setRootElement does not set the actual root, just the
        # metadata, this is temporary until I find the right way to use the lib.
        result = result.replace("<descriptor ", "<createApplianceDescriptor ")
        result = result.replace("</descriptor>", "</createApplianceDescriptor>")
        return result

class SourceManager(basemanager.BaseManager):
    @exposed
    def getSourceByShortName(self, short_name):
        return platformModels.ContentSource.objects.get(short_name=short_name)
        
    @exposed
    def getSources(self):
        ContentSources = platformModels.ContentSources()
        ContentSources.content_source = platformModels.ContentSource.objects.all()
        return ContentSources
    
    @exposed
    def getSourcesByType(self, source_type):
        ContentSources = platformModels.ContentSources()
        ContentSources.content_source = platformModels.ContentSource.objects.all().filter(content_source_type=source_type)
        return ContentSources
        
    @exposed
    def updateSource(self, short_name, source):
        source.save()
        return source
        
    @exposed
    def createSource(self, source):
        source.save()
        return source
    
    @exposed    
    def deleteSource(self, short_name):
        source = platformModels.ContentSource.objects.get(short_name=short_name)
        source.delete()
        

class PlatformSourceManager(basemanager.BaseManager):
    @exposed
    def getSourcesByPlatform(self, platform_id):
        ContentSources = platformModels.ContentSources()
        platform = platformModels.Platform.objects.get(platform_id=platform_id)
        ContentSources.content_source = platform.content_sources.objects.all()
        return ContentSources


class SourceTypeDescriptorManager(basemanager.BaseManager):
    @exposed
    def getSourceTypeDescriptor(self, source_type):
        pass


class SourceTypeStatusTestManager(basemanager.BaseManager):
    @exposed
    def getSourceStatus(self, source):
        return source.content_source_status


class PlatformLoadStatusManager(basemanager.BaseManager):
    @exposed
    def getPlatformLoadStatus(self, platform_id, job_id):
        platform_loads = platformModels.PlatformLoad.objects.all().filter(
            platform_id=platform_id, job_id=job_id)
        Statuses = platformModels.PlatformLoadStatuses()
        Statuses.platform_load_status = [p.platform_load_status for p in platform_loads]
        return Statuses

    @exposed
    def getPlatformStatusTest(self, platform):
        pass


class PlatformSourceTypeManager(basemanager.BaseManager):
    @exposed
    def getSourceTypesByPlatform(self, platform_id):
        ContentSourceTypes = platformModels.ContentSourceTypes()
        platform = platformModels.Platform.objects.get(platform_id=platform_id)
        ContentSourceTypes.content_source_type = platform.content_source_types
        return ContentSourceTypes
        
        
class PlatformImageTypeManager(basemanager.BaseManager):
    @exposed
    def getPlatformImageTypeDefs(self, request, platform_id):
        pass
        

class PlatformLoadManager(basemanager.BaseManager):
        
    @exposed
    def loadPlatform(self, platform_id, platform_load):
        platform_load.save()
        return platform_load
        

class PlatformVersionManager(basemanager.BaseManager):
    @exposed
    def getPlatformVersion(self, platform_id, platform_version_id):
        return platformModels.PlatformVersion.objects.get(pk=platform_version_id)
    
    @exposed
    def getPlatformVersions(self, platform_id):
        PlatformVersions = platformModels.PlatformVersions()
        PlatformVersions.platform_version = \
            platformModels.PlatformVersion.objects.all().filter(platform_id=platform_id)
        return PlatformVersions


class SourceStatusManager(basemanager.BaseManager):
    @exposed
    def getSourceStatusByName(self, source_type, short_name):
        status = \
            platformModels.SourceStatus.objects.all().filter(
                content_source_type=source_type, short_name=short_name)
        return status


class SourceErrorsManager(basemanager.BaseManager):
    @exposed
    def getPlatformContentError(self, source_type, short_name, error_id):
        platformContentError = \
            platformModels.PlatformContentError.objects.all().filter(
                content_source_type=source_type, short_name=short_name, error_id=error_id)
        return platformContentError

    @exposed
    def getPlatformContentErrors(self, source_type, short_name):
        PlatformContentErrors = platformModels.PlatformContentErrors()
        PlatformContentErrors.platform_content_error = \
            platformModels.PlatformContentError.objects.all().filter(
                content_source_type=source_type, short_name=short_name)
        return PlatformContentErrors

    @exposed
    def updatePlatformContentError(self, source_type, short_name, error_id, resource_error):
        pass

