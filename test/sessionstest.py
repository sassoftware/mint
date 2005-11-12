#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import time
import testsuite
testsuite.setup()

import rephelp

from mint_rephelp import MintRepositoryHelper
from mint import dbversion
from mint import sessiondb

class SessionTest(MintRepositoryHelper):
    def testClientSessions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        sid = "dae86825ca6c4681c68e173a18417f91"

        sessionData = {'_data':      500*sid,
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
        assert not d

        client.saveSession(sid, sessionData)
        client.deleteSession(sid)

        d = client.loadSession(sid)
        assert not d

        # now emulate a thread race condition... this is different than a
        # deleteSession call because the session table's internal index
        # caching is guaranteed to be out of sync
        client.saveSession(sid, sessionData)
        client.loadSession(sid)
        cu = self.db.cursor()
        cu.execute("DELETE FROM Sessions")

        d = client.loadSession(sid)
        assert not d

if __name__ == "__main__":
    testsuite.main()
