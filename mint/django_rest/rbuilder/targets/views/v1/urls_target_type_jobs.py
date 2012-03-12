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
        targetsviews.TargetTypeAllJobsService(),
        name='TargetTypeAllJobs',
        model='jobs.Jobs'),
)
