#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import url, patterns

from mint.django_rest.rbuilder.reporting import reportdispatcher, \
                                                views

from mint.django_rest.rbuilder.discovery import views as discoveryviews
from mint.django_rest.rbuilder.inventory import views as inventoryviews
from mint.django_rest.rbuilder.querysets import views as querysetviews
# from mint.django_rest.rbuilder.packages import views as packageviews
from mint.django_rest.rbuilder.packageindex import views as packageindexviews
from mint.django_rest.rbuilder.changelog import views as changelogviews
from mint.django_rest.rbuilder.projects import views as projectviews
from mint.django_rest.rbuilder.users import views as usersviews
from mint.django_rest.rbuilder.notices import views as noticesviews
from mint.django_rest.rbuilder.platforms import views as platformsviews
from mint.django_rest.rbuilder.rbac import views as rbacviews
from mint.django_rest.rbuilder.jobs import views as jobviews
from mint.django_rest.rbuilder.modulehooks import views as modulehooksviews
from mint.django_rest.rbuilder.targets import views as targetsviews
from mint.django_rest.rbuilder.images import views as imagesviews

handler404 = 'mint.django_rest.handler.handler404'
handler500 = 'mint.django_rest.handler.handler500'

VERSION = '1'
def URL(regex, *args, **kwargs):
    if not regex.startswith('^'):
        regex = "^api/v%s/%s" % (VERSION, regex)
    return url(regex, *args, **kwargs)

