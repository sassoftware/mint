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
            return self.mgr.getImageBuild(image_id)
        else:
            return self.mgr.getImageBuilds()
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        return self.mgr.createImageBuild(image)
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        return self.mgr.updateImageBuild(image_id, image)

    @access.admin
    def rest_DELETE(self, request, image_id):
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
    @requires('file')
    @return_xml
    def rest_POST(self, request, image_id, file):
        file.save()
        return file

    @access.admin
    @requires('file')
    @return_xml
    def rest_PUT(self, request, image_id, file_id, file):
        file.save()
        return file  
        
    @access.admin
    def rest_DELETE(self, request, image_id, file_id):
        models.BuildFile.objects.get(pk=file_id).delete()
        return HttpResponse(status=204)
        
        
class ReleaseService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, release_id=None):
        return self.get(release_id)
        
    def get(self, release_id):
        if release_id:
            return self.mgr.getReleaseById(release_id)
        else:
            return self.mgr.getReleases()
            
    @access.admin
    @requires('release')
    @return_xml
    def rest_POST(self, request, release):
        return self.mgr.createRelease(release)
        
    @access.admin
    @requires('release')
    @return_xml
    def rest_PUT(self, request, release_id, release):
        return self.mgr.updateRelease(release_id, release)
        
    @access.admin
    def rest_DELETE(self, request, release_id):
        release = models.Release.objects.get(pk=release_id)
        release.delete()
        return HttpResponse(status=204)
        
# write manager for this!
class ImageBuildFileUrlService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, image_id, file_id):
        return self.get(image_id, file_id)
        
    def get(self, image_id, file_id):
        return models.BuildFilesUrlsMap.objects.get(file=file_id).url
        
    @access.admin
    @requires('file_url')
    @return_xml
    def rest_POST(self, request, image_id, file_id, file_url):
        file_url.save()
        return file_url
        
        
class BuildLogService(service.BaseService):
    @access.admin
    def rest_GET(self, request, image_id):
        return self.get(image_id)
        
    def get(self, image_id):
        return self.mgr.getBuildLog(image_id)