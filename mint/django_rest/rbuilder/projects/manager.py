#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import os
import exceptions
import time

from conary.lib import util

from mint import helperfuncs
from mint import mint_error
from mint import userlevels
from mint import projects

from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.repos import models as repomodels
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.platforms import models as platform_models
from mint.django_rest.rbuilder.projects import models
from mint.django_rest.rbuilder.images import models as imagesmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder import modellib
from django.db import connection

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
    def addProject(self, project, for_user):
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
        self.mgr.retagQuerySetsByType('project_branch', for_user)
        self.mgr.retagQuerySetsByType('project_branch_stage', for_user)

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

    def saveProductVersionDefinition(self, productVersion, prodDef):
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
            dbStage = models.Stage(name=str(stage.name),
                 label=str(prodDef.getLabelForStage(stage.name)),
                 promotable=promotable)
            dbStage.project = productVersion.project
            dbStage.project_branch = productVersion
            dbStage.save()

    def setProductVersionDefinition(self, prodDef):
        cclient = self.mgr.getAdminClient(write=True)
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    @exposed
    def addProjectBranch(self, projectShortName, projectVersion):

        if not projectVersion.namespace:
            projectVersion.namespace = projectVersion.project.namespace

        # validate the label, which will be added later.  This is done
        # here so the project is not be created before this error occurs
        if projects.validLabel.match(projectVersion.label) == None:
            raise mint_error.InvalidLabel(projectVersion.label)

        project = projectVersion.project
        pd = helperfuncs.sanitizeProductDefinition(
                projectName=project.name,
                projectDescription=project.description or '',
                hostname=project.hostname,
                domainname=project.domain_name,
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
            pd.rebase(cclient, platform.label)
        self.saveProductVersionDefinition(projectVersion, pd)

        projectVersion.save()
        
        self.mgr.invalidateQuerySetByName('All Project Stages')
        return projectVersion

    @exposed
    def updateProjectBranch(self, projectVersion):
        projectVersion.save()
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
        project = projectVersion.project
        pd = proddef.ProductDefinition()
        pd.setBaseLabel(projectVersion.label)
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
        stage = models.Stage.objects.select_related(depth=2).get(pk=stageId)
        return stage

    @exposed
    def getStageByProjectBranchAndStageName(self, projectBranch, stageName):
        if hasattr(projectBranch, 'branch_id'):
            projectBranchId = projectBranch.branch_id
        else:
            projectBranchId = projectBranch
        stages = models.Stage.objects.filter(project_branch_id=projectBranchId,
            name=stageName)
        if stages:
            return stages[0]
        return None

    @exposed
    def getImage(self, image_id):
        return imagesmodels.Image.objects.select_related(depth=2).get(pk=image_id)

    @exposed
    def getImagesForProject(self, short_name):
        project = self.getProject(short_name)
        Images = imagesmodels.Images()
        Images.image = imagesmodels.Image.objects.select_related(depth=2).filter(
            project__project_id=project.project_id).order_by('image_id')
        Images.url_key = [ short_name ]
        Images.view_name = 'ProjectImages'
        return Images

    @exposed
    def updateImage(self, image):
        # For now only metadata can be updated, in the future it will be
        # necessary to figure out what changed before needlessly re-committing
        # the image trove.
        image.saveMetadata()
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
        return stages

    @exposed
    def getProjectBranchStages(self, project_short_name, project_branch_label):
        stages = models.Stages()
        stages.project_branch_stage = models.Stage.objects.select_related(depth=2).filter(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label).order_by(
                    'project__project_id', 'project_branch__branch_id', 'stage_id')
        return stages

    @exposed
    def getAllProjectBranchStages(self):
        stages = models.Stages()
        stages.project_branch_stage = models.Stage.objects.select_related(depth=2).order_by(
            'project__project_id', 'project_branch__branch_id', 'stage_id')
        return stages

    @exposed
    def getProjectBranchStageImages(self, project_short_name, project_branch_label, stage_name):
        stage = self.getProjectBranchStage(project_short_name, project_branch_label, stage_name)

        # FIXME -- this needs to be rewritten to run in a constant number of queries

        # First, find all images directly linked to this stage
        imagesMap = dict((x.image_id, x)
            for x in imagesmodels.Image.objects.select_related().filter(
                project_branch_stage__stage_id=stage.stage_id))
        # Then get the ones belonging to the same branch, that only have
        # a stage name
        imagesMap.update((x.image_id, x)
            for x in imagesmodels.Image.objects.filter(
                project_branch__branch_id=stage.project_branch.branch_id,
                stage_name=stage.name))

        # Sort images by image id
        images = imagesmodels.Images()
        images.image = [ x[1] for x in sorted(imagesMap.items()) ]
        images.url_key = [ project_short_name, project_branch_label, stage_name ]
        images.view_name = 'ProjectBranchStageImages'
        return images

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
        raise exceptions.NotImplementedError()

    @exposed
    def isReleasePublished(self, release_id):
        cu = connection.cursor()
        published = cu.execute('''SELECT timePublished FROM PublishedReleases 
                                   WHERE pubReleaseId=?''', str(release_id)).next()
        if len(published) == 1 and published[0] is None:
            return False
        return True

    @exposed
    def publishRelease(self, release, publishedBy):
        releaseId = release.release_id
        shouldMirror = release.should_mirror
        userId = publishedBy.user_id
            
        if not self._getBuildCount(releaseId):
            raise mint_error.PublishedReleaseEmpty
  
        if self.isReleasePublished(releaseId):
            raise mint_error.PublishedReleasePublished

        cu = connection.cursor()
        cu.execute('''UPDATE PublishedReleases 
                      SET timePublished=?, publishedBy=?, 
                      shouldMirror=? WHERE pubReleaseId=?''', 
                      [time.time(), userId, int(shouldMirror), releaseId])

    @exposed
    def unpublishRelease(self, release):
        releaseId = release.release_id
        if not self.isReleasePublished(releaseId):
            raise mint_error.PublishedReleaseNotPublished

        cu = connection.cursor()
        cu.execute('''UPDATE PublishedReleases 
                      SET timePublished=?, publishedBy=?, 
                      shouldMirror=? WHERE pubReleaseId=?''', 
                      [None, None, 0, releaseId])
        
    @exposed
    def createReleaseByProject(self, release, creatingUser, project=None):
        if not release.project:
            release.project = project
        release.created_by = creatingUser
        release.time_created = time.time()
        release.save()
        return release
        
    @exposed
    def updateRelease(self, release, updatedBy):
        if release.published is u'True':
            self.publishRelease(release, publishedBy=publishedBy)
        elif release.published is u'False':
            self.unpublishRelease(release.release_id)
        release.time_updated = time.time()
        release.updated_by = updatedBy
        release.save()
        return release
        
    @exposed
    def addImageToRelease(self, release_id, image):
        if image.release and release_id != image.release.release_id:
            raise mint_error.BuildPublished()
        release = projectsmodels.Release.objects.get(pk=release_id)
        image.release = release
        
        # FIXME: is this still needed?
        # if (image.image_type not in ('amiImage', 'imageless')
        #         and not image.files.files):
        #     raise mint_error.BuildEmpty()
        # cu = connection.cursor()
        # cu.execute('''UPDATE Builds SET pubReleaseId=?
        #               WHERE buildId=?''', [release_id, image_id])
        image.save()
        return image

    @exposed
    def createTopLevelRelease(self, release):
        release.save()
        return release

    @exposed
    def getTopLevelReleases(self):
        Releases = projectsmodels.Releases()
        Releases.release = projectsmodels.Release.objects.all()
        return Releases

    def _getBuildCount(self, releaseId):
        cu = connection.cursor()
        buildCount, = cu.execute(
                    'SELECT COUNT(*) from Builds WHERE pubReleaseId=?',
                    [releaseId]).next()
        return buildCount
