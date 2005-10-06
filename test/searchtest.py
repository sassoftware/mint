#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.projectlisting import PROJECTNAME_ASC, PROJECTNAME_DES, LASTMODIFIED_ASC, LASTMODIFIED_DES, CREATED_ASC, CREATED_DES, NUMDEVELOPERS_ASC, NUMDEVELOPERS_DES
class BrowseTest(MintRepositoryHelper):

    def _changeTimestamps(self, projectId, timeCreated, timeModified):
        cu = self.db.cursor()
        r = cu.execute("UPDATE Projects SET timeCreated=?, timeModified=? WHERE projectId=?", timeCreated, timeModified, projectId)
        self.db.commit()

    def _sortOrderDict(self):
        return {
            PROJECTNAME_ASC: [[4, 'bal', 'Bal', '', 1128540003.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [1, 'foo', 'Foo', '', 1128540046.5455239, 1]],
            PROJECTNAME_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1]],
            LASTMODIFIED_ASC: [[2, 'bar', 'Bar', '', 1124540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1], [1, 'foo', 'Foo', '', 1128540046.5455239, 1]],
            LASTMODIFIED_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1]],
            CREATED_ASC: [[2, 'bar', 'Bar', '', 1124540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1], [1, 'foo', 'Foo', '', 1128540046.5455239, 1]],
            CREATED_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1]],
            NUMDEVELOPERS_ASC: [[1, 'foo', 'Foo', '', 1128540046.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1]],
            NUMDEVELOPERS_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239, 1], [2, 'bar', 'Bar', '', 1124540046.5455239, 1], [3, 'baz', 'Baz', '', 1126540046.5455239, 1], [4, 'bal', 'Bal', '', 1128540003.5455239, 1]],
            }

    def testBrowse(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        fooId = client.newProject("Foo", "foo", "rpath.org")
        self._changeTimestamps(fooId, 1128540046.5455239, 1128540046.5455239)
        barId = client.newProject("Bar", "bar", "rpath.org")
        self._changeTimestamps(barId, 1124540046.5455239, 1124540046.5455239)
        bazId = client.newProject("Baz", "baz", "rpath.org")
        self._changeTimestamps(bazId, 1126540046.5455239, 1126640046.5455239)
        balId = client.newProject("Bal", "bal", "rpath.org")
        self._changeTimestamps(balId, 1128540003.5455239, 1129540003.5455239)

        sortOrderDict = self._sortOrderDict()
        for sortOrder in range(8):
            results, count = client.getProjects(sortOrder, 30, 0)
            assert (results == sortOrderDict[sortOrder])

if __name__ == "__main__":
    testsuite.main()
