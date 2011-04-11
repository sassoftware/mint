#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint import helperfuncs
from mint import mint_error
from mint import userlevels
from mint.rest.db import reposmgr

from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.projects import models

class ProjectManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)
        self._reposMgr = None

    @property
    def reposMgr(self):
        if not self._reposMgr:
            self._reposMgr = reposmgr.RepositoryManager(self.cfg, self.restDb,
                self.restDb.auth)
            return self._reposMgr

    @exposed 
    def getProjects(self):
        projects = models.Projects()
        projects.project = [p for p in models.Project.objects.all()
            if self.checkAccess(p)]
        return projects

    @exposed
    def getProject(self, shortName):
        project = models.Project.objects.get(short_name=shortName)
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

    def validateNamespace(self, namespace):
        # Use the default namespace if one was not provided.
        if namespace is None:
            namespace = self.cfg.namespace
        else:
            v = helperfuncs.validateNamespace(namespace)
            if v != True:
                raise mint_error.InvalidNamespace

    @exposed
    def addProject(self, project):
        self.validateNamespace(project.namespace)

        # Set creator to current user
        if self.user:
            project.creator = self.user

        # Save the project, we need the pk populated to create the repository
        project.save()

        # Create project repository
        self.reposMgr.createRepository(project.pk)

        # Add current user as project owner
        if self.user:
            member = models.Member(project=project, user=self.user, 
                level=userlevels.OWNER)
            member.save()

        return project

    @exposed
    def updateProject(self, project):
        self.validateNamespace(project.namespace)

        # Only an admin can hide a project.
        # XXX Is this correct?
        if project.hidden:
            if self.auth.admin:
                project.hidden = 1
            else:
                project.hidden = 0

        oldProject = models.Project.objects.get(hostname=project.hostname)
        if project.hidden == 0 and oldProject.hidden == 1:
            self.restDb.publisher.notify('ProductUnhidden', oldProject.pk)

        self.reposMgr._generateConaryrcFile()

    @exposed
    def deleteProject(self, project):
        project.delete()

    @exposed
    def addProjectMember(self, project, user, level, notify=True):
        oldMember = project.members.filter(user=user)
        if oldMember:
            oldMember = [0]
        else:
            oldMember = None

        # Delete outstanding membership requests
        if level != userlevels.USER:
            self.restDb.db.membershipRequests.deleteRequest(
                project.project_id, user.userid, commit=False)

        if oldMember:
            # If old level is the same, nothing to do
            if level == oldMember.level:
                return user
            
            # Can not demote the last owner
            allOwners = project.member.filter(level=userlevels.OWNER)
            if len(allOwners) == 1 and oldMember.level == userlevels.OWNER:
                raise mint_error.LastOwner

            # Update the old level
            oldMember.level = level
            oldMember.save()

            # Edit repository perms for non-external projects
            if not project.external:
                self.reposMgr.editUser(project.fqdn, user.username, level)

            # Send notification
            if notify:
                self.restDb.publisher.notify('UserProductChanged',
                    user.userid, project.project_id, oldMember.level, level)
        else:
            # Add membership
            member = models.Project.member(project=project, user=user, level=level)
            member.save()

            # Add repository perms for non-external projects
            if not project.external:
                self.reposMgr.addUserByMd5(project.fqdn, user.username,
                    user.salt, user.password, level)

            # Send notification
            if notify:
                self.restDb.publisher.notify('UserProductAdded', user.userid,
                    project.project_id, None, level)

        return user

    @exposed
    def deleteProjectMember(self, project, user):
        member = models.Member.filter(project=project, user=user)

        # Can not demote the last owner
        allOwners = project.member.filter(level=userlevels.OWNER)
        if len(allOwners) == 1 and user in allOwners:
            raise mint_error.LastOwner

        member.delete()

    @exposed
    def getProjectVersions(self, shortName):
        versions = models.Versions()
        project = models.Project.objects.get(short_name=shortName)
        versions.version = project.versions.all()
        versions._parents = [project]
        return versions

    @exposed
    def getProjectVersion(self, shortName, versionName):
        version = models.Version.objects.get(name=versionName)
        return version

    @exposed
    def getProjectMembers(self, shortName):
        project = models.Project.objects.get(short_name=shortName)
        members = models.Members()
        members.member = [m for m in project.members.all()]
        members._parents = [project]
        return members

