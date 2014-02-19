#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
import time

import unittest

import fixtures

from mint import buildtypes
from mint import userlevels
from mint import searcher
from mint.db import pkgindex

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

        self.failUnlessEqual(
            searcher.parseTerms("server=conary.rpath.com", ['server']),
            ([], ['server=conary.rpath.com']))
        self.failUnlessEqual(
            searcher.parseTerms("server=conary.rpath.com", ['server2']),
            (['server=conary.rpath.com'], []))

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
            searcher.limitersForDisplay("foo bar baz= =zab"),
            ([], ['foo', 'bar']))

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

    def testParseLimiters(self):
        self.failUnlessEqual(
            searcher.parseLimiters("foo=bar baz=biz =wak bak=",
                                   ['foo', 'baz', 'bak']),
            [('foo', 'bar'), ('baz', 'biz')]
        )

    def testLastModified(self):
        search = searcher.Searcher()

        oldTime = time.time
        time.time = lambda x = 100: x
        self.failUnlessEqual(
            search.lastModified(100, searcher.THREEDAYS),
            '100 > (100 - 259200)')
        time.time = oldTime

    def testTruncate(self):
        search = searcher.Searcher()

        ls = "this is a very long string that has many many words. "\
             "it goes on and on and never ends, until we hit the far "\
             "side of the screen. still going!"

        self.failUnlessEqual(search.truncate(None, "frob"), "")
        shortened = '...has many many words. it goes on and on and never '\
                    'ends, until we hit the far side of the screen....'
        self.failUnlessEqual(search.truncate(ls, "never"), shortened)

    def testWhere(self):
        search = searcher.Searcher()

        x = search.where('"this is" "a test"', ['bah'])
        self.failUnlessEqual(x, ('WHERE (UPPER(bah) LIKE UPPER(?) ) '\
                                 ' AND (UPPER(bah) LIKE UPPER(?) ) '\
                                 ' AND (UPPER(bah) LIKE UPPER(?) ) '\
                                 ' AND (UPPER(bah) LIKE UPPER(?) ) '\
                                 ' AND (UPPER(bah) LIKE UPPER(?) )',
                                 ['%this%', '%is%', '% %', '%a%', '%test%']))

