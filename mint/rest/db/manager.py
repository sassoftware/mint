#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import weakref

class Manager(object):
    def __init__(self, cfg, db, auth, publisher=None):
        self.cfg = cfg
        self.auth = auth
        self._db = weakref.ref(db)
        self.publisher = publisher

    def _getDb(self):
        return self._db()

    db = property(_getDb)
