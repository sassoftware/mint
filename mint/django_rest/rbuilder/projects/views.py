#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse, HttpResponseRedirect

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.rbac.rbacauth import rbac, manual_rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.projects import models as projectmodels
from mint.django_rest.rbuilder.images import models as imagemodels
from mint import userlevels
from mint.django_rest.rbuilder.modellib import Flags
import time

class ProjectCallbacks(object):
    """
    RBAC callbacks for Project(s)
    """
    @staticmethod
    def _checkPermissions(view, request, project_short_name, action, transitive=True):
        if request._is_admin:
            return True

        if not project_short_name:
            raise Exception("internal error: invalid permission check usage")

        obj = view.mgr.getProject(project_short_name)
        user = request._authUser
        if request.method == 'PUT' and \
            obj.short_name != project_short_name:
            return False
        if view.mgr.userHasRbacPermission(user, obj, action):
           return True

        # if no explicit Project permission, check all PBSes
        # that have this project, ability to access any implies 
        # access on the project, this will be a bit sluggish
        # but prevents confusion in setting up an extra set of QS
        # permissions.  Unsafe for anything but reads
        if transitive and action in [ READMEMBERS ] :
            stages_for_project = projectmodels.Stage.objects.filter(
                project = obj
            )
            for stage in stages_for_project:
                if view.mgr.userHasRbacPermission(user, stage, action):
                    return True
        return False

    @staticmethod
    def can_read_project(view, request, project_short_name=None, *args, **kwargs):
        """
        project_short_name needs to be a kwarg until the views are more granularly refactored.
        """
        return ProjectCallbacks._checkPermissions(view, request, project_short_name, READMEMBERS)
    
    @staticmethod
    def can_read_project_not_transitive(view, request, project_short_name=None, *args, **kwargs):
        return ProjectCallbacks._checkPermissions(view, request, project_short_name, READMEMBERS, transitive=False)

    @staticmethod
    def can_write_project(view, request, project_short_name, *args, **kwargs):
        """
        project_short_name always required for write to succeed, so don't make it kwarg
        """
        return ProjectCallbacks._checkPermissions(view, request, project_short_name, MODMEMBERS)

    @staticmethod
    def can_create_project(view, request, *args, **kwargs):
        return view.mgr.userHasRbacCreatePermission(request._authUser, 'project')

class BranchCallbacks(object):
    """
    RBAC callbacks for Project Branches
    """
    @staticmethod
    def _checkPermissions(view, request, branch_or_label, action):
  
        # this is very special cased because:
        #    (A) legacy access control exists in the repo
        #    (B) there are attemps to make P and PBS do the right thing without
        #        having to set up very explicit perms
        #    (C) branches aren't queryseted, and RBAC wants querysets
        # do _NOT_ use this as a model on how to rbac other resources -- MPD       
 
        if request._is_admin:
            return True

        branch = branch_or_label
        if isinstance(branch_or_label, basestring):
            branch = projectmodels.ProjectVersion.objects.get(label=branch_or_label)

        # permissions are additive, if I can write the project via the old
        # system, (or read as specified) I can assume true and skip the explicit
        # granting...  this solves some catch-22s where I need to create a PB
        # and need to know if I can write it to create it, but might not have
        # the project in the queryset yet because the UI has yet to add it
        # and plans to in the immediate next REST call

        project = branch.project
        membership = None
        if action in [ MODMEMBERS ] :
            # write access
            membership = projectmodels.Member.objects.filter(
                user      = request._authUser,
                level__in = [ userlevels.ADMIN, userlevels.OWNER ] ,
                project   = project
            )
        else:
            # read access
            membership = projectmodels.Member.objects.filter(
                user       = request._authUser,
                level__gte = 0,
                project    = project
            )
        if len(membership) > 0:
            return True
       
        # if no old-school membership, we can read the branch if we can
        # read any of the stages (which might not exist yet) 
        if action == READMEMBERS:
            stages_for_project = projectmodels.Stage.objects.filter(
                project_branch = branch
            )
            for stage in stages_for_project:
                if view.mgr.userHasRbacPermission(request._authUser, stage, action):
                    return True

        # we can X on the stage if we can X on the project
        if view.mgr.userHasRbacPermission(request._authUser, branch.project, action):
            return True

        return False
        
    @staticmethod
    def can_read_branch(view, request, *args, **kwargs):
        branch_or_label = kwargs.get('project_branch_label', kwargs.get('project_branch',None))
        rc = BranchCallbacks._checkPermissions(view, request, branch_or_label, READMEMBERS)
        return rc
    
    @staticmethod
    def can_write_branch(view, request, *args, **kwargs):
        # must use project_branch_label first or security is wrong on PUTs
        branch_or_label = kwargs.get('project_branch_label', kwargs.get('project_branch', None))
        rc = BranchCallbacks._checkPermissions(view, request, branch_or_label, MODMEMBERS)
        return rc

    @staticmethod
    def can_write_branch_by_project(view, request, project_short_name, *args, **kwargs):
        retval = ProjectCallbacks._checkPermissions(view, request, project_short_name, MODMEMBERS)
        return retval

