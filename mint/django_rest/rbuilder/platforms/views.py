# Create your views here.

from django.http import HttpResponse

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access


class SourceStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, content_source_type, short_name):
        return self.get(content_source_type, short_name)

    def get(self, content_source_type, short_name):
        return self.mgr.getSourceStatus(content_source_type, short_name)


class SourceErrorsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, content_source_type, short_name, error_id=None):
        return self.get(content_source_type, short_name, error_id)

    def get(self, content_source_type, short_name, error_id):
        if error_id:
            return self.mgr.getSourceError(content_source_type, short_name, error_id)
        else:
            return self.mgr.getSourceErrors(content_source_type, short_name)

    @return_xml
    @requires('resource_error')
    def rest_PUT(self, request, source_type, short_name, error_id, resource_error):
        return self.mgr.updateSourceErrors(source_type, short_name, error_id, resource_error)
        

class SourceService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type, short_name=None):
        return self.get(source_type, short_name)
        
    def get(self, source_type, short_name):
        return self.mgr.getSource(source_type, short_name)

    @return_xml
    @requires('source')
    def rest_PUT(self, request, source_type, short_name, source):
        return self.mgr.updateSource(source_type, short_name, source)

    @return_xml
    @requires('source')
    def rest_POST(self, request, source_type, source):
        return self.mgr.createSource(source_type, source)

    def rest_DELETE(self, source_type, short_name):
        self.mgr.deleteSource(source_type, short_name)
        

class SourceTypeDescriptorService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourceTypeDescriptor(source_type)
    

class SourceTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, source_type=None):
        return self.get(source_type)
        
    def get(self, source_type):
        return self.mgr.getSourceType(source_type)


class PlatformStatusService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getPlatformStatus(platform_id)
    
    @return_xml
    @requires('platform')
    def rest_POST(self, request, platform_id, platform):
        return self.mgr.createPlatformStatus(platform_id, platform)

    
class PlatformSourceService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getPlatformSource(platform_id)

    
class PlatformSourceTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getPlatformSourceType(platform_id)
    
    
class PlatformImageTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)
        
    def get(self, platform_id):
        return self.mgr.getPlatformImageType(platform_id)
    
    
class PlatformLoadService(service.BaseService):
    pass
    
    
class PlatformVersionService(service.BaseService):
    pass
    

class PlatformService(service.BaseService):
    pass