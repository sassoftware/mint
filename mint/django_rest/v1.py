#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns, include

# FIXME: these will be moved to sub url files until this list has zero size:
# FIXME: "products" used below really should be it's own seperate service?
from mint.django_rest.rbuilder.inventory.views.v1 import views as inventoryviews
from mint.django_rest.rbuilder.querysets.views.v1 import views as querysetviews
# from mint.django_rest.rbuilder.packages import views as packageviews
from mint.django_rest.rbuilder.packageindex import views as packageindexviews
from mint.django_rest.rbuilder.projects import views as projectviews
from mint.django_rest.rbuilder.users import views as usersviews
from mint.django_rest.rbuilder.notices import views as noticesviews
from mint.django_rest.rbuilder.platforms import views as platformsviews
from mint.django_rest.rbuilder.rbac import views as rbacviews
from mint.django_rest.rbuilder.jobs import views as jobviews
from mint.django_rest.rbuilder.modulehooks import views as modulehooksviews
from mint.django_rest.rbuilder.targets import views as targetsviews
from mint.django_rest.rbuilder.images import views as imagesviews
from mint.django_rest import urls

# TODO: move this? 
handler404 = 'mint.django_rest.handler.handler404'
handler500 = 'mint.django_rest.handler.handler500'

URL = urls.URLRegistry.URL

# FIXME: view names will need the version as a prefix or postfix so resolvers
# can support v2, can update URL function to know & append context

urlpatterns = patterns(

    (r'^/reports',    include('mint.django_rest.rbuilder.reporting.views.v1.urls')),
    (r'^/inventory',  include('mint.django_rest.rbuilder.inventory.views.v1.urls')),
    (r'^/query_sets', include('mint.django_rest.rbuilder.querysets.views.v1.urls')),

    # FIXME: this will require a seperate service
    URL(r'/products/(?P<short_name>(\w|\-)*)/versions/(?P<version>(\w|\.)*)/?$',
        inventoryviews.MajorVersionService(),
        name='MajorVersions'),
    # Products
    URL(r'/products/(\w|\-)*/?$',
        inventoryviews.ApplianceService(),
        name='Products'),

    # FIXME: this will require a seperate service
    URL(r'/favorites/query_sets/?$',
        querysetviews.FavoriteQuerySetService(),
        name='FavoriteQuerySets',
        model='querysets.QuerySets'),

    
    # project branches
    URL(r'/project_branches/?$',
        projectviews.AllProjectBranchesService(),
        name='AllProjectBranches',
        model='projects.ProjectVersions'),
    URL(r'/project_branch_stages/?$',
        projectviews.AllProjectBranchesStagesService(),
        name='AllProjectBranchStages',
        model='projects.Stages'),
    URL(r'/projects/?$',
        projectviews.ProjectsService(),
        name='Projects',
        model='projects.Projects'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/?$',
        projectviews.ProjectService(),
        name='Project',
        model='projects.Project'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/members/?$',
        projectviews.ProjectMemberService(),
        name='ProjectMembers',
        model='projects.Members'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/releases/?$',
        projectviews.ProjectReleasesService(),
        name='ProjectReleases',
        model='projects.Releases'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/?$',
        projectviews.ProjectReleaseService(),
        name='ProjectRelease',
        model='projects.Release'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/images/?$',
        projectviews.ProjectReleaseImagesService(),
        name='ProjectReleaseImages',
        model='images.Images'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/images/(?P<image_id>\d+)/?$',
        projectviews.ProjectReleaseImageService(),
        name='ProjectReleaseImage',
        model='images.Image'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branches/?$',
        projectviews.ProjectAllBranchesService(),  
        name='ProjectVersions',
        model='projects.ProjectVersions'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/?$',
        projectviews.ProjectBranchService(),
        name='ProjectVersion',
        model='projects.ProjectVersion'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/?$',
        projectviews.ProjectBranchStagesService(),
        name='ProjectBranchStages',
        model='projects.Stages'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)$',
        projectviews.ProjectBranchStageService(),
        name='ProjectBranchStage',
        model='projects.Stage'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)/images/?$',
        projectviews.ProjectBranchStageImagesService(),
        name='ProjectBranchStageImages',
        model='images.Images'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/project_branch_stages/?$',
        projectviews.ProjectAllBranchStagesService(),
        name='ProjectBranchesAllStages',
        model='projects.Stages'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/images/?$',
        projectviews.ProjectImagesService(),
        name='ProjectImages',
        model='images.Images'),
    URL(r'/projects/(?P<project_short_name>(\w|\-)*)/images/(?P<image_id>\d+)/?$',
        projectviews.ProjectImageService(),
        name='ProjectImage',
        model='images.Image'),

    # Packages
    # --incomplete -- 
    URL(r'/packages/?$',
        packageindexviews.PackagesService(),
        name='Packages'),
    URL(r'/packages/(?P<package_id>\d+)/?$',
        packageindexviews.PackageService(),
        name='Package'),

