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

from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.repos import models as repomodels
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.projects import models

from conary import conarycfg
from conary import conaryclient
from conary.repository import errors as repoerrors
from rpath_proddef import api1 as proddef

class ProjectManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)

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
        elif not project.hidden:
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
            
        return namespace

    def validateProjectVersionName(self, versionName):
        validProjectVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')
        if not versionName:
            raise projects.ProductVersionInvalid
        if not validProjectVersion.match(versionName):
            raise projects.ProductVersionInvalid
        return None

    @exposed
    def addProject(self, project):
        if not project.repository_hostname:
            project.repository_hostname = (
                    project.short_name + self.cfg.projectDomainName)
        elif '.' not in project.repository_hostname:
            raise projects.ProductVersionInvalid
        project.host_name = project.short_name
        project.domain_name = project.repository_hostname.split('.', 1)[1]
        project.namespace = self.validateNamespace(project.namespace)

        label = None
        if project.labels and len(project.labels.all()) > 0:
            label = project.labels.all()[0]
        else:
            label = repomodels.Label()

        if project.external:
            self._validateExternalProject(project)
            if (project.inbound_mirrors and
                    len(project.inbound_mirrors.all()) > 0):
                # Mirror mode must have a database
                if not project.database:
                    project.database = self.cfg.defaultDatabase
            else:
                # Proxy-mode must not have a database
                project.database = None

            if not project.auth_type:
                project.auth_type = 'none'
            if not project.database:
                # These fields only make sense for proxy mode, otherwise the
                # ones on the inbound mirror model are used.
                label.url = project.upstream_url
                label.auth_type = project.auth_type
                label.user_name = project.user_name
                label.password = project.password
                label.entitlement = project.entitlement
        else:
            # Internal projects always need a database
            project.auth_type = label.auth_type = 'none'
            project.user_name = label.user_name = None
            project.password = label.password = None
            project.entitlement = label.entitlement = None
            project.upstream_url = label.url = None
            if not project.database:
                project.database = self.cfg.defaultDatabase

            # Make sure there isn't an inbound mirror
            if (project.inbound_mirrors and
                    len(project.inbound_mirrors.all()) > 0):
                raise projects.ProductVersionInvalid

        # Set creator to current user
        if self.user:
            project.creator = self.user

        # Save the project, we need the pk populated to create the repository
        project.save()
        label.project = project
        label.save()

        # Create project repository
        self.mgr.createRepositoryForProject(project)

        # Add current user as project owner
        if self.user:
            member = models.Member(project=project, user=self.user, 
                level=userlevels.OWNER)
            member.save()

        return project

    def _validateExternalProject(self, project):
        fqdn = project.repository_hostname
        mirrors = (project.inbound_mirrors
                and project.inbound_mirrors.all() or [])
        for mirror in mirrors:
            testcfg = conarycfg.ConaryConfiguration(False)
            if not mirror.source_url:
                mirror.source_url = 'https://%s/conary/' % (fqdn,)
            testcfg.configLine('repositoryMap %s %s' % (
                fqdn, mirror.source_url))
            if mirror.source_auth_type == 'userpass':
                testcfg.user.addServerGlob(fqdn, (mirror.source_user_name,
                    mirror.source_password))
            elif mirror.source_auth_type == 'entitlement':
                testcfg.entitlement.addEntitlement(fqdn,
                        mirror.source_entitlement)
            else:
                # Don't test mirror permissions if no entitlement is provided.
                mirror.source_auth_type = 'none'
                continue
            testrepos = conaryclient.ConaryClient(testcfg).getRepos()
            try:
                # use 2**64 to ensure we won't make the server do much
                testrepos.getNewTroveList(fqdn, '4611686018427387904')
            except repoerrors.InsufficientPermission:
                raise errors.MirrorCredentialsInvalid(
                        creds=mirror.source_auth_type, url=mirror.source_url)
            except repoerrors.OpenError, err:
                raise errors.MirrorNotReachable(
                        url=mirror.source_url, reason=str(err))
        if not mirrors and not project.upstream_url:
            project.upstream_url = 'https://%s/conary/' % (fqdn,)

    @exposed
    def updateProject(self, project):
        project.namespace = self.validateNamespace(project.namespace)

        # Only an admin can hide a project.
        # XXX Is this correct?
        if project.hidden:
            if self.auth.admin:
                project.hidden = True
            else:
                project.hidden = False

        oldProject = models.Project.objects.get(hostname=project.hostname)
        if not project.hidden and oldProject.hidden:
            self.restDb.publisher.notify('ProductUnhidden', oldProject.pk)
            self.mgr.addUser('.'.join((oldProject.hostname,
                                            oldProject.domain_name)), 
                                  'anonymous',
                                  password='anonymous',
                                  level=userlevels.USER)   
            self.publisher.notify('ProductUnhidden', oldProject.id)

        project.save()
        self.mgr.generateConaryrcFile()
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
                repos = self.mgr.getRepositoryForProject(project)
                self.mgr.editUser(repos, user.username, level)

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
                repos = self.mgr.getRepositoryForProject(project)
                self.mgr.addUserByMd5(repos, user.username,
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
    def getProjectVersions(self):
        allVersions = models.ProjectVersions()
        allVersions.project_branch = models.ProjectVersion.objects.all()
        return allVersions

    @exposed
    def getProjectVersion(self, versionId):
        version = models.ProjectVersion.objects.get(pk=versionId)
        return version
    
    def saveProductVersionDefinition(self, productVersion, prodDef):
        self.setProductVersionDefinition(prodDef)
        # now save them in the DB also
        stages = prodDef.getStages()
        for stage in stages:
            promotable = ((stage.name != stages[-1].name and True) or False)
            dbStage = models.Stage(name=str(stage.name),
                 label=str(prodDef.getLabelForStage(stage.name)),
                 promotable=promotable)
            dbStage.project = productVersion.project
            dbStage.project_branch = productVersion
            dbStage.save()

    def setProductVersionDefinition(self, prodDef):
        cclient = self.mgr.getUserClient()
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    @exposed
    def addProjectVersion(self, projectVersion):

        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()

        if not projectVersion.namespace:
            projectVersion.namespace = projectVersion.project.namespace

        projectVersion.namespace = self.validateNamespace(projectVersion.namespace)
        self.validateProjectVersionName(projectVersion.name)

        # initial product definition
        prodDef = helperfuncs.sanitizeProductDefinition(projectVersion.project.name,
                        projectVersion.project.description, projectVersion.project.hostname, 
                        projectVersion.project.domain_name, 
                        projectVersion.project.short_name, projectVersion.name,
                        '', projectVersion.namespace)
        label = prodDef.getDefaultLabel()

        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if projects.validLabel.match(label) == None:
            raise mint_error.InvalidLabel(label)

        projectVersion.save()
        
        self.saveProductVersionDefinition(projectVersion, prodDef)

        # TODO: get the correct platformLabel
        platformLabel = None

        if projectVersion.project.project_type == 'Appliance' or \
           projectVersion.project.project_type == 'PlatformFoundation':
            groupName = helperfuncs.getDefaultImageGroupName(projectVersion.project.hostname)
            className = util.convertPackageNameToClassName(groupName)
            # convert from unicode
            recipeStr = str(templates.write(groupTemplate,
                            cfg = self.cfg,
                            groupApplianceLabel=platformLabel,
                            groupName=groupName,
                            recipeClassName=className,
                            version=projectVersion.name) + '\n')
            self.mgr.createSourceTrove(str(projectVersion.project.repository_hostname),
                str(groupName), str(label), str(projectVersion.name),
                {'%s.recipe' % str(groupName): recipeStr},
                'Initial appliance image group template')

        return projectVersion

    @exposed
    def updateProjectVersion(self, projectVersion):
        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()
        projectVersion.save()
        return projectVersion

    @exposed
    def deleteProjectVersion(self, projectVersion):
        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()
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
        cclient = self.mgr.getAdminClient(write=False)
        try:
            pd.loadFromRepository(cclient)
        except Exception:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise mint_error.ProductDefinitionVersionNotFound
        return pd

    @exposed
    def getStage(self, stageId):
        stage = models.Stage.objects.get(pk=stageId)
        return stage

    @exposed
    def getStageOld(self, shortName, projectVersionId, stageName):
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
    def getStages(self, version_id=None):
        stages = models.Stages()
        if version_id:
            version = models.ProjectVersion.objects.get(pk=version_id)
            stages.project_branch_stage = version.project_branch_stages.all()
        else:
            stages.project_branch_stage = models.Stage.objects.all()
        return stages

    @exposed
    def getImage(self, short_name, image_id):
        return models.Image.objects.get(pk=image_id)
        
    @exposed
    def getImages(self, short_name, image_id):
        Images = models.Images()
        Images.image = models.Image.all().filter(short_name=short_name)
        return Images
        
    @exposed
    def getProjectBranch(self, short_name, project_branch_name):
        ProjectVersions = models.ProjectVersions()
        ProjectVersions.project_branch = models.ProjectVersion.objects.all().filter(
                project_branch_name=project_branch_name).filter(project__short_name__exact=short_name)
        return ProjectVersions
        
        
        
        