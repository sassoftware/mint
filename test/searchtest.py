#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
import unittest
testsuite.setup()

import fixtures

from mint.projectlisting import PROJECTNAME_ASC, PROJECTNAME_DES, \
    LASTMODIFIED_ASC, LASTMODIFIED_DES, CREATED_ASC, CREATED_DES, \
    NUMDEVELOPERS_ASC, NUMDEVELOPERS_DES, ACTIVITY_ASC, ACTIVITY_DES
from mint.projectlisting import ordersql
from mint import buildtypes
from mint import userlevels
from mint import searcher
from mint import pkgindex

class SearchHelperTest(unittest.TestCase):
    def testParseTerms(self):
        self.failUnlessEqual(
            searcher.parseTerms("httpd branch=rpl:1"),
            (['httpd'], ['branch=rpl:1']))

        self.failUnlessEqual(
            searcher.parseTerms("httpd"),
            (['httpd'], []))

        self.failUnlessEqual(
            searcher.parseTerms("server=conary.rpath.com"),
            ([], ['server=conary.rpath.com']))

    def testLimitersToSQL(self):
        self.failUnlessEqual(
            searcher.limitersToSQL(["server=conary.rpath.com"], pkgindex.termMap),
            (" AND serverName=?", ['conary.rpath.com']))

        self.failUnlessEqual(
            searcher.limitersToSQL(["server=conary.rpath.com", "branch=rpl:1"], pkgindex.termMap),
            (" AND serverName=? AND branchName=?", ['conary.rpath.com', 'rpl:1']))

        # don't fail on unknown limiters
        self.failUnlessEqual(
            searcher.limitersToSQL(["server=conary.rpath.com", "frobnitz=blah"], pkgindex.termMap),
            (" AND serverName=?", ['conary.rpath.com']))

    def testLimitersForDisplay(self):
        self.failUnlessEqual(
            searcher.limitersForDisplay("foo bar baz=biz"),
            ([{'newSearch': 'foo bar', 'desc': 'baz is biz'}], ['foo', 'bar']))

        self.failUnlessEqual(
            searcher.limitersForDisplay("foo bar"),
            ([], ['foo', 'bar']))

    def testSearchEmpty(self):
        search = searcher.Searcher()
        # empty search
        self.assertRaises(searcher.SearchTermsError,
                          search.where, '', ['foo', 'bar'])

    def testSearchDefunctToken(self):
        search = searcher.Searcher()
        # empty token
        self.assertRaises(searcher.SearchTermsError,
                          search.where, '""', ['foo', 'bar'])

    def testExactResults(self):
        search = searcher.Searcher()
        self.failIf(search.order('foo OR bar', ['name']) != \
                    "UPPER(name)<>'BAR', UPPER(name)<>'FOO'",
                    "order is incorrect")

    def testOrderFilter(self):
        search = searcher.Searcher()
        self.failIf(search.order(';8 or a', ['name']) != "UPPER(name)<>'A'",
                    "invalid token was allowed")

    def testFilterAllTokens(self):
        search = searcher.Searcher()
        self.failIf(search.order(';', ['name']) != "",
                    "empty token and extra parsing combined incorrectly")
        self.failIf(search.order(';', ['name'], 'name') != "name",
                    "token and extra parsing combined incorrectly")

    def testExtraOrder(self):
        search = searcher.Searcher()
        self.failIf(search.order('a', ['name'], 'name') != \
                    "UPPER(name)<>'A', name",
                    "extra term disregaded")