urlpatterns = patterns('',
    # Versioning. Note that this URL does NOT get versioned
    URL(r'^api/?$',
        discoveryviews.VersionsService(),
        name='API'),
    URL(r'^api/v%s/?$' % VERSION,
        discoveryviews.ApiVersionService(),
        name='APIVersion'),
    # Reporting urls
    URL(r'reports/(.*?)/descriptor/?$',
        reportdispatcher.ReportDescriptor()),
    URL(r'reports/(.*?)/data/(.*?)/?$',
        reportdispatcher.ReportDispatcher()),
    URL(r'reports/(.*?)/?$', views.ReportView()),

    #
    # Inventory urls
    #
    URL(r'inventory/?$',
        inventoryviews.InventoryService(),
        name='Inventory'),

    # Log
    URL(r'inventory/log/?$',
        inventoryviews.InventoryLogService(),
        name='Log'),

    # System States
    URL(r'inventory/system_states/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemStates'),
    URL(r'inventory/system_states/(?P<system_state_id>\d+)/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemState'),

    # Zones
    URL(r'inventory/zones/?$',
        inventoryviews.InventoryZoneService(),
        name='Zones'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/?$',
        inventoryviews.InventoryZoneService(),
        name='Zone'),

    # Management Nodes
    URL(r'inventory/management_nodes/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNodes'),
    URL(r'inventory/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNode'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/management_nodes/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ManagementNodes'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ManagementNode'),
        
    # Management Interfaces
    URL(r'inventory/management_interfaces/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterfaces'),
    URL(r'inventory/management_interfaces/(?P<management_interface_id>\d+)/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterface'),
        
    # System types
    URL(r'inventory/system_types/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemTypes'),
    URL(r'inventory/system_types/(?P<system_type_id>\d+)/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemType'),
    URL(r'inventory/system_types/(?P<system_type_id>\d+)/systems/?$',
        inventoryviews.InventorySystemTypeSystemsService(),
        name='SystemTypeSystems'),
       
    # Networks
    URL(r'inventory/networks/?$',
        inventoryviews.InventoryNetworkService(),
        name='Networks'),
    URL(r'inventory/networks/(?P<network_id>\d+)/?$',
        inventoryviews.InventoryNetworkService(),
        name='Network'),

    # Systems
    URL(r'inventory/systems/?$',
        inventoryviews.InventorySystemsService(),
        name='Systems'),
    URL(r'inventory/inventory_systems/?$',
        inventoryviews.InventoryInventorySystemsService(),
        name='InventorySystems'),
    URL(r'inventory/infrastructure_systems/?$',
        inventoryviews.InventoryInfrastructureSystemsService(),
        name='ImageImportMetadataDescriptor'),
    URL(r'inventory/image_import_metadata_descriptor/?$',
        inventoryviews.ImageImportMetadataDescriptorService(),
        name='InfrastructureSystems'),
    URL(r'inventory/systems/(?P<system_id>\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_log/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLog'),
    URL(r'inventory/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs'),
    URL(r'inventory/systems/(?P<system_id>\d+)/descriptors/(?P<job_type>\d+)?$',
        inventoryviews.InventorySystemJobDescriptorService(),
        name='SystemJobDescriptors'),
    URL(r'inventory/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJob'),
    URL(r'inventory/systems/(?P<system_id>\d+)/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventorySystemJobStatesService(),
        name='SystemJobStateJobs'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_events/?$',
        inventoryviews.InventorySystemsSystemEventService(),
        name='SystemsSystemEvent'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_log/(?P<format>[a-zA-Z]+)/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat'),
    URL(r'inventory/systems/(?P<system_id>\d+)/installed_software/?$',
        inventoryviews.InventorySystemsInstalledSoftwareService(),
        name='InstalledSoftware'),
    URL(r'inventory/systems/(?P<system_id>\d+)/credentials/?$',
        inventoryviews.InventorySystemCredentialsServices(),
        name='SystemCredentials'),
    URL(r'inventory/systems/(?P<system_id>\d+)/configuration/?$',
        inventoryviews.InventorySystemConfigurationServices(),
        name='SystemConfiguration'),
    URL(r'inventory/systems/(?P<system_id>\d+)/configuration_descriptor/?$',
        inventoryviews.InventorySystemConfigurationDescriptorServices(),
        name='SystemConfigurationDescriptor'),

    # System Events
    URL(r'inventory/system_events/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvents'),
    URL(r'inventory/system_events/(?P<system_event_id>\d+)/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvent'),

    # System Tags
    URL(r'inventory/systems/(?P<system_id>\d+)/system_tags/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTags'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_tags/(?P<system_tag_id>\d+)/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTag'),

    # Event Types
    URL(r'inventory/event_types/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventTypes'),
    URL(r'inventory/event_types/(?P<event_type_id>\d+)/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventType'),

    # Jobs
    URL(r'jobs/?$',
        jobviews.JobsService(),
        name='Jobs'),
    URL(r'jobs/(?P<job_uuid>[-a-zA-Z0-9]+)/?$',
        jobviews.JobsService(),
        name='Job'),

    # Job States
    URL(r'job_states/?$',
        jobviews.JobStatesService(),
        name='JobStates'),
    URL(r'job_states/(?P<job_state_id>[a-zA-Z0-9]+)/?$',
        jobviews.JobStatesService(),
        name='JobState'),
    URL(r'job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        jobviews.JobStatesJobsService(),
        name='JobStateJobs'),

    # Major Versions
    URL(r'products/(?P<short_name>(\w|\-)*)/versions/(?P<version>(\w|\.)*)/?$',
        inventoryviews.MajorVersionService(),
        name='MajorVersions'),

    # Products
    URL(r'products/(\w|\-)*/?$',
        inventoryviews.ApplianceService(),
        name='Projects'),

    # URL(r'projects/(?P<short_name>(\w|\-)*)/project_branches/(?P<project_branch_name>(\w|\-|[0-9])*)/repos/?$',
    #        projectviews.ProjectBranchService(),
    #        name='ProjectVersion'),

    # Query Sets
    URL(r'query_sets/?$',
        querysetviews.QuerySetService(),
        name='QuerySets'),
    URL(r'query_sets/(?P<query_set_id>\d+)/?$',
        querysetviews.QuerySetService(),
        name='QuerySet'),
    URL(r'query_sets/(?P<query_set_id>\d+)/all/?$',
        querysetviews.QuerySetAllResultService(),
        name='QuerySetAllResult'),
    URL(r'query_sets/(?P<query_set_id>\d+)/chosen/?$',
        querysetviews.QuerySetChosenResultService(),
        name='QuerySetChosenResult'),
    URL(r'query_sets/(?P<query_set_id>\d+)/filtered/?$',
        querysetviews.QuerySetFilteredResultService(),
        name='QuerySetFilteredResult'),
    URL(r'query_sets/(?P<query_set_id>\d+)/child/?$',
        querysetviews.QuerySetChildResultService(),
        name='QuerySetChildResult'),
    URL(r'query_sets/(?P<query_set_id>\d+)/jobs/?$',
        querysetviews.QuerySetJobsService(),
        name='QuerySetJobs'),
    URL(r'query_sets/filter_descriptor/?$',
        querysetviews.QuerySetFilterDescriptorService(),
        name='QuerySetFilterDescriptor'),

    # Change Logs
    URL(r'changelogs/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLogs'),
    URL(r'changelogs/(?P<change_log_id>\d+)/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLog'),

    # These are aggregates
    # Aggregate all project branches
    URL(r'project_branches/?$',
        projectviews.AllProjectBranchesService(),
        name='AllProjectBranches'),

    # Aggregate all project branch stages
    URL(r'project_branch_stages/?$',
        projectviews.AllProjectBranchesStagesService(),
        name='AllProjectBranchStages'),

    # Proper hierarchy for projects
    URL(r'projects/?$',
        projectviews.ProjectService(),
        name='Projects'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/?$',
        projectviews.ProjectService(),
        name='Project'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/members/?$',
        projectviews.ProjectMemberService(),
        name='ProjectMembers'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/?$',
        projectviews.ProjectBranchService(),
        name='ProjectVersions'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/?$',
        projectviews.ProjectBranchService(),
        name='ProjectVersion'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/?$',
        projectviews.ProjectBranchStageService(),
        name='ProjectBranchStages'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)$',
        projectviews.ProjectBranchStageService(),
        name='ProjectBranchStage'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)/images/?$',
        projectviews.ProjectBranchStageImagesService(),
        name='ProjectBranchStageImages'),

    # Aggregate all stages for a project
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branch_stages/?$',
        projectviews.ProjectAllBranchStagesService(),
        name='ProjectBranchesAllStages'),

    URL(r'projects/(?P<project_short_name>(\w|\-)*)/images/?$',
        projectviews.ProjectImageService(),
        name='ProjectImages'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/images/(?P<image_id>\d+)/?$',
        projectviews.ProjectImageService(),
        name='ProjectImage'),

    # Packages
    URL(r'packages/?$',
        packageindexviews.PackageService(),
        name='Packages'),
    URL(r'packages/(?P<package_id>\d+)/?$',
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
    URL(r'session/?$',
        usersviews.SessionService(),
        name='Session'),
    # Users
    URL(r'users/?$',
        usersviews.UsersService(),
        name='Users'),
    
    URL(r'users/(?P<user_id>\d+)/?$',
        usersviews.UsersService(),
        name='User'),

    # UserNotices
    URL(r'users/(?P<user_id>\d+)/notices/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices'),
    
    URL(r'notices/users/(?P<user_id>\d+)/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices'),

    # Begin all things platforms
    URL(r'platforms/?$',
        platformsviews.PlatformService(),
        name='Platforms'),
    URL(r'platforms/(?P<platform_id>\d+)/?$',
        platformsviews.PlatformService(),
        name='Platform'),
    # URL(r'platforms/(?P<platform_id>\d+)/platform_status/?$',
    #     platformsviews.PlatformStatusService(),
    #     name='PlatformStatus'),
    URL(r'platforms/(?P<platform_id>\d+)/content_sources/?$',
        platformsviews.PlatformSourceService(),
        name='PlatformSource'),
    URL(r'platforms/(?P<platform_id>\d+)/content_source_types/?$',
        platformsviews.PlatformSourceTypeService(),
        name='PlatformSourceType'),
    # URL(r'platforms/(?P<platform_id>\d+)/platform_image_type/?$',
    #     platformsviews.PlatformImageTypeService(),
    #     name='PlatformImageType'),
    #     
    # URL(r'platforms/(?P<platform_id>\d+)/platform_load/(?P<job_uuid>[-a-zA-X0-9+])/?$',
    #     platformsviews.PlatformLoadService(),
    #     name='PlatformLoad'),
    # 
    # URL(r'platforms/(?P<platform_id>\d+)/platform_load/(?P<job_uuid>[-a-zA-X0-9+])/status/?$',
    #     platformsviews.PlatformLoadStatusService(),
    #     name='PlatformLoad'),
    # 
    # URL(r'platforms/(?P<platform_id>\d+)/platform_versions/?$',
    #     platformsviews.PlatformVersionService(),
    #     name='PlatformVersions'),
    #     
    # URL(r'platforms/(?P<platform_id>\d+)/platform_versions/(?P<platform_version_id>\d+)/?$',
    #     platformsviews.PlatformVersionService(),
    #     name='PlatformVersion'),
        
    # Do platforms/content_sources/...
    URL(r'platforms/content_sources/?$',
        platformsviews.SourceService(),
        name='ContentSources'),
    URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourceService(),
        name='ContentSources'),
    URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/?$',
        platformsviews.SourceService(),
        name='ContentSource'),
    # URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_status/?$',
    #     platformsviews.SourceStatusService(),
    #     name='SourceStatus'),
    #     
    # URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_errors/?$',
    #     platformsviews.SourceErrorsService(),
    #     name='SourceErrors'),
    #     
    # URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/source_errors/(?P<error_id>\d+)/?$',
    #     platformsviews.SourceErrorsService(),
    #     name='SourceError'),
        
    # URL(r'platforms/sources/(?P<source_type>[_a-zA-Z0-9]+)/source_type_descriptor/?$',
        # platformsviews.SourceTypeDescriptor(),
        # name='SourceTypeDescriptor'),
    URL(r'platforms/content_source_types/?$',
        platformsviews.SourceTypeService(),
        name='ContentSourceTypes'),
    URL(r'platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourceTypeService(),
        name='ContentSourceType'),
    URL(r'platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/(?P<content_source_type_id>\d+)/?$',
        platformsviews.SourceTypeService(),
        name='ContentSourceType'),
    URL(r'platforms/image_type_definitions/(?P<name>\w+)/?$',
        platformsviews.ImageTypeDefinitionDescriptorService(),
        name='ImageTypeDefinitionDescriptor'),

 
    # ModuleHooks
    URL(r'module_hooks/?$',
        modulehooksviews.ModuleHooksService(),
        name='ModuleHooks'),
 
    # Role Based Access Control
    URL(r'rbac/?$',
        rbacviews.RbacService(),
        name='Rbac'),
    URL(r'rbac/grants/?$',
        rbacviews.RbacPermissionsService(),
        name='RbacPermissions'),
    URL(r'rbac/grants/(?P<permission_id>\d+)?$',
        rbacviews.RbacPermissionsService(),
        name='RbacPermission'),
    URL(r'rbac/roles/?$',
        rbacviews.RbacRolesService(),
        name='RbacRoles'),
    URL(r'rbac/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacRolesService(),
        name='RbacRole'),
    URL(r'users/(?P<user_id>\d+)/roles/?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRoles'),
    URL(r'rbac/roles/(?P<role_id>\d+)/grants/?$',
        rbacviews.RbacRoleGrantsService(),
        name='RbacRoleGrants'),
    URL(r'rbac/roles/(?P<role_id>\d+)/users/?$',
        rbacviews.RbacRoleUsersService(),
        name='RbacRoleUser'),
    URL(r'users/(?P<user_id>\d+)/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRole'),
    URL(r'rbac/permissions/?$',
        rbacviews.RbacPermissionTypeService(),
        name='RbacPermissionTypes'),
    URL(r'rbac/permissions/(?P<permission_type_id>\d+)?$',
        rbacviews.RbacPermissionTypeService(),
        name='RbacPermissionType'),
    
    # Begin Targets/TargetTypes
    URL(r'targets/?$',
        targetsviews.TargetService(),
        name='Targets'),
    URL(r'targets/(?P<target_id>\d+)/?$',
        targetsviews.TargetService(),
        name='Target'),
    URL(r'targets/(?P<target_id>\d+)/target_types/?$',
        targetsviews.TargetTypeByTargetService(),
        name='TargetTypes'),
    URL(r'targets/(?P<target_id>\d+)/target_credentials/(?P<target_credentials_id>\d+)/?$',
        targetsviews.TargetCredentialsService(),
        name='TargetCredentials'),
    URL(r'targets/(?P<target_id>\d+)/target_user_credentials/(?P<user_id>\d+)/?$',
        targetsviews.TargetUserCredentialsService(),
        name='TargetUserCredentials'),
    URL(r'targets/(?P<target_id>\d+)/descriptor_configure_credentials/?$',
        targetsviews.TargetConfigureCredentialsService(),
        name='TargetConfigureCredentials'),
    URL(r'target_types/?$',
        targetsviews.TargetTypeService(),
        name='TargetTypes'),
    URL(r'target_types/(?P<target_type_id>\d+)/?$',
        targetsviews.TargetTypeService(),
        name='TargetType'),
    URL(r'target_types/(?P<target_type_id>\d+)/targets/?$',
        targetsviews.TargetTypeTargetsService(),
        name='TargetTypeTargets'),
    URL(r'target_types/(?P<target_type_id>\d+)/descriptor_create_target/?$',
        targetsviews.TargetTypeCreateTargetService(),
        name='TargetTypeCreateTarget'),
    URL(r'target_type_jobs/?$',
        targetsviews.TargetTypeAllJobsService(),
        name='TargetTypeAllJobs'),
    URL(r'target_types/(?P<target_type_id>\d+)/jobs/?$',
        targetsviews.TargetTypeJobsService(),
        name='TargetTypeJob'),
    URL(r'targets/(?P<target_id>\d+)/jobs/?$',
        targetsviews.TargetJobsService(),
        name='TargetJobs'),
    
    # Begin Images service
    URL(r'images/?$',
        imagesviews.ImagesService(),
        name='Images'),
    URL(r'images/(?P<image_id>\d+)/?$',
        imagesviews.ImageService(),
        name='Image'),

)
