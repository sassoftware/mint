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


from django.conf.urls.defaults import url, patterns, include
from mint.django_rest.rbuilder.discovery import views as discoveryviews
from mint.django_rest.rbuilder.inventory.views.v1 import views as inventoryviews

class URLRegistry(object):
    _registry = {}
    VERSION = '1'
    @classmethod
    def URL(cls, regex, *args, **kwargs):
        viewName = kwargs.get('name', None)
        if not regex.startswith("^"):
            regex = "^%s" % regex
        if viewName:
            # disabling temporarily for now as it seems to be hiding some tracebacks
            #oldUrl = cls._registry.get(viewName)
            #if oldUrl:
            #    raise Exception("Duplicate view name: %s (urls: %s, %s)" %
            #        (viewName, oldUrl, regex))
            cls._registry[viewName] = regex
        # try to get model name, is optional
        modelName = kwargs.pop('model', None)
        u = url(regex, *args, **kwargs)
        u.model = modelName
        return u

URL = URLRegistry.URL

urlpatterns = patterns('',

    # not versioned
    # support outdated rpath-register (needed for older platforms)
    URL(r'^api/systems/?$',
        inventoryviews.InventorySystemsService(),
        name='SystemsHack2'),

    URL(r'^api/?$', discoveryviews.VersionsService(), name='API'),

    # API v1
    URL(r'^api/v1/?$', discoveryviews.ApiVersionService(), name='APIVersion'),
    (r'^api/v1', include('mint.django_rest.v1')),

    # API v2
)
