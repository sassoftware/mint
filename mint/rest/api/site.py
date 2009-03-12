#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib.controller import RestController

from mint import constants
from conary import constants as conaryConstants

from mint.rest.api import models
from mint.rest.api import product
from mint.rest.api import notices
from mint.rest.api import users

class RbuilderRestServer(RestController):
    urls = {'products' : product.ProductController,
            'projects' : product.ProductController,
            'users'    : users.UserController,
            'notices'  : notices.NoticesController,}

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, None, None, [cfg, db])

    def index(self, request):
        identity = self.db.getIdentity()
        return models.RbuilderStatus(version=constants.mintVersion,
                                     conaryVersion=conaryConstants.version,
                                     isRBO=self.cfg.rBuilderOnline, 
                                     identity=identity)

    def url(self, request, *args, **kw):
        result = RestController.url(self, request, *args, **kw)
        if not request.extension:
            return result
        if result[-1] == '/':
            return result[:-1] + request.extension  + '/'
        return result + request.extension
