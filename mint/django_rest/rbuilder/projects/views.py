#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.inventory.views import StageProxyService
from mint.django_rest.rbuilder.projects import models as projectsmodels

class AllProjectBranchesStagesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getAllProjectBranchStages()

class AllProjectBranchesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getAllProjectBranches()

    @requires('project_branch')
    @return_xml
    def rest_POST(self, request, project_branch):
        project_branch.save()
        return project_branch

class ProjectAllBranchStagesService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.mgr.getProjectAllBranchStages(project_short_name)

class ProjectBranchService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label=None):
        return self.get(project_short_name, project_branch_label)
        
    def get(self, project_short_name, project_branch_label):
        return self.mgr.getProjectBranch(project_short_name, project_branch_label)

    @access.anonymous
    @requires("project_branch")
    @return_xml
    def rest_POST(self, request, project_short_name, project_branch):
        return self.mgr.addProjectBranch(project_short_name, project_branch)

    @requires("project_branch")
    @return_xml
    def rest_PUT(self, request, project_short_name, project_branch_label, project_branch):
        return self.mgr.updateProjectBranch(project_branch)

    def rest_DELETE(self, request, project_short_name, project_branch_label):
        projectBranch = self.get(project_short_name, project_branch_label)
        self.mgr.deleteProjectBranch(projectBranch)
        response = HttpResponse(status=204)
        return response

class ProjectService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, project_short_name=None):
        model = self.get(project_short_name)
        return model

    def get(self, project_short_name):
        if project_short_name:
            model = self.mgr.getProject(project_short_name)
        else:
            model = self.mgr.getProjects()
        return model
        
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        return self.mgr.addProject(project)

    @requires('project')
    @return_xml
    def rest_PUT(self, request, project_short_name, project):
        return self.mgr.updateProject(project)

    def rest_DELETE(self, request, project_short_name):
        project = self.get(project_short_name)
        self.mgr.deleteProject(project)
        response = HttpResponse(status=204)
        return response

class ProjectStageService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, stage_id=None):
        return self.get(request, stage_id)
    
    def get(self, request, stage_id=None):
        if stage_id:
            return StageProxyService.getStageAndSetGroup(request, stage_id)
        else:
            return StageProxyService.getStagesAndSetGroup(request)

class ProjectBranchStageService(service.BaseService):
    @access.anonymous
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

    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name, image_id=None):
        return self.get(request, short_name, image_id)

    def get(self, request, short_name, image_id):
        if image_id:
            model = self.mgr.getImage(image_id)
        else:
            model = self.mgr.getImagesForProject(short_name)
        return model

class ProjectBranchStageImagesService(service.BaseService):
    def get(self, request, project_short_name, project_branch_label, stage_name):
        return self.mgr.getProjectBranchStageImages(project_short_name,
            project_branch_label, stage_name)

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

    # TODO: figure out correct perms
    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name):
        return self.get(short_name)

    def get(self, short_name):
        return self.mgr.getProjectMembers(short_name)
