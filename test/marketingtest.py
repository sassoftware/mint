#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import time
import fixtures
from mint import mint_error
from mint import selections

from conary.dbstore.sqllib import toDatabaseTimestamp

class MarketingTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Empty")
    def testSpotlight(self, db, data):
        adminClient = self.getClient("admin")
        ownerClient = self.getClient("owner")
        developerClient = self.getClient("developer")
        userClient = self.getClient("user")
        nobodyClient = self.getClient("nobody")

        # addSpotlightItem: insure admin only
        startDate = time.strftime('%m/%d/%Y', time.localtime())
        endDate = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 2))
        try:
            nobodyClient.addSpotlightItem('test title', 'test text', 'test url',
                                          "", 0, startDate, endDate)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")

        try:
            userClient.addSpotlightItem('test title', 'test text', 'test url',
                                        "", 0, startDate, endDate)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")

        try:
            developerClient.addSpotlightItem('test title', 'test text', 
                                             'test url', "", 0, startDate, 
                                             endDate)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")

        try:
            ownerClient.addSpotlightItem('test title', 'test text', 'test url',
                                         "", 0, startDate, endDate)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")

        adminClient.addSpotlightItem('test title', 'test text', 'test url',
                                         "", 0, startDate, endDate)


        # deleteSpotlightItem: insure admin only
        itemId = nobodyClient.getCurrentSpotlight()['itemId']
        try:
            nobodyClient.deleteSpotlightItem(itemId)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail()

        try:
            userClient.deleteSpotlightItem(itemId)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail()

        try:
            developerClient.deleteSpotlightItem(itemId)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail()

        try:
            ownerClient.deleteSpotlightItem(itemId)
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail()

        adminClient.deleteSpotlightItem(itemId)

        # test that everyone can access getSpotlightAll and getCurrentSpotlight
        adminClient.addSpotlightItem('test title', 'test text', 'test url',
                                     "", 0, startDate, endDate)
        nobodyClient.getCurrentSpotlight()
        nobodyClient.getSpotlightAll()
        userClient.getCurrentSpotlight()
        userClient.getSpotlightAll()
        developerClient.getCurrentSpotlight()
        developerClient.getSpotlightAll()
        ownerClient.getCurrentSpotlight()
        ownerClient.getSpotlightAll()
        adminClient.getCurrentSpotlight()
        adminClient.getSpotlightAll()

        itemId = nobodyClient.getCurrentSpotlight()['itemId']
        adminClient.deleteSpotlightItem(itemId)

        # test addSpotlightItem
        minus6 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() - 60 * 60 * 24 * 6))
        minus5 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() - 60 * 60 * 24 * 5))
        minus4 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() - 60 * 60 * 24 * 4))
        minus2 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() - 60 * 60 * 24 * 2))
        today = time.strftime('%m/%d/%Y', time.localtime())
        plus2 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 2))
        plus3 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 3))
        plus4 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 4))
        plus5 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 5))
        plus6 = time.strftime('%m/%d/%Y', 
                                time.gmtime(time.time() + 60 * 60 * 24 * 6))
        
        self.failIf(not adminClient.addSpotlightItem('title1', 'test text',
                                                     'test link', '', 1, today,
                                                     plus2), 
                    "Failed to add spotlight appliance.")
        self.failIf(not adminClient.addSpotlightItem('title2', 'test text',
                                                     'test link', '', 1, plus2,
                                                     plus3), 
                    "Failed to add spotlight appliance.")
        self.failIf(not adminClient.addSpotlightItem('title3', 'test text 3',
                                                     'linking', 'logo', 0,
                                                     minus6, today), 
                    "Failed to add spotlight appliance.")
        self.failIf(not adminClient.addSpotlightItem('title4', 'test text',
                                                     'test link', '', 1, 
                                                     '1/1/1990', minus6), 
                    "Failed to add spotlight appliance.")
        self.failIf(adminClient.addSpotlightItem('title6', 'test text',
                                                 'test link', 'logo', 1, 
                                                 plus6, plus5), 
                    "Added conflicted spotlight appliances.")
        self.failIf(adminClient.addSpotlightItem('title7', 'test text',
                                                 'test link', '', 1, 
                                                 plus6, plus6), 
                    "Added conflicted spotlight appliances.")
        self.failIf(adminClient.addSpotlightItem('title8', 'test text',
                                                 'test link', '', 1, 
                                                 minus5, minus4), 
                    "Added conflicted spotlight appliances.")
        self.failIf(adminClient.addSpotlightItem('title9', 'test text',
                                                 'test link', '', 1, 
                                                 plus2, plus4), 
                    "Added conflicted spotlight appliances.")
        self.failIf(adminClient.addSpotlightItem('title10', 'test text',
                                                 'test link', '', 1, 
                                                 minus2, plus3), 
                    "Added conflicted spotlight appliances.")
        self.failIf(not adminClient.addSpotlightItem('title11', 'test text',
                                                     'test link', '', 1, 
                                                     plus5, plus6), 
                    "Failed to add spotlight appliance.")

        # Check one complete entry and make a list of all titles
        data = nobodyClient.getSpotlightAll()
        titles = []
        for x in data:
            titles.append(x['title'])
            if x['title'] == 'title3':
                # Check the integrity of the data
                self.failIf(not self._checkSpotlightContents(x,
                            {'itemId': 5, 'startDate': minus6, 
                             'endDate': today, 'title': 'title3', 
                             'text': 'test text 3', 'showArchive': 0, 
                             'link': 'linking', 'logo': 'logo'}),
                             "Contents of table not as expected.")
        # Check the titles
        for x in ['1', '2', '3', '4', '11', ]:
            self.failIf('title%s' % x not in titles, 
                        "Contents of table not as expected.")
        self.failIf(len(data) != 5, "Too many items in table.")

        current = nobodyClient.getCurrentSpotlight()
        self.failIf(current['title'] != 'title1', 
                    "Failed to retreive current spotlight")
        self.failIf(not self._checkSpotlightContents(current,
                    {'itemId': 3, 'startDate': today, 
                     'endDate': plus2, 'title': 'title1', 
                     'text': 'test text', 'showArchive': 1, 
                     'link': 'test link', 'logo': ''}),
                    "Contents of table not as expected.")

        adminClient.deleteSpotlightItem(3)
        self.failIf(adminClient.getCurrentSpotlight(),
                    "Spotlight data returned when none present")
        
        for x in adminClient.getSpotlightAll():
            count = len(adminClient.getSpotlightAll())
            adminClient.deleteSpotlightItem(x['itemId'])
            if (count != 1 or adminClient.getSpotlightAll()):
                self.failIf(len(adminClient.getSpotlightAll()) != count - 1,
                            "Unable to delete spotlight item")

        self.failIf(adminClient.getSpotlightAll(),
                    "Error deleting spotlight items")

    def _checkSpotlightContents(self, data, test):
        test['startDate'] = int(time.mktime(time.strptime(test['startDate'], 
                                                      '%m/%d/%Y')))
        test['endDate'] = int(time.mktime(time.strptime(test['endDate'], 
                                                      '%m/%d/%Y')))
        test.pop('itemId')
        data.pop('itemId')

        return test == data

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

    @fixtures.fixture("Empty")
    def testUseIt(self, db, data):
        adminClient = self.getClient("admin")
        ownerClient = self.getClient("owner")
        developerClient = self.getClient("developer")
        userClient = self.getClient("user")
        nobodyClient = self.getClient("nobody") 

        try:
            nobodyClient.addUseItIcon(1, 'test name', 'test link') 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            ownerClient.addUseItIcon(1, 'test name', 'test link') 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            developerClient.addUseItIcon(1, 'test name', 'test link') 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            userClient.addUseItIcon(1, 'test name', 'test link') 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        adminClient.addUseItIcon(1, 'test name', 'test link')
        
        try:
            nobodyClient.deleteUseItIcon(1) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            userClient.deleteUseItIcon(1) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            developerClient.deleteUseItIcon(1) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        try:
            ownerClient.deleteUseItIcon(1) 
        except mint_error.PermissionDenied:
            pass
        else:
            self.fail("Allowed to access restricted resource while not admin.")
        adminClient.deleteUseItIcon(1)
        
        adminClient.addUseItIcon(1, 'test 1', 'link 1')
        adminClient.addUseItIcon(2, 'test 2', 'link 2')
        adminClient.addUseItIcon(5, 'test 5', 'link 5')

        icons = nobodyClient.getUseItIcons()
        icons.sort(lambda x,y: cmp(x['itemId'], y['itemId']))

        self.failIf(icons != [{'itemId': 1, 'link': 'link 1', 'name': 'test 1'},
                              {'itemId': 2, 'link': 'link 2', 'name': 'test 2'},
                              {'itemId': 5, 'link': 'link 5', 'name': 'test 5'}
                             ],
                    "getUseItIcons returned the wrong data")

        adminClient.addUseItIcon(3, 'test 3', 'link 3')
        icons = nobodyClient.getUseItIcons()
        icons.sort(lambda x,y: cmp(x['itemId'], y['itemId']))
        
        self.failIf(icons != [{'itemId': 1, 'link': 'link 1', 'name': 'test 1'},
                              {'itemId': 2, 'link': 'link 2', 'name': 'test 2'},
                              {'itemId': 3, 'link': 'link 3', 'name': 'test 3'},
                              {'itemId': 5, 'link': 'link 5', 'name': 'test 5'}
                             ],
                    "getUseItIcons returned the wrong data")
        adminClient.addUseItIcon(2, 'new 2', 'new link')

        icons = nobodyClient.getUseItIcons()
        icons.sort(lambda x,y: cmp(x['itemId'], y['itemId']))

        self.failIf(icons != [{'itemId': 1, 'link': 'link 1', 'name': 'test 1'},
                             {'itemId': 2, 'link': 'new link', 'name': 'new 2'},
                             {'itemId': 3, 'link': 'link 3', 'name': 'test 3'},
                             {'itemId': 5, 'link': 'link 5', 'name': 'test 5'}],
                    "getUseItIcons returned the wrong data")

        adminClient.deleteUseItIcon(3)
        adminClient.deleteUseItIcon(1)

        icons = nobodyClient.getUseItIcons()
        icons.sort(lambda x,y: cmp(x['itemId'], y['itemId']))
        self.failIf(icons != [{'itemId': 2, 'link': 'new link', 
                               'name': 'new 2'}, {'itemId': 5, 'link': 'link 5',
                                                  'name': 'test 5'}],
                    "deleteUseItIcons functioning improperly")

    @fixtures.fixture('Full')
    def testEmptyAddit(self, db, data):
        client = self.getClient('admin')
        self.failIf(client.addUseItIcon(1, '', ''),
                    "Allowed to submit an empty name and link")
        self.failIf(client.addUseItIcon(1, 'foo', ''),
                    "Allowed to submit an empty link")
        self.failIf(client.addUseItIcon(1, '', 'foo'),
                    "Allowed to submit an empty name")
        self.failIf(not client.addUseItIcon(1, 'foo', 'foo'),
                    "Valid submission not accepted")

    @fixtures.fixture('Empty')
    def testRankedProjectTables(self, db, data):
        db.loadSchema()
        topProjects = selections.TopProjectsTable(db)
        client = self.getClient('admin')

        p1 = client.newProject('p1', 'p1', 'localhost')
        p2 = client.newProject('p2', 'p2', 'localhost')
        p3 = client.newProject('p3', 'p3', 'localhost')

        topProjects.setList([p1, p3, p2])
        self.failUnlessEqual(topProjects.getList(),
            [{'projectId': 1, 'hostname': 'p1', 'name': 'p1'},
             {'projectId': 3, 'hostname': 'p3', 'name': 'p3'},
             {'projectId': 2, 'hostname': 'p2', 'name': 'p2'}])

    @fixtures.fixture('Full')
    def testProjectCalculation(self, db, data):
        client = self.getClient('admin')
        p2 = client.newProject('p2', 'p2', 'localhost')
        p3 = client.newProject('p3', 'p3', 'localhost')

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
        upl = selections.UpdateProjectLists()
        upl.logPath = None
        upl.cfg = self.cfg
        upl.run()

        l = topProjects.getList()
        self.failUnlessEqual([x['projectId'] for x in l], [p2, p3, data['projectId']])


if __name__ == "__main__":
    testsuite.main()
