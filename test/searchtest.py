#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.projectlisting import PROJECTNAME_ASC, PROJECTNAME_DES, LASTMODIFIED_ASC, LASTMODIFIED_DES, CREATED_ASC, CREATED_DES, NUMDEVELOPERS_ASC, NUMDEVELOPERS_DES, ACTIVITY_ASC, ACTIVITY_DES, ordersql
from mint import userlevels
from mint.searcher import SearchTermsError

class BrowseTest(MintRepositoryHelper):

    def _changeTimestamps(self, projectId, timeCreated, timeModified):
        cu = self.db.cursor()
        r = cu.execute("UPDATE Projects SET timeCreated=?, timeModified=? WHERE projectId=?", timeCreated, timeModified, projectId)
        self.db.commit()

    def _fakeCommit(self, projectId, timestamp, userId):
        cu = self.db.cursor()
        r = cu.execute("INSERT INTO Commits VALUES(?, ?, 'whoCares', '1.0', ?)", projectId, timestamp, userId)
        self.db.commit()

    def _fakePackage(self, projectId, name):
        cu = self.db.cursor()
        r = cu.execute("SELECT IFNULL(MAX(pkgId) + 1, 1) FROM PackageIndex")
        pkgId = r.fetchone()[0]

        r = cu.execute("INSERT INTO PackageIndex VALUES(?, ?, ?, 'whoCares')", (pkgId, projectId, name))
        self.db.commit()

    def _sortOrderDict(self):
        return {
            PROJECTNAME_ASC: [[4, 'bal', 'Bal', '', 1129542003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [1, 'foo', 'Foo', '', 1128540046.5455239]],
            PROJECTNAME_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239]],
            LASTMODIFIED_ASC: [[1, 'foo', 'Foo', '', 1128540046.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239]],
            LASTMODIFIED_DES: [[3, 'baz', 'Baz', '', 1129560003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [1, 'foo', 'Foo', '', 1128540046.5455239]],
            CREATED_ASC: [[2, 'bar', 'Bar', '', 1129550003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [1, 'foo', 'Foo', '', 1128540046.5455239]],
            CREATED_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239]],
            NUMDEVELOPERS_ASC: [[2, 'bar', 'Bar', '', 1129550003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [1, 'foo', 'Foo', '', 1128540046.5455239]],
            NUMDEVELOPERS_DES: [[1, 'foo', 'Foo', '', 1128540046.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239]],
            ACTIVITY_ASC: [[1, 'foo', 'Foo', '', 1128540046.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [2, 'bar', 'Bar', '', 1129550003.5455239]],
            ACTIVITY_DES: [[2, 'bar', 'Bar', '', 1129550003.5455239], [4, 'bal', 'Bal', '', 1129542003.5455239], [3, 'baz', 'Baz', '', 1129560003.5455239], [1, 'foo', 'Foo', '', 1128540046.5455239]],
            }

    def testBrowse(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")

        fooId = client.newProject("Foo", "foo", "rpath.org")
        self._changeTimestamps(fooId, 1128540046.5455239, 1128540046.5455239)
        barId = client.newProject("Bar", "bar", "rpath.org")
        self._changeTimestamps(barId, 1124540046.5455239, 1124540046.5455239)
        bazId = client.newProject("Baz", "baz", "rpath.org")
        self._changeTimestamps(bazId, 1126540046.5455239, 1126640046.5455239)
        balId = client.newProject("Bal", "bal", "rpath.org")
        self._changeTimestamps(balId, 1128540003.5455239, 1129540003.5455239)

        fooProject = client.getProject(fooId)
        barProject = client.getProject(barId)
        bazProject = client.getProject(bazId)
        balProject = client.getProject(balId)

        # add some fake commits for sorting
        self._fakeCommit(barId, 1129550003.5455239, userId)
        self._fakeCommit(bazId, 1129560003.5455239, userId2)
        self._fakeCommit(balId, 1129541003.5455239, userId4)
        self._fakeCommit(balId, 1129542003.5455239, userId3)
        self._fakeCommit(barId, 1129543003.5455239, userId)
        self._fakeCommit(barId, 1129544003.5455239, userId)
        # and a couple of really old ones that won't show up...
        self._fakeCommit(bazId, 1120040003.5455239, userId2)
        self._fakeCommit(bazId, 1120040013.5455239, userId2)

        # add some members to each project to make the popularity sort useful
        fooProject.addMemberById(userId2, userlevels. DEVELOPER)
        fooProject.addMemberById(userId3, userlevels. DEVELOPER)
        fooProject.addMemberById(userId4, userlevels. DEVELOPER)

        bazProject.addMemberById(userId3, userlevels. DEVELOPER)

        balProject.addMemberById(userId3, userlevels. DEVELOPER)
        balProject.addMemberById(userId4, userlevels. DEVELOPER)

        sortOrderDict = self._sortOrderDict()
        for sortOrder in range(10):
            results, count = client.getProjects(sortOrder, 30, 0)
            if results != sortOrderDict[sortOrder]:
                self.fail("sort problem during sort: %s"% ordersql[sortOrder])

    def testSearchProjects(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        fooId = client.newProject("Foo Project", "foo", "rpath.org")
        self._changeTimestamps(fooId, 1128540046.5455239, 1128540046.5455239)
        booId = client.newProject("Boo Project", "boo", "rpath.org")
        self._changeTimestamps(booId, 1124540046.5455239, 1124540046.5455239)
        snoozeId = client.newProject("Snooze Project", "snooze", "rpath.org")
        self._changeTimestamps(snoozeId, 1126540046.5455239, 1126640046.5455239)
        snoofId = client.newProject("Snoof Project", "snoof", "rpath.org")
        self._changeTimestamps(snoofId, 1128540003.5455239, 1129540003.5455239)

        try:
            client.getProjectSearchResults('oo ')
            self.fail("Search for illegal values 'oo ' succeeded")
        except SearchTermsError:
            pass

        if client.getProjectSearchResults('Foo') != ([[1, 'foo', 'Foo Project', '', 1128540046.5455239]], 1):
            self.fail("Search for 'Foo' did not return the correct results.")
        res = client.getProjectSearchResults('Project')
        assert(res[1] == 4)
        assert(len(res[0]) == res[1])
        assert(client.getProjectSearchResults('Snoo')[1] == 2)
        assert(client.getProjectSearchResults('Camp Town Racers sing this song... doo dah... doo dah...') == ([], 0) )
        assert(client.getProjectSearchResults('snooze OR Boo')[1] == 2)

    def testSearchUsers(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")
        assert(len(client.getUserSearchResults('test')[0]) == 4)
        assert(client.getUserSearchResults('er3') == ([[3, 'testuser3', 'Test User', 'test at example.com', '', 0]], 1))
        assert(client.getUserSearchResults('Sir Not Appearing In This Film') == ([], 0) )

    def testSearchPackages(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        self._fakePackage(projectId, "brokenPackage")
        self._fakePackage(projectId, "foomatic")
        self._fakePackage(projectId, "barmatic")
        self._fakePackage(projectId, "foobar")
        assert(client.getPackageSearchResults('broken') == ([['brokenPackage', 'whoCares', 1]], 1))
        assert(client.getPackageSearchResults('foo')[1] == 2)

if __name__ == "__main__":
    testsuite.main()
