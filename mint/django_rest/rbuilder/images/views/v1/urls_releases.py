#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.projects.views.v1 import views as projectviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',
    URL(r'/?$',
        projectviews.TopLevelReleasesService(),
        name='Releases',
        model='projects.Releases'),
    URL(r'/(?P<release_id>\d+)/?$',
        projectviews.TopLevelReleaseService(),
        name='TopLevelRelease',
        model='projects.Release'),
)
