#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint import releases

from mint_rephelp import MintRepositoryHelper

class TablesTest(MintRepositoryHelper):
    def testReleasesTable(self):
        releaseTable = releases.ReleasesTable(self.db)
        id = releaseTable.new(projectId = 0, name = "Release", desc = "A release.")
        release = releaseTable.get(id)
        
        assert(release['name'] == 'Release')
        assert(release['desc'] == 'A release.')
        assert(release['releaseId'] == id)

if __name__ == "__main__":
    testsuite.main()
