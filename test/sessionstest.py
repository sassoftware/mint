#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import time
import testsuite
testsuite.setup()

import sqlite3
import rephelp 
from mint_rephelp import MintRepositoryHelper

from mint import dbversion
from mint import sessiondb

class SessionTest(MintRepositoryHelper):
    def testSessions(self):
        st = sessiondb.SessionsTable(self.db)

        # create a session
        st.save("abcdefg123456", {'_data':      'data',
                                  '_accessed':  time.time() - 20,
                                  '_timeout':   10}
        )

        # load and check data
        d = st.load("abcdefg123456")
        assert(d['_data'] == 'data')

        # clean up expired sessions
        st.cleanup()

        # confirm that expired session went away
        d = st.load("abcdefg123456")
        assert(not d)

    # note: sessionData should really mimic what we'd see from a web
    # client since this will help detect errors due to typeChecking
    def testClientSessions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        sid = "abcdefg123456"
        sessionData = {'_data':      {},
                       '_accessed':  time.time() - 20,
                       '_timeout':   10}
        client.saveSession(sid, sessionData)

        d = client.loadSession(sid)

        if d != sessionData:
            self.fail("Data did not survive being saved on server")

        client.cleanupSessions()

        d = client.loadSession("abcdefg123456")
        assert not d

        client.saveSession(sid, sessionData)
        client.deleteSession(sid)

        d = client.loadSession("abcdefg123456")
        assert not d

if __name__ == "__main__":
    testsuite.main()
