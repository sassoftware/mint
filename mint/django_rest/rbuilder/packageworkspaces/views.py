from django.http import HttpResponse, HttpResponseNotFound

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access, ACCESS

from mint.django_rest.rbuilder.packageworkspaces import models

class PackageWorkspaceService(service.BaseService):
    """docstring for PackageWorkspaceService"""
    
    @return_xml
    def rest_GET(self, request, workspace_id=None):
        """docstring for rest_GET"""
        if workspace_id:
            return self.mgr.getPackageWorkspace(workspace_id)
        else:
            return self.mgr.getPackageWorkspaces()
    
    # access.admin
    @requires('package_workspace')
    @return_xml
    def rest_POST(self, request, package_workspace):
        """docstring for rest_POST"""
        return self.mgr.addPackageWorkspace(package_workspace)
    
    # @access.admin
    @requires('package_workspace')
    @return_xml
    def rest_PUT(self, request, workspace_id, package_workspace):
        """docstring for rest_PUT"""
        return self.mgr.updatePackageWorkspace(workspace_id, package_workspace)
    
    # @access.admin   
    def rest_DELETE(self, request, workspace_id):
        """docstring for rest_DELETE"""
        self.mgr.deletePackageWorkspace(workspace_id)
        response = HttpResponse(status=204)
        return response