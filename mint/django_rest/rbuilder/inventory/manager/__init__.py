#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import weakref

from mint.django_rest.rbuilder import rbuilder_manager

from mint.db.database import Database
from mint.rest.db.database import Database as RestDatabase

from mint.django_rest.rbuilder.inventory.manager import systemmgr
from mint.django_rest.rbuilder.inventory.manager import versionmgr
from mint.django_rest.rbuilder.inventory.manager import repeatermgr
from mint.django_rest.rbuilder.inventory.manager import jobmgr

class Manager(rbuilder_manager.RbuilderDjangoManager):
    def __init__(self, cfg=None, userName=None):
        super(self.__class__, self).__init__(cfg=cfg, userName=userName)
        self.sysMgr = systemmgr.SystemManager(weakref.proxy(self))
        self.versionMgr = versionmgr.VersionManager(weakref.proxy(self))
        self.repeaterMgr = repeatermgr.RepeaterManager(weakref.proxy(self))
        self.jobMgr = jobmgr.JobManager(weakref.proxy(self))
        # We instantiate _rest_db lazily
        self._rest_db = None

        # Methods we simply copy
        for subMgr in [ self.sysMgr, self.versionMgr, self.jobMgr ]:
            for objName in subMgr.__class__.__dict__:
                obj = getattr(subMgr, objName, None)
                if getattr(obj, 'exposed', None):
                    if hasattr(self, objName):
                        raise Exception("Conflict for method %s" % objName)
                    setattr(self, objName, obj)

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
