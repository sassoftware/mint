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
            sessIdx     INTEGER PRIMARY KEY,
            sid         STR,
            data        STR
        );
    """
    createSQL_mysql = """
        CREATE TABLE Sessions (
            sessIdx    INT PRIMARY KEY AUTO_INCREMENT,
            sid        VARCHAR(64),
            data       TEXT
        );
    """
    fields = ['sid', 'data']

    # objects specific to SessionsTable follow
    indexCache = {}

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

    def getSessIndex(self, sid):
        """Translate the sid from the web session into an index appropriate
        For use in a database scenario"""
        if sid in self.indexCache:
            idxTuple = self.indexCache[sid]
            self.indexCache[sid] = (idxTuple[0], time.time())
            return idxTuple[0]
        # if we hadn't cached the idx, we need to go look up in the db...
        cu = self.db.cursor()
        cu.execute("SELECT sessIdx FROM Sessions WHERE sid = ?", sid)
        sessIdx = cu.fetchone()
        if sessIdx:
            sessIdx=sessIdx[0]
            self.indexCache[sid] = (sessIdx, time.time())
        return sessIdx

    def delSessIndex(self, sid):
        if sid in self.indexCache:
            del(self.indexCache[sid])

    def load(self, sid):
        cu = self.db.cursor()
        sessIdx = self.getSessIndex(sid)
        if sessIdx:
            cu.execute("SELECT data FROM Sessions WHERE sessIdx=?", sessIdx)
            r = cu.fetchone()
        else:
            r = None
        if r:
            return cPickle.loads(r[0])
        else:
            self.delSessIndex(sid)
            return None

    def save(self, sid, data):
        cu = self.db.cursor()
        sessIdx = self.getSessIndex(sid)
        if sessIdx:
            # beware of this UPDATE statement. There exists one extremely
            # unlikely corner case which is probably an error condition
            # anyway... you could get here if the session was deleted and
            # then the same sid was re-saved in a different thread.
            # under these conditions, your session WON'T get saved--
            # however the only realisticly imaginible time that could
            # happen is if someone hijacked a session anyway.
            # UPDATE was chosen because empirical data suggests it is
            # up to 100 times faster than delete->insert.
            cu.execute("UPDATE Sessions SET sid=?, data=? WHERE sessidx=?",
                       sid, cPickle.dumps(data), sessIdx)
        else:
            cu.execute("INSERT INTO Sessions (sid, data) VALUES(?, ?)",
                       sid, cPickle.dumps(data))

    def delete(self, sid):
        cu = self.db.cursor()
        sessIdx = self.getSessIndex(sid)
        cu.execute("DELETE FROM Sessions WHERE sessIdx=?", sessIdx)
        self.delSessIndex(sid)

    def cleanup(self):
        # clean up the indexCache to mitigate memory leaks
        for sid in self.indexCache:
            if (time.time() - self.indexCache[sid][1]) > 3600:
                self.delSessIndex(sid)
        # this is inefficient because we don't store accessed/timeout in
        # separate table fields, but instead encoded as a pickle object.
        cu  = self.db.transaction()
        try:
            cu.execute("SELECT sessIdx, data FROM Sessions")
            for r in cu.fetchall():
                d = cPickle.loads(r[1])
                if (time.time() - d["_accessed"]) > d["_timeout"]:
                    cu.execute("DELETE FROM Sessions WHERE sessIdx=?", r[0])
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
