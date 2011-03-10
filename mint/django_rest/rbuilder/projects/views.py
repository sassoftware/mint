#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service

class ProjectService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name=None):
        return self.get(short_name)

    def get(self, short_name):
        if short_name:
            return self.mgr.getProject(short_name)
        else:
            return self.mgr.getProjects()
        
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
    def rest_GET(self, request, short_name, version_name=None):
        return self.get(short_name, version_name)

    def get(self, short_name, version_name=None):
        if version_name:
            return self.mgr.getProjectVersion(short_name, version_name)
        else:
            return self.mgr.getProjectVersions(short_name)

class ProjectVersionStageService(service.BaseService):
    pass


class ProjectImageService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, short_name, image_id=None):
        return self.get(short_name, image_id)

    def get(self, short_name, image_id):
        return None       
