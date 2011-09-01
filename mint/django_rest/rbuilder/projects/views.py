#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse, HttpResponseRedirect

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.inventory.views import StageProxyService
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.projects import models as projectmodels

class PCallbacks(object):
    """
    RBAC callbacks for Project(s)
    """
    @staticmethod
    def _checkPermissions(view, request, project_short_name, action):
        if project_short_name:
            obj = view.mgr.getProject(project_short_name)
            user = request._authUser
            if request.method == 'PUT' and \
                obj.short_name != project_short_name:
                return False
            return view.mgr.userHasRbacPermission(user, obj, action)
        elif request._is_admin:
            return True
        return False

    @staticmethod
    def rbac_can_read_project_by_short_name(view, request, project_short_name=None, *args, **kwargs):
        """
        project_short_name needs to be a kwarg until the views are more granularly refactored.
        """
        return PCallbacks._checkPermissions(view, request, project_short_name, READMEMBERS)

    @staticmethod
    def rbac_can_write_project_by_short_name(view, request, project_short_name, *args, **kwargs):
        """
        project_short_name always required for write to succeed, so don't make it kwarg
        """
        return PCallbacks._checkPermissions(view, request, project_short_name, MODMEMBERS)
        
    @staticmethod
    def rbac_can_write_project(view, request, project, *args, **kwargs):
        user = request._authUser
        return view.mgr.userHasRbacPermission(user, args, MODMEMBERS)

class PBSCallbacks(object):
    @staticmethod
    def rbac_can_read_all_project_branches_stages(view, request, *args, **kwargs):
        if request._is_admin:
            return True
        else:
            return False
    
    @staticmethod
    def rbac_can_read_stage_by_project(view, 
        request, project_short_name, project_branch_label, stage_name=None, *args, **kwargs):
        obj = view.mgr.getProjectBranchStage(project_short_name, project_branch_label, stage_name)
        user = request._authUser
        if not stage_name and request._is_admin:
            return True
        elif stage_name:
            return view.mgr.userHasRbacPermission(user, obj, READMEMBERS)
        return False

    @staticmethod
    def rbac_can_read_pbs_by_project_short_name(view, request, project_short_name):
        user = request._authUser
        collection = projectmodels.Stage.objects.filter(project__short_name=project_short_name)
        tv = all(view.mgr.userHasRbacPermission(user, obj, READMEMBERS) for obj in collection)
        if tv:
            return True
        return False

# class AllProjectBranchesStagesService(service.BaseService):
#     @rbac(PBSCallbacks.rbac_can_read_all_project_branches_stages)
#     @return_xml
#     def rest_GET(self, request):
#         return self.mgr.getAllProjectBranchStages()

class AllProjectBranchesStagesService(service.BaseService):
    """
    get all pbs's
    """
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        if PBSCallbacks.rbac_can_read_all_project_branches_stages(self, request):
            qs = querymodels.QuerySet.objects.get(name='All Project Stages')
            url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
            return HttpResponseRedirect(url)
        raise PermissionDenied()


class AllProjectBranchesService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getAllProjectBranches()

    @access.admin
    @requires('project_branch')
    @return_xml
    def rest_POST(self, request, project_branch):
        project_branch.save()
        return project_branch


class ProjectAllBranchStagesService(service.BaseService):
    """
    returns all pbs associated with a given project.
    """
    @access.authenticated
    @return_xml
    def rest_GET(self, request, project_short_name):
        if PBSCallbacks.rbac_can_read_pbs_by_project_short_name(
            self, request, project_short_name):
            return self.mgr.getProjectAllBranchStages(project_short_name)
        raise PermissionDenied()


class ProjectBranchService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label=None):
        return self.get(project_short_name, project_branch_label)
        
    def get(self, project_short_name, project_branch_label):
        return self.mgr.getProjectBranch(project_short_name, project_branch_label)

    @access.admin
    @requires("project_branch")
    @return_xml
    def rest_POST(self, request, project_short_name, project_branch):
        return self.mgr.addProjectBranch(project_short_name, project_branch)

    @access.admin
    @requires("project_branch")
    @return_xml
    def rest_PUT(self, request, project_short_name, project_branch_label, project_branch):
        return self.mgr.updateProjectBranch(project_branch)

    @access.admin
    def rest_DELETE(self, request, project_short_name, project_branch_label):
        projectBranch = self.get(project_short_name, project_branch_label)
        self.mgr.deleteProjectBranch(projectBranch)
        response = HttpResponse(status=204)
        return response


