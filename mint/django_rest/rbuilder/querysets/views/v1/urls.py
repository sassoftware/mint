#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns

from mint.django_rest.rbuilder.querysets.views.v1 import views as querysetviews
# FIXME: will change to have a v1 URL once migrated
from mint.django_rest.rbuilder.rbac import views as rbacviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('querysets.views.v1',

    URL(r'/?$',
        querysetviews.QuerySetsService(),
        name='QuerySets',
        model='querysets.QuerySets'),
    URL(r'/(?P<query_set_id>\d+)/?$',
        querysetviews.QuerySetService(),
        name='QuerySet',
        model='querysets.QuerySet'),
    URL(r'/(?P<query_set_id>\d+)/all/?$',
        querysetviews.QuerySetAllResultService(),
        name='QuerySetAllResult',
        model='querysets.AllMembers'),
    URL(r'/(?P<query_set_id>\d+)/chosen/?$',
        querysetviews.QuerySetChosenResultService(),
        name='QuerySetChosenResult',
        model='querysets.ChosenMembers'),
    URL(r'/(?P<query_set_id>\d+)/filtered/?$',
        querysetviews.QuerySetFilteredResultService(),
        name='QuerySetFilteredResult',
        model='querysets.FilteredMembers'),
    URL(r'/(?P<query_set_id>\d+)/child/?$',
        querysetviews.QuerySetChildResultService(),
        name='QuerySetChildResult',
        model='querysets.ChildMembers'),
    URL(r'/(?P<query_set_id>\d+)/universe/?$',
        querysetviews.QuerySetUniverseResultService(),
        name='QuerySetUniverseResult',
        model='querysets.Universe'),
    URL(r'/(?P<query_set_id>\d+)/jobs/?$',
        querysetviews.QuerySetJobsService(),
        name='QuerySetJobs'),
    URL(r'/(?P<query_set_id>\d+)/filter_descriptor/?$',
        querysetviews.QuerySetFilterDescriptorService(),
        name='QuerySetFilterDescriptor'),
    URL(r'/(?P<query_set_id>\d+)/grant_matrix/?$',
        rbacviews.RbacQuerySetGrantMatrixService(),
        name='QuerySetGrantMatrix',
        model='querysets.GrantMatrix'),
    
)
