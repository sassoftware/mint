#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import re

from conary.lib import util

from mint import helperfuncs
from mint import mint_error
from mint import userlevels
from mint import projects
from mint import templates
from mint.templates import groupTemplate
from mint.rest.db import reposmgr

from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.projects import models

from rpath_proddef import api1 as proddef

class ProjectManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)
        self._reposMgr = None

    def reposMgr(self):
        if not self._reposMgr:
            self._reposMgr = reposmgr.RepositoryManager(self.cfg, self.restDb,
                self.restDb.auth)
            return self._reposMgr

    @exposed 
    def getProjects(self):
        allProjects = models.Projects()
        allProjects.project = [p for p in models.Project.objects.all()
            if self.checkAccess(p)]
        return allProjects

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

    def isProjectOwner(self, project):
        # Admins can see all projects
        if auth.isAdmin(self.user):
            return True
        membership = project.membership.filter(user=self.user)
        if not membership:
            return False
        membership = membership[0]
        return membership.level == userlevels.OWNER

    def validateNamespace(self, namespace):
        # Use the default namespace if one was not provided.
        if namespace is None:
            namespace = self.cfg.namespace
        else:
            v = helperfuncs.validateNamespace(namespace)
            if v != True:
                raise mint_error.InvalidNamespace

    def validateProjectVersionName(self, versionName):
        validProjectVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')
        if not versionName:
            raise projects.ProductVersionInvalid
        if not validProjectVersion.match(versionName):
            raise projects.ProductVersionInvalid
        return None

    @exposed
    def addProject(self, project):
        self.validateNamespace(project.namespace)

        # Set creator to current user
        if self.user:
            project.creator = self.user

        if not project.database:
            project.database = self.cfg.defaultDatabase

        # Save the project, we need the pk populated to create the repository
        project.save()

        # Create project repository
        self.mgr.createRepositoryForProject(project)

        # Add current user as project owner
        if self.user:
            member = models.Member(project=project, user=self.user, 
                level=userlevels.OWNER)
            member.save()

        self.restDb.publisher.notify('ProductCreated', project.project_id)

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

        project.save()
        self.reposMgr()._generateConaryrcFile()
        return project

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
                self.reposMgr().editUser(project.repository_hostname, 
                    user.username, level)

            # Send notification
            if notify:
                self.restDb.publisher.notify('UserProductChanged',
                    user.userid, project.project_id, oldMember.level, level)
        else:
            # Add membership
            member = models.Project.member(project=project, user=user, 
                level=level)
            member.save()

            # Add repository perms for non-external projects
            if not project.external:
                self.reposMgr().addUserByMd5(project.repository_hostname, 
                    user.username,
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
        versions = models.ProjectVersions()
        project = models.Project.objects.get(short_name=shortName)
        versions.project_version = project.versions.all()
        versions._parents = [project]
        return versions

    @exposed
    def getProjectVersion(self, shortName, versionId):
        version = models.ProjectVersion.objects.get(pk=versionId)
        return version

    @exposed
    def addProjectVersion(self, shortName, projectVersion):
        project = models.Project.objects.get(short_name=shortName)

        if not self.isProjectOwner(project):
            raise errors.PermissionDenied()

        if not projectVersion.namespace:
            projectVersion.namespace = project.namespace

        self.validateNamespace(projectVersion.namespace)
        self.validateProjectVersionName(projectVersion.name)

        # initial product definition
        prodDef = helperfuncs.sanitizeProductDefinition(project.name,
                        projectVersion.description, project.hostname, 
                        project.domain_name, 
                        project.short_name, projectVersion.name,
                        '', projectVersion.namespace)
        label = prodDef.getDefaultLabel()

        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if projects.validLabel.match(label) == None:
            raise mint_error.InvalidLabel(label)

        projectVersion.project = project
        projectVersion.save()

        # TODO: get the correct platformLabel
        platformLabel = None

        if project.project_type == 'Appliance' or \
           project.project_type == 'PlatformFoundation':
            groupName = helperfuncs.getDefaultImageGroupName(project.hostname)
            className = util.convertPackageNameToClassName(groupName)
            # convert from unicode
            recipeStr = str(templates.write(groupTemplate,
                            cfg = self.cfg,
                            groupApplianceLabel=platformLabel,
                            groupName=groupName,
                            recipeClassName=className,
                            version=projectVersion.name) + '\n')
            self.mgr.createSourceTrove(str(project.repository_hostname),
                str(groupName), str(label), str(projectVersion.name),
                {'%s.recipe' % str(groupName): recipeStr},
                'Initial appliance image group template')

        return projectVersion

    @exposed
    def updateProjectVersion(self, shortName, projectVersion):
        project = models.Project.objects.get(short_name=shortName)
        if not self.isProjectOwner(project):
            raise errors.PermissionDenied()
        projectVersion.save()
        return projectVersion

    @exposed
    def deleteProjectVersion(self, projectVersion):
        projectVersion.delete()

    @exposed
    def getProjectMembers(self, shortName):
        project = models.Project.objects.get(short_name=shortName)
        members = models.Members()
        members.member = [m for m in project.members.all()]
        members._parents = [project]
        return members

    def getProductVersionDefinitionByProjectVersion(self, projectVersion):
        project = projectVersion.project
        pd = proddef.ProductDefinition()
        pd.setProductShortname(project.short_name)
        pd.setConaryRepositoryHostname(project.repository_hostname)
        pd.setConaryNamespace(projectVersion.namespace)
        pd.setProductVersion(projectVersion.name)
        cclient = self.reposMgr().getAdminClient(write=False)
        try:
            pd.loadFromRepository(cclient)
        except Exception:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise mint_error.ProductDefinitionVersionNotFound
        return pd

    @exposed
    def getStage(self, shortName, projectVersionId, stageName):
        projectVersion = models.ProjectVersion.objects.get(
            pk=projectVersionId) 
        project = projectVersion.project
        pd = self.getProductVersionDefinitionByProjectVersion(projectVersion)
        pdStages = pd.getStages()
        stage = [s for s in pdStages if s.name == stageName][0]
        promotable = ((stage.name != pdStages[-1].name and True) or False)
        dbStage = models.Stage(name=str(stage.name),
             label=str(pd.getLabelForStage(stage.name)),
             hostname=project.hostname, project_version=projectVersion,
             Promotable=promotable)
        return dbStage

    @exposed
    def getStages(self, shortName, projectVersionId):
        projectVersion = models.ProjectVersion.objects.get(
            pk=projectVersionId) 
        project = projectVersion.project
        pd = self.getProductVersionDefinitionByProjectVersion(projectVersion)
        stages = models.Stages()
        stages.stage = []
        pdStages = pd.getStages()
        for stage in pdStages:
            promotable = ((stage.name != pdStages[-1].name and True) or False)
            # TODO: now that we've created a model for this stage, should we
            # save it in the db?
            dbStage = models.Stage(name=str(stage.name),
                 label=str(pd.getLabelForStage(stage.name)),
                 hostname=project.hostname, project_version=projectVersion,
                 Promotable=promotable)
            stages.stage.append(dbStage)
        return stages
