#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
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

if __name__ == "__main__":
    testsuite.main()
