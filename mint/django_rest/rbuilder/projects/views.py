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
    pass

class AllProjectBranchesService(service.BaseService):
    pass

class ProjectBranchesAllStagesService(service.BaseService):
    pass

class ProjectBranchService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label=None):
        return self.get(project_short_name, project_branch_label)
        
    def get(self, project_short_name, project_branch_label):
        return self.mgr.getProjectBranch(project_short_name, project_branch_label)


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

class ProjectVersionService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, branch_id=None):
        return self.get(branch_id)

    def get(self, branch_id=None):
        if branch_id:
            return self.mgr.getProjectVersion(branch_id)
        else:
            return self.mgr.getProjectVersions()

    @requires("project_branch")
    @return_xml
    def rest_POST(self, request, project_branch):
        return self.mgr.addProjectVersion(project_branch)

    @requires("project_branch")
    @return_xml
    def rest_PUT(self, request, branch_id, project_branch):
        return self.mgr.updateProjectVersion(project_branch)

    def rest_DELETE(self, request, branch_id):
        projectBranch = self.get(branch_id)
        self.mgr.deleteProjectVersion(projectBranch)
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
            return projectmodels.Stage.objects.get(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label,
                stage_name=stage_name)

        Stages = projectsmodels.Stages()
        iterator = projectsmodels.Stage.objects.filter(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label)
        Stages.project_branch_stage = sorted(iterator,
            key=lambda x: x.stage_id)
        return Stages


class ProjectImageService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name, image_id=None):
        return self.get(request, short_name, image_id)

    def get(self, request, short_name, image_id):
        if image_id:
            model = self.mgr.getImage(image_id)
        else:
            model = self.mgr.getImages()
        return model

class ProjectMemberService(service.BaseService):

    # TODO: figure out correct perms
    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name):
        return self.get(short_name)

    def get(self, short_name):
        return self.mgr.getProjectMembers(short_name)
