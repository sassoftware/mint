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
            sessIdx     %(PRIMARYKEY)s,
            sid         CHAR(64),
            data        TEXT
        );
    """

    fields = ['sessIdx', 'sid', 'data']

    indexes = {'sessionSidIdx': 'CREATE INDEX sessionSidIdx ON Sessions(sid)'}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 6:
                cu = self.db.cursor()
                # dropping and re-making is by far the best choice.
                cu.execute("DROP TABLE Sessions")
                if self.db.driver== "mysql":
                    cu.execute(self.createSQL_mysql)
                if self.db.driver == 'sqlite':
                    cu.execute(self.createSQL)
                else:
                    raise AssertionError("INVALID DATABASE TYPE: " + \
                                         self.db.driver)
                return (dbversion + 1) == self.schemaVersion
        return True

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
        cu.execute("SELECT sessIdx FROM Sessions WHERE sid=?", sid)
        r = cu.fetchone()
        sessIdx = None
        if r:
            sessIdx = r[0]
        self.db.transaction()
        try:
            if sessIdx:
                cu.execute("UPDATE Sessions set data=? WHERE sessIdx=?",
                           cPickle.dumps(data), sessIdx)
            else:
                cu.execute("INSERT INTO Sessions (sid, data) VALUES(?, ?)",
                           sid, cPickle.dumps(data))
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def delete(self, sid):
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions WHERE sid=?", sid)
        self.db.commit()

    def cleanup(self):
        # this is inefficient because we don't store accessed/timeout in
        # separate table fields, but instead encoded as a pickle object.
        cu  = self.db.transaction()
        try:
            cu.execute("SELECT sessIdx, data FROM Sessions")
            for sessIdx, data in cu.fetchall():
                d = cPickle.loads(data)
                if (time.time() - d["_accessed"]) > d["_timeout"]:
                    cu.execute("DELETE FROM Sessions WHERE sessIdx=?", sessIdx)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