class StageCallbacks(object):
    
    @staticmethod
    def can_read_stage(view, request, project_short_name, project_branch_label, 
            stage_name=None, *args, **kwargs):
        user = request._authUser
        if stage_name:
            obj = view.mgr.getProjectBranchStage(project_short_name, project_branch_label, stage_name)
            if not stage_name and request._is_admin:
                return True
            elif stage_name:
                if view.mgr.userHasRbacPermission(user, obj, READMEMBERS):
                    return True
            return False
        else:
            # if user has permissions on any stage then allow to read all stages
            obj = view.mgr.getProjectBranchStages(project_short_name, project_branch_label)
            for stage in obj.project_branch_stage:
                if view.mgr.userHasRbacPermission(user, stage, READMEMBERS):
                    return True
            return False

    @staticmethod
    def can_write_stage(view, request, project_short_name, project_branch_label, 
            stage_name, *args, **kwargs):
        obj = view.mgr.getProjectBranchStage(project_short_name, project_branch_label, stage_name)
        user = request._authUser
        if not stage_name and request._is_admin:
            return True
        elif stage_name:
            if view.mgr.userHasRbacPermission(user, obj, READMEMBERS):
                return True
        return False

    @staticmethod
    def can_read_all_for_project(view, request, project_short_name):
        user = request._authUser
        # BOOKMARK 
        collection = projectmodels.Stage.objects.filter(project__short_name=project_short_name)
        tv = all(view.mgr.userHasRbacPermission(user, obj, READMEMBERS) for obj in collection)
        if tv:
            return True
        return False

class AllProjectBranchesStagesService(service.BaseService):
    """
    get all pbs's
    """

    # redirect, no rbac needed
    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        qs = querymodels.QuerySet.objects.get(name='All Project Stages')
        url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
        return HttpResponseRedirect(url)


class AllProjectBranchesService(service.BaseService):

    # UI is not allowed to request All Project Branches
    # and should be fetching all PBS and all P, and then getting
    # the PB for any PBS acquired.

    # UI does not call this, correct?
    @access.admin
    @return_xml
    def rest_GET(self, request):
        retval = self.mgr.getAllProjectBranches()
        return retval

    @rbac(BranchCallbacks.can_write_branch)
    @requires('project_branch')
    @return_xml
    def rest_POST(self, request, project_branch):
        # FIXME: should call into manager
        # FIXME: no validation that we are not overwriting an existing PB
        project_branch.save()
        return project_branch


class ProjectAllBranchStagesService(service.BaseService):
    """
    returns all pbs associated with a given project. manual rbac
    """

    # branches are secured through project if you want to get
    @rbac(ProjectCallbacks.can_read_project_not_transitive)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.mgr.getProjectAllBranchStages(project_short_name)

