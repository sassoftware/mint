#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.targets.views.v1 import views as targetsviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',
    URL(r'/?$',
        targetsviews.TargetsService(),
        name='Targets',
        model='targets.Targets'),
    URL(r'/(?P<target_id>\d+)/?$',
        targetsviews.TargetService(),
        name='Target',
        model='targets.Target'),
    URL(r'/(?P<target_id>\d+)/target_configuration/?$',
        targetsviews.TargetConfigurationService(),
        name='TargetConfiguration',
        model='targets.TargetConfiguration'),
    URL(r'/(?P<target_id>\d+)/target_types/?$',
        targetsviews.TargetTypeByTargetService(),
        name='TargetTypeByTarget',
        model='targets.TargetTypes'),
    URL(r'/(?P<target_id>\d+)/target_credentials/(?P<target_credentials_id>\d+)/?$',
        targetsviews.TargetCredentialsService(),
        name='TargetCredentials',
        model='targets.TargetCredentials'),
    URL(r'/(?P<target_id>\d+)/target_user_credentials/?$',
        targetsviews.TargetUserCredentialsService(),
        name='TargetUserCredentials',
        model='targets.TargetUserCredentials'),
    URL(r'/(?P<target_id>\d+)/descriptors/configuration/?$',
        targetsviews.TargetConfigurationDescriptorService(),
        name='TargetConfigurationDescriptor'),
    URL(r'/(?P<target_id>\d+)/descriptors/configure_credentials/?$',
        targetsviews.TargetConfigureCredentialsService(),
        name='TargetConfigureCredentials'),
    URL(r'/(?P<target_id>\d+)/descriptors/refresh_images/?$',
        targetsviews.TargetRefreshImagesService(),
        name='TargetRefreshImages'),
    URL(r'/(?P<target_id>\d+)/descriptors/refresh_systems/?$',
        targetsviews.TargetRefreshSystemsService(),
        name='TargetRefreshSystems'),
    URL(r'/(?P<target_id>\d+)/descriptors/deploy/file/(?P<file_id>\d+)/?$',
        targetsviews.TargetImageDeploymentService(),
        name='TargetImageDeployment'),
    URL(r'/(?P<target_id>\d+)/descriptors/launch/file/(?P<file_id>\d+)/?$',
        targetsviews.TargetSystemLaunchService(),
        name='TargetSystemLaunch'),
    URL(r'/(?P<target_id>\d+)/jobs/?$',
        targetsviews.TargetJobsService(),
        name='TargetJobs',
        model='jobs.Jobs'),
)
