#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#


import time

import fixtures

from mint.db import sessiondb

class SessionTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Empty")
    def testClientSessions(self, db, data):
        client = self.getClient("test")
        sid = "dae86825ca6c4681c68e173a18417f91"

        sessionData = {'_created':   0,
                       '_data':      500*sid,
                       '_accessed':  time.time() - 20,
                       '_timeout':   10}
        client.saveSession(sid, sessionData)
        # exercise the cached index codepath in saveSession
        client.saveSession(sid, sessionData)

        d = client.loadSession(sid)

        if d != sessionData:
            self.fail("Data did not survive being saved on server")

        client.cleanupSessions()

        d = client.loadSession(sid)
        self.failIf(d, "Stale session data not deleted")

        client.saveSession(sid, sessionData)
        client.deleteSession(sid)

        d = client.loadSession(sid)
        self.failIf(d, "Session data not explicitly deleted")

        # now emulate a thread race condition...
        client.saveSession(sid, sessionData)
        client.loadSession(sid)
        cu = db.cursor()
        cu.execute("DELETE FROM Sessions")
        db.commit()

        d = client.loadSession(sid)
        self.failIf(d, "Session data improperly survived race condition")

