#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary import constants as conaryConstants
from restlib.controller import RestController
from rpath_proddef import api1 as proddef

from mint import constants
from mint import maintenance
from mint.rest.api import models
from mint.rest.api import product
from mint.rest.api import notices
from mint.rest.api import platforms
from mint.rest.api import registration
from mint.rest.api import users
from mint.rest.middleware import auth

class RbuilderRestServer(RestController):
    urls = {'products' : product.ProductController,
            'projects' : product.ProductController,
            'users'    : users.UserController,
            'platforms' : platforms.PlatformController,
            'registration' : registration.RegistrationController,
            'notices'  : notices.NoticesController,}

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, None, None, [cfg, db])

    @auth.public
    @auth.noDisablement
    def index(self, request):
        identity = self.db.getIdentity()
        maintMode = bool(maintenance.getMaintenanceMode(self.cfg))
        proddefSchemaVersion = proddef.BaseDefinition.version
        return models.RbuilderStatus(version=constants.mintVersion,
                                     conaryVersion=conaryConstants.version,
                                     isRBO=self.cfg.rBuilderOnline, 
                                     identity=identity,
                                     maintMode=maintMode,
                                     proddefSchemaVersion=proddefSchemaVersion)

    def url(self, request, *args, **kw):
        result = RestController.url(self, request, *args, **kw)
        if not request.extension:
            return result
        if result[-1] == '/':
            return result[:-1] + request.extension  + '/'
        return result + request.extension
