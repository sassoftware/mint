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
    URL(r'^/(?P<platform_id>\d+)/content_sources/?$',
        views.PlatformSourceService(),
        name='PlatformSource',
        model='platforms.ContentSources'),
    URL(r'^/(?P<platform_id>\d+)/content_source_types/?$',
        views.PlatformSourceTypeService(),
        name='PlatformSourceType',
        model='platforms.ContentSourceTypes'),
    URL(r'^/content_sources/?$',
        views.AllSourcesService(),
        name='ContentSources',
        model='platforms.ContentSources'),
    URL(r'^/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        views.SourcesService(),
        name='ContentSource',
        model='platforms.ContentSources'),
    URL(r'^/content_sources/(?P<source_type>[_a-zA-Z0-9]+)/(?P<short_name>(\w|\-)*)/?$',
        views.SourceService(),
        name='ContentSourceShortName',
        model='platforms.ContentSource'),
    URL(r'^/content_source_types/?$',
        views.AllSourceTypesService(),
        name='ContentSourceTypes',
        model='platforms.ContentSourceTypes'),
    URL(r'^/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/?$',
        views.SourceTypesService(),
        name='ContentSourceType',
        model='platforms.ContentSourceTypes'),
    URL(r'^/content_source_types/(?P<source_type>[_a-zA-Z0-9]+)/(?P<content_source_type_id>\d+)/?$',
        views.SourceTypeService(),
        name='ContentSourceTypeById',
        model='platforms.ContentSourceType'),
    URL(r'^/image_type_definition_descriptors/(?P<name>\w+)/?$',
        views.ImageTypeDefinitionDescriptorService(),
        name='ImageTypeDefinitionDescriptor'),

)


