#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.projectlisting import PROJECTNAME_ASC, PROJECTNAME_DES, LASTMODIFIED_ASC, LASTMODIFIED_DES, CREATED_ASC, CREATED_DES, NUMDEVELOPERS_ASC, NUMDEVELOPERS_DES, ACTIVITY_ASC, ACTIVITY_DES, ordersql
from mint import userlevels
from mint import searcher

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
        cu.execute("SELECT IFNULL(MAX(pkgId) + 1, 1) FROM PackageIndex")
        pkgId = cu.fetchone()[0]

        r = cu.execute("INSERT INTO PackageIndex VALUES(?, ?, ?, 'whoCares')", (pkgId, projectId, name))
        self.db.commit()

    def _sortOrderDict(self):
        return {
            PROJECTNAME_ASC:   ['bal', 'bar', 'baz', 'biz'],
            PROJECTNAME_DES:   ['biz', 'baz', 'bar', 'bal'],
            LASTMODIFIED_ASC:  ['biz', 'bal', 'bar', 'baz'],
            LASTMODIFIED_DES:  ['baz', 'bar', 'bal', 'biz'],
            CREATED_ASC:       ['bar', 'baz', 'bal', 'biz'],
            CREATED_DES:       ['biz', 'bal', 'baz', 'bar'],
            NUMDEVELOPERS_ASC: ['bar', 'biz', 'baz', 'bal'],
            NUMDEVELOPERS_DES: ['bal', 'baz', 'bar', 'biz'],
            ACTIVITY_ASC:      ['biz', 'baz', 'bal', 'bar'],
            ACTIVITY_DES:      ['bar', 'bal', 'baz', 'biz'],
            }

    def testBrowse(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")

        fooId = client.newProject("Foo", "foo", "rpath.org")
        self._changeTimestamps(fooId, 1128540046, 1128540046)
        barId = client.newProject("Bar", "bar", "rpath.org")
        self._changeTimestamps(barId, 1124540046, 1124540046)
        bazId = client.newProject("Baz", "baz", "rpath.org")
        self._changeTimestamps(bazId, 1126540046, 1126640046)
        balId = client.newProject("Bal", "bal", "rpath.org")
        self._changeTimestamps(balId, 1128540003, 1129540003)
        bizId = client.newProject("Biz", "biz", "rpath.org")
        self._changeTimestamps(balId, 1128540003, 1129540003)

        fooProject = client.getProject(fooId)
        barProject = client.getProject(barId)
        bazProject = client.getProject(bazId)
        balProject = client.getProject(balId)

        # add some fake commits for sorting
        self._fakeCommit(barId, 1129550003, userId)
        self._fakeCommit(bazId, 1129560003, userId2)
        self._fakeCommit(balId, 1129541003, userId4)
        self._fakeCommit(balId, 1129542003, userId3)
        self._fakeCommit(barId, 1129543003, userId)
        self._fakeCommit(barId, 1129544003, userId)
        # and a couple of really old ones that won't show up...
        self._fakeCommit(bazId, 1120040003, userId2)
        self._fakeCommit(bazId, 1120040013, userId2)
        self._fakeCommit(bizId, 1120040008, userId2)

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
            if count != 4:
                self.fail('getProjects returned the wrong project count.')
            if [x[1] for x in results] != sortOrderDict[sortOrder]:
                self.fail("sort problem during sort: %s. expected %s, but got %s"% (ordersql[sortOrder], sortOrderDict[sortOrder],[x[1] for x in results]))
        if client.getProjectsList() != [(4, 0, 0, 'bal - Bal'), (2, 0, 0, 'bar - Bar'), (3, 0, 0, 'baz - Baz'), (5, 0, 0, 'biz - Biz'), (1, 0, 0, 'foo - Foo')]:
            self.fail("getProjectsList did not return alphabetical results")

    def testFledgling(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        hideFledgling = self.mintCfg.hideFledgling
        try:
            projectId = client.newProject("Bar", "bar", "rpath.org")
            self._changeTimestamps(projectId, 1124540046, 1124540046)

            self.mintCfg.hideFledgling = False
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Fledgling projects not counted in project list")

            self.mintCfg.hideFledgling = True
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1],
                        "Fledgling projects counted in project list")

            # add a fake commit to trigger non-fledgling status
            self._fakeCommit(projectId, 1129550003, userId)

            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Non fledgling project didn't show up")

        finally:
            self.mintCfg.hideFledgling = hideFledgling

    def testExternal(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        hideFledgling = self.mintCfg.hideFledgling
        try:
            projectId = client.newProject("Bar", "bar", "rpath.org")
            self._changeTimestamps(projectId, 1124540046, 1124540046)

            self.mintCfg.hideFledgling = False
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Fledgling projects not counted in project list")

            self.mintCfg.hideFledgling = True
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1],
                        "Fledgling projects counted in project list")

            # alter project to appear to be external
            cu = self.db.cursor()
            cu.execute("UPDATE Projects set external=1")
            self.db.commit()

            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "external project counted as fledgling")
        finally:
            self.mintCfg.hideFledgling = hideFledgling

    def testSearchProjects(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        fooId = client.newProject("Foo Project", "foo", "rpath.org")
        self._changeTimestamps(fooId, 1128540046, 1128540046)
        booId = client.newProject("Boo Project", "boo", "rpath.org")
        self._changeTimestamps(booId, 1124540046, 1124540046)
        snoozeId = client.newProject("Snooze Project", "snooze", "rpath.org")
        self._changeTimestamps(snoozeId, 1126540046, 1126640046)
        snoofId = client.newProject("Snoof Project", "snoof", "rpath.org")
        self._changeTimestamps(snoofId, 1128540003, 1129540003)

        if client.getProjectSearchResults('Foo') != ([[1, 'foo', 'Foo Project', '', 1128540046]], 1):
            self.fail("Search for 'Foo' did not return the correct results.")
        res = client.getProjectSearchResults('Project')
        assert(res[1] == 4)
        assert(len(res[0]) == res[1])
        assert(client.getProjectSearchResults('Snoo')[1] == 2)
        assert(client.getProjectSearchResults('Camp Town Racers sing this song... doo dah... doo dah...') == ([], 0) )
        assert(client.getProjectSearchResults('snooze OR Boo')[1] == 2)

    def testSearchProjectOrder(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        zId = client.newProject("Zarumba Project", "zarumba", "rpath.org")
        self._changeTimestamps(zId, 1128540046, 1128540046)
        bId = client.newProject("Banjo Project", "banjo", "rpath.org")
        self._changeTimestamps(bId, 1124540046, 1124540046)
        aId = client.newProject("Animal Project", "animal", "rpath.org")
        self._changeTimestamps(aId, 1124540046, 1124540046)

        rId = client.newProject("rPath Project", "rpath1", "rpath.org")
        self._changeTimestamps(rId, 1124540046, 1124540046)

        projectList, len= client.getProjectSearchResults('Project')

        self.failIf([x[1] for x in projectList] != \
                    ['animal', 'banjo', 'rpath1','zarumba'],
                    "search results not in alphabetical order")

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
        self._fakePackage(projectId, "BarBotIcs")
        assert(client.getPackageSearchResults('broken') == ([['brokenPackage', 'whoCares', 1]], 1))
        assert client.getPackageSearchResults('foo')[1] == 2, "substring match failed"
        assert client.getPackageSearchResults('barbot')[1] == 1, "case-insensitive match failed"

    def testSearchEmpty(self):
        search = searcher.Searcher()
        # empty search
        self.assertRaises(searcher.SearchTermsError,
                          search.where, '', ['foo', 'bar'])

    def testSearchDefuntToken(self):
        search = searcher.Searcher()
        # empty token
        self.assertRaises(searcher.SearchTermsError,
                          search.where, '""', ['foo', 'bar'])

if __name__ == "__main__":
    testsuite.main()
