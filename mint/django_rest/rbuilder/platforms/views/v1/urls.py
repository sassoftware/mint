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
from mint.django_rest.rbuilder.platforms.views.v1 import views
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    # FIXME -- migrate to new structure
    URL(r'^/?$',
        views.PlatformsService(),
        name='Platforms',
        model='platforms.Platforms'),
    URL(r'^/(?P<platform_id>\d+)/?$',
        views.PlatformService(),
        name='Platform',
        model='platforms.Platform'),
    URL(r'^/image_type_definition_descriptors/(?P<name>\w+)/?$',
        views.ImageTypeDefinitionDescriptorService(),
        name='ImageTypeDefinitionDescriptor'),

)
