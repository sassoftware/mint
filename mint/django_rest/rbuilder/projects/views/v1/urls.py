#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.projects.views.v1 import views
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    URL(r'/?$',
        views.ProjectsService(),
        name='Projects',
        model='projects.Projects'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/?$',
        views.ProjectService(),
        name='Project',
        model='projects.Project'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/members/?$',
        views.ProjectMemberService(),
        name='ProjectMembers',
        model='projects.Members'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/?$',
        views.ProjectAllBranchesService(),
        name='ProjectVersions',
        model='projects.ProjectVersions'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/?$',
        views.ProjectBranchService(),
        name='ProjectVersion',
        model='projects.ProjectVersion'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/?$',
        views.ProjectBranchStagesService(),
        name='ProjectBranchStages',
        model='projects.Stages'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)$',
        views.ProjectBranchStageService(),
        name='ProjectBranchStage',
        model='projects.Stage'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)/images/?$',
        views.ProjectBranchStageImagesService(),
        name='ProjectBranchStageImages',
        model='images.Images'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)/images_by_name/(?P<image_name>(\w|\-)*)/latest_file/?$',
        views.ProjectBranchStageLatestImageFileService(),
        name='ProjectBranchStageLatestImageFile'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/project_branch_stages/?$',
        views.ProjectAllBranchStagesService(),
        name='ProjectBranchesAllStages',
        model='projects.Stages'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/images/?$',
        views.ProjectImagesService(),
        name='ProjectImages',
        model='images.Images'),
    URL(r'/(?P<project_short_name>(\w|\-)*)/images/(?P<image_id>\d+)/?$',
        views.ProjectImageService(),
        name='ProjectImage',
        model='images.Image'),

)
