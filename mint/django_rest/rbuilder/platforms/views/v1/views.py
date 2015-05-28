#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.http import HttpResponse, HttpResponseNotFound
from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access


class PlatformImageTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(request, platform_id)
        
    def get(self, request, platform_id):
        return self.mgr.getPlatformImageTypeDefs(request, platform_id)


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
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getPlatforms()

    @access.authenticated
    @requires('platform')
    @return_xml
    def rest_POST(self, request, platform):
        return self.mgr.createPlatform(platform)
    
class PlatformService(service.BaseService):
    @access.authenticated
    @return_xml
    def rest_GET(self, request, platform_id):
        return self.get(platform_id)

    def get(self, platform_id):
        return self.mgr.getPlatform(platform_id)
    
    @access.authenticated
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
