#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib.controller import RestController

class BaseController(RestController):
    def __init__(self, parent, path, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, parent, path, [cfg, db])

    def url(self, request, *args, **kw):
        result = RestController.url(self, request, *args, **kw)
        if not request.extension:
            return result
        if result[-1] == '/':
            return result[:-1] + request.extension  + '/'
        return result[:-1] + request.extension
