#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.http import HttpResponse, HttpResponseRedirect

from mint.django_rest.deco import access, return_xml, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.inventory.views import StageProxyService
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.projects import models as projectmodels
from mint.django_rest.rbuilder.images import models as imagemodels

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

class BranchCallbacks(object):
    """
    RBAC callbacks for Project Branches
    """
    @staticmethod
    def _checkPermissions(view, request, branch_or_label, action):
        if request._is_admin:
            return True

        branch = branch_or_label
        if isinstance(branch_or_label, basestring):
            branch = projectmodels.ProjectVersion.objects.get(label=branch_or_label)

        
        # if no explicit Project permission, check all PBSes
        # that have this project, ability to access any implies 
        # access on the project, this will be a bit sluggish
        # but prevents confusion in setting up an extra set of QS
        # permissions.  Unsafe for anything but reads
        stages_for_project = projectmodels.Stage.objects.filter(
            project_branch = branch
        )
        project = branch.project
        for stage in stages_for_project:
            if view.mgr.userHasRbacPermission(request._authUser, stage, action):
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

    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        # BIG FIXME: querysets should filter out what items you can't see
        # in them
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
        # ProjectBranches = projectmodels.ProjectVersions()
        # ProjectBranches.project_branch = projectmodels.ProjectVersion.objects.all()
        # return ProjectBranches
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


class ProjectService(service.BaseService):
    # manual RBAC, see get function
    @access.authenticated
    @return_xml
    def rest_GET(self, request, project_short_name=None):
        if project_short_name:
            if ProjectCallbacks.can_read_project(self, request, project_short_name):
                return self.get(project_short_name)
            raise PermissionDenied()
        else:
            # all security here done by the queryset
            qs = querymodels.QuerySet.objects.get(name='All Projects')
            url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
            return HttpResponseRedirect(url)

    def get(self, project_short_name):
        assert project_short_name is not None
        model = self.mgr.getProject(project_short_name)
        return model
    
    # anybody can create a new project for now
    @access.authenticated
    @requires('project')
    @return_xml
    def rest_POST(self, request, project):
        return self.mgr.addProject(project)

    @rbac(ProjectCallbacks.can_write_project)
    @requires('project')
    @return_xml
    def rest_PUT(self, request, project_short_name, project):
        return self.mgr.updateProject(project)

    @rbac(ProjectCallbacks.can_write_project)
    def rest_DELETE(self, request, project_short_name):
        project = self.get(project_short_name)
        self.mgr.deleteProject(project)
        response = HttpResponse(status=204)
        return response

class ProjectStageService(service.BaseService):
    
    # FIXME: HACKED FOR DEMO PURPOSES ONLY, must rbac for release
    @access.authenticated # was admin
    @return_xml
    def rest_GET(self, request, stage_id=None):
        return self.get(request, stage_id)
    
    def get(self, request, stage_id=None):
        if stage_id:
            return StageProxyService.getStageAndSetGroup(request, stage_id)
        else:
            return StageProxyService.getStagesAndSetGroup(request)


class ProjectBranchStageService(service.BaseService):
    @rbac(StageCallbacks.can_read_stage)
    @return_xml
    def rest_GET(self, request, project_short_name, project_branch_label, stage_name=None):
        return self.get(project_short_name, project_branch_label, stage_name)

    def get(self, project_short_name, project_branch_label, stage_name):
        if stage_name:
            return self.mgr.getProjectBranchStage(project_short_name,
                project_branch_label, stage_name)
        return self.mgr.getProjectBranchStages(project_short_name,
            project_branch_label)

    @rbac(StageCallbacks.can_write_stage)
    @requires('stage')
    @return_xml
    def rest_PUT(self, request, project_short_name, project_branch_label, stage_name, stage):
        return self.mgr.updateProjectBranchStage(
            project_short_name, project_branch_label, stage_name, stage)


class ProjectImageService(service.BaseService):

    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name, image_id=None):
        return self.get(request, project_short_name, image_id)

    def get(self, request, project_short_name, image_id):
        if image_id:
            model = self.mgr.getImage(image_id)
        else:
            model = self.mgr.getImagesForProject(project_short_name)
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

# FIXME -- not sure why this is commented out?
"""        
class ProjectJobDescriptorServiceservice.BaseService):

    @access.anonymous
    # smartform object already is XML, no need
    @return_xml
    def rest_GET(self, request, , job_type):
        '''
        Get a smartform descriptor for starting a action on
        InventorySystemJobsService.  An action is not *quite* a job.
        It's a request to start a job.
        '''
        content = self.get(, job_type, request.GET.copy())
        response = HttpResponse(status=200, content=content)
        response['Content-Type'] = 'text/xml'
        return response

    def get(self, , job_type, parameters):
        return self.mgr.getDescriptorForImageBuildAction(
            , job_type, parameters
        ) 
               
        
class ProjectImageBuildsJobService(service.BaseService):   
   
    @access.admin
    @xObjRequires('job')
    @return_xml
    def rest_POST(self, request, job):
        '''request starting build image'''
        image = self.mgr.getImage(image_id)
        return self.mgr.scheduleJobAction(
            system, job
        )        
"""


class ProjectMemberService(service.BaseService):
    @rbac(ProjectCallbacks.can_read_project)
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)

    def get(self, project_short_name):
        return self.mgr.getProjectMembers(project_short_name)


class ProjectReleaseService(service.BaseService):
    @return_xml
    def rest_GET(self, request, project_short_name):
        return self.get(project_short_name)

    def get(self, project_short_name):
        Releases = projectmodels.Releases()
        Releases.release = projectmodels.Release.objects.filter(
                project__short_name=project_short_name)
        return Releases

    @requires('release')
    @return_xml
    def rest_POST(self, request, project_short_name, release):
        release.save()
        return release
        
class ProjectReleaseImageService(service.BaseService):
    @return_xml
    def rest_GET(self, request, project_short_name, release_id, image_id=None):
        return self.get(project_short_name, release_id, image_id)
        
    def get(self, project_short_name, release_id, image_id):
        if image_id:
            return self.mgr.getImageBuild(image_id)
        else:
            Images = imagemodels.Images()
            Images.image = imagemodels.Image.objects.filter(release__release_id=release_id)
            return Images
    
    @requires('image')
    @return_xml
    def rest_POST(self, request, project_short_name, release_id, image):
        return self.mgr.createImageBuild(image)
        

