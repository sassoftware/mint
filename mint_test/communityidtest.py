#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time
import tempfile

import fixtures

from mint.db import communityids
from mint import communitytypes

class CommunityIdsTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testBuildData(self, db, data):
        client = self.getClient('admin')
        self.failIf(client.getCommunityId(1, communitytypes.VMWARE_VAM), 
                     'Value returned when not present.')
        client.setCommunityId(1, communitytypes.VMWARE_VAM, '1000')
        client.setCommunityId(2, communitytypes.VMWARE_VAM, '20abc')
        id = client.getCommunityId(1, communitytypes.VMWARE_VAM)
        self.failIf(id != '1000', "Incorrect id returned")
        client.setCommunityId(1, communitytypes.VMWARE_VAM, 'cat')
        id = client.getCommunityId(1, communitytypes.VMWARE_VAM)
        self.failIf(id != 'cat', "Incorrect id returned")
        id = client.getCommunityId(2, communitytypes.VMWARE_VAM)
        self.failIf(id != '20abc', "Incorrect id returned")
        client.deleteCommunityId(1, communitytypes.VMWARE_VAM)
        id = client.getCommunityId(1, communitytypes.VMWARE_VAM)
        self.failIf(client.getCommunityId(1, communitytypes.VMWARE_VAM), 
                     'Value returned when not present.')
        id = client.getCommunityId(2, communitytypes.VMWARE_VAM)
        self.failIf(id != '20abc', "Incorrect id returned")

if __name__ == "__main__":
    testsuite.main()
