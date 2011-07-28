#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
import urllib2 as url2

class ProjectBranchService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name, project_branch_name):
        return self.get(short_name, project_branch_name)
        
    def get(self, short_name, project_branch_name):
        return self.mgr.getProjectBranch(short_name, project_branch_name)


class ProjectService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name=None):
        model = self.get(short_name)
        return model

    def get(self, short_name):
        if short_name:
            model = self.mgr.getProject(short_name)
        else:
            model = self.mgr.getProjects()
        return model
        
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        return self.mgr.addProject(project)

    @requires('project')
    @return_xml
    def rest_PUT(self, request, short_name, project):
        return self.mgr.updateProject(project)

    def rest_DELETE(self, request, short_name):
        project = self.get(short_name)
        self.mgr.deleteProject(project)
        response = HttpResponse(status=204)
        return response

class ProjectVersionService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, branch_id=None):
        return self.get(request, branch_id)

    def get(self, request, branch_id=None):
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
        return self.get(stage_id)

    def get(self, stage_id):
        if stage_id:
            return self.mgr.getStage(stage_id)
        else:
            return self.mgr.getStages()
        
class ProjectBranchStageService(service.BaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, version_name, stage_id=None):
        return self.get(version_name, stage_id)

    def get(self, version_name, stage_id):
        if stage_id:
            return self.mgr.getStage(stage_id)
        else:
            return self.mgr.getStages(version_name)

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


class GroupsService(service.BaseService):

    @access.anonymous # what are actual permissions for this?
    def rest_GET(self, request, hostname, search):
        return self.get(request, hostname, search)
    
    def get(self, request, hostname=None, search=None):
        """
        hostname and search should not be None but to hack together
        groups (so I can call "get" with just the request), they need to be
        """
        old_api_url = request.get_full_path().replace('/v1', '')
        host = request.get_host()
        raw_xml = url2.urlopen('http://' + host.strip('/') + old_api_url).read()
        return HttpResponse(raw_xml, mimetype='text/xml')