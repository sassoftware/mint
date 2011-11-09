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
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.rbac.rbacauth import rbac #, manual_rbac
# from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS

"""
FIXME:
After refactoring, many of the view methods do the model processing directly
while the naming scheme for the corresponding manager methods are worked out.
This is a mess and should be corrected ASAP.
"""

def _rbac_image_access_check(view, request, image_id, action, *args, **kwargs):
    '''core rbac policy for images'''
    # first look to explicit access on the image, if available, if not
    # then inherit permissions based on the project
    obj = view.mgr.getImageBuild(image_id)
    user = request._authUser
    if view.mgr.userHasRbacPermission(user, obj, action):
        return True
    project = obj.project
    return view.mgr.userHasRbacPermission(user, project, action)
       
def can_write_image(view, request, image_id, *args, **kwargs):
    '''can the user write this?'''
    return _rbac_image_access_check(
        view, request, image_id, 
        MODMEMBERS, *args, **kwargs
    )

def can_read_image(view, request, image_id, *args, **kwargs):
    '''can the user read this?'''
    return _rbac_image_access_check(
        view, request, image_id, 
        READMEMBERS, *args, **kwargs
    )

def can_create_image(view, request, *args, **kwargs):
    '''can a user create new images?'''
    return view.mgr.userHasRbacCreatePermission(request._authUser, 'image')

def _rbac_release_access_check(view, request, release_id, action, *args, **kwargs):
    release = view.mgr.getReleaseById(release_id)
    project = release.project 
    user = request._authUser
    return view.mgr.userHasRbacPermission(user, project, action)

def can_read_release(view, request, release_id, *args, **kwargs):
    return _rbac_release_access_check(
        view, request, release_id, 
        READMEMBERS, *args, **kwargs
    )

def can_write_release(view, request, release_id, *args, **kwargs):
    return _rbac_release_access_check(
        view, request, release_id, 
        MODMEMBERS, *args, **kwargs
    )

def can_create_release(view, request, *args, **kwargs):
    user = request._authUser
    project = kwargs['release'].project
    return view.mgr.userHasRbacPermission(user, project, MODMEMBERS)

class BaseImageService(service.BaseService):
    pass

class ImagesService(BaseImageService):

    # FIXME: will be @rbac(manual_rbac) after redirect
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        # FIXME: redirect to queryset required, see inventory/systems
        return self.get()
    
    def get(self):
        return self.mgr.getImageBuilds()
    
    @rbac(can_create_image)
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        return self.mgr.createImageBuild(image, for_user=request._authUser)
    
class ImageService(BaseImageService):

    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)
    
    def get(self, image_id):
        return self.mgr.getImageBuild(image_id)
    
    @rbac(can_write_image)
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        return self.mgr.updateImageBuild(image_id, image)

    @rbac(can_write_image)
    def rest_DELETE(self, request, image_id):
        self.mgr.deleteImageBuild(image_id)
        return HttpResponse(status=204)


class ImageJobsService(BaseImageService):

    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)

    def get(self, imageId):
        return self.mgr.getJobsByImageId(imageId)

    @rbac(can_write_image)
    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, image_id, job):
        return self.mgr.addJob(job, imageId=image_id)

class ImageBuildFilesService(service.BaseService):
 
    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)
        
    def get(self, image_id):
        return self.mgr.getImageBuildFiles(image_id)
            
    @rbac(can_write_image)
    @requires('file')
    @return_xml
    def rest_POST(self, request, image_id, file):
        file.save()
        return file


class ImageBuildFileService(service.BaseAuthService):

    def _check_uuid_auth(self, request, kwargs):
        request._withAuthToken = False
        headerName = 'X-rBuilder-Job-Token'
        jobToken = self.getHeaderValue(request, headerName)
        if not jobToken:
            return None
        fileId = kwargs['file_id']
        # Check for existance
        jobs = jobsmodels.Job.objects.filter(
            images__image__files__file_id=fileId, job_token=jobToken)
        if not jobs:
            return False
        self._setMintAuth(jobs[0].created_by)
        request._withAuthToken = True
        return True

    # explicitly allowed so image files can be passed around
    # URL is hard to guess
    @access.anonymous
    @return_xml
    def rest_GET(self, request, image_id, file_id):
        return self.get(image_id, file_id)

    def get(self, image_id, file_id):
        return self.mgr.getImageBuildFile(image_id, file_id)

    # FIXME: ok to leave admin only and not rbacify this?
    # rbac may need to be taught to coexist with
    # auth_token
    @access.auth_token
    @access.admin
    @requires('file')
    @return_xml
    def rest_PUT(self, request, image_id, file_id, file):
        if request._withAuthToken:
            self.mgr.addTargetImagesForFile(file)
        file.save()
        return file

    @rbac(can_write_image)
    def rest_DELETE(self, request, image_id, file_id):
        models.BuildFile.objects.get(pk=file_id).delete()
        return HttpResponse(status=204)

# write manager for this!
class ImageBuildFileUrlService(service.BaseService):

    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id, file_id):
        return self.get(image_id, file_id)
        
    def get(self, image_id, file_id):
        return models.BuildFilesUrlsMap.objects.get(file=file_id).url
      
    @rbac(can_write_image)
    @requires('file_url')
    @return_xml
    def rest_POST(self, request, image_id, file_id, file_url):
        file_url.save()
        return file_url
        
        
class BuildLogService(service.BaseService):

    @rbac(can_read_image)
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

    # TODO: verify there's not any reason this can't
    # be public
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getImageTypes()

class ImageTypeService(service.BaseService):

    # TODO: verify there's not any reason this can't
    # be public
    @access.anonymous
    @return_xml
    def rest_GET(self, request, image_type_id):
        return self.get(image_type_id)

    def get(self, image_type_id):
        return self.mgr.getImageType(image_type_id)


