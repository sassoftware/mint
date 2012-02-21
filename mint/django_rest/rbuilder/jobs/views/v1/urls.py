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
        jobviews.JobsService(),
        name='Jobs',
        model='jobs.Jobs'),
    URL(r'/(?P<job_uuid>[-a-zA-Z0-9]+)/?$',
        jobviews.JobService(),
        name='Job',
        model='jobs.Job'),
)
