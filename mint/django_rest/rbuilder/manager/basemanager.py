#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint import config
from mint import mint_error

from mint.db.database import Database
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.rest.db.database import Database as RestDatabase

log = logging.getLogger(__name__)

def exposed(fn):
    fn.exposed = True
    return fn

class BaseManager(object):
    def __init__(self, cfg=None, userName=None):
        self.cfg = cfg
        self._auth = None
        
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
            # The salt field contains binary data that blows django's little
            # mind when it tries to decode it as UTF-8. Since we don't need it
            # here, defer the loading of that column
            self.user = rbuildermodels.Users.objects.defer("salt").get(username = userName)

        # We instantiate _rest_db lazily
        self._rest_db = None

    def setAuth(self, auth, user):
        self._auth = auth
        self.user = user

    @property
    def rest_db(self):
        if self.cfg is None:
            return None
        if self._rest_db is None:
            from django.conf import settings
            if settings.DATABASE_ENGINE == 'sqlite3':
                self.cfg.dbPath = settings.DATABASE_NAME
            else:
                self.cfg.dbPath = '%s:%s/%s' % (settings.DATABASE_HOST, 
                    settings.DATABASE_PORT, settings.DATABASE_NAME)
            mint_db = Database(self.cfg)
            self._rest_db = RestDatabase(self.cfg, mint_db)
            if self._auth:
                self._rest_db.setAuth(self._auth, self._auth.getToken())
        return self._rest_db
