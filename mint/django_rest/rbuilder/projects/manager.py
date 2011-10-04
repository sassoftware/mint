#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import os

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
# from mint.django_rest.rbuilder.jobs import models as jobsmodels

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
    def getProjects(self):
        # FIXME -- this needs to be rewritten to run in a constant number of queries
        allProjects = models.Projects()
        # We better return things in a stable order
        allProjects.project = sorted(
            (p for p in models.Project.objects.select_related().all() if self.checkProjectAccess(p)),
            key=lambda x: x.project_id)
        return allProjects

    @exposed
    def getProject(self, project_name):
        project = models.Project.objects.select_related().get(short_name=project_name)
        if self.checkProjectAccess(project):   
            return project
        raise errors.PermissionDenied() 

    def checkProjectAccess(self, project):
        # Admins can see all projects
        if auth.isAdmin(self.user):
            return True
        # Public projects are visible to all
        if not project.hidden:
            return True
        if self.user is None:
            return False
        # Is the current user a project member
        if [ x for x in project.members.filter(user_id=self.user.user_id) ]:
            return True
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

    @exposed
    def addProject(self, project):
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

        self.mgr.invalidateQuerySetByName('All Projects')
        self.mgr.invalidateQuerySetByName('All Project Stages')
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
        cclient = self.mgr.getUserClient()
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    @exposed
    def addProjectBranch(self, projectShortName, projectVersion):

        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()

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
        platformLabel = getattr(projectVersion.platform, 'label', None)
        if platformLabel:
            platform = platform_models.Platform.objects.select_related().get(label=str(platformLabel))
            cclient = self.mgr.getAdminClient(write=True)
            pd.rebase(cclient, platform.label)
        self.saveProductVersionDefinition(projectVersion, pd)

        projectVersion.save()
        
        self.mgr.invalidateQuerySetByName('All Project Stages')
        return projectVersion

    @exposed
    def updateProjectBranch(self, projectVersion):
        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()
        projectVersion.save()
        return projectVersion

    @exposed
    def deleteProjectBranch(self, projectVersion):
        if not self.isProjectOwner(projectVersion.project):
            raise errors.PermissionDenied()
        projectVersion.delete()

    @exposed
    def getProjectMembers(self, shortName):
        project = models.Project.objects.select_related().get(short_name=shortName)
        members = models.Members()
        # FIXME -- to avoid serialization overhead, should this be a paged
        # collection versus inline?
        members.member = [m for m in project.members.select_related().all()]
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
        stage = models.Stage.objects.select_related().get(pk=stageId)
        return stage

    @exposed
    def getStageOld(self, shortName, projectVersionId, stageName):
        projectVersion = models.ProjectVersion.objects.select_related().get(
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
    def getImage(self, image_id):
        return imagesmodels.Image.objects.select_related().get(pk=image_id)

    @exposed
    def getImagesForProject(self, short_name):
        project = self.getProject(short_name)
        Images = imagesmodels.Images()
        Images.image = imagesmodels.Image.objects.select_related().filter(
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
            branch = models.ProjectVersion.objects.select_related(depth=2).get(
                label=project_branch_label, project__short_name=project_name)
            return self._projectValidator(branch)

        ProjectVersions = models.ProjectVersions()
        iterator = models.ProjectVersion.objects.select_related(depth=2).filter(
            project__short_name=project_name).order_by('branch_id')
        return self._branchFilter(iterator)

    @exposed
    def getAllProjectBranches(self):
        # use select_related so we catch projects in the same query
        iterator = models.ProjectVersion.objects.select_related(depth=2).order_by(
            'project__project_id', 'branch_id')
        return self._branchFilter(iterator)

    def _branchFilter(self, iterator):
        return self._objectFilterOnProjects(iterator, models.ProjectVersions, 'project_branch')

    def _stageFilter(self, iterator):
        return self._objectFilterOnProjects(iterator, models.Stages, 'project_branch_stage')

    def _objectFilterOnProjects(self, iterator, modelClass, fieldName):
        # We need to check project permissions for all objects in the iterator
        model = modelClass()
        collector = []
        setattr(model, fieldName, collector)
        for obj in iterator:
            if self.checkProjectAccess(obj.project):
                collector.append(obj)
        return model

    def _projectValidator(self, obj):
        if self.checkProjectAccess(obj.project):
            return obj
        raise errors.NotFound()

    @exposed
    def getProjectBranchStage(self, project_short_name, project_branch_label, stage_name):
        # stage = models.Stage.objects.select_related(depth=2).get(
        #     project__short_name=project_short_name,
        #     project_branch__label=project_branch_label,
        #     name=stage_name)
        stages = models.Stage.objects.filter(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label,
                name=stage_name)
        # differentiate between the cases where we are asking for
        # a specific stage, or a filtered collection of stages
        if not stage_name:  # asking for collection
            Stages = models.Stages()
            Stages.project_branch_stage = []
            # check access for each individual stage in the
            # django query set
            for stage in stages:
                if self.checkProjectAccess(stage.project):
                    Stages.project_branch_stage.append(stage)
            return Stages
        else:              #  asking for specific stage
            if self.checkProjectAccess(stages[0].project):
                return stages[0]
            raise errors.NotFound()

    @exposed
    def getProjectAllBranchStages(self, project_short_name):
        iterator = models.Stage.objects.select_related().filter(
                project__short_name=project_short_name).order_by(
                    'project__project_id', 'project_branch__branch_id', 'stage_id')
        return self._stageFilter(iterator)


    @exposed
    def getProjectBranchStages(self, project_short_name, project_branch_label):
        iterator = models.Stage.objects.select_related().filter(
                project__short_name=project_short_name,
                project_branch__label=project_branch_label).order_by(
                    'project__project_id', 'project_branch__branch_id', 'stage_id')
        return self._stageFilter(iterator)

    @exposed
    def getAllProjectBranchStages(self):
        iterator = models.Stage.objects.select_related(depth=2).order_by(
            'project__project_id', 'project_branch__branch_id', 'stage_id')
        return self._stageFilter(iterator)

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
        image.save()
        return image

    # FINISH: commented out until there are tests for this
    @exposed
    def updateProjectBranchStage(self, project_short_name, project_branch_label, stage_name, stage):
        stage.save()
        # project = stage.project
        fqdn = stage.project.repository_hostname
        version = stage.project_branch
        client = self.restDb.productMgr.reposMgr.getConaryClient()
        # this way doesn't seem to work inside the test suite -- prolly
        # failure to correctly mock the prodDef.
        pd = self.getProductVersionDefinitionByProjectVersion(version)
        
        # er is version or version.name supposed to be passed in...
        # works either way
        rpath_job.BackgroundRunner(self.restDb.productMgr._promoteGroup)(
                client, pd, job, fqdn, version, stage_name, stage)
        return stage

"""    
    @exposed
    def getDescriptorForImageBuildAction(self, , job_type, query_dict):
        '''To submit a job to the system, what smartform data do I need?'''
        #system     = models.System.objects.get(pk=system_id)
        event_type = jobmodels.EventType.objects.get(pk=job_type).name
        descriptor = jobmodels.EventType.DESCRIPTOR_MAP.get(event_type, None)
        if descriptor is None:
            raise Exception("no descriptor for job type %s" % event_type)
        # NOTE: it may be that depending on system context and event type
        # we may need to dynamically create parameters.  For instance,
        # if foo=3 on VMware.  When that happens, add some conditionals
        # here based on system state.
        query_dict = query_dict.copy()
        query_dict['system_id'] = system_id
        result = descriptor % query_dict
        return result
    
    
    @exposed
    def scheduleJobAction(self, system, job):  #change inputs
        '''
        An action is a bare job submission that is a request to start
        a real job.

        Job coming in will be xobj only,
        containing job_type, descriptor, and descriptor_data.  We'll use
        that data to schedule a completely different job, which will
        be more complete.
        '''
        # get integer job type even if not a django model
        jt = job.job_type.id
        if str(jt).find("/") != -1:
            jt = int(jt.split("/")[-1])
        event_type = jobmodels.EventType.objects.get(job_type_id=jt)
        job_name   = event_type.name

        event = None
        if job_name == jobmodels.EventType.IMAGE_BUILDS:
            #creds = self.getSystemCredentials(system)
            #auth = [dict(
               # sshUser     = 'root',
                #sshPassword = creds.password,
                #sshKey      = creds.key,
           # )]
           # event = self._scheduleEvent(system, job_name, eventData=auth)
            # we can completely ignore descriptor and descriptor_data
            # for this job, because we have that data stored in credentials
            # but other actions will have work to do with them in this
            # function.
        else:
            raise Exception("action dispatch not yet supported on job type: %s" % jt)
        
        if event is None:
            # this can happen if the event preconditions are not met and the exception
            # gets caught somewhere up the chain (which we should fix)
            raise Exception("failed to schedule event")
        return event
 """       
