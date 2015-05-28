#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.conf.urls.defaults import patterns

from mint.django_rest.rbuilder.querysets.views.v1 import views as querysetviews
from mint.django_rest.rbuilder.rbac.views.v1 import views as rbacviews
from mint.django_rest import urls
URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    URL(r'^/?$',
        querysetviews.QuerySetsService(),
        name='QuerySets',
        model='querysets.QuerySets'),
    URL(r'^/(?P<query_set_id>\d+)/?$',
        querysetviews.QuerySetService(),
        name='QuerySet',
        model='querysets.QuerySet'),
    URL(r'^/(?P<query_set_id>\d+)/all/?$',
        querysetviews.QuerySetAllResultService(),
        name='QuerySetAllResult',
        model='querysets.AllMembers'),
    URL(r'^/(?P<query_set_id>\d+)/chosen/?$',
        querysetviews.QuerySetChosenResultService(),
        name='QuerySetChosenResult',
        model='querysets.ChosenMembers'),
    URL(r'^/(?P<query_set_id>\d+)/filtered/?$',
        querysetviews.QuerySetFilteredResultService(),
        name='QuerySetFilteredResult',
        model='querysets.FilteredMembers'),
    URL(r'^/(?P<query_set_id>\d+)/child/?$',
        querysetviews.QuerySetChildResultService(),
        name='QuerySetChildResult',
        model='querysets.ChildMembers'),
    URL(r'^/(?P<query_set_id>\d+)/universe/?$',
        querysetviews.QuerySetUniverseResultService(),
        name='QuerySetUniverseResult',
        model='querysets.Universe'),
    URL(r'^/(?P<query_set_id>\d+)/jobs/?$',
        querysetviews.QuerySetJobsService(),
        name='QuerySetJobs'),
    URL(r'^/(?P<query_set_id>\d+)/filter_descriptor/?$',
        querysetviews.QuerySetFilterDescriptorService(),
        name='QuerySetFilterDescriptor'),
    URL(r'^/(?P<query_set_id>\d+)/grant_matrix/?$',
        rbacviews.RbacQuerySetGrantMatrixService(),
        name='QuerySetGrantMatrix',
        model='querysets.GrantMatrix'),
    
)