class BrowseTest(fixtures.FixturedUnitTest):
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

        r = cu.execute("INSERT INTO PackageIndex VALUES(?, ?, ?, 'whoCares', 'who', 'cares', 0)", (pkgId, projectId, name))
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

    @fixtures.fixture("Empty")
    def testBrowse(self, db, data):
        self.db = db
        client, userId = self.getClient('admin'), data['admin']

        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")

        barId = client.newProject("Bar", "bar", "rpath.org")
        self._changeTimestamps(barId, 1124540046, 1124540046)
        bazId = client.newProject("Baz", "baz", "rpath.org")
        self._changeTimestamps(bazId, 1126540046, 1126640046)
        balId = client.newProject("Bal", "bal", "rpath.org")
        self._changeTimestamps(balId, 1128540003, 1129540003)
        bizId = client.newProject("Biz", "biz", "rpath.org")
        self._changeTimestamps(balId, 1128540003, 1129540003)

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

        bazProject.addMemberById(userId3, userlevels. DEVELOPER)

        balProject.addMemberById(userId3, userlevels. DEVELOPER)
        balProject.addMemberById(userId4, userlevels. DEVELOPER)

        sortOrderDict = self._sortOrderDict()
        for sortOrder in range(10):
            # For admins, all projects should be returned
            results, count = client.getProjects(sortOrder, 30, 0)
            self.failUnlessEqual(count, 4, msg = 'getProjects returned the wrong project count (admin).')

            # For non-admins, hidden/fledglings should be ignored
            results, count = client2.getProjects(sortOrder, 30, 0)
            self.failUnlessEqual(count, 4, msg = 'getProjects returned the wrong project count.')

            self.failUnlessEqual([x[1] for x in results], sortOrderDict[sortOrder])

        self.failUnlessEqual(client.getProjectsList(),
            [(balId, 0, 'bal - Bal'), (barId, 0, 'bar - Bar'), (bazId, 0, 'baz - Baz'), (bizId, 0, 'biz - Biz')])

    @fixtures.fixture("Empty")
    def testFledgling(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

        hideFledgling = self.cfg.hideFledgling
        try:
            projectId = client.newProject("Bar", "bar", "rpath.org")
            self._changeTimestamps(projectId, 1124540046, 1124540046)

            self.cfg.hideFledgling = False
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Fledgling projects not counted in project list")

            self.cfg.hideFledgling = True
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1],
                        "Fledgling projects counted in project list")

            # add a fake commit to trigger non-fledgling status
            self._fakeCommit(projectId, 1129550003, userId)

            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Non fledgling project didn't show up")

        finally:
            self.cfg.hideFledgling = hideFledgling

    @fixtures.fixture("Empty")
    def testExternal(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

        hideFledgling = self.cfg.hideFledgling
        try:
            projectId = client.newProject("Bar", "bar", "rpath.org")
            self._changeTimestamps(projectId, 1124540046, 1124540046)

            self.cfg.hideFledgling = False
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "Fledgling projects not counted in project list")

            self.cfg.hideFledgling = True
            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1],
                        "Fledgling projects counted in project list")

            # alter project to appear to be external
            cu = self.db.cursor()
            cu.execute("UPDATE Projects set external=1")
            self.db.commit()

            self.failIf(client.getProjects(PROJECTNAME_ASC, 30, 0)[1] != 1,
                        "external project counted as fledgling")
        finally:
            self.cfg.hideFledgling = hideFledgling

    @fixtures.fixture("Empty")
    def testSearchProjects(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

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


    @fixtures.fixture("Empty")
    def testSearchProjectOrder(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

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

    @fixtures.fixture("Empty")
    def testSearchUsers(self, db, data):
        client, userId = self.getClient('test'), data['test']
        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")

        self.failUnlessEqual(len(client.getUserSearchResults('test')[0]), 4)
        # XXX we do this because search results now returns timestamps
        self.failUnlessEqual(client.getUserSearchResults('er3')[0][0][0:4],
            [userId3, 'testuser3', 'Test User', 'test at example.com'])
        self.failUnlessEqual(client.getUserSearchResults('Sir Not Appearing In This Film'), ([], 0))

    @fixtures.fixture("Empty")
    def testSearchPackages(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

        projectId = client.newProject("Foo", "foo", "rpath.org")
        self._fakePackage(projectId, "brokenPackage")
        self._fakePackage(projectId, "foomatic")
        self._fakePackage(projectId, "barmatic")
        self._fakePackage(projectId, "foobar")
        self._fakePackage(projectId, "BarBotIcs")
        self.failUnlessEqual(client.getPackageSearchResults('broken'),
            ([['brokenPackage', 'whoCares', 1]], 1))
        self.failUnlessEqual(client.getPackageSearchResults('foo')[1], 2)
        self.failUnlessEqual(client.getPackageSearchResults('barbot')[1], 1)

    @fixtures.fixture("Full")
    def testSearchProjectsWithBuilds(self, db, data):
        client, userId = self.getClient('admin'), data['admin']
        self.db = db

        self._changeTimestamps(data['projectId'], 1128540046, 1128540046)

        x = client.getProjectSearchResults("buildtype=2")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046]], 1))

        x = client.getProjectSearchResults("buildtype=0")
        self.failUnlessEqual(x, ([], 0))

        x = client.getProjectSearchResults("buildtype=0 buildtype=2")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046]], 1))

        build = client.getBuild(data['buildId'])
        build.setTrove("group-dist", str(build.getTroveVersion()), "1#x86|5#use:xen:domU")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.addBuild(build.id)
        pubRelease.publish()

        # create another project
        projectId = client.newProject("Bar", "bar", "rpath.org")
        self._changeTimestamps(projectId, 1128540046, 1128540046)
        rel2 = client.newPublishedRelease(projectId)
        build = client.newBuild(projectId, "Test Published Build")
        build.setTrove("group-dist", "localhost@rpl:devel/0.0:1.0-1-1", "1#x86|5#use:appliance")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])
        rel2.addBuild(build.id)
        rel2.publish()

        x = client.getProjectSearchResults("buildtype=100")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046]], 1))

        # broken search queries shouldn't traceback
        x = client.getProjectSearchResults("b buildtype=")
        self.failUnlessEqual(x, ([[projectId, 'bar', 'Bar', '', 1128540046]], 1))
        x = client.getProjectSearchResults("b =101")
        self.failUnlessEqual(x, ([[projectId, 'bar', 'Bar', '', 1128540046]], 1))

        # search for two different flavor flags
        x = client.getProjectSearchResults("buildtype=100 buildtype=101")
        self.failUnlessEqual(([[2, 'bar', 'Bar', '', 1128540046.0],
                               [1, 'foo', 'Foo', '', 1128540046.0]], 2), x)

        # search for a build type and a flavor flag
        x = client.getProjectSearchResults("buildtype=2 buildtype=101")
        self.failUnlessEqual(([[2, 'bar', 'Bar', '', 1128540046.0],
                               [1, 'foo', 'Foo', '', 1128540046.0]], 2), x)


if __name__ == "__main__":
    testsuite.main()
