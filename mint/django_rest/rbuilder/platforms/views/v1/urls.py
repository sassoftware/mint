#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
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


