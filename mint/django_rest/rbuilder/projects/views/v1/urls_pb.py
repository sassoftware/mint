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

    # project branches
    URL(r'^/?$',
        views.AllProjectBranchesService(),
        name='AllProjectBranches',
        model='projects.ProjectVersions'),

)

