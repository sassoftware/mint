#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, requires
from mint.django_rest.rbuilder import service

class ProjectService(service.BaseService):

    @return_xml
    def rest_GET(self, request, project_name=None):
        return self.get(project_name)

    def get(self, project_name):
        if project_name:
            return self.mgr.getProject(project_name)
        else:
            return self.mgr.getProjects()
        
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        return self.mgr.addProject(project)

    @requires('project')
    @return_xml
    def rest_PUT(self, request, project_name, project):
        return self.mgr.updateProject(project)

    def rest_DELETE(self, request, project_name):
        project = self.get(project_name)
        return self.mgr.deleteProject(project)


class ProjectVersionService(service.BaseService):

    @return_xml
    def rest_GET(self, request, project_name, version_id=None):
        return self.get(project_name, version_id)

    def get(self, project_name, version_id):
        return None


class ProjectImageService(service.BaseService):

    @return_xml
    def rest_GET(self, request, project_name, image_id=None):
        return self.get(project_name, image_id)

    def get(self, project_name, image_id):
        return None       
