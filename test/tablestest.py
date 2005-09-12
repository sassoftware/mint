#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

import rephelp
import sqlite3

from mint import dbversion
from mint import releases

class TablesTest(rephelp.RepositoryHelper):
    def testReleasesTable(self):
        releaseTable = releases.ReleasesTable(self.db)
        id = releaseTable.new(projectId = 0, name = "Release", desc = "A release.")
        release = releaseTable.get(id)
        
        assert(release['name'] == 'Release')
        assert(release['desc'] == 'A release.')
        assert(release['releaseId'] == id)

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)
        try:
            os.unlink(self.reposDir + "/db")
        except:
            pass
        self.db = sqlite3.connect(self.reposDir + "/db")
        self.versionTable = dbversion.VersionTable(self.db)
        self.db.commit()

if __name__ == "__main__":
    testsuite.main()
