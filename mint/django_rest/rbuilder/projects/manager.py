#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging
import os
import exceptions
import time

from django.db import IntegrityError
from conary.lib import util

from mint import helperfuncs
from mint import mint_error
from mint import userlevels
from mint import projects

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.repos import models as repomodels
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.platforms import models as platform_models
from mint.django_rest.rbuilder.projects import models
from mint.django_rest.rbuilder.images import models as imagemodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.users import models as usermodels

from conary import conarycfg
from conary import conaryclient
from conary.repository import errors as repoerrors
from rpath_proddef import api1 as proddef
from rpath_job import api1 as rpath_job

log = logging.getLogger(__name__)


class ProductJobStore(rpath_job.JobStore):
    _storageSubdir = 'product-load-jobs'


class ProjectManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)

    @exposed
    def getProject(self, project_name):
        project = models.Project.objects.select_related(depth=2).get(short_name=project_name)
        return project

    @exposed
    def getProjectById(self, project_id):
        return models.Project.objects.get(pk=project_id)

    @exposed
    def projectNameInUse(self, project):
        found = projectsmodels.Project.objects.filter(name=project.name)
        if len(found) > 0:
            return True
        return False

    @exposed
    def addProject(self, project, for_user):
        if project.project_id is not None:
            # No updates via addProject
            raise errors.Conflict(msg='Project already exists')
        project.save()

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
                label.url = str(project.upstream_url)
                label.auth_type = str(project.auth_type)
                label.user_name = str(project.user_name)
                label.password = str(project.password)
                label.entitlement = str(project.entitlement)
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
        project.created_by  = for_user
        project.modified_by = for_user
        project.created_date = time.time()
        project.modified_date = time.time()

        # Save the project, we need the pk populated to create the repository
        project.save()
        label.project = project
        label.save()

        # Create project repository
        self.mgr.createRepositoryForProject(project)

        # legacy permissions system
        # Add current user as project owner
        if for_user:
            member = models.Member(project=project, user=for_user,
                level=userlevels.OWNER)
            member.save()

        self.mgr.retagQuerySetsByType('project', for_user)
        # UI or API consumer will follow up this with a seperate call to create
        # the branch via addProjectBranch, so no need to retag stages now
        self.mgr.addToMyQuerySet(project, for_user)

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
    def updateProject(self, project, for_user):
        oldProject = models.Project.objects.get(hostname=project.hostname)
        if not project.hidden and oldProject.hidden:
            self.restDb.publisher.notify('ProductUnhidden', oldProject.pk)
        elif project.hidden:
            handle = self.mgr.getRepositoryForProject(oldProject)
            try:
                handle.deleteUser('anonymous')
            except repoerrors.UserNotFound:
                pass
            if not oldProject.hidden:
                self.restDb.publisher.notify('ProductHidden', oldProject.pk)

        project.save()
        project.modified_by = for_user
        project.modifed_date = time.time()
        return project

    @exposed
    def deleteProject(self, project):
        handle = self.mgr.getRepositoryForProject(project)
        # Delete the repository database.
        if handle.hasDatabase:
            try:
                handle.destroy()
            except:
                log.exception("Could not delete repository for project %s:",
                        handle.shortName)

        # Clean up the stragglers
        imagesDir = os.path.join(self.cfg.imagesPath, handle.shortName)
        if os.path.exists(imagesDir):
            try:
                util.rmtree(imagesDir)
            except:
                log.warning("Could not delete project images directory %s:",
                        imagesDir, exc_info=True)
        project.delete()

    @exposed
    def addProjectMember(self, project, user, level, notify=True):
        oldMember = project.members.filter(user=user)
        if oldMember:
            oldMember = [0]
        else:
            oldMember = None

        if oldMember:
            # If old level is the same, nothing to do
            if level == oldMember.level:
                return user

            # Can not demote the last owner
            allOwners = project.member.filter(level=userlevels.OWNER)
            if len(allOwners) == 1 and oldMember.level == userlevels.OWNER:
                raise errors.Conflict(msg='cannot demote the last owner')

            # Update the old level
            oldMember.level = level
            oldMember.save()

            # Send notification
            if notify:
                self.restDb.publisher.notify('UserProductChanged',
                    user.userid, project.project_id, oldMember.level, level)
        else:
            # Add membership
            member = models.Project.member(project=project, user=user,
                level=level)
            member.save()

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
            raise errors.Conflict(msg='cannot demote the last owner')

        member.delete()

    def saveProductVersionDefinition(self, productVersion, prodDef, forUser=None):
        # Make sure users can't overwrite proddefs on other projects by
        # tweaking their own proddef XML.
        checkFQDN = productVersion.label.split('@')[0]
        expectFQDN = productVersion.project.repository_hostname
        assert checkFQDN.lower() == expectFQDN.lower()

        prodDef.setBaseLabel(productVersion.label)
        self.setProductVersionDefinition(prodDef)
        # now save them in the DB also
        stages = prodDef.getStages()
        for stage in stages:
            promotable = ((stage.name != stages[-1].name and True) or False)
            models.Stage.objects.create(name=str(stage.name),
                    label=str(prodDef.getLabelForStage(stage.name)),
                    promotable=promotable,
                    created_by=forUser,
                    modified_by=forUser,
                    project = productVersion.project,
                    project_branch = productVersion)

    def setProductVersionDefinition(self, prodDef):
        cclient = self.mgr.getAdminClient(write=True)
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    @exposed
    def addProjectBranch(self, projectShortName, projectVersion, forUser):
        projectVersion._prepareSave()

        if not projectVersion.namespace:
            projectVersion.namespace = projectVersion.project.namespace

        # validate the label, which will be added later.  This is done
        # here so the project is not be created before this error occurs
        if projects.validLabel.match(projectVersion.label) == None:
            raise errors.Conflict(msg="invalid label=%s" % projectVersion.label)

        if not projectVersion.name.replace(".","").isalnum():
            raise errors.Conflict(msg="branch name (%s) must be alpha-numeric" % projectVersion.name)

        projectVersion.created_by = forUser
        projectVersion.modified_by = forUser

        project = projectVersion.project

        pd = helperfuncs.sanitizeProductDefinition(
                projectName=project.name,
                projectDescription=project.description or '',
                repositoryHostname=project.repository_hostname,
                shortname=project.short_name,
                version=projectVersion.name,
                versionDescription=projectVersion.description or '',
                namespace=projectVersion.namespace)
        pd.setBaseLabel(projectVersion.label)

        # FIXME: use the href and look up the platform in the DB instead
        platformLabel = str(projectVersion.platform_label or '')
        if platformLabel:
            platform = platform_models.Platform.objects.select_related(depth=2
                    ).get(label=platformLabel)
            cclient = self.mgr.getAdminClient(write=True)
            pd.rebase(cclient, platform.label, overwriteStages=True)

        tnow = time.time()
        projectVersion.created_date = tnow
        projectVersion.modified_date = tnow
        try:
            projectVersion.save()
        except IntegrityError, e:
            if 'duplicate key' in str(e):
                raise errors.Conflict(
                        msg='Conflict with an existing project branch')
            raise

        self.saveProductVersionDefinition(projectVersion, pd, forUser=forUser)

        self.mgr.retagQuerySetsByType('project_branch_stage', forUser)
        return projectVersion

    @exposed
    def updateProjectBranch(self, projectVersion, forUser=None):
        projectVersion.save()
        projectVersion.modified_by = forUser
        projectVersion.modifed_date = time.time()
        return projectVersion

    @exposed
    def deleteProjectBranch(self, projectVersion):
        projectVersion.delete()

    @exposed
    def getProjectMembers(self, shortName):
        project = models.Project.objects.select_related(depth=2).get(short_name=shortName)
        members = models.Members()
        # FIXME -- to avoid serialization overhead, should this be a paged
        # collection versus inline?
        members.member = [m for m in project.members.select_related(depth=2).all()]
        members._parents = [project]
        return members

    def getProductVersionDefinitionByProjectVersion(self, projectVersion):
        pd = proddef.ProductDefinition()
        pd.setBaseLabel(projectVersion.label)
        cclient = self.mgr.getAdminClient(write=False)
        try:
            pd.loadFromRepository(cclient)
        except Exception:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise errors.Conflict(msg='product version definition not found')
        return pd

    @exposed
    def getStage(self, stageId):
        stage = models.Stage.objects.select_related(depth=2).get(pk=stageId)
        return stage

    @exposed
    def getStageByProjectBranchAndStageName(self, projectBranch, stageName):
        if hasattr(projectBranch, 'branch_id'):
            projectBranchId = projectBranch.branch_id
        else:
            projectBranchId = projectBranch
        stages = models.Stage.objects.filter(project_branch__branch_id=projectBranchId,
            name=stageName)
        if stages:
            return stages[0]
        return None

    @exposed
    def getImage(self, image_id):
        return imagemodels.Image.objects.select_related(depth=2).get(pk=image_id)

    @exposed
    def getImagesForProject(self, short_name):
        project = self.getProject(short_name)
        images = imagemodels.Images()
        images.image = imagemodels.Image.objects.select_related(depth=2).filter(
            project__project_id=project.project_id
        ).order_by('image_id').all()
        images.url_key = [ short_name ]
        images.view_name = 'ProjectImages'
        return images

    @exposed
    def updateImage(self, image):
        # Nothing to update for the moment
        return image

    @exposed
    def getProjectBranch(self, project_name, project_branch_label):
        if project_branch_label:
            # Even though technically doing a GET and letting it fail
            # is not efficient, this is what most of the code does
            return models.ProjectVersion.objects.select_related(depth=2).get(
                label=project_branch_label, project__short_name=project_name)

        projectVersions = models.ProjectVersions()
        projectVersions.project_branches = models.ProjectVersion.objects.select_related(depth=2).filter(
            project__short_name=project_name).order_by('branch_id')
        return projectVersions

    @exposed
    def getAllProjectBranches(self):
        """
        FIXME, two different ways of retrieving pb's, both giving different results
        """
        branches = models.ProjectVersions()
        branches.project_branch = models.ProjectVersion.objects.select_related(depth=2).order_by(
            'project__project_id', 'branch_id')
        return branches


    @exposed
    def getProjectBranchStage(self, project_short_name, project_branch_label, stage_name):
        stage = models.Stage.objects.get(
            project__short_name=project_short_name,
            project_branch__label=project_branch_label,
            name=stage_name)
        return stage

    @exposed
    def getProjectAllBranchStages(self, project_short_name):
        stages = models.Stages()
        stages.project_branch_stage = models.Stage.objects.select_related(depth=2).filter(
                project__short_name=project_short_name).order_by(
                    'project__project_id', 'project_branch__branch_id', 'stage_id')
        stages._url_key = [ project_short_name ]
        return stages

    @exposed
    def getProjectBranchStages(self, project_short_name, project_branch_label):
        stages = models.Stages()
        stages.project_branch_stage = models.Stage.objects.select_related(depth=2).filter(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label).order_by(
                    'project__project_id', 'project_branch__branch_id', 'stage_id')
        stages._url_key = [ project_short_name, project_branch_label ]
        return stages

    # should not be used due to querysets
    @exposed
    def getAllProjectBranchStages(self):
        stages = models.Stages()
        stages.project_branch_stage = models.Stage.objects.select_related(depth=2).order_by(
            'project__project_id', 'project_branch__branch_id', 'stage_id')
        return stages

    @exposed
    def getProjectBranchStageImages(self, project_short_name, project_branch_label, stage_name):
        project = self.getProject(project_short_name)
        stage = self.getProjectBranchStage(project_short_name, project_branch_label, stage_name)
        my_images = imagemodels.Image.objects.filter(
            # stage_id is not set in the database even though it's on the model, awesome.
            # don't try to use the project_branch_stage relation
            project_branch__branch_id   = stage.project_branch_id,
            stage_name                  = stage.name
        ).distinct() | imagemodels.Image.objects.filter(
            project                     = project,
            stage_name                  = ''
        ).distinct() | imagemodels.Image.objects.filter(
            project                     = project,
            stage_name                  = None
        ).distinct()

        images = imagemodels.Images()
        images.image = my_images
        images.url_key = [ project_short_name, project_branch_label, stage_name ]
        images.view_name = 'ProjectBranchStageImages'

        images.latest_files = imagemodels.LatestFiles()
        images.latest_files.latest_file = latestFiles = []
        for img in stage.images.values('name').distinct('name').order_by('name'):
            lf = imagemodels.LatestFile()
            lf.image_name = img['name']
            lf.project_branch_stage = stage
            latestFiles.append(lf)
        return images
    
    @exposed
    def getProjectBranchStageLatestImageFile(self, project_short_name,
            project_branch_label, stage_name, image_name):
        stage = self.getProjectBranchStage(project_short_name, project_branch_label, stage_name)
        buildFiles = list(
                imagemodels.BuildFile.objects.filter(
                    image__name=image_name,
                    image__project_branch_stage=stage,
                    image__status=300).order_by(
                        '-image__image_id',
                        '-size',
                        'file_id')[:1])

        if not buildFiles:
            raise errors.ResourceNotFound()
        buildFile = buildFiles[0]
        location = buildFile.getDownloadUrl()
        raise errors.TemporaryRedirect(msg="Redirected to %(location)s",
                location=location,
                headers = dict(Location=models.modellib.AbsoluteHref(location)))

    @exposed
    def createProjectBranchStageImage(self, image):
        return self.mgr.imagesManager.createImageBuild(image)

    @exposed
    def getAllProjectBranchesForProject(self, project_short_name):
        branches = models.ProjectVersions()
        branches.project_branch = models.ProjectVersion.objects.filter(
            project__short_name=project_short_name)
        return branches

    @exposed
    def updateProjectBranchStage(self, project_short_name, project_branch_label, stage_name, stage):
        # if ever implemented be sure to update modified_by/modified_date
        raise exceptions.NotImplementedError()
