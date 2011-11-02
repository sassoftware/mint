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


class URLRegistry(object):
    _registry = {}
    VERSION = '1'
    @classmethod
    def URL(cls, regex, *args, **kwargs):
        if not regex.startswith('^'):
            regex = "^api/v%s/%s" % (cls.VERSION, regex)
        viewName = kwargs.get('name', None)
        if viewName:
            oldUrl = cls._registry.get(viewName)
            if oldUrl:
                raise Exception("Duplicate view name: %s (urls: %s, %s)" %
                    (viewName, oldUrl, regex))
            cls._registry[viewName] = regex
        # try and get model name
        modelName = kwargs.pop('model', None)
        u = url(regex, *args, **kwargs)
        u.model = modelName
        return u
        
URL = URLRegistry.URL

urlpatterns = patterns('',
    # Versioning. Note that this URL does NOT get versioned
    URL(r'^api/?$',
        discoveryviews.VersionsService(),
        name='API'),
    URL(r'^api/v%s/?$' % URLRegistry.VERSION,
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
        inventoryviews.InventorySystemStatesService(),
        name='SystemStates'),
    URL(r'inventory/system_states/(?P<system_state_id>\d+)/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemState'),

    # Zones
    URL(r'inventory/zones/?$',
        inventoryviews.InventoryZonesService(),
        name='Zones'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/?$',
        inventoryviews.InventoryZoneService(),
        name='Zone'),

    # Management Nodes
    URL(r'inventory/management_nodes/?$',
        inventoryviews.InventoryManagementNodesService(),
        name='ManagementNodes',
        model='ManagementNodes'),
    URL(r'inventory/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNode',
        model='ManagementNode'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/management_nodes/?$',
        inventoryviews.InventoryZoneManagementNodesService(),
        name='ZoneManagementNodes',
        model='ZoneManagementNodes'),
    URL(r'inventory/zones/(?P<zone_id>\d+)/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ZoneManagementNode',
        model='ZoneManagementNode'),
        
    # Management Interfaces
    URL(r'inventory/management_interfaces/?$',
        inventoryviews.InventoryManagementInterfacesService(),
        name='ManagementInterfaces',
        model='ManagementInterfaces'),
    URL(r'inventory/management_interfaces/(?P<management_interface_id>\d+)/?$',
        inventoryviews.InventoryManagementInterfaceService(),
        name='ManagementInterface',
        model='ManagementInterface'),
        
    # System types
    URL(r'inventory/system_types/?$',
        inventoryviews.InventorySystemTypesService(),
        name='SystemTypes',
        model='SystemTypes'),
    URL(r'inventory/system_types/(?P<system_type_id>\d+)/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemType',
        model='SystemType'),
    URL(r'inventory/system_types/(?P<system_type_id>\d+)/systems/?$',
        inventoryviews.InventorySystemTypeSystemsService(),
        name='SystemTypeSystems',
        model='Systems'),
       
    # Networks
    URL(r'inventory/networks/?$',
        inventoryviews.InventoryNetworksService(),
        name='Networks',
        model='Networks'),
    URL(r'inventory/networks/(?P<network_id>\d+)/?$',
        inventoryviews.InventoryNetworkService(),
        name='Network',
        model='Network'),

    # Systems
    # RBL-8919 - accept double slashes to accommodate an rpath-tools bug
    URL(r'inventory//?systems/?$',
        inventoryviews.InventorySystemsService(),
        name='Systems',
        model='Systems'),
    # support outdated rpath-register (needed for older platforms)
    URL(r'^api/inventory/systems/?$',
        inventoryviews.InventorySystemsService(),
        name='SystemsHack2'),
    URL(r'inventory/inventory_systems/?$',
        inventoryviews.InventoryInventorySystemsService(),
        name='InventorySystems',
        model='Systems'),
    URL(r'inventory/infrastructure_systems/?$',
        inventoryviews.InventoryInfrastructureSystemsService(),
        name='ImageImportMetadataDescriptor',
        model='Systems'),
    URL(r'inventory/image_import_metadata_descriptor/?$',
        inventoryviews.ImageImportMetadataDescriptorService(),
        name='InfrastructureSystems'),
    URL(r'inventory/systems/(?P<system_id>\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System',
        model='System'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_log/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLog',
        model='SystemLog'),
    URL(r'inventory/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs',
        model='SystemJobs'),
    URL(r'inventory/systems/(?P<system_id>\d+)/descriptors/(?P<descriptor_type>[_A-Za-z]+)/?$',
        inventoryviews.InventorySystemJobDescriptorService(),
        name='SystemJobDescriptors'),
    URL(r'inventory/systems/(?P<system_id>\d+)/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventorySystemJobStatesService(),
        name='SystemJobStateJobs',
        model='SystemJobs'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_events/?$',
        inventoryviews.InventorySystemsSystemEventService(),
        name='SystemsSystemEvent',
        model='SystemEvents'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_log/(?P<format>[a-zA-Z]+)/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat',
        model='SystemLog'),
    URL(r'inventory/systems/(?P<system_id>\d+)/installed_software/?$',
        inventoryviews.InventorySystemsInstalledSoftwareService(),
        name='InstalledSoftware',
        model='InstalledSoftware'),
    URL(r'inventory/systems/(?P<system_id>\d+)/credentials/?$',
        inventoryviews.InventorySystemCredentialsServices(),
        name='SystemCredentials',
        model='Credentials'),
    URL(r'inventory/systems/(?P<system_id>\d+)/configuration/?$',
        inventoryviews.InventorySystemConfigurationServices(),
        name='SystemConfiguration',
        model='Configuration'),
    URL(r'inventory/systems/(?P<system_id>\d+)/configuration_descriptor/?$',
        inventoryviews.InventorySystemConfigurationDescriptorServices(),
        name='SystemConfigurationDescriptor',
        model='ConfigurationDescriptor'),

    # System Events
    URL(r'inventory/system_events/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvents',
        model='SystemEvents'),
    URL(r'inventory/system_events/(?P<system_event_id>\d+)/?$',
        inventoryviews.InventorySystemEventService(),
        name='SystemEvent',
        model='SystemEvent'),

    # System Tags
    URL(r'inventory/systems/(?P<system_id>\d+)/system_tags/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTags'),
    URL(r'inventory/systems/(?P<system_id>\d+)/system_tags/(?P<system_tag_id>\d+)/?$',
        inventoryviews.InventorySystemTagService(),
        name='SystemTag'),

    # Event Types
    URL(r'inventory/event_types/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventTypes',
        model='EventTypes'),
    URL(r'inventory/event_types/(?P<event_type_id>\d+)/?$',
        inventoryviews.InventoryEventTypeService(),
        name='EventType',
        model='EventType'),

    # Jobs
    URL(r'jobs/?$',
        jobviews.JobsService(),
        name='Jobs',
        model='Jobs'),
    URL(r'jobs/(?P<job_uuid>[-a-zA-Z0-9]+)/?$',
        jobviews.JobService(),
        name='Job',
        model='Job'),

    # Job States
    URL(r'job_states/?$',
        jobviews.JobStatesService(),
        name='JobStates',
        model='JobStates'),
    URL(r'job_states/(?P<job_state_id>[a-zA-Z0-9]+)/?$',
        jobviews.JobStateService(),
        name='JobState',
        model='JobState'),
    URL(r'job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        jobviews.JobStatesJobsService(),
        name='JobStateJobs',
        model='Jobs'),

    # Major Versions
    URL(r'products/(?P<short_name>(\w|\-)*)/versions/(?P<version>(\w|\.)*)/?$',
        inventoryviews.MajorVersionService(),
        name='MajorVersions'),

    # Products
    URL(r'products/(\w|\-)*/?$',
        inventoryviews.ApplianceService(),
        name='Products'),

    # URL(r'projects/(?P<short_name>(\w|\-)*)/project_branches/(?P<project_branch_name>(\w|\-|[0-9])*)/repos/?$',
    #        projectviews.ProjectBranchService(),
    #        name='ProjectVersion'),

    # Query Sets
    URL(r'query_sets/?$',
        querysetviews.QuerySetsService(),
        name='QuerySets',
        model='QuerySets'),
    URL(r'favorites/query_sets/?$',
        querysetviews.FavoriteQuerySetService(),
        name='FavoriteQuerySets',
        model='QuerySets'),
    URL(r'query_sets/(?P<query_set_id>\d+)/?$',
        querysetviews.QuerySetService(),
        name='QuerySet',
        model='QuerySet'),
    URL(r'query_sets/(?P<query_set_id>\d+)/all/?$',
        querysetviews.QuerySetAllResultService(),
        name='QuerySetAllResult',
        model='AllMembers'),
    URL(r'query_sets/(?P<query_set_id>\d+)/chosen/?$',
        querysetviews.QuerySetChosenResultService(),
        name='QuerySetChosenResult',
        model='ChosenMembers'),
    URL(r'query_sets/(?P<query_set_id>\d+)/filtered/?$',
        querysetviews.QuerySetFilteredResultService(),
        name='QuerySetFilteredResult',
        model='FilteredMembers'),
    URL(r'query_sets/(?P<query_set_id>\d+)/child/?$',
        querysetviews.QuerySetChildResultService(),
        name='QuerySetChildResult',
        model='ChildMembers'),
    URL(r'query_sets/(?P<query_set_id>\d+)/universe/?$',
        querysetviews.QuerySetUniverseResultService(),
        name='QuerySetUniverseResult',
        model='Universe'),
    URL(r'query_sets/(?P<query_set_id>\d+)/jobs/?$',
        querysetviews.QuerySetJobsService(),
        name='QuerySetJobs'),
    URL(r'query_sets/(?P<query_set_id>\d+)/filter_descriptor/?$',
        querysetviews.QuerySetFilterDescriptorService(),
        name='QuerySetFilterDescriptor'),
    URL(r'query_sets/(?P<query_set_id>\d+)/grant_matrix/?$',
        rbacviews.RbacQuerySetGrantMatrixService(),
        name='QuerySetGrantMatrix',
        model='GrantMatrix'),
    

    # Change Logs
    URL(r'changelogs/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLogs',
        model='ChangeLogs'),
    URL(r'changelogs/(?P<change_log_id>\d+)/?$',
        changelogviews.ChangeLogService(),
        name='ChangeLog',
        model='ChangeLog'),

    # These are aggregates
    # Aggregate all project branches
    URL(r'project_branches/?$',
        projectviews.AllProjectBranchesService(),
        name='AllProjectBranches',
        model='ProjectVersions'),

    # Aggregate all project branch stages
    URL(r'project_branch_stages/?$',
        projectviews.AllProjectBranchesStagesService(),
        name='AllProjectBranchStages',
        model='Stages'),

    # Proper hierarchy for projects
    URL(r'projects/?$',
        projectviews.ProjectService(),
        name='Projects',
        model='Projects'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/?$',
        projectviews.ProjectService(),
        name='Project',
        model='Project'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/members/?$',
        projectviews.ProjectMemberService(),
        name='ProjectMembers',
        model='Members'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/releases/?$',
        projectviews.ProjectReleasesService(),
        name='ProjectReleases',
        model='Releases'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/?$',
        projectviews.ProjectReleaseService(),
        name='ProjectRelease',
        model='Release'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/images/?$',
        projectviews.ProjectReleaseImagesService(),
        name='ProjectReleaseImages',
        model='Images'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/releases/(?P<release_id>\d+)/images/(?P<image_id>\d+)/?$',
        projectviews.ProjectReleaseImageService(),
        name='ProjectReleaseImage',
        model='Image'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/?$',
        projectviews.ProjectAllBranchesService(),  # WRONG
        name='ProjectVersions',
        model='ProjectVersions'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/?$',
        projectviews.ProjectBranchService(),
        name='ProjectVersion',
        model='ProjectVersion'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/?$',
        projectviews.ProjectBranchStagesService(),
        name='ProjectBranchStages',
        model='Stages'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)$',
        projectviews.ProjectBranchStageService(),
        name='ProjectBranchStage',
        model='Stage'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branches/(?P<project_branch_label>[a-zA-Z0-9]+(\.|\w|\-|\@|\:)*)/project_branch_stages/(?P<stage_name>(\w|-)+)/images/?$',
        projectviews.ProjectBranchStageImagesService(),
        name='ProjectBranchStageImages',
        model='Images'),

    # Aggregate all stages for a project
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/project_branch_stages/?$',
        projectviews.ProjectAllBranchStagesService(),
        name='ProjectBranchesAllStages',
        model='Stages'),

    URL(r'projects/(?P<project_short_name>(\w|\-)*)/images/?$',
        projectviews.ProjectImagesService(),
        name='ProjectImages',
        model='Images'),
    URL(r'projects/(?P<project_short_name>(\w|\-)*)/images/(?P<image_id>\d+)/?$',
        projectviews.ProjectImageService(),
        name='ProjectImage',
        model='Image'),

    # Packages
    URL(r'packages/?$',
        packageindexviews.PackagesService(),
        name='Packages',
        model='Packages'),
    URL(r'packages/(?P<package_id>\d+)/?$',
        packageindexviews.PackageService(),
        name='Package',
        model='Package'),

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
        name='Session',
        model='Session'),
    # Users
    URL(r'users/?$',
        usersviews.UsersService(),
        name='Users',
        model='Users'),
    
    URL(r'users/(?P<user_id>\d+)/?$',
        usersviews.UserService(),
        name='User',
        model='User'),

    # UserNotices
    URL(r'users/(?P<user_id>\d+)/notices/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices'),
    
    URL(r'notices/users/(?P<user_id>\d+)/?$',
        noticesviews.UserNoticesService(),
        name='UserNotices2'),

    # Begin all things platforms
    URL(r'platforms/?$',
        platformsviews.PlatformsService(),
        name='Platforms',
        model='Platforms'),
    URL(r'platforms/(?P<platform_id>\d+)/?$',
        platformsviews.PlatformService(),
        name='Platform',
        model='Platform'),
    # URL(r'platforms/(?P<platform_id>\d+)/platform_status/?$',
    #     platformsviews.PlatformStatusService(),
    #     name='PlatformStatus'),
    URL(r'platforms/(?P<platform_id>\d+)/content_sources/?$',
        platformsviews.PlatformSourceService(),
        name='PlatformSource',
        model='ContentSources'),
    URL(r'platforms/(?P<platform_id>\d+)/content_source_types/?$',
        platformsviews.PlatformSourceTypeService(),
        name='PlatformSourceType',
        model='ContentSourceTypes'),
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
        platformsviews.AllSourcesService(),
        name='ContentSources',
        model='ContentSources'),
    URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourcesService(),
        name='ContentSource',
        model='ContentSources'),
    URL(r'platforms/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/?$',
        platformsviews.SourceService(),
        name='ContentSourceShortName',
        model='ContentSource'),
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
        platformsviews.AllSourceTypesService(),
        name='ContentSourceTypes',
        model='ContentSourceTypes'),
    URL(r'platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        platformsviews.SourceTypesService(),
        name='ContentSourceType',
        model='ContentSourceTypes'),
    URL(r'platforms/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/(?P<content_source_type_id>\d+)/?$',
        platformsviews.SourceTypeService(),
        name='ContentSourceTypeById',
        model='ContentSourceType'),
    URL(r'platforms/image_type_definition_descriptors/(?P<name>\w+)/?$',
        platformsviews.ImageTypeDefinitionDescriptorService(),
        name='ImageTypeDefinitionDescriptor'),

 
    # ModuleHooks
    URL(r'module_hooks/?$',
        modulehooksviews.ModuleHooksService(),
        name='ModuleHooks'),
 
    # Role Based Access Control
    URL(r'rbac/?$',
        rbacviews.RbacService(),
        name='Rbac',
        model='Rbac'),
    URL(r'rbac/grants/?$',
        rbacviews.RbacPermissionsService(),
        name='RbacPermissions',
        model='RbacPermissions'),
    URL(r'rbac/grants/(?P<permission_id>\d+)?$',
        rbacviews.RbacPermissionService(),
        name='RbacPermission',
        model='RbacPermission'),
    URL(r'rbac/roles/?$',
        rbacviews.RbacRolesService(),
        name='RbacRoles',
        model='RbacRoles'),
    URL(r'rbac/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacRoleService(),
        name='RbacRole',
        model='RbacRole'),
    URL(r'users/(?P<user_id>\d+)/roles/?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRoles',
        model='RbacUserRoles'),
    URL(r'rbac/roles/(?P<role_id>\d+)/grants/?$',
        rbacviews.RbacRoleGrantsService(),
        name='RbacRoleGrants',
        model='RbacPermissions'),
    URL(r'rbac/roles/(?P<role_id>\d+)/users/?$',
        rbacviews.RbacRoleUsersService(),
        name='RbacRoleUser',
        model='Users'),
    URL(r'users/(?P<user_id>\d+)/roles/(?P<role_id>\d+)?$',
        rbacviews.RbacUserRolesService(),
        name='RbacUserRole',
        model='RbacUserRole'),
    URL(r'rbac/permissions/?$',
        rbacviews.RbacPermissionTypesService(),
        name='RbacPermissionTypes',
        model='RbacPermissionTypes'),
    URL(r'rbac/permissions/(?P<permission_type_id>\d+)?$',
        rbacviews.RbacPermissionTypeService(),
        name='RbacPermissionType',
        model='RbacPermissionType'),
    
    # Begin Targets/TargetTypes
    URL(r'targets/?$',
        targetsviews.TargetsService(),
        name='Targets',
        model='Targets'),
    URL(r'targets/(?P<target_id>\d+)/?$',
        targetsviews.TargetService(),
        name='Target',
        model='Target'),
    URL(r'targets/(?P<target_id>\d+)/target_types/?$',
        targetsviews.TargetTypeByTargetService(),
        name='TargetTypeByTarget',
        model='TargetTypes'),
    URL(r'targets/(?P<target_id>\d+)/target_credentials/(?P<target_credentials_id>\d+)/?$',
        targetsviews.TargetCredentialsService(),
        name='TargetCredentials',
        model='TargetCredentials'),
    URL(r'targets/(?P<target_id>\d+)/target_user_credentials/(?P<user_id>\d+)/?$',
        targetsviews.TargetUserCredentialsService(),
        name='TargetUserCredentials',
        model='TargetUserCredentials'),
    URL(r'targets/(?P<target_id>\d+)/descriptor_configure_credentials/?$',
        targetsviews.TargetConfigureCredentialsService(),
        name='TargetConfigureCredentials'),
    URL(r'targets/(?P<target_id>\d+)/descriptor_refresh_images/?$',
        targetsviews.TargetRefreshImagesService(),
        name='TargetRefreshImages'),
    URL(r'target_types/?$',
        targetsviews.TargetTypesService(),
        name='TargetTypes',
        model='TargetTypes'),
    URL(r'target_types/(?P<target_type_id>\d+)/?$',
        targetsviews.TargetTypeService(),
        name='TargetType',
        model='TargetType'),
    URL(r'target_types/(?P<target_type_id>\d+)/targets/?$',
        targetsviews.TargetTypeTargetsService(),
        name='TargetTypeTargets',
        model='Targets'),
    URL(r'target_types/(?P<target_type_id>\d+)/descriptor_create_target/?$',
        targetsviews.TargetTypeCreateTargetService(),
        name='TargetTypeCreateTarget'),
    URL(r'target_type_jobs/?$',
        targetsviews.TargetTypeAllJobsService(),
        name='TargetTypeAllJobs',
        model='Jobs'),
    URL(r'target_types/(?P<target_type_id>\d+)/jobs/?$',
        targetsviews.TargetTypeJobsService(),
        name='TargetTypeJob',
        model='Jobs'),
        
    # begin target jobs
    URL(r'targets/(?P<target_id>\d+)/jobs/?$',
        targetsviews.TargetJobsService(),
        name='TargetJobs',
        model='Jobs'),
    URL(r'target_jobs/?$',
        targetsviews.AllTargetJobsService(),
        name='AllTargetJobs',
        model='Jobs'),
    
    # Begin all things Images service
    URL(r'images/?$',
        imagesviews.ImagesService(),
        name='Images',
        model='Images'),
    URL(r'images/(?P<image_id>\d+)/?$',
        imagesviews.ImageService(),
        name='Image',
        model='Image'),
    
    # Digress for build_log
    URL(r'images/(?P<image_id>\d+)/build_log/?$',
        imagesviews.BuildLogService(),
        name='BuildLog'),
    
    URL(r'images/(?P<image_id>\d+)/build_files/?$',
        imagesviews.ImageBuildFilesService(),
        name='BuildFiles',
        model='BuildFiles'),
    URL(r'images/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/?$',
        imagesviews.ImageBuildFileService(),
        name='BuildFile',
        model='BuildFile'),
    URL(r'images/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/file_url/?$',
        imagesviews.ImageBuildFileUrlService(),
        name='FileUrl',
        model='FileUrl'),
        
    # Begin Releases service
    URL(r'releases/?$',
        imagesviews.ReleasesService(),
        name='Releases',
        model='Releases'),
    URL(r'releases/(?P<release_id>\d+)/?$',
        imagesviews.ReleaseService(),
        name='TopLevelRelease',
        model='Release'),
    
    # Begin image types
    URL(r'image_types/?$',
        imagesviews.ImageTypesService(),
        name='ImageTypes',
        model='ImageTypes'),
    URL(r'image_types/(?P<image_type_id>\d+)/?$',
        imagesviews.ImageTypeService(),
        name='ImageType',
        model='ImageType')
)
