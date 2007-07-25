#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import os

import mint_rephelp
import fixtures
from mint.web import site
from mint.data import RDT_STRING
from mint import database
from mint.web.webhandler import HttpNotFound, HttpMoved
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint import users

from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_HOST, FQDN

from conary import versions
from conary.lib import util

from mint_rephelp import FakeRequest

class FixturedProjectTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.sh = site.SiteHandler()
        self.sh.session = {}

        def fakeRedirect(*args, **kwargs):
            raise HttpMoved

        self.sh._redirect = fakeRedirect

    @fixtures.fixture('Full')
    def testUploadBuild(self, db, data):
        client = self.getClient("developer")
        p = client.getProject(data['projectId'])
        b = client.getBuild(data['anotherBuildId'])
        b.setDataValue('outputHash', 'thisisasecret',
            RDT_STRING, False)

        self.sh.cfg = self.cfg
        self.sh.client = client
        self.sh.req = FakeRequest(FQDN, 'PUT', '/uploadBuild/%d/testChunkedFile' % data['anotherBuildId'])
        self.sh.req.headers_in['X-rBuilder-OutputHash'] = 'thisisasecret'
        self.sh.auth = users.Authorization(admin = True, authorized = True)

        testFile = open(self.archiveDir + "/testChunkedFile")
        self.sh.req.read = testFile.read

        method = self.sh.handle({'cmd': 'uploadBuild'})
        method(auth = self.sh.auth)

        f1 = os.path.join(self.cfg.imagesPath, 'foo', str(data['anotherBuildId']), 'testChunkedFile')
        self.failUnless(os.path.exists(f1))


if __name__ == "__main__":
    testsuite.main()
