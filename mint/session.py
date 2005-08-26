#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import cPickle

from mod_python.Session import BaseSession
from database import DatabaseTable

class SqlSession(BaseSession, DatabaseTable):
    """An implementation of mod_python's Session support for an sqlite backend."""
    name = "Sessions"
    createSQL = """
        CREATE TABLE Sessions (
            sid         STR,
            data        STR
        );
    """
    fields = ['sid', 'data']

    def __init__(self, req, db = None, sid = 0,
                 secret = None, timeout = 0, lock = 1):
        if not db:
            db = sqlite3.connect(":memory:")

        self._db = db

        DatabaseTable.__init__(self, db)
        BaseSession.__init__(self, req, sid = sid, secret = secret,
                             timeout = timeout, lock = lock)
    
    def do_cleanup(self):
        self._req.register_cleanup(dbm_cleanup, self._db)
        self._req.log_error("SqlSession: registered database cleanup.",
                            apache.APLOG_NOTICE)

    def do_load(self):
        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", self._sid)
        r = cu.fetchone()
        if r:
            return cPickle.loads(r[0])
        else:
            return None

    def do_save(self, dict):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions WHERE sid=?",
            self._sid)
        cu.execute("INSERT INTO Sessions VALUES(?, ?)",
            self._sid, cPickle.dumps(dict))
        self.db.commit()

    def do_delete(self):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions WHERE sid=?", self._sid)
        self.db.commit()


def sql_cleanup(self, db):
    cu = db.cursor()
    # this is inefficient because we don't store accessed/timeout in
    # separate table fields, but instead encoded as a pickle object.
    cu.execute("SELECT sid, data FROM Sessions")
    for r in cu.fetchall():
        d = cPickle.loads(r[1])
        if (time.time() - d["_accessed"]) > d["_timeout"]:
            cu.execute("DELETE FROM Sessions WHERE sid=?", r[0])
    db.commit()
