#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import cPickle

from mod_python.Session import BaseSession
from database import DatabaseTable

class SessionsTable(DatabaseTable):
    name = "Sessions"
    createSQL = """
        CREATE TABLE Sessions (
            sid         STR,
            data        STR
        );
    """
    fields = ['sid', 'data']

    def load(self, sid):
        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)
        r = cu.fetchone()
        if r:
            return cPickle.loads(r[0])
        else:
            return None

    def save(self, sid, data):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions WHERE sid=?", sid)
        cu.execute("INSERT INTO Sessions VALUES(?, ?)",
            sid, cPickle.dumps(data))
        self.db.commit()

    def delete(self, sid):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions WHERE sid=?", sid)
        self.db.commit()

    def cleanup(self):
        # this is inefficient because we don't store accessed/timeout in
        # separate table fields, but instead encoded as a pickle object.
        cu  = self.db.cursor()

        cu.execute("SELECT sid, data FROM Sessions")
        for r in cu.fetchall():
            d = cPickle.loads(r[1])
            if (time.time() - d["_accessed"]) > d["_timeout"]:
                cu.execute("DELETE FROM Sessions WHERE sid=?", r[0])
        self.db.commit()


class SqlSession(BaseSession, DatabaseTable):
    """An implementation of mod_python's Session support for an sqlite backend."""
    def __init__(self, req, client, sid = 0,
                 secret = None, timeout = 0, lock = 1):
        self._client = client

        BaseSession.__init__(self, req, sid = sid, secret = secret,
                             timeout = timeout, lock = lock)
    
    def do_cleanup(self):
        self._req.register_cleanup(sql_cleanup, self._client)
        self._req.log_error("SqlSession: registered database cleanup.",
                            apache.APLOG_NOTICE)

    def do_load(self):
        return self._client.loadSession(self._sid)

    def do_save(self, data):
        self._client.saveSession(self._sid, data)

    def do_delete(self):
        self._client.deleteSession(self._sid)

def sql_cleanup(self, client):
    client.cleanupSessions()
