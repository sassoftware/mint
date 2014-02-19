#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#


import fixtures

from conary.dbstore import sqlerrors

class InjectionTest(fixtures.FixturedUnitTest):
    attackStrings = {"garbage'; system ls'" : "Multiple statements"}

    @fixtures.fixture("Full")
    def testDirectSQL(self, db, data):
        cu = db.cursor()
        for name in self.attackStrings.keys():
            self.assertRaises(sqlerrors.CursorError, cu.execute,
                              "SELECT * FROM Projects WHERE hostname='%s'" % \
                              name)

    @fixtures.fixture("Full")
    def testBoundStrings(self, db, data):
        hackedHostname = "' OR '1'='1"

        cu = db.cursor()

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

    @fixtures.fixture("Full")
    def testBoundIntegers(self, db, data):
        hackedProjectId = 'NULL OR 1=1'

        cu = db.cursor()

        # if bound parameters work correctly, this query will result
        # in NULL results
        cu.execute("SELECT projectId FROM Projects WHERE hostname=?",
                   hackedProjectId)

        self.failIf(cu.fetchall(), "Bound parameters for integers failed to "
                    "protect against SQL injection")