class ProjectService(service.BaseService):
    # manual RBAC, see get function
    @access.authenticated
    @return_xml
    def rest_GET(self, request, project_short_name=None):
        if PCallbacks.rbac_can_read_project_by_short_name(
            self, request, project_short_name):
            if project_short_name:
                return self.get(project_short_name)
            else:
                qs = querymodels.QuerySet.objects.get(name='All Projects')
                url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
                return HttpResponseRedirect(url)
        raise PermissionDenied()

    def get(self, project_short_name):
        assert project_short_name is not None
        model = self.mgr.getProject(project_short_name)
        return model
    
    # Unknown bug requires manual rbac
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        user = request._authUser
        if self.mgr.userHasRbacPermission(user, project, MODMEMBERS):
            return self.mgr.addProject(project)
        raise PermissionDenied()

    @rbac(PCallbacks.rbac_can_write_project_by_short_name)
    @requires('project')
    @return_xml
    def rest_PUT(self, request, project_short_name, project):
        return self.mgr.updateProject(project)

    @rbac(PCallbacks.rbac_can_write_project_by_short_name)
    def rest_DELETE(self, request, project_short_name):
        project = self.get(project_short_name)
        self.mgr.deleteProject(project)
        response = HttpResponse(status=204)
        return response


# XXX StageProxyService is no longer in use, is
#     ProjectStageService still being used by anything?
class ProjectStageService(service.BaseService):
    
    # FIXME if no longer in use, add access.admin until we are sure we can remove it.
    # else it's a security leak
    @access.admin
    @return_xml
    def rest_GET(self, request, stage_id=None):
        return self.get(request, stage_id)
    
    def get(self, request, stage_id=None):
        if stage_id:
            return StageProxyService.getStageAndSetGroup(request, stage_id)
        else:
            return StageProxyService.getStagesAndSetGroup(request)


class ProjectBranchStageService(service.BaseService):
    @rbac(PBSCallbacks.rbac_can_read_stage_by_project)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label, stage_name=None):
        return self.get(project_short_name, project_branch_label, stage_name)

    def get(self, project_short_name, project_branch_label, stage_name):
        if stage_name:
            return self.mgr.getProjectBranchStage(project_short_name,
                project_branch_label, stage_name)
        return self.mgr.getProjectBranchStages(project_short_name,
            project_branch_label)


class ProjectImageService(service.BaseService):

    @rbac(PCallbacks.rbac_can_read_project_by_short_name)
    @return_xml
    def rest_GET(self, request, project_short_name, image_id=None):
        return self.get(request, project_short_name, image_id)

    def get(self, request, project_short_name, image_id):
        if image_id:
            model = self.mgr.getImage(image_id)
        else:
            model = self.mgr.getImagesForProject(project_short_name)
        return model

    @rbac(PCallbacks.rbac_can_write_project_by_short_name)
    @requires("image")
    @return_xml
    def rest_PUT(self, request, project_short_name, image_id, image):
        image.image_id = image_id
        return self.mgr.updateImage(image)


class ProjectBranchStageImagesService(service.BaseService):
    
    def get(self, request, project_short_name, project_branch_label, stage_name):
        return self.mgr.getProjectBranchStageImages(project_short_name,
            project_branch_label, stage_name)
    
    @rbac(PBSCallbacks.rbac_can_read_stage_by_project)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label, stage_name):
        return self.get(request, project_short_name, project_branch_label, stage_name)

"""        
class ProjectJobDescriptorServiceservice.BaseService):

    @access.anonymous
    # smartform object already is XML, no need
    @return_xml
    def rest_GET(self, request, , job_type):
        '''
        Get a smartform descriptor for starting a action on
        InventorySystemJobsService.  An action is not *quite* a job.
        It's a request to start a job.
        '''
        content = self.get(, job_type, request.GET.copy())
        response = HttpResponse(status=200, content=content)
        response['Content-Type'] = 'text/xml'
        return response

    def get(self, , job_type, parameters):
        return self.mgr.getDescriptorForImageBuildAction(
            , job_type, parameters
        ) 
               
        
class ProjectImageBuildsJobService(service.BaseService):   
    
    @access.admin
    @xObjRequires('job')
    @return_xml
    def rest_POST(self, request, job):
        '''request starting build image'''
        image = self.mgr.getImage(image_id)
        return self.mgr.scheduleJobAction(
            system, job
        )        
"""


class ProjectMemberService(service.BaseService):
    @rbac(PCallbacks.rbac_can_read_project_by_short_name)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)

    def get(self, project_short_name):
        return self.mgr.getProjectMembers(project_short_name)