### Commented out future packages API
#     # Packages
#     URL(r'packages/?$',
#         packageviews.PackageService(),
#         name='Packages'),
#     URL(r'packages/(?P<package_id>\d+)/?$',
#         packageviews.PackageService(),
#         name='Package'),
#         
#     # Package Actions
#     URL(r'package_action_types/?$',
#         packageviews.PackageActionTypeService(),
#         name='PackageActionTypes'),
#     URL(r'package_action_types/(?P<package_action_type_id>\d+)/?$',
#         packageviews.PackageActionTypeService(),
#         name='PackageActionType'),
# 
#     # Package Versions
#     URL(r'packages/(?P<package_id>\d+)/package_versions/?$',
#         packageviews.PackagePackageVersionService(),
#         name='PackageVersions'),
# 
#      URL(r'package_versions/?$',
#         packageviews.PackageVersionService(),
#         name='AllPackageVersions'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/?$',
#         packageviews.PackageVersionService(),
#         name='PackageVersion'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/'
#          'package_actions/?$',
#         packageviews.PackageVersionActionService(),
#         name='PackageVersionActions'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/'
#          'package_actions/(?P<package_version_action_id>\d+)/?$',
#         packageviews.PackageVersionActionService(),
#         name='PackageVersionAction'),
# 
#     # Package Version Urls
#     URL(r'package_versions/(?P<package_version_id>\d+)/urls/?$',
#         packageviews.PackageVersionUrlService(),
#         name='PackageVersionUrls'),
# 
#      URL(r'package_versions/(?P<package_version_id>\d+)/urls/'
#           '(?P<package_version_url_id>\d+)/?$',
#         packageviews.PackageVersionUrlService(),
#         name='PackageVersionUrl'),
#     
#     # Package Version Jobs  
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_version_jobs/?$',
#         packageviews.PackageVersionJobService(),
#         name='PackageVersionJobs'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_version_jobs/'
#          '(?P<package_version_job_id>\d+)/?$',
#         packageviews.PackageVersionJobService(),
#         name='PackageVersionJob'),
# 
#     # Package Sources
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/?$',
#         packageviews.PackageSourceService(),
#         name='PackageSources'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/?$',
#         packageviews.PackageSourceService(),
#         name='PackageSource'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_source_jobs/?$',
#         packageviews.PackageSourceJobService(),
#         name='PackageSourceJobs'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_source_jobs/(?P<package_source_job_id>\d+)/?$',
#         packageviews.PackageSourceJobService(),
#         name='PackageSourceJob'),
# 
#     # Package Builds
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_builds/?$',
#         packageviews.PackageBuildService(),
#         name='PackageBuilds'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_builds/(?P<package_build_id>\d+)/?$',
#         packageviews.PackageBuildService(),
#         name='PackageBuild'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_builds/(?P<package_build_id>\d+)/'
#          'package_build_jobs/?$',
#         packageviews.PackageBuildJobService(),
#         name='PackageBuildJobs'),
# 
#     URL(r'package_versions/(?P<package_version_id>\d+)/package_sources/'
#          '(?P<package_source_id>\d+)/package_builds/(?P<package_build_id>\d+)/'
#           'package_build_jobs/(?P<package_build_job_id>\d+)/?$',
#         packageviews.PackageBuildJobService(),
#         name='PackageBuildJob'),
# 
    URL(r'/session/?$',
        usersviews.SessionService(),
        name='Session',
        model='users.Session'),
    # Users
    URL(r'/users/?$',
        usersviews.UsersService(),
        name='Users',
        model='users.Users'),
    
    URL(r'/users/(?P<user_id>\d+)/?$',
        usersviews.UserService(),
        name='User',
        model='users.User'),

    # UserNotices
    URL(r'/users/(?P<user_id>\d+)/notices/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices'),
    
    URL(r'/notices/users/(?P<user_id>\d+)/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices2'),

    # Begin all things platforms
    URL(r'/platforms/?$',
        platformsviews.PlatformsService(),
        name='Platforms',
        model='platforms.Platforms'),
    URL(r'/platforms/(?P<platform_id>\d+)/?$',
        platformsviews.PlatformService(),
        name='Platform',
        model='platforms.Platform'),
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_status/?$',
    #     platformsviews.PlatformStatusService(),
    #     name='PlatformStatus'),
    URL(r'/platforms/(?P<platform_id>\d+)/content_sources/?$',
        platformsviews.PlatformSourceService(),
        name='PlatformSource',
        model='platforms.ContentSources'),
    URL(r'/platforms/(?P<platform_id>\d+)/content_source_types/?$',
        platformsviews.PlatformSourceTypeService(),
        name='PlatformSourceType',
        model='platforms.ContentSourceTypes'),
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_image_type/?$',
    #     platformsviews.PlatformImageTypeService(),
    #     name='PlatformImageType'),
    #     
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_load/(?P<job_uuid>[-a-zA-X0-9+])/?$',
    #     platformsviews.PlatformLoadService(),
    #     name='PlatformLoad'),
    # 
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_load/(?P<job_uuid>[-a-zA-X0-9+])/status/?$',
    #     platformsviews.PlatformLoadStatusService(),
    #     name='PlatformLoad'),
    # 
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_versions/?$',
    #     platformsviews.PlatformVersionService(),
    #     name='PlatformVersions'),
    #     
    # URL(r'/platforms/(?P<platform_id>\d+)/platform_versions/(?P<platform_version_id>\d+)/?$',
    #     platformsviews.PlatformVersionService(),
    #     name='PlatformVersion'),
        
    # Do platforms/content_sources/...
    URL(r'/platforms/content_sources/?$',
        platformsviews.AllSourcesService(),
        name='ContentSources',
        model='platforms.ContentSources'),
    URL(r'/platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourcesService(),
        name='ContentSource',
        model='platforms.ContentSources'),
    URL(r'/platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/?$',
        platformsviews.SourceService(),
        name='ContentSourceShortName',
        model='platforms.ContentSource'),
    # URL(r'/platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_status/?$',
    #     platformsviews.SourceStatusService(),
    #     name='SourceStatus'),
    #     
    # URL(r'/platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_errors/?$',
    #     platformsviews.SourceErrorsService(),
    #     name='SourceErrors'),
    #     
    # URL(r'/platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_errors/(?P<error_id>\d+)/?$',
    #     platformsviews.SourceErrorsService(),
    #     name='SourceError'),
        
    # URL(r'/platforms/sources/(?P<source_type>[_a-zA-Z0-9]+)/source_type_descriptor/?$',
        # platformsviews.SourceTypeDescriptor(),
        # name='SourceTypeDescriptor'),
    URL(r'/platforms/content_source_types/?$',
        platformsviews.AllSourceTypesService(),
        name='ContentSourceTypes',
        model='platforms.ContentSourceTypes'),
    URL(r'/platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourceTypesService(),
        name='ContentSourceType',
        model='platforms.ContentSourceTypes'),
    URL(r'/platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/(?P<content_source_type_id>\d+)/?$',
        platformsviews.SourceTypeService(),
        name='ContentSourceTypeById',
        model='platforms.ContentSourceType'),
    URL(r'/platforms/image_type_definition_descriptors/(?P<name>\w+)/?$',
        platformsviews.ImageTypeDefinitionDescriptorService(),
        name='ImageTypeDefinitionDescriptor'),

 
    # ModuleHooks
    URL(r'/module_hooks/?$',
        modulehooksviews.ModuleHooksService(),
        name='ModuleHooks'),
 
    # Role Based Access Control
    URL(r'/rbac/?$',
        rbacviews.RbacService(),
        name='Rbac',
        model='rbac.Rbac'),
    URL(r'/rbac/grants/?$',
        rbacviews.RbacPermissionsService(),
        name='RbacPermissions',
        model='rbac.RbacPermissions'),
    URL(r'/rbac/grants/(?P<permission_id>\d+)?$',
        rbacviews.RbacPermissionService(),
        name='RbacPermission',
        model='rbac.RbacPermission'),
    URL(r'/rbac/roles/?$',
        rbacviews.RbacRolesService(),
        name='RbacRoles',
        model='rbac.RbacRoles'),
    URL(r'/rbac/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacRoleService(),
        name='RbacRole',
        model='rbac.RbacRole'),
    URL(r'/users/(?P<user_id>\d+)/roles/?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRoles',
        model='rbac.RbacUserRoles'),
    URL(r'/rbac/roles/(?P<role_id>\d+)/grants/?$',
        rbacviews.RbacRoleGrantsService(),
        name='RbacRoleGrants',
        model='rbac.RbacPermissions'),
    URL(r'/rbac/roles/(?P<role_id>\d+)/users/?$',
        rbacviews.RbacRoleUsersService(),
        name='RbacRoleUser',
        model='users.Users'),
    URL(r'/users/(?P<user_id>\d+)/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRole',
        model='rbac.RbacUserRole'),
    URL(r'/rbac/permissions/?$',
        rbacviews.RbacPermissionTypesService(),
        name='RbacPermissionTypes',
        model='rbac.RbacPermissionTypes'),
    URL(r'/rbac/permissions/(?P<permission_type_id>\d+)?$',
        rbacviews.RbacPermissionTypeService(),
        name='RbacPermissionType',
        model='rbac.RbacPermissionType'),

    # Generic descriptors for creating resources
    URL(r'/descriptors/targets/create/?$',
        targetsviews.DescriptorTargetsCreationService(),
        name='DescriptorsTargetsCreate'),

    # Begin Targets/TargetTypes
    URL(r'/targets/?$',
        targetsviews.TargetsService(),
        name='Targets',
        model='targets.Targets'),
    URL(r'/targets/(?P<target_id>\d+)/?$',
        targetsviews.TargetService(),
        name='Target',
        model='targets.Target'),
    URL(r'/targets/(?P<target_id>\d+)/target_configuration/?$',
        targetsviews.TargetConfigurationService(),
        name='TargetConfiguration',
        model='targets.TargetConfiguration'),
    URL(r'/targets/(?P<target_id>\d+)/target_types/?$',
        targetsviews.TargetTypeByTargetService(),
        name='TargetTypeByTarget',
        model='targets.TargetTypes'),
    URL(r'/targets/(?P<target_id>\d+)/target_credentials/(?P<target_credentials_id>\d+)/?$',
        targetsviews.TargetCredentialsService(),
        name='TargetCredentials',
        model='targets.TargetCredentials'),
    URL(r'/targets/(?P<target_id>\d+)/target_user_credentials/?$',
        targetsviews.TargetUserCredentialsService(),
        name='TargetUserCredentials',
        model='targets.TargetUserCredentials'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/configuration/?$',
        targetsviews.TargetConfigurationDescriptorService(),
        name='TargetConfigurationDescriptor'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/configure_credentials/?$',
        targetsviews.TargetConfigureCredentialsService(),
        name='TargetConfigureCredentials'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/refresh_images/?$',
        targetsviews.TargetRefreshImagesService(),
        name='TargetRefreshImages'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/refresh_systems/?$',
        targetsviews.TargetRefreshSystemsService(),
        name='TargetRefreshSystems'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/deploy/file/(?P<file_id>\d+)/?$',
        targetsviews.TargetImageDeploymentService(),
        name='TargetImageDeployment'),
    URL(r'/targets/(?P<target_id>\d+)/descriptors/launch/file/(?P<file_id>\d+)/?$',
        targetsviews.TargetSystemLaunchService(),
        name='TargetSystemLaunch'),
    URL(r'/target_types/?$',
        targetsviews.TargetTypesService(),
        name='TargetTypes',
        model='targets.TargetTypes'),
    URL(r'/target_types/(?P<target_type_id>\d+)/?$',
        targetsviews.TargetTypeService(),
        name='TargetType',
        model='targets.TargetType'),
    URL(r'/target_types/(?P<target_type_id>\d+)/targets/?$',
        targetsviews.TargetTypeTargetsService(),
        name='TargetTypeTargets',
        model='targets.Targets'),
    URL(r'/target_types/(?P<target_type_id>\d+)/descriptor_create_target/?$',
        targetsviews.TargetTypeCreateTargetService(),
        name='TargetTypeCreateTarget'),
    URL(r'/target_type_jobs/?$',
        targetsviews.TargetTypeAllJobsService(),
        name='TargetTypeAllJobs',
        model='jobs.Jobs'),
    URL(r'/target_types/(?P<target_type_id>\d+)/jobs/?$',
        targetsviews.TargetTypeJobsService(),
        name='TargetTypeJob',
        model='jobs.Jobs'),
        
    # begin target jobs
    URL(r'/targets/(?P<target_id>\d+)/jobs/?$',
        targetsviews.TargetJobsService(),
        name='TargetJobs',
        model='jobs.Jobs'),
    URL(r'/target_jobs/?$',
        targetsviews.AllTargetJobsService(),
        name='AllTargetJobs',
        model='jobs.Jobs'),
    
    # Begin all things Images service
    URL(r'/images/?$',
        imagesviews.ImagesService(),
        name='Images',
        model='images.Images'),
    URL(r'/images/(?P<image_id>\d+)/?$',
        imagesviews.ImageService(),
        name='Image',
        model='images.Image'),

    URL(r'/images/(?P<image_id>\d+)/jobs/?$',
        imagesviews.ImageJobsService(),
        name='ImageJobs',
        model='jobs.Jobs'),

    URL(r'/images/(?P<image_id>\d+)/systems/?$',
        imagesviews.ImageSystemsService(),
        name='ImageSystems',
        model='inventory.Systems'),

    # Digress for build_log
    URL(r'/images/(?P<image_id>\d+)/build_log/?$',
        imagesviews.BuildLogService(),
        name='images.BuildLog'),
    
    URL(r'/images/(?P<image_id>\d+)/build_files/?$',
        imagesviews.ImageBuildFilesService(),
        name='BuildFiles',
        model='images.BuildFiles'),
    URL(r'/images/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/?$',
        imagesviews.ImageBuildFileService(),
        name='BuildFile',
        model='images.BuildFile'),
    URL(r'/images/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/file_url/?$',
        imagesviews.ImageBuildFileUrlService(),
        name='FileUrl',
        model='images.FileUrl'),
        
    # Begin Releases service
    URL(r'/releases/?$',
        projectviews.TopLevelReleasesService(),
        name='Releases',
        model='projects.Releases'),
    URL(r'/releases/(?P<release_id>\d+)/?$',
        projectviews.TopLevelReleaseService(),
        name='TopLevelRelease',
        model='projects.Release'),
    
    # Begin image types
    URL(r'/image_types/?$',
        imagesviews.ImageTypesService(),
        name='ImageTypes',
        model='images.ImageTypes'),
    URL(r'/image_types/(?P<image_type_id>\d+)/?$',
        imagesviews.ImageTypeService(),
        name='ImageType',
        model='images.ImageType')
)
