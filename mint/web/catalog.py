#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import base64
import os

from mod_python import Cookie
from conary.lib import coveragehook
from mint import maintenance
from mint import shimclient
from mint.db import database
from mint.session import SqlSession

from catalogService import handler_apache
from catalogService.rest.middleware import auth
from catalogService.rest.database import RestDatabase

class RbuilderCatalogRESTHandler(handler_apache.ApacheRESTHandler):
    def __init__(self, pathPrefix, cfg, db):
        restdb = RestDatabase(cfg, db)
        handler_apache.ApacheRESTHandler.__init__(self, pathPrefix,
            restdb)

    def handle(self, req):
        return self.handler.handle(req, self.pathPrefix)

def catalogHandler(context):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(context.cfg)
    topLevel = os.path.join(context.cfg.basePath, 'catalog')
    db = database.Database(context.cfg, db=context.db)
    handler = RbuilderCatalogRESTHandler(topLevel, context.cfg,
        db)
    return handler.handle(context.req)
