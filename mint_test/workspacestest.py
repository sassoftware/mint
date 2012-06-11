#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures

from mint import buildtypes
from mint.lib.data import RDT_BOOL

# arbitrary sha1 is trhe sha1 of nothing for when it doesn't matter
fakeSha1 = 'da39a3ee5e6b4b0d3255bfef95601890afd80709'


class VwsTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testGetAllVwsBuilds(self, db, data):
        client = self.getClient("admin")
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.assertEquals(buildList, {})
        cu = db.cursor()
        buildId = data['buildId']
        cu.execute('UPDATE BuildFiles SET sha1=?', fakeSha1)
        # now set the build type to raw filesystem image
        # this is still a no-go test, we need XEN_DOMU
        cu.execute('UPDATE Builds SET buildType=? WHERE buildId=?',
                buildtypes.RAW_FS_IMAGE, buildId)
        db.commit()
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.assertEquals(buildList, {})
        build = client.getBuild(buildId)
        build.setDataValue('XEN_DOMU', True, RDT_BOOL, validate = False)
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x.pop('sha1'), x) for x in buildList)
        self.assertEquals(buildList,
                {fakeSha1: {'productDescription': '',
                    'buildId': 1,
                    'projectId': 1,
                    'isPublished': 0,
                    'buildDescription': '',
                    'productName': 'Foo',
                    'isPrivate': 0,
                    'role': '',
                    'createdBy': 'owner',
                    'buildName': 'Test Build',
                    'files': [
                         {'downloadUrl': 'http://test.rpath.local/downloadImage?fileId=1',
                          'sha1': 'da39a3ee5e6b4b0d3255bfef95601890afd80709',
                          'filename': 'file', 'idx': 0, 'size': '0'}
                        ],
                    'buildPageUrl':
                            'http://test.rpath.local/project/foo/build?id=1',
                    'downloadUrl':
                            'http://test.rpath.local/downloadImage?fileId=1',
                    'baseFileName': 'foo-1.1-x86_64' }})

        client = self.getClient("owner")
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.assertEquals(buildList[fakeSha1]['role'], 'Product Owner')

    @fixtures.fixture('Full')
    def testHiddenVisibility(self, db, data):
        client = self.getClient("admin")
        client.hideProject(data['projectId'])
        buildId = data['buildId']
        cu = db.cursor()
        cu.execute('UPDATE BuildFiles SET sha1=?', fakeSha1)
        cu.execute('UPDATE Builds SET buildType=? WHERE buildId=?',
                buildtypes.RAW_FS_IMAGE, buildId)
        db.commit()
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.assertEquals(buildList, {})
        build = client.getBuild(buildId)
        build.setDataValue('XEN_DOMU', True, RDT_BOOL, validate = False)
        db.commit()
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.failIf(len(buildList) != 1)
        client = self.getClient('nobody')
        buildList = client.getAllBuildsByType('VWS')
        buildList = dict((x['sha1'], x) for x in buildList)
        self.assertEquals(buildList, {})


if __name__ == '__main__':
    testsuite.main()
