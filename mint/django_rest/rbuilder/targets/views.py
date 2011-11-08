#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse# HttpResponseRedirect
from mint.django_rest.deco import access, return_xml, requires, Flags
from mint.django_rest.rbuilder import service
# from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.targets import models

class TargetsService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getTargets()

class TargetService(service.BaseService):

    @return_xml
    def rest_GET(self, request, target_id):
        return self.get(target_id)

    def get(self, target_id):
        return self.mgr.getTargetById(target_id)

    @access.admin
    def rest_DELETE(self, request, target_id):
        self.mgr.deleteTarget(target_id)
        return HttpResponse(status=204)


class TargetTypesService(service.BaseService):
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getTargetTypes()

class TargetTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_type_id):
        return self.get(target_type_id)

    def get(self, target_type_id):
        return self.mgr.getTargetTypeById(target_type_id)

class TargetTypeByTargetService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id):
        return self.get(target_id)
        
    def get(self, target_id):
        return self.mgr.getTargetTypesByTargetId(target_id)
        
class TargetTypeTargetsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_type_id):
        return self.get(target_type_id)

    def get(self, target_type_id):
        return self.mgr.getTargetsByTargetType(target_type_id)

class TargetCredentialsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id, target_credentials_id):
        return self.get(target_id, target_credentials_id)
        
    def get(self, target_id, target_credentials_id):
        return self.mgr.getTargetCredentialsForTarget(target_id, target_credentials_id)

class TargetConfigureCredentialsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id):
        return self.get(target_id)

    def get(self, target_id):
        return self.mgr.serializeDescriptor(
            self.mgr.getDescriptorConfigureCredentials(target_id))

class TargetUserCredentialsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id, user_id):
        return self.get(target_id, user_id)
        
    def get(self, target_id, user_id):
        return self.mgr.getTargetCredentialsForTargetByUserId(target_id, user_id)

class TargetRefreshImagesService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id):
        return self.get(target_id)

    def get(self, target_id):
        return self.mgr.serializeDescriptor(
            self.mgr.getDescriptorRefreshImages(target_id))

    @requires('target_credentials')
    @return_xml
    def rest_POST(self, request, target_credentials):
        return self.mgr.createTargetCredentials(target_credentials)
        
    @requires('target_credentials')
    @return_xml
    def rest_PUT(self, request, target_credentials_id, target_credentials):
        return self.mgr.updateTargetCredentials(target_credentials_id, target_credentials)

class TargetImageDeploymentService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id, file_id):
        return self.get(target_id, file_id)

    def get(self, target_id, file_id):
        return self.mgr.serializeDescriptor(
            self.mgr.getDescriptorDeployImage(target_id, file_id))

class TargetTypeCreateTargetService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_type_id):
        return self.get(target_type_id)

    def get(self, target_type_id):
        return self.mgr.serializeDescriptor(
            self.mgr.getDescriptorCreateTargetByTargetType(target_type_id))

class TargetTypeAllJobsService(service.BaseService):
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getAllTargetTypeJobs()

    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, job):
        return self.mgr.addJob(job)

class TargetTypeJobsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_type_id):
        return self.get(target_type_id)

    def get(self, target_type_id):
        return self.mgr.getJobsByTargetType(target_type_id)

class TargetJobsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id):
        return self.get(target_id)
        
    def get(self, target_id):
        return self.mgr.getJobsByTargetId(target_id)

    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, target_id, job):
        return self.mgr.addJob(job)

class AllTargetJobsService(service.BaseService):
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getAllTargetJobs()

class TargetConfigurationService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id):
        targetConfig = models.TargetConfiguration(target_id)
        return targetConfig