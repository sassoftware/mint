#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
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
