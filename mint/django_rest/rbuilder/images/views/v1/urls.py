#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
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
    URL(r'/(?P<image_id>\d+)/systems/?$',
        imagesviews.ImageSystemsService(),
        name='ImageSystems',
        model='inventory.Systems'),
    # Digress for build_log
    URL(r'/(?P<image_id>\d+)/build_log/?$',
        imagesviews.BuildLogService(),
        name='images.BuildLog'),
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
    URL(r'/(?P<image_id>\d+)/upload_files/(?P<token>[A-Fa-f0-9]+)/?$',
        imagesviews.ImageUploadFilesService(),
        name='ImageUpload',
        model='images.Image'),
)
