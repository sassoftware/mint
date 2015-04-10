#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to images -- expect heavy changes
# as target service evolves

import urllib
from django.http import HttpResponse, HttpResponseRedirect 
from mint.django_rest.deco import requires, return_xml, access, Flags
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.rbacauth import rbac, manual_rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
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

class _JobOutputTokenAuthService(service.BaseAuthService):

    def _check_uuid_auth(self, request, kwargs):
        request._withAuthToken = False
        headerName = 'X-rBuilder-OutputToken'
        imageOutputToken = self.getHeaderValue(request, headerName)
        if not imageOutputToken:
            return None
        imageId = kwargs['image_id']
        # Check for existance
        imgs = models.ImageData.objects.filter(image__image_id=imageId,
            name='outputToken', value=imageOutputToken).select_related('image__created_by')
        if not imgs:
            return False
        self._setMintAuth(request, imgs[0].image.created_by)
        request._withAuthToken = True
        return True

class ImagesService(service.BaseService):

    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request):
        qs = querymodels.QuerySet.objects.get(name='All Images')
        url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
        return HttpResponseRedirect(url)
    
    @rbac(manual_rbac)
    @requires('image')
    @return_xml
    def rest_POST(self, request, image):
        # RBAC depends on two resources so you can't build an image you can't
        # read.
        user = request._authUser
        if not self.mgr.userHasRbacCreatePermission(user, 'image'):
            raise PermissionDenied(msg="missing create permission on image")
        if not self.mgr.userHasRbacPermission(user, image.project, READMEMBERS):
            raise PermissionDenied(msg="missing read permission on project")
        return self.mgr.createImageBuild(image, for_user=user)
    
class ImageService(_JobOutputTokenAuthService):

    @access.auth_token
    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)
    
    def get(self, image_id):
        return self.mgr.getImageBuild(image_id)
    
    @access.auth_token
    @rbac(can_write_image)
    @requires('image', flags=Flags(save=False))
    @return_xml
    def rest_PUT(self, request, image_id, image):
        if str(image_id) != str(image.pk):
            raise PermissionDenied(msg="id does not match URL")
        if request._withAuthToken:
            self.mgr.setImageBuildStatus(image)
            return self.mgr.getImageBuild(image_id)

        return self.mgr.updateImage(image)

    @rbac(can_write_image)
    def rest_DELETE(self, request, image_id):
        self.mgr.deleteImageBuild(image_id)
        return HttpResponse(status=204)


class ImageJobsService(service.BaseService):

    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id):
        return self.get(image_id)

    def get(self, imageId):
        return self.mgr.getJobsByImageId(imageId)

    @rbac(can_read_image)
    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, image_id, job):
        return self.mgr.addJob(job, imageId=image_id)

class ImageBuildFilesService(_JobOutputTokenAuthService):
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

    @access.auth_token
    @requires('files', flags=Flags(save=False))
    @return_xml
    def rest_PUT(self, request, image_id, files):
        return self.mgr.updateImageBuildFiles(image_id, files)

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
        self._setMintAuth(request, jobs[0].created_by)
        request._withAuthToken = True
        return True

    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id, file_id):
        return self.get(image_id, file_id)

    def get(self, image_id, file_id):
        return self.mgr.getImageBuildFile(image_id, file_id)

    @access.auth_token
    @rbac(can_write_image)
    @requires('file')
    @return_xml
    def rest_PUT(self, request, image_id, file_id, file):
        if str(file_id) != str(file.pk):
            raise PermissionDenied(msg="id does not match URL")
        if request._withAuthToken:
            self.mgr.addTargetImagesForFile(file)
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
        
        
class BuildLogService(_JobOutputTokenAuthService):

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

    @access.auth_token
    @return_xml
    def rest_POST(self, request, image_id):
        self.mgr.appendToBuildLog(image_id, request.read())
        return HttpResponse(status=204)

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

class ImageDescriptorsService(service.BaseService):
    @rbac(can_read_image)
    @return_xml
    def rest_GET(self, request, image_id, descriptor_type):
        return self.get(image_id, descriptor_type)

    def get(self, image_id, descriptor_type):
        return self.mgr.serializeDescriptor(
            self.mgr.getImageDescriptor(image_id, descriptor_type))
