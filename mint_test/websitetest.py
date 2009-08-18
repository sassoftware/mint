#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import os

from mint_test import mint_rephelp
import fixtures
from mint.web import site
from mint.lib.data import RDT_STRING
from mint.lib import database
from mint.web.webhandler import HttpNotFound, HttpMoved
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint import users

from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_HOST, FQDN

from conary import versions
from conary.lib import util

from testrunner import pathManager

from mint_rephelp import FakeRequest

class FixturedProjectTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.sh = site.SiteHandler()
        self.sh.session = {}

        def fakeRedirect(*args, **kwargs):
            raise HttpMoved

        self.sh._redirect = fakeRedirect

    def _testUploadBuild(self, db, data, hidden=False):
        client = self.getClient("developer")
        p = client.getProject(data['projectId'])
        if hidden:
            # hide the project
            admin = self.getClient("admin")
            admin.hideProject(data['projectId'])
        b = client.getBuild(data['anotherBuildId'])
        b.setDataValue('outputToken', 'thisisasecret',
            RDT_STRING, False)

        self.sh.cfg = self.cfg
        self.sh.req = FakeRequest(FQDN, 'PUT', '/uploadBuild/%d/testChunkedFile' % data['anotherBuildId'])
        self.sh.req.headers_in['X-rBuilder-OutputToken'] = 'thisisasecret'

        # the PUT handler runs with anonymous authorization
        self.sh.client = self.getClient('anonymous')
        self.sh.auth = users.Authorization(admin = False, authorized = False)

        testFile = open(pathManager.getPath("MINT_ARCHIVE_PATH") + "/testChunkedFile")
        self.sh.req.read = testFile.read

        method = self.sh.handle({'cmd': 'uploadBuild'})
        method(auth = self.sh.auth)

        f1 = os.path.join(self.cfg.imagesPath, 'foo', str(data['anotherBuildId']), 'testChunkedFile')
        self.failUnless(os.path.exists(f1))

    @fixtures.fixture('Full')
    def testUploadBuild(self, db, data):
        self._testUploadBuild(db, data, hidden=False)

    @fixtures.fixture('Full')
    def testUploadHiddenBuild(self, db, data):
        self._testUploadBuild(db, data, hidden=True)

if __name__ == "__main__":
    testsuite.main()