class ProjectAllBranchesService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)
        
    def get(self, project_short_name):
        return self.mgr.getAllProjectBranchesForProject(project_short_name)

    @rbac(ProjectCallbacks.can_write_project)
    @requires('project_branch')
    @return_xml
    def rest_POST(self, request, project_short_name, project_branch):
        return self.mgr.addProjectBranch(project_short_name, project_branch)
        

class ProjectBranchService(service.BaseService):

    @rbac(BranchCallbacks.can_read_branch)
    @return_xml
    def rest_GET(self, request, project_short_name=None, project_branch_label=None):
        return self.get(project_short_name, project_branch_label)
        
    def get(self, project_short_name, project_branch_label):
        return self.mgr.getProjectBranch(project_short_name, project_branch_label)

    @rbac(ProjectCallbacks.can_write_project)
    @requires("project_branch")
    @return_xml
    def rest_POST(self, request, project_short_name=None, project_branch=None):
        return self.mgr.addProjectBranch(project_short_name, project_branch)

    @rbac(BranchCallbacks.can_write_branch)
    @requires("project_branch")
    @return_xml
    def rest_PUT(self, request, project_short_name=None, project_branch_label=None, project_branch=None):
        return self.mgr.updateProjectBranch(project_branch)

    @rbac(BranchCallbacks.can_write_branch)
    def rest_DELETE(self, request, project_short_name=None, project_branch_label=None):
        projectBranch = self.get(project_short_name, project_branch_label)
        self.mgr.deleteProjectBranch(projectBranch)
        response = HttpResponse(status=204)
        return response


class ProjectsService(service.BaseService):

    # manual RBAC, see get function
    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request):
        # all security here done by the queryset
        qs = querymodels.QuerySet.objects.get(name='All Projects')
        url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
        return HttpResponseRedirect(url)

    def get(self):
        pass

    @rbac(ProjectCallbacks.can_create_project)
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        return self.mgr.addProject(project, for_user=request._authUser)

class ProjectService(service.BaseService):

    # manual RBAC, see get function
    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request, project_short_name):
        if ProjectCallbacks.can_read_project(self, request, project_short_name):
            return self.get(project_short_name)
        raise PermissionDenied(msg='Missing read permissions on project')

    def get(self, project_short_name):
        model = self.mgr.getProject(project_short_name)
        return model

    @rbac(ProjectCallbacks.can_write_project)
    @requires('project')
    @return_xml
    def rest_PUT(self, request, project_short_name, project):
        return self.mgr.updateProject(project, for_user=request._authUser)

    @rbac(ProjectCallbacks.can_write_project)
    def rest_DELETE(self, request, project_short_name):
        project = self.get(project_short_name)
        self.mgr.deleteProject(project)
        response = HttpResponse(status=204)
        return response

class ProjectBranchStagesService(service.BaseService):

    @rbac(StageCallbacks.can_read_stage)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label):
        return self.get(project_short_name, project_branch_label)

    def get(self, project_short_name, project_branch_label):
        return self.mgr.getProjectBranchStages(project_short_name,
            project_branch_label)

class ProjectBranchStageService(service.BaseService):

    @rbac(StageCallbacks.can_read_stage)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label, stage_name):
        return self.get(project_short_name, project_branch_label, stage_name)

    def get(self, project_short_name, project_branch_label, stage_name):
        return self.mgr.getProjectBranchStage(project_short_name,
            project_branch_label, stage_name)


class ProjectImagesService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(request, project_short_name)

    def get(self, request, project_short_name):
        return self.mgr.getImagesForProject(project_short_name)


class ProjectImageService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name, image_id):
        return self.get(request, project_short_name, image_id)

    def get(self, request, project_short_name, image_id):
        model = self.mgr.getImage(image_id)
        return model

    @rbac(ProjectCallbacks.can_write_project)
    @requires("image")
    @return_xml
    def rest_PUT(self, request, project_short_name, image_id, image):
        image.image_id = image_id
        return self.mgr.updateImage(image)

