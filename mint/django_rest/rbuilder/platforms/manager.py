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
        return platformModels.ContentSource.objects.get(short_name=short_name)
        
    @exposed
    def getSources(self, source_type):
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
    def createContentSourceType(self, content_source_type):
        content_source_type.save()
        return content_source_type
        
    @exposed
    def updateSourceType(self, content_source_type):
        content_source_type.save()
        return content_source_type
        
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
        

class PlatformSourceManager(basemanager.BaseManager):
    @exposed
    def getSourcesByPlatform(self, platform_id):
        ContentSources = platformModels.ContentSources()
        platform = platformModels.Platform.objects.get(platform_id=platform_id)
        ContentSources.content_source = platform.content_sources.objects.all()
        return ContentSources

        
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