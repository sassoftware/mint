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


import exceptions

from restlib.controller import RestController

from mint.rest.api import modulehooks
from mint.rest.api import product
from mint.rest.api import platforms
from mint.rest.api import users

class RbuilderRestServer(RestController):
    urls = {'products' : product.ProductController,
            'projects' : product.ProductController,
            'users'    : users.UserController,
            'platforms' : platforms.PlatformController,
            'moduleHooks' : modulehooks.ModuleController,}

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, None, None, [cfg, db])

    def url(self, request, *args, **kw):
        result = None
        try:
            result = RestController.url(self, request, *args, **kw)
        except exceptions.KeyError:
            # workaround to be able to return URLs linking to Django
            # which are hard coded string return values from the
            # get_absolute_url function
            return ''.join(args) 

        if not request.extension:
            return result
        if result[-1] == '/':
            return result[:-1] + request.extension  + '/'
        return result + request.extension
