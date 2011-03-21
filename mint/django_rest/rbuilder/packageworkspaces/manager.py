from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.packageworkspaces import models

class BaseManager(object):
    def __init__(self, mgr):
        # mgr is a weakref to avoid circular references. Access its fields
        # through properties
        self.mgr = mgr

    @property
    def cfg(self):
        return self.mgr.cfg

    @property
    def rest_db(self):
        return self.mgr.rest_db

    @property
    def user(self):
        return self.mgr.user
        

class PackageWorkspaceManager(BaseManager):
    """docstring for PackageWorkspaceManager"""
    
    @exposed
    def getPackageWorkspaces(self):
        """docstring for getWorkspace"""
        PackageWorkspaces = models.PackageWorkspaces()
        PackageWorkspaces.package_workspace = list(models.PackageWorkspace.objects.all())
        return PackageWorkspaces
    
    @exposed
    def getPackageWorkspace(self, workspace_id):
        """docstring for PackageWorkspace"""
        package_workspace = models.PackageWorkspace.objects.get(pk=workspace_id)
        return package_workspace
        
    @exposed
    def addPackageWorkspace(self, workspace):
        """docstring for addWorkspace"""
        workspace.save()
        return workspace
        
    @exposed
    def updatePackageWorkspace(self, workspace_id, workspace):
        """docstring for updateWorkspace"""
        if not workspace:
            return
        w = models.PackageWorkspace.objects.get(pk=workspace_id)
        field_names = w.get_field_dict().keys()
        for name in field_names:
            attr = getattr(workspace, name, None)
            if not attr:
                continue
            setattr(w, name, attr)
        w.save()
        return w
    
    # @exposed
    # def updatePackageWorkspace(self, workspace):
    #     """docstring for updateWorkspace"""
    #     if not workspace:
    #         return
    #     workspace.save()
    #     return workspace
    
    @exposed
    def deletePackageWorkspace(self, workspace_id):
        """docstring for deletePackageWorkspace"""
        workspace = models.PackageWorkspace.objects.get(pk=workspace_id)
        workspace.delete()