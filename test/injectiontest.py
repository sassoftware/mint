#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from conary.dbstore import sqlerrors

class InjectionTest(MintRepositoryHelper):
    attackStrings = {"garbage'; system ls'" : "Multiple statements"}

    def testDirectSQL(self):
        cu = self.db.cursor()

        for name in self.attackStrings.keys():
            self.assertRaises(sqlerrors.CursorError, cu.execute,
                              "SELECT * FROM Projects WHERE hostname='%s'" % \
                              name)

if __name__ == "__main__":
    testsuite.main()
