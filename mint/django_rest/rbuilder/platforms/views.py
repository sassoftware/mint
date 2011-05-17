# Create your views here.

from django.http import HttpResponse

from mint.django_rest.rbuilder import service  # pyflakes=ignore
from mint.django_rest.deco import requires, return_xml, access  # pyflakes=ignore


class SourceStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type, short_name):
        return self.get(source_type, short_name)

    def get(self, content_source_type, short_name):
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

    @return_xml
    @requires('resource_error')
    def rest_PUT(self, request, source_type, short_name, error_id, resource_error):
        return self.mgr.updatePlatformContentError(source_type, short_name, error_id, resource_error)
        

class SourceService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type, short_name=None):
        return self.get(source_type, short_name)
        
    def get(self, source_type, short_name):
        if short_name:
            return self.mgr.getSource(short_name)
        else:
            return self.mgr.getSources(source_type)

    @return_xml
    @requires('source')
    def rest_PUT(self, request, source_type, short_name, source):
        return self.mgr.updateSource(short_name, source)

    @return_xml
    @requires('source')
    def rest_POST(self, request, source_type, source):
        return self.mgr.createSource(source)

    def rest_DELETE(self, source_type, short_name):
        self.mgr.deleteSource(short_name)
        

class SourceTypeDescriptorService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourceTypeDescriptor(source_type)
    
    
class SourceTypeStatusTestService(service.BaseService):
    @return_xml
    @requires('source')
    def rest_POST(self, request, source_type, source):
        return self.mgr.getSourceStatus(source)


class SourceTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type=None):
        return self.get(source_type)
        
    def get(self, source_type):
        if source_type:
            return self.mgr.getSourceType(source_type)
        else:
            return self.mgr.getSourceTypes()


class PlatformStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getPlatformStatus(platform_id)
    
    @return_xml
    @requires('platform')
    def rest_POST(self, request, platform_id, platform):
        return self.mgr.getPlatformStatusTest(platform)

    
class PlatformSourceService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getSourcesByPlatform(platform_id)

    
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


class PlatformService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id=None):
        return self.get(platform_id)
        
    def get(self, platform_id):
        if platform_id:
            return self.mgr.getPlatform(platform_id)
        else:
            return self.mgr.getPlatforms()
            
    @return_xml
    @requires('platform')
    def rest_POST(self, request, platform):
        return self.mgr.createPlatform(platform)
        
    @return_xml
    @requires('platform')
    def rest_PUT(self, request, platform_id, platform):
        return self.mgr.updatePlatform(platform_id, platform)