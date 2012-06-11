#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import cPickle
import time

from conary.lib import util

from mint.lib.database import DatabaseTable

class SessionsTable(DatabaseTable):
    name = "Sessions"

    fields = ['sessIdx', 'sid', 'data']

    def load(self, sid):
        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)
        r = cu.fetchone()
        if r:
            data = cPickle.loads(r[0])
            if '_data' in data:
                if 'authToken' in data['_data']:
                    data['_data']['authToken'] = (data['_data']['authToken'][0],
                            util.ProtectedString(data['_data']['authToken'][1]))
            return data
        else:
            return False

    def save(self, sid, data):
        if '_data' in data:
            if 'authToken' in data['_data']:
                data['_data']['authToken'] = (data['_data']['authToken'][0],
                        util.ProtectedString(data['_data']['authToken'][1]))
        cu = self.db.cursor()
        cu.execute("SELECT sessIdx FROM Sessions WHERE sid=?", sid)
        r = cu.fetchone()
        sessIdx = None
        if r:
            sessIdx = r[0]

        # retry up to 10 times to make sure that we save the session data
        tries = 0
        while tries < 10:
            try:
                self.db.transaction()
                if sessIdx:
                    cu.execute("UPDATE Sessions set data=? WHERE sessIdx=?",
                               cPickle.dumps(data), sessIdx)
                else:
                    cu.execute("INSERT INTO Sessions (sid, data) VALUES(?, ?)",
                               sid, cPickle.dumps(data))
                self.db.commit()
                break
            except:
                self.db.rollback()
                tries += 1
                time.sleep(1)

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
