#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import exceptions

from conary import constants as conaryConstants
from rmake import constants as rmakeConstants
from restlib.controller import RestController
from rpath_proddef import api1 as proddef

from mint import constants
from mint import maintenance
from mint.rest.api import capsules
from mint.rest.api import models
from mint.rest.api import modulehooks
from mint.rest.api import product
from mint.rest.api import platforms
from mint.rest.api import users
from mint.rest.middleware import auth

class RbuilderRestServer(RestController):
    urls = {'products' : product.ProductController,
            'projects' : product.ProductController,
            'users'    : users.UserController,
            'platforms' : platforms.PlatformController,
            'contentSources' : platforms.SourceTypeController,
            'capsules'  : capsules.CapsulesController,
            'moduleHooks' : modulehooks.ModuleController,}

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
        username=((request.mintAuth and request.mintAuth.username) or 'anonymous')
        return models.RbuilderStatus(version=constants.mintVersion,
                                     conaryVersion=conaryConstants.changeset,
                                     rmakeVersion=rmakeConstants.changeset,
                                     userName=username,
                                     hostName=os.uname()[1],
                                     isRBO=self.cfg.rBuilderOnline, 
                                     isExternalRba=self.cfg.rBuilderExternal, 
                                     accountCreationRequiresAdmin=self.cfg.adminNewUsers,
                                     identity=identity,
                                     maintMode=maintMode,
                                     inventoryConfigurationEnabled=self.cfg.inventoryConfigurationEnabled,
                                     imageImportEnabled=self.cfg.imageImportEnabled,
                                     proddefSchemaVersion=proddefSchemaVersion)

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
