#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.jobs.views.v1 import views as jobviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',
    URL(r'/?$',
        jobviews.JobStatesService(),
        name='JobStates',
        model='jobs.JobStates'),
    URL(r'/(?P<job_state_id>[a-zA-Z0-9]+)/?$',
        jobviews.JobStateService(),
        name='JobState',
        model='jobs.JobState'),
    URL(r'/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        jobviews.JobStatesJobsService(),
        name='JobStateJobs',
        model='jobs.Jobs'),
)


