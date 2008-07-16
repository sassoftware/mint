#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures

from mint import buildtypes
from mint.data import RDT_BOOL


class GlobusTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testGetAllGlobusBuilds(self, db, data):
        client = self.getClient("admin")
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [])
        cu = db.cursor()
        buildId = data['buildId']
        # now set the build type to raw filesystem image
        # this is still a no-go test, we need XEN_DOMU
        cu.execute('UPDATE Builds SET buildType=? WHERE buildId=?',
                buildtypes.RAW_FS_IMAGE, buildId)
        db.commit()
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [])
        build = client.getBuild(buildId)
        build.setDataValue('XEN_DOMU', True, RDT_BOOL, validate = False)
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [{'productDescription': '',
                                            'buildId': 1,
                                            'projectId': 1,
                                            'isPublished': 0,
                                            'buildDescription': '',
                                            'productName': 'Foo',
                                            'isPrivate': 0,
                                            'role': '',
                                            'createdBy': 'owner',
                                            'buildName': 'Test Build'}])

        client = self.getClient("owner")
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [{'productDescription': '',
                                            'buildId': 1,
                                            'projectId': 1,
                                            'isPublished': 0,
                                            'buildDescription': '',
                                            'productName': 'Foo',
                                            'isPrivate': 0,
                                            'role': 'Product Owner',
                                            'createdBy': 'owner',
                                            'buildName': 'Test Build'}])

    @fixtures.fixture('Full')
    def testHiddenVisibility(self, db, data):
        client = self.getClient("admin")
        client.hideProject(data['projectId'])
        buildId = data['buildId']
        cu = db.cursor()
        cu.execute('UPDATE Builds SET buildType=? WHERE buildId=?',
                buildtypes.RAW_FS_IMAGE, buildId)
        db.commit()
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [])
        build = client.getBuild(buildId)
        build.setDataValue('XEN_DOMU', True, RDT_BOOL, validate = False)
        db.commit()
        buildList = client.getAllGlobusBuilds()
        self.failIf(len(buildList) != 1)
        client = self.getClient('nobody')
        buildList = client.getAllGlobusBuilds()
        self.assertEquals(buildList, [])


if __name__ == '__main__':
    testsuite.main()
