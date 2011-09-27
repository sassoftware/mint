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
from mint.django_rest.rbuilder.images import models

"""
FIXME:
After refactoring, many of the view methods do the model processing directly
while the naming scheme for the corresponding manager methods are worked out.
This is a mess and should be corrected ASAP.
"""

class BaseImageService(service.BaseService):
    pass

# class ImagesService(BaseImageService):
# 
#     # leaving as admin until we can determine RBAC policy
#     # and create an "All Images" queryset
#     @access.admin
#     @return_xml
#     def rest_GET(self, request):
#         # unified images are the
#         # images on the targets + images we can deploy
#         return self.mgr.getUnifiedImages()

class ImagesService(BaseImageService):

    @access.admin
    @return_xml
    def rest_GET(self, request, image_id=None):
        return self.get(image_id)
    
    def get(self, image_id):
        if image_id:
            return self.mgr.getImageById(image_id)
        else:
            return self.mgr.getAllImages()
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        image.save()
        return image
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        image.save()
        return image

    @access.admin
    def rest_DELETE(self, image_id):
        self.mgr.deleteImageBuild(image_id)
        return HttpResponse(status=204)
    
        
class ImageBuildFileService(service.BaseService):
    
    @access.admin
    @return_xml
    def rest_GET(self, request, image_id, file_id=None):
        return self.get(image_id, file_id)
        
    def get(self, image_id, file_id):
        if file_id:
            return self.mgr.getImageBuildFile(image_id, file_id)
        else:
            return self.mgr.getImageBuildFiles(image_id)
            
    @access.admin
    @requires('build_file')
    @return_xml
    def rest_POST(self, image_id, build_file):
        build_file.save()
        return build_file

    @access.admin
    @requires('build_file')
    @return_xml
    def rest_PUT(self, image_id, file_id, build_file):
        build_file.save()
        return build_file  
        
    @access.admin
    def rest_DELETE(self, image_id, file_id):
        models.BuildFile.objects.get(pk=file_id).delete()
        return HttpResponse(status=204)