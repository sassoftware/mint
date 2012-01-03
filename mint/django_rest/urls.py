#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import url, patterns, include
from mint.django_rest.rbuilder.discovery import views as discoveryviews

class URLRegistry(object):
    _registry = {}
    VERSION = '1'
    @classmethod
    def URL(cls, regex, *args, **kwargs):
        viewName = kwargs.get('name', None)
        if not regex.startswith("^"):
            regex = "^%s" % regex
        if viewName:
            oldUrl = cls._registry.get(viewName)
            if oldUrl:
                raise Exception("Duplicate view name: %s (urls: %s, %s)" %
                    (viewName, oldUrl, regex))
            cls._registry[viewName] = regex
        # try to get model name, is optional
        modelName = kwargs.pop('model', None)
        u = url(regex, *args, **kwargs)
        u.model = modelName
        return u

URL = URLRegistry.URL

urlpatterns = patterns('',
    URL(r'^api/?$', discoveryviews.VersionsService(), name='API'),

    # API v1
    URL(r'^api/v1/?$', discoveryviews.ApiVersionService(), name='APIVersion'),
    (r'^api/v1', include('mint.django_rest.v1')),

    # API v2
)

