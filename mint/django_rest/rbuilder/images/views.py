#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to images -- expect heavy changes
# as target service evolves

from django.http import HttpResponse 
from mint.django_rest.deco import requires, return_xml, access, Flags
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.projects import models as projectsmodels

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

    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        return self.get()
    
    def get(self):
        return self.mgr.getImageBuilds()
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        return self.mgr.createImageBuild(image)
    
class ImageService(BaseImageService):
    @access.authenticated
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)
    
    def get(self, image_id):
        return self.mgr.getImageBuild(image_id)
    
    @access.admin
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        return self.mgr.updateImageBuild(image_id, image)

    @access.admin
    def rest_DELETE(self, request, image_id):
        self.mgr.deleteImageBuild(image_id)
        return HttpResponse(status=204)


class ImageJobsService(BaseImageService):
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)

    def get(self, imageId):
        return self.mgr.getJobsByImageId(imageId)

    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, image_id, job):
        return self.mgr.addJob(job)

class ImageBuildFilesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)
        
    def get(self, image_id):
        return self.mgr.getImageBuildFiles(image_id)
            
    @access.admin
    @requires('file')
    @return_xml
    def rest_POST(self, request, image_id, file):
        file.save()
        return file


class ImageBuildFileService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, image_id, file_id):
        return self.get(image_id, file_id)

    def get(self, image_id, file_id):
        return self.mgr.getImageBuildFile(image_id, file_id)

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


class ReleasesService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getReleases()
            
    @access.admin
    @requires('release')
    @return_xml
    def rest_POST(self, request, release):
        return self.mgr.createRelease(release)


class ReleaseService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, release_id):
        return self.get(release_id)

    def get(self, release_id):
        return self.mgr.getReleaseById(release_id)

    @access.admin
    @requires('release')
    @return_xml
    def rest_PUT(self, request, release_id, release):
        return self.mgr.updateRelease(release_id, release)

    @access.admin
    def rest_DELETE(self, request, release_id):
        release = projectsmodels.Release.objects.get(pk=release_id)
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
        # host = request.get_host()
        return self.get(image_id)
        
    def get(self, image_id):
        buildLog = self.mgr.getBuildLog(image_id)
        response = HttpResponse()
        response['Content-Type'] = 'text/plain'
        response.write(buildLog)
        return response
        
class ImageTypesService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getImageTypes()

class ImageTypeService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, image_type_id):
        return self.get(image_type_id)

    def get(self, image_type_id):
        return self.mgr.getImageType(image_type_id)