#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse, HttpResponseNotFound
from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access

class SourceStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type, short_name):
        return self.get(source_type, short_name)

    def get(self, source_type, short_name):
        return self.mgr.getSourceStatusByName(source_type, short_name)


class SourceErrorsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type, short_name, error_id=None):
        return self.get(source_type, short_name, error_id)

    def get(self, source_type, short_name, error_id):
        if error_id:
            return self.mgr.getPlatformContentError(source_type, short_name, error_id)
        else:
            return self.mgr.getPlatformContentErrors(source_type, short_name)

    @requires('resource_error')
    @return_xml
    def rest_PUT(self, request, source_type, short_name, error_id, resource_error):
        return self.mgr.updatePlatformContentError(source_type, short_name, error_id, resource_error)

class AllSourcesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getSources()

    @access.anonymous # needs to be changed
    @requires('content_source')
    @return_xml
    def rest_POST(self, request, content_source):
        return self.mgr.createSource(content_source)

class SourcesService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourcesByType(source_type)

class SourceService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, source_type, short_name):
        return self.get(source_type, short_name)
        
    def get(self, source_type, short_name):
        return self.mgr.getSourceByShortName(short_name)

    @access.anonymous
    @requires('content_source')
    @return_xml
    def rest_PUT(self, request, source_type, short_name, content_source):
        return self.mgr.updateSource(short_name, content_source)

    @access.anonymous # needs to be changed
    def rest_DELETE(self, source_type, short_name):
        self.mgr.deleteSource(short_name)
        

class SourceTypeDescriptorService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourceTypeDescriptor(source_type)
    
    
class SourceTypeStatusTestService(service.BaseService):
    @requires('content_source')
    @return_xml
    def rest_POST(self, request, source_type, source):
        return self.mgr.getSourceStatus(source)

class AllSourceTypesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getSourceTypes()
    
    @access.anonymous # what are permissions for this
    @requires('content_source_type')
    @return_xml
    def rest_POST(self, request, content_source_type):
        return self.mgr.createSourceType(content_source_type)
    

class SourceTypesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, source_type):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourceType(source_type)
            
            
class SourceTypeService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, source_type, content_source_type_id):
        return self.get(source_type, content_source_type_id)
        
    def get(self, source_type, content_source_type_id):
        return self.mgr.getSourceTypeById(content_source_type_id)

    @access.anonymous # change
    @requires('content_source_type')
    @return_xml
    def rest_PUT(self, request, source_type, content_source_type_id, content_source_type):
        return self.mgr.updateSourceType(content_source_type)


class PlatformLoadStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id, job_id=None):
        return self.get(platform_id, job_id)
        
    def get(self, platform_id, job_id):
        return self.mgr.getPlatformLoadStatus(platform_id, job_id)
    
    @requires('platform')
    @return_xml
    def rest_POST(self, request, platform_id, platform):
        return self.mgr.getPlatformStatusTest(platform)

    
class PlatformSourceService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getSourcesByPlatform(platform_id)

    @access.anonymous
    @requires('content_source')
    @return_xml
    def rest_POST(self, request, platform_id, content_source):
        return self.mgr.createSource(content_source)
    
    @requires('content_source')
    @return_xml
    def rest_PUT(self, request, platform_id, content_source):
        return self.mgr.updateSource(content_source)
    
class PlatformSourceTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getSourceTypesByPlatform(platform_id)
    
    
class PlatformImageTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(request, platform_id)
        
    def get(self, request, platform_id):
        return self.mgr.getPlatformImageTypeDefs(request, platform_id)
    
    
class PlatformLoadService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id, job_id):
        return self.get(platform_id, job_id)
        
    def get(self, platform_id, job_id):
        return self.mgr.getPlatformLoadStatus(platform_id, job_id)
        
    @return_xml
    @requires('platform_load')
    def rest_POST(self, request, platform_id, platform_load):
        return self.mgr.loadPlatform(platform_id, platform_load)
    
    
class PlatformVersionService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id, platform_version_id=None):
        return self.get(platform_id, platform_version_id)
    
    def get(self, platform_id, platform_version_id):
        if platform_version_id:
            return self.mgr.getPlatformVersion(platform_id, platform_version_id)
        else:
            return self.mgr.getPlatformVersions(platform_id)


class PlatformsService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getPlatforms()

    @access.anonymous # needs to change!
    @requires('platform')
    @return_xml
    def rest_POST(self, request, platform):
        return self.mgr.createPlatform(platform)
    
class PlatformService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)

    def get(self, platform_id):
        return self.mgr.getPlatform(platform_id)
    
    @access.anonymous
    @requires('platform')
    @return_xml
    def rest_PUT(self, request, platform_id, platform):
        return self.mgr.updatePlatform(platform_id, platform)

class ImageTypeDefinitionDescriptorService(service.BaseService):
    '''Returns a smartform with options required for each image type'''

    @access.anonymous
    def rest_GET(self, request, name=None):
        descriptor_xml = self.mgr.getImageTypeDefinitionDescriptor(name)
        if descriptor_xml is None:
            return HttpResponseNotFound()
        return HttpResponse(content=descriptor_xml)


