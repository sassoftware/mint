#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns, include

# FIXME: to be removed as things move into new url files:
from mint.django_rest.rbuilder.projects.views.v1 import views as projectviews
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

urlpatterns = patterns('', 

    # FIXME: something wrong with these URLs if enabled
    #(r'^/reports',          
    # include('mint.django_rest.rbuilder.reporting.views.v1.urls')),

    (r'^/inventory',        
     include('mint.django_rest.rbuilder.inventory.views.v1.urls')),

    (r'^/query_sets',       
     include('mint.django_rest.rbuilder.querysets.views.v1.urls')),

    (r'^/products',         
     include('mint.django_rest.rbuilder.products.views.v1.urls')),

    (r'^/favorites',        
     include('mint.django_rest.rbuilder.favorites.views.v1.urls')),

    (r'^/project_branches', 
     include('mint.django_rest.rbuilder.projects.views.v1.urls_pb')),

    (r'^/project_branch_stages', 
     include('mint.django_rest.rbuilder.projects.views.v1.urls_pbs')),
  
    (r'^/projects',         
     include('mint.django_rest.rbuilder.projects.views.v1.urls')),

    (r'^/packages',
     include('mint.django_rest.rbuilder.packages.views.v1.urls')),
    
    (r'^/session',
     include('mint.django_rest.rbuilder.session.views.v1.urls')),
    
    (r'^/users',
     include('mint.django_rest.rbuilder.users.views.v1.urls')),
    
    (r'^/notices',
     include('mint.django_rest.rbuilder.notices.views.v1.urls')),
    
    (r'^/platforms',
     include('mint.django_rest.rbuilder.platforms.views.v1.urls')),

    # Role Based Access Control
    # FIXME -- migrate to new structure
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
    # FIXME -- migrate to new structure
    URL(r'/descriptors/targets/create/?$',
        targetsviews.DescriptorTargetsCreationService(),
        name='DescriptorsTargetsCreate'),

    # Begin Targets/TargetTypes
    # FIXME -- migrate to new structure
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

    # Target types
    # FIXME -- migrate to new structure
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

    URL(r'/target_types/(?P<target_type_id>\d+)/jobs/?$',
        targetsviews.TargetTypeJobsService(),
        name='TargetTypeJob',
        model='jobs.Jobs'),
    # begin target jobs
    # FIXME -- migrate to new structure
    URL(r'/targets/(?P<target_id>\d+)/jobs/?$',
        targetsviews.TargetJobsService(),
        name='TargetJobs',
        model='jobs.Jobs'),
    # FIXME -- migrate to new structure
    URL(r'/target_jobs/?$',
        targetsviews.AllTargetJobsService(),
        name='AllTargetJobs',
        model='jobs.Jobs'),
    # FIXME -- migrate to new structure
    URL(r'/target_type_jobs/?$',
        targetsviews.TargetTypeAllJobsService(),
        name='TargetTypeAllJobs',
        model='jobs.Jobs'),
    
    # Begin all things Images service
    # FIXME -- migrate to new structure
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
    # FIXME -- migrate to new structure
    URL(r'/releases/?$',
        projectviews.TopLevelReleasesService(),
        name='Releases',
        model='projects.Releases'),
    URL(r'/releases/(?P<release_id>\d+)/?$',
        projectviews.TopLevelReleaseService(),
        name='TopLevelRelease',
        model='projects.Release'),
    
    # Begin image types
    # FIXME -- migrate to new structure
    URL(r'/image_types/?$',
        imagesviews.ImageTypesService(),
        name='ImageTypes',
        model='images.ImageTypes'),
    URL(r'/image_types/(?P<image_type_id>\d+)/?$',
        imagesviews.ImageTypeService(),
        name='ImageType',
        model='images.ImageType')
)
