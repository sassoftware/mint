#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.projects import models

class ProjectManager(basemanager.BaseManager):

    @exposed 
    def getProjects(self):
        projects = models.Projects()
        projects.project = models.Project.objects.all()
        return projects

    @exposed
    def getProject(self, project_id):
        project = models.Project.objects.get(pk=project_id)
        return project

    @exposed
    def updateProject(self, project):
        pass

    @exposed
    def addProject(self, project):
        pass