class ProjectBranchStageImagesService(service.BaseService):
    
    def get(self, request, project_short_name, project_branch_label, stage_name):
        return self.mgr.getProjectBranchStageImages(project_short_name,
            project_branch_label, stage_name)
    
    @rbac(StageCallbacks.can_read_stage)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label, stage_name):
        return self.get(request, project_short_name, project_branch_label, stage_name)
     
    @rbac(StageCallbacks.can_write_stage)
    @requires("image")
    @return_xml
    def rest_POST(self, request, project_short_name, project_branch_label, stage_name, image):
        return self.mgr.createProjectBranchStageImage(image)

class ProjectMemberService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)

    def get(self, project_short_name):
        return self.mgr.getProjectMembers(project_short_name)


class ProjectReleasesService(service.BaseService):
 
    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)

    def get(self, project_short_name):
        Releases = projectmodels.Releases()
        Releases.release = projectmodels.Release.objects.filter(
                project__short_name=project_short_name)
        return Releases

    @rbac(ProjectCallbacks.can_write_project)
    @requires('release', flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, project_short_name, release):
        project = projectmodels.Project.objects.get(short_name=project_short_name)
        user = request._authUser
        return self.mgr.createRelease(release, user, project=project)
        
class ProjectReleaseService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name, release_id):
        return self.get(project_short_name, release_id)

    def get(self, project_short_name, release_id):
        return projectmodels.Release.objects.get(release_id=release_id)
        
    @return_xml
    @requires('release')
    def rest_PUT(self, request, project_short_name, release_id, release):
        user = request._authUser
        if release.published == u'True':
            self.mgr.publishRelease(release, user)
            release.published_by = user
            release.time_published = time.time()
        elif release.published == u'False':
            self.mgr.unpublishRelease(release)
            release.published_by = None
            release.time_published = None
            
        if release.should_mirror != 0:
            release.time_mirrored = time.time()
        elif release.should_mirror == 0:
            release.time_mirrored = None 
        
        release.updated_by = user
        release.time_updated = time.time()
        release.save()
        
        return release
        
class ProjectReleaseImagesService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name, release_id):
        return self.get(project_short_name, release_id)
        
    def get(self, project_short_name, release_id):
        Images = imagemodels.Images()
        Images.image = imagemodels.Image.objects.filter(release__release_id=release_id)
        return Images
    
    @rbac(ProjectCallbacks.can_write_project)
    @requires('image')
    @return_xml
    def rest_POST(self, request, project_short_name, release_id, image):
        return self.mgr.addImageToRelease(release_id, image)
        
class ProjectReleaseImageService(service.BaseService):
    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name, release_id, image_id):
        return self.get(project_short_name, release_id, image_id)
        
    def get(self, project_short_name, release_id, image_id):
        return self.mgr.getImageBuild(image_id)

    @rbac(ProjectCallbacks.can_write_project)
    def rest_DELETE(self, request, project_short_name, release_id, image_id):
        imagemodels.Image.objects.get(pk=image_id).delete()
        return HttpResponse(status=204)

class TopLevelReleasesService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getReleases()

    @access.admin
    @requires('release')
    @return_xml
    def rest_POST(self, request, release):
        createdBy = request._authUser
        return self.mgr.createRelease(release, createdBy)

class TopLevelReleaseService(service.BaseService):
    @access.admin
    @return_xml
    def rest_GET(self, request, release_id):
        return self.get(release_id)

    def get(self, release_id):
        return self.mgr.getReleaseById(release_id)

    @access.admin
    @requires('release')
    @return_xml
    def rest_PUT(self, request, release_id, release):
        updatingUser = request._authUser
        return self.mgr.updateRelease(release, updatingUser)

    @access.admin
    def rest_DELETE(self, request, release_id):
        release = projectsmodels.Release.objects.get(pk=release_id)
        release.delete()
        return HttpResponse(status=204)