class BrowseTest(fixtures.FixturedUnitTest):
    def _changeTimestamps(self, projectId, timeCreated, timeModified):
        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET timeCreated=?, timeModified=? WHERE projectId=?", timeCreated, timeModified, projectId)

        # normalize published release times if already published
        cu.execute("SELECT pubReleaseId, timePublished FROM PublishedReleases WHERE projectId=?", projectId)
        for x in cu.fetchall():
            if x[1]:
                cu.execute("UPDATE PublishedReleases SET timePublished=? WHERE pubReleaseId=?", timeModified, x[0])

        self.db.commit()

    def _fakeCommit(self, projectId, timestamp, userId):
        cu = self.db.cursor()
        r = cu.execute("INSERT INTO Commits VALUES(?, ?, 'whoCares', '1.0', ?)", projectId, timestamp, userId)
        self.db.commit()

    def _fakePackage(self, projectId, name):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE(MAX(pkgId) + 1, 1) FROM PackageIndex")
        pkgId = cu.fetchone()[0]

        r = cu.execute("INSERT INTO PackageIndex VALUES(?, ?, ?, 'whoCares', 'who', 'cares', 0)", (pkgId, projectId, name))
        self.db.commit()

    @fixtures.fixture("Empty")
    def testBrowse(self, db, data):
        self.db = db
        client, userId = self.getClient('admin'), data['admin']

        client2, userId2 = self.quickMintUser("testuser2", "testpass")
        client3, userId3 = self.quickMintUser("testuser3", "testpass")
        client4, userId4 = self.quickMintUser("testuser4", "testpass")

        barId = client.newProject("Bar", "bar", "rpath.org", 
                        shortname="bar", version="1.0", prodtype="Component")
        self._changeTimestamps(barId, 1124540046, 1124540046)
        bazId = client.newProject("Baz", "baz", "rpath.org",
                        shortname="baz", version="1.0", prodtype="Component")
        self._changeTimestamps(bazId, 1126540046, 1126640046)
        balId = client.newProject("Bal", "bal", "rpath.org",
                        shortname="bal", version="1.0", prodtype="Component")
        self._changeTimestamps(balId, 1128540003, 1129540003)
        bizId = client.newProject("Biz", "biz", "rpath.org",
                        shortname="biz", version="1.0", prodtype="Component")
        self._changeTimestamps(bizId, 1128540003, 1129540003)

        self.failUnlessEqual(client.getNewProjects(10, True),
            [[3, 'bal', 'Bal', '', 1129540003], [4, 'biz', 'Biz', '', 1129540003],
             [2, 'baz', 'Baz', '', 1126640046], [1, 'bar', 'Bar', '', 1124540046]])

        self.failUnlessEqual(client.getNewProjects(10, False), [])

        self._fakeCommit(barId, 1124540047, userId2)

        self.failUnlessEqual(client.getNewProjects(10, False),
            [[1, 'bar', 'Bar', '', 1124540046]])

    @fixtures.fixture("Empty")
    def testSearchProjects(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

        fooId = client.newProject("Foo Project", "foo", "rpath.org",
                        shortname="foo", version="1.0", prodtype="Component")
        self._changeTimestamps(fooId, 1128540046, 1128540046)
        booId = client.newProject("Boo Project", "boo", "rpath.org",
                        shortname="boo", version="1.0", prodtype="Component")
        self._changeTimestamps(booId, 1124540046, 1124540046)
        snoozeId = client.newProject("Snooze Project", "snooze", "rpath.org",
                        shortname="snooze", version="1.0", prodtype="Component")
        self._changeTimestamps(snoozeId, 1126540046, 1126640046)
        snoofId = client.newProject("Snoof Project", "snoof", "rpath.org",
                        shortname="snoof", version="1.0", prodtype="Component")
        self._changeTimestamps(snoofId, 1128540003, 1129540003)

        if client.getProjectSearchResults('Foo') != ([[1, 'foo', 'Foo Project', '', 1128540046, 4, 0]], 1):
            self.fail("Search for 'Foo' did not return the correct results.")
        res = client.getProjectSearchResults('Project')
        assert(res[1] == 4)
        assert(len(res[0]) == res[1])
        assert(client.getProjectSearchResults('Snoo')[1] == 2)
        assert(client.getProjectSearchResults('Camp Town Racers sing this song... doo dah... doo dah...') == ([], 0) )
        assert(client.getProjectSearchResults('snooze OR Boo')[1] == 2)
        assert(client.getProjectSearchResults('snooze OR Boo')[1] == 2)

    @fixtures.fixture("Empty")
    def testSearchProjectOrder(self, db, data):
        self.db = db
        client, userId = self.getClient('test'), data['test']

        zId = client.newProject("Zarumba Project", "zarumba", "rpath.org",
                        shortname="zarumba", version="1.0", 
                        prodtype="Component")
        self._changeTimestamps(zId, 1128540046, 1128540046)
        bId = client.newProject("Banjo Project", "banjo", "rpath.org",
                        shortname="banjo", version="1.0", prodtype="Component")
        self._changeTimestamps(bId, 1124540046, 1124540046)
        aId = client.newProject("Animal Project", "animal", "rpath.org",
                        shortname="animal", version="1.0", prodtype="Component")
        self._changeTimestamps(aId, 1124540046, 1124540046)

        rId = client.newProject("rPath Project", "rpath1", "rpath.org",
                        shortname="rpath1", version="1.0", prodtype="Component")
        self._changeTimestamps(rId, 1124540046, 1124540046)

        projectList, len= client.getProjectSearchResults('Project', byPopularity = False)

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

        projectId = client.newProject("Foo", "foo", "rpath.org",
                        shortname="foo", version="1.0", prodtype="Component")
        self._fakePackage(projectId, "brokenPackage")
        self._fakePackage(projectId, "foomatic")
        self._fakePackage(projectId, "barmatic")
        self._fakePackage(projectId, "foobar")
        self._fakePackage(projectId, "BarBotIcs")
        self._fakePackage(projectId, "BarBotIcs:source")
        self.failUnlessEqual(client.getPackageSearchResults('broken'),
            ([['brokenPackage', 'whoCares', 1]], 1))
        self.failUnlessEqual(client.getPackageSearchResults('foo')[1], 2)
        self.failUnlessEqual(client.getPackageSearchResults('barbot')[1], 2)
        self.failUnlessEqual(client.getPackageSearchResults(':source')[1], 1)
        self.failUnlessEqual(client.getPackageSearchResults('foo=conary.rpath.com@rpl:1')[1], 0)

    @fixtures.fixture("Full")
    def testSearchProjectsWithBuilds(self, db, data):
        client, userId = self.getClient('admin'), data['admin']
        self.db = db

        self._changeTimestamps(data['projectId'], 1128540046, 1128540046)

        x = client.getProjectSearchResults("buildtype=2")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046, 1, 1128540046]], 1))

        x = client.getProjectSearchResults("buildtype=0")
        self.failUnlessEqual(x, ([], 0))

        x = client.getProjectSearchResults("buildtype=0 buildtype=2")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046, 1, 1128540046]], 1))

        build = client.getBuild(data['buildId'])
        build.setTrove("group-dist", str(build.getTroveVersion()), "1#x86|5#use:xen:domU")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.addBuild(build.id)
        pubRelease.publish()

        # create another project
        projectId = client.newProject("Bar", "bar", "rpath.org",
                        shortname="bar", version="1.0", prodtype="Component")
        rel2 = client.newPublishedRelease(projectId)
        build = client.newBuild(projectId, "Test Published Build")
        build.setTrove("group-dist", "/localhost@rpl:devel/0.0:1.0-1-1", "1#x86|5#use:appliance")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])
        rel2.addBuild(build.id)
        rel2.publish()

        self._changeTimestamps(projectId, 1128540046, 1128540046)
        self._changeTimestamps(data['projectId'], 1128540046, 1128540046)


        x = client.getProjectSearchResults("buildtype=100")
        self.failUnlessEqual(x, ([[data['projectId'], 'foo', 'Foo', '', 1128540046, 2, 1128540046]], 1))

        # broken search queries shouldn't traceback
        x = client.getProjectSearchResults("b buildtype=")
        self.failUnlessEqual(x, ([[projectId, 'bar', 'Bar', '', 1128540046, 2, 1128540046]], 1))
        # this is just a bad search term now so no results
        x = client.getProjectSearchResults("b =101")
        self.failUnlessEqual(x, ([], 0))

        # search for two different flavor flags
        x = client.getProjectSearchResults("buildtype=100 buildtype=101")
        self.failUnlessEqual(([[1, 'foo', 'Foo', '', 1128540046.0, 2, 1128540046],
                               [2, 'bar', 'Bar', '', 1128540046.0, 2, 1128540046]], 2), x)

        # search for a build type and a flavor flag
        x = client.getProjectSearchResults("buildtype=2 buildtype=101")
        self.failUnlessEqual(([[1, 'foo', 'Foo', '', 1128540046.0, 2, 1128540046],
                               [2, 'bar', 'Bar', '', 1128540046.0, 2, 1128540046]], 2), x)

        # test filterNoDownloads
        x = client.getProjectSearchResults("", filterNoDownloads = True)
        self.failUnlessEqual(([[1, 'foo', 'Foo', '', 1128540046.0, 2, 1128540046],
                               [2, 'bar', 'Bar', '', 1128540046.0, 2, 1128540046]], 2), x)


