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
