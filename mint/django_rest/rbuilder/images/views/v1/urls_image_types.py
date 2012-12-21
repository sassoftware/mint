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
        imagesviews.ImageTypesService(),
        name='ImageTypes',
        model='images.ImageTypes'),
    URL(r'/(?P<image_type_id>\d+)/?$',
        imagesviews.ImageTypeService(),
        name='ImageType',
        model='images.ImageType')
)
