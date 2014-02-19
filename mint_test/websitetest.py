#
# Copyright (c) SAS Institute Inc.
#

import os

import fixtures
from mint.web import site
from mint.lib.data import RDT_STRING
from mint.web.webhandler import HttpMoved
from mint import users

from mint_rephelp import FQDN

from mint_rephelp import FakeRequest
from mint_test import resources

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

        testFile = open(resources.get_archive('testChunkedFile'))
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

