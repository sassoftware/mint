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
from mint.django_rest.rbuilder.images.views.v1 import views as imagesviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',
    URL(r'/?$',
        imagesviews.ImagesService(),
        name='Images',
        model='images.Images'),
    URL(r'/(?P<image_id>\d+)/?$',
        imagesviews.ImageService(),
        name='Image',
        model='images.Image'),
    URL(r'/(?P<image_id>\d+)/jobs/?$',
        imagesviews.ImageJobsService(),
        name='ImageJobs',
        model='jobs.Jobs'),
    # Digress for build_log
    URL(r'/(?P<image_id>\d+)/build_log/?$',
        imagesviews.BuildLogService(),
        name='BuildLog'),
    URL(r'/(?P<image_id>\d+)/build_files/?$',
        imagesviews.ImageBuildFilesService(),
        name='BuildFiles',
        model='images.BuildFiles'),
    URL(r'/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/?$',
        imagesviews.ImageBuildFileService(),
        name='BuildFile',
        model='images.BuildFile'),
    URL(r'/(?P<image_id>\d+)/build_files/(?P<file_id>\d+)/file_url/?$',
        imagesviews.ImageBuildFileUrlService(),
        name='FileUrl',
        model='images.FileUrl'),
    URL(r'/(?P<image_id>\d+)/descriptors/(?P<descriptor_type>[_A-Za-z]+)/?$',
        imagesviews.ImageDescriptorsService(),
        name='images.Descriptors'),
)
