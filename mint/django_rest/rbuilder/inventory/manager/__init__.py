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

class Manager(rbuilder_manager.RbuilderDjangoManager):
    def __init__(self, cfg=None, userName=None):
        super(self.__class__, self).__init__(cfg=cfg, userName=userName)
        self.sysMgr = systemmgr.SystemManager(weakref.proxy(self))
        self.versionMgr = versionmgr.VersionManager(weakref.proxy(self))
        # We instantiate _restDb lazily
        self._restDb = None

        # Methods we simply copy
        for subMgr in [ self.sysMgr, self.versionMgr ]:
            for objName in subMgr.__class__.__dict__:
                obj = getattr(subMgr, objName, None)
                if getattr(obj, 'exposed', None):
                    if hasattr(self, objName):
                        raise Exception("Conflict for method %s" % objName)
                    setattr(self, objName, obj)

    @property
    def restDb(self):
        if self.cfg is None:
            return None
        if self._restDb is None:
            from django.conf import settings
            self.cfg.dbPath = settings.DATABASE_NAME
            mint_db = Database(self.cfg)
            self.rest_db = RestDatabase(self.cfg, mint_db)
        return self._restDb
