#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import time
import fixtures
from mint import mint_error
import mint.scripts.selections
from mint import selections
from mint.helperfuncs import toDatabaseTimestamp

class MarketingTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Empty")
    def testFrontPageSelections(self, db, data):
        adminClient = self.getClient("admin")
        ownerClient = self.getClient("owner")
        developerClient = self.getClient("developer")
        userClient = self.getClient("user")
        nobodyClient = self.getClient("nobody")

        try:
            nobodyClient.addFrontPageSelection('test name', 'test link', 7) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            userClient.addFrontPageSelection('test name', 'test link', 7) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            developerClient.addFrontPageSelection('test name', 'test link', 7) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            ownerClient.addFrontPageSelection('test name', 'test link', 7) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        adminClient.addFrontPageSelection('test name', 'test link', 7) 

        selection = adminClient.getFrontPageSelection()[0]['itemId']
        try:
            nobodyClient.deleteFrontPageSelection(selection) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            userClient.deleteFrontPageSelection(selection) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            developerClient.deleteFrontPageSelection(selection) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            ownerClient.deleteFrontPageSelection(selection) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")

        adminClient.deleteFrontPageSelection(selection)

        adminClient.addFrontPageSelection('test1', 'link1', 1)
        adminClient.addFrontPageSelection('test4', 'link4', 4)
        adminClient.addFrontPageSelection('test3', 'link3', 3)
        adminClient.addFrontPageSelection('test2', 'link2', 2)
        adminClient.addFrontPageSelection('test5', 'link5', 5)

        selections = nobodyClient.getFrontPageSelection()
        for x in range(len(selections)):
            selections[x].pop('itemId')
        self.failIf(not selections == [{'link': 'link1', 'name': 'test1', 
                                       'rank': 1}, {'link': 'link2',
                                       'name': 'test2', 'rank': 2},
                                       {'link': 'link3', 'name': 'test3', 
                                       'rank': 3}, {'link': 'link4', 
                                       'name': 'test4', 'rank': 4}, 
                                       {'link': 'link5', 'name': 'test5', 
                                       'rank': 5}],
                    "getFrontPageSelection returned bad data")

    @fixtures.fixture('Empty')
    def testRankedProjectTables(self, db, data):
        db.loadSchema()
        topProjects = selections.TopProjectsTable(db)
        client = self.getClient('admin')

        p1 = client.newProject('p1', 'p1', 'localhost', shortname='p1',
                version="1.0", prodtype="Component")
        p2 = client.newProject('p2', 'p2', 'localhost', shortname='p2',
                version="1.0", prodtype="Component")
        p3 = client.newProject('p3', 'p3', 'localhost', shortname='p3',
                version="1.0", prodtype="Component")

        topProjects.setList([p1, p3, p2])
        self.failUnlessEqual(topProjects.getList(),
            [{'projectId': 1, 'hostname': 'p1', 'name': 'p1'},
             {'projectId': 3, 'hostname': 'p3', 'name': 'p3'},
             {'projectId': 2, 'hostname': 'p2', 'name': 'p2'}])

    @fixtures.fixture('Full')
    def testProjectCalculation(self, db, data):
        client = self.getClient('admin')
        p2 = client.newProject('p2', 'p2', 'localhost', shortname="p2",
                version="1.0", prodtype="Component")
        p3 = client.newProject('p3', 'p3', 'localhost', shortname="p3",
                version="1.0", prodtype="Component")

        projects = [data['projectId'], p3, p2]
        builds = [data['buildId'], data['pubBuildId'], data['anotherBuildId']]
        cu = db.cursor()
        for buildId, projectId, count in zip(builds, projects, [10, 20, 30]):
            # assuming urlId == buildId...
            for c in range(count):
                cu.execute("INSERT INTO UrlDownloads VALUES (?, ?, '127.0.0.1')",
                    buildId, toDatabaseTimestamp(time.time()))
            cu.execute("UPDATE Builds SET projectId=? WHERE buildId=?", projectId, buildId)
        db.commit()

        db.loadSchema()
        topProjects = selections.TopProjectsTable(db)
        topProjects.calculate()

        l = topProjects.getList()
        self.failUnlessEqual([x['projectId'] for x in l], [p2, p3, data['projectId']])

        # test the update script mechanism
        upl = mint.scripts.selections.UpdateProjectLists()
        upl.logPath = None
        upl.cfg = self.cfg
        upl.run()

        l = topProjects.getList()
        self.failUnlessEqual([x['projectId'] for x in l], [p2, p3, data['projectId']])


if __name__ == "__main__":
    testsuite.main()
