#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint import releases
from mint_rephelp import MintRepositoryHelper

from conary.dbstore import sqlerrors 

class TablesTest(MintRepositoryHelper):
    def testReleasesTable(self):
        releaseTable = releases.ReleasesTable(self.db)
        id = releaseTable.new(projectId = 0, name = "Release", description = "A release.")
        release = releaseTable.get(id)
        
        assert(release['name'] == 'Release')
        assert(release['description'] == 'A release.')
        assert(release['releaseId'] == id)

    def testDatabaseExceptions(self):
        db = self.db

        cu = db.cursor()
        cu.execute("CREATE TEMPORARY TABLE TestTable ( id INT UNIQUE )")
        cu.execute("INSERT INTO TestTable VALUES (1)")

        try:
            cu.execute("INSERT INTO TestTable VALUES(1)")
        except sqlerrors.CursorError:
            pass
        else:
            self.fail("expected sql_error.ColumNotUnique exception but insert succeeded")

if __name__ == "__main__":
    testsuite.main()
