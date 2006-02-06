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

    def testBoundStrings(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        hackedHostname = "' OR '1'='1"

        cu = self.db.cursor()

        # go about things in a manner definitely susceptible to injection.
        # when hackedHostname is applied, this will result in a list of all
        # projectIds
        cu.execute("SELECT projectId FROM Projects WHERE hostname='%s'" % \
                   hackedHostname)

        unboundRes = cu.fetchall()

        # if bound parameters work correctly, the exact same query will result
        # in NULL results
        cu.execute("SELECT projectId FROM Projects WHERE hostname=?",
                   hackedHostname)

        boundRes = cu.fetchall()

        self.failIf(unboundRes == boundRes,
                    "Bound parameters failed to protect against SQL injection")

    def testBoundIntegers(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        hackedProjectId = 'NULL OR 1=1'

        cu = self.db.cursor()

        # if bound parameters work correctly, this query will result
        # in NULL results
        cu.execute("SELECT projectId FROM Projects WHERE hostname=?",
                   hackedProjectId)

        self.failIf(cu.fetchall(), "Bound parameters for integers failed to "
                    "protect against SQL injection")


if __name__ == "__main__":
    testsuite.main()
