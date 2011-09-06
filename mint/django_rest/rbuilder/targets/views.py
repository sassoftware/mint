from django.http import HttpResponse, HttpResponseRedirect
from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.errors import PermissionDenied

class TargetService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request, target_id=None):
        return self.get(target_id)
        
    def get(self, target_id):
        if target_id:
            return self.mgr.getTargetById(target_id)
        else:
            return self.mgr.getTargets()
    
    @requires('target')
    @return_xml
    def rest_POST(self, request, target):
        return self.mgr.createTarget(target)
        
    @requires('target')
    @return_xml
    def rest_PUT(self, request, target_id, target):
        return self.mgr.updateTarget(target_id, target)
        
    def rest_DELETE(self, request, target_id):
        self.mgr.deleteTarget(target_id)
        return HttpResponse(status=204)
        

class TargetTypeService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_type_id=None):
        return self.get(target_type_id)
        
    def get(self, target_type_id):
        if target_type_id:
            return self.mgr.getTargetTypeById(target_type_id)
        else:
            return self.mgr.getTargetTypes()

    
class TargetUserCredentialsService(service.BaseService):
    @return_xml
    def rest_GET(self, request, target_id, user_id):
        return self.get(target_id, user_id)
        
    def get(self, target_id, user_id):
        return self.mgr.getTargetCredentialsForTargetByUserId(target_id, user_id)
        
    @requires('target_credentials')
    @return_xml
    def rest_POST(self, request, target_credentials):
        return self.mgr.createTargetCredentials(target_credentials)
        
    @requires('target_credentials')
    @return_xml
    def rest_PUT(self, request, target_credentials_id, target_credentials):
        return self.mgr.updateTargetCredentials(target_credentials_id, target_credentials)
