#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os

from conary.lib import coveragehook

from restlib.http import modpython

from mint import maintenance
from mint.db import database
from mint.rest.api import site
from mint.rest.db import database as restDatabase
from mint.rest.middleware import auth
from mint.rest.middleware import formatter

class RbuilderRESTHandler(object):
    httpHandlerClass = modpython.ModPythonHttpHandler

    def __init__(self, pathPrefix, cfg, db):
        self.cfg = cfg
        self.pathPrefix = pathPrefix
        db = restDatabase.Database(cfg, db)
        controller = site.RbuilderRestServer(self.cfg, db)
        self.handler = self.httpHandlerClass(controller)
        self.handler.addCallback(auth.AuthenticationCallback(self.cfg, db))
        self.handler.addCallback(formatter.FormatCallback(controller))

    def handle(self, req):
        return self.handler.handle(req, req.unparsed_uri[len(self.pathPrefix):])


def restHandler(req, cfg, pathInfo = None):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(cfg)
    topLevel = os.path.join(cfg.basePath, 'api/v1')
    db = database.Database(cfg)
    handler = RbuilderRESTHandler(topLevel, cfg, db)
    return handler.handle(req)
