#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.platforms import models as platformModels


exposed = basemanager.exposed


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
        

class SourceManager(basemanager.BaseManager):
    @exposed
    def getSource(self, short_name):
        return platformModels.Source.objects.get(short_name=short_name)
        
    @exposed
    def getSources(self, source_type):
        Sources = platformModels.Sources()
        Sources.source = platformModels.Source.objects.all().filter(content_source_type=source_type)
        return Sources
        
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
        source = platformModels.Source.objects.get(short_name=short_name)
        source.delete()
        

class SourceTypeDescriptorManager(basemanager.BaseManager):
    @exposed
    def getSourceTypeDescriptor(self, source_type):
        pass
        

class SourceTypeStatusTestManager(basemanager.BaseManager):
    @exposed
    def getSourceStatus(self, source):
        return source.content_source_status
        
    
class SourceTypeManager(basemanager.BaseManager):
    @exposed
    def getSourceType(self, source_type):
        return platformModels.SourceType.objects.all().filter(content_source_type=source_type)
        
    @exposed
    def getSourceTypes(self):
        SourceTypes = platformModels.SourceTypes()
        SourceTypes.source_type = platformModels.SourceType.objects.all()
        return SourceTypes
        
        
class PlatformStatusManager(basemanager.BaseManager):
    @exposed
    def getPlatformStatus(self, platform_id):
        return platformModels.Platform.objects.get(
            platform_id=platform_id).platform_status
        
    @exposed
    def getPlatformStatusTest(self, platform):
        pass
        

class PlatformSourceManager(basemanager.BaseManager):
    @exposed
    def getSourcesByPlatform(self, platform_id):
        platform = platformModels.Platform.objects.get(platform_id=platform_id)
        return platform.content_sources.objects.all()
        
        
class PlatformSourceTypeManager(basemanager.BaseManager):
    @exposed
    def getSourceTypesByPlatform(self, platform_id):
        platform = platformModels.Platform.objects.get(platform_id=platform_id)
        return platform.content_source_types.objects.all()
        
        
class PlatformImageTypeManager(basemanager.BaseManager):
    @exposed
    def getPlatformImageTypeDefs(self, request, platform_id):
        pass
        

class PlatformLoadManager(basemanager.BaseManager):
    @exposed
    def getPlatformLoadStatus(self, platform_id, job_id):
        pass
        
    @exposed
    def loadPlatform(self, platform_id, platform_load):
        pass
        

class PlatformVersionManager(basemanager.BaseManager):
    @exposed
    def getPlatformVersion(self, platform_id, platform_version_id):
        return platformModels.PlatformVersion.objects.get(platform_id=platform_id)
    
    @exposed
    def getPlatformVersions(self, platform_id):
        PlatformVersions = platformModels.PlatformVersions()
        PlatformVersions.platform_version = \
            platformModels.PlatformVersion.objects.all().filter(platform_id=platform_id)
        return PlatformVersions
        

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
    def updatePlatform(platform_id, platform):
        platform.save()
        return platform