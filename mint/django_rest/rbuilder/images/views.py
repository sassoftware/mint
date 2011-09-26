#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to images -- expect heavy changes
# as target service evolves

from django.http import HttpResponse 
from mint.django_rest.deco import requires, return_xml, access #, requires
from mint.django_rest.rbuilder import service
#from mint.django_rest.rbuilder.images import models

class BaseImageService(service.BaseService):
    pass

class ImagesService(BaseImageService):

    # leaving as admin until we can determine RBAC policy
    # and create an "All Images" queryset
    @access.admin
    @return_xml
    def rest_GET(self, request):
        # unified images are the
        # images on the targets + images we can deploy
        return self.mgr.getUnifiedImages()

class ImageService(BaseImageService):

    @access.admin
    @return_xml
    def rest_GET(self, request, image_id):
        return self.mgr.getUnifiedImage(image_id)
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        return self.mgr.createUnifiedImage(image)
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        return self.mgr.updateUnifiedImage(image_id, image)


class ImageBuildService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, build_id=None):
        return self.get(build_id)
        
    def get(self, build_id):
        if build_id:
            return self.mgr.getImageBuild(build_id)
        else:
            return self.mgr.getImageBuilds()
    
    @access.admin
    @requires('build')
    @return_xml
    def rest_POST(self, build_id, build):
        return self.mgr.createImageBuild(build)
        
    @access.admin
    @requires('build')
    @return_xml
    def rest_PUT(self, build_id, build):
        return self.mgr.updateImageBuild(build)
    
    @access.admin
    def rest_DELETE(self, build_id):
        self.mgr.deleteImageBuild(build_id)
        return HttpResponse(status=204)
    
        
class ImageBuildFileService(service.BaseService):
    
    @access.admin
    @return_xml
    def rest_GET(self, build_id, file_id=None):
        return self.get(build_id, file_id)
        
    def get(self, build_id, file_id):
        if file_id:
            return self.mgr.getImageBuildFile(build_id, file_id)
        else:
            return self.mgr.getImageBuildFiles(build_id)       