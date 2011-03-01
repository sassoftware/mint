#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.projects import models

class ProjectManager(basemanager.BaseManager):

    @exposed 
    def getProjects(self):
        projects = models.Projects()
        projects.project = [p for p in models.Project.objects.all()
            if self.checkAccess(p)]
        return projects

    @exposed
    def getProject(self, project_id):
        project = models.Project.objects.get(pk=project_id)
        if self.checkAccess(project):   
            return project
        else:
            raise errors.PermissionDenied() 

    def checkAccess(self, project):
        # Admins can see all projects
        if auth.isAdmin(self.user):
            return True
        # Public projects are visible to all
        elif project.hidden == 0:
            return True
        # Is the current user a project member
        elif self.user in project.members.all():
            return True
        else:
            return False

    @exposed
    def updateProject(self, project):
        project.save()
        return project

    @exposed
    def addProject(self, project):
        project.save()
        return project

    @exposed
    def deleteProject(self, project):
        project.delete()
        return project
