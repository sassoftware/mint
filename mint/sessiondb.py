#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import cPickle
import time

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
