#
# Copyright (c) 2008 rPath, Inc.
#

import os

from conary.lib import coveragehook
from mint import maintenance
from mint.db import database

from catalogService import handler_apache
from catalogService.rest.database import RestDatabase

class RbuilderCatalogRESTHandler(handler_apache.ApacheRESTHandler):
    def __init__(self, pathPrefix, cfg, db):
        restdb = RestDatabase(cfg, db)
        handler_apache.ApacheRESTHandler.__init__(self, pathPrefix,
            restdb)

def catalogHandler(context):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(context.cfg)
    topLevel = os.path.join(context.cfg.basePath, 'catalog')
    db = database.Database(context.cfg, db=context.db)
    handler = RbuilderCatalogRESTHandler(topLevel, context.cfg,
        db)
    return handler.handle(context.req)
