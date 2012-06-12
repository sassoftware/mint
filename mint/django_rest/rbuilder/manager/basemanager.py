#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint import config
from mint import mint_error

from mint.db import database
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.rest.db.database import Database as RestDatabase

log = logging.getLogger(__name__)

def exposed(fn):
    fn.exposed = True
    return fn

class BaseManager(object):
    def __init__(self, mgr):
        # mgr is a weakref to avoid circular references. Access its fields
        # through properties
        self.mgr = mgr

    @property
    def cfg(self):
        return self.mgr.cfg

    @property
    def restDb(self):
        return self.mgr.restDb

    @property
    def user(self):
        return self.mgr.user

    @property
    def auth(self):
        return self.mgr._auth

class BaseRbuilderManager(object):

    MANAGERS = {}

    def __init__(self, cfg=None, userName=None):
        self.cfg = cfg
        self._auth = None
        self.managers = []
        
        if not self.cfg:
            try:
                cfgPath = config.RBUILDER_CONFIG
                self.cfg = config.getConfig(cfgPath)
            except mint_error.ConfigurationMissing:
                log.info("Failed to build mint configuration, "
                        "expected in local mode only")
                # Use an empty config object
                self.cfg = None
        
        if userName is None:
            self.user = None
        else:
            self.user = usersmodels.User.objects.get(user_name=userName)

        # We instantiate _restDb lazily
        self._restDb = None

    def setAuth(self, auth, user):
        self._auth = auth
        self.user = user

    @property
    def restDb(self):
        if self.cfg is None:
            return None
        if self._restDb is None:
            self.setRestDbPath()
            mint_db = self.getMintDatabase()
            self._restDb = RestDatabase(self.cfg, mint_db)
            if self._auth:
                self._restDb.setAuth(self._auth, self._auth.getToken())
        return self._restDb

    def setRestDbPath(self):
        from django.conf import settings
        DB = settings.DATABASES['default']
        if DB['ENGINE'].endswith('sqlite3'):
            self.cfg.dbPath = DB['NAME']
        else:
            self.cfg.dbPath = '%s:%s/%s' % (DB['HOST'], DB['PORT'], DB['NAME'])

    def getMintDatabase(self):
        return database.Database(self.cfg)

    def close(self):
        if self._restDb is not None:
            self._restDb.close()
            self._restDb = None
