#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import os

import conary.lib.util

import fixtures

from mint import packagecreator
from mint.web import whizzyupload
from mint.server import deriveBaseFunc
import mint.mint_error
from conary.conarycfg import ConaryConfiguration

class PkgCreatorTest(fixtures.FixturedUnitTest):

    def _set_up_path(self):
        self.id = u'99999'
        conary.lib.util.mkdirChain(os.path.join(self.cfg.dataPath, 'tmp',
                'rb-pc-upload-%s' % self.id))
        self.client = self.getClient("owner")

    def tearDown(self):
        if self.id:
            conary.lib.util.rmtree(packagecreator.getWorkingDir(self.cfg, self.id))
            self.id = None

    @fixtures.fixture('Full')
    @testsuite.context('more_cowbell')
    def testPollUploadStatus(self, db, data):
        self._set_up_path()
        # Have to bypass the auth checks
        pollUploadStatus = deriveBaseFunc(self.client.server._server.pollUploadStatus)

        #Try to fetch status for an id that doesn't exist
        self.assertRaises(mint.mint_error.PermissionDenied, pollUploadStatus, self.client.server._server, '99998', 'some-fieldname')

        # We're not going to worry about all the different permutations at this
        # level, since they're covered by the library tests
        ret = pollUploadStatus(self.client.server._server, 99999, 'some-fieldname')
        self.assertEquals(ret['read'], 0)
        self.assertEquals(ret['finished'], {})
        assert ret['currenttime'], 'The starttime should be non-zero'

    @fixtures.fixture('Full')
    @testsuite.context('more_cowbell')
    def testCancelUpload(self, db, data):
        self._set_up_path()
        # Have to bypass the auth checks
        cancelUploadProcess = deriveBaseFunc(self.client.server._server.cancelUploadProcess)    

        assert not cancelUploadProcess(self.client.server._server, '99998', [])

        assert cancelUploadProcess(self.client.server._server, self.id, ['some-fieldname'])

    @fixtures.fixture('Full')
    def testCreatePkgTmpDir(self, db, data):
        self.client = self.getClient('owner')
        self.id = self.client.createPackageTmpDir()

        #Check to see that the directory was in fact created
        wd = packagecreator.getWorkingDir(self.cfg, self.id)

        assert os.path.isdir(wd), "The working directory for createPackage was not created"

    @fixtures.fixture('Full')
    def testCreatePackage(self, db, data):
        self._set_up_path()

        projectId = data['projectId']

        #Create the manifest files
        wd = packagecreator.getWorkingDir(self.cfg, self.id)
        fup = whizzyupload.fileuploader(wd, 'uploadfile')
        i = open(fup.manifestfile, 'wt')
        i.write('''fieldname='uploadfile'
filename=garbage.txt
tempfile=asdfasdf
content-type=text/plain
''')
        i.close()

        i = open(os.path.join(wd, 'asdfasdf'), 'wt')
        i.write('a' * 350)
        i.close()

        oldBackend = packagecreator.DirectLibraryBackend
        def vacuum(s, *args, **kwargs):
            self.assertEquals(args[0], {'user': 'someuser'})
            self.assertEquals(args[1], 'asdfasdf')
            assert isinstance(args[2], ConaryConfiguration)
            self.assertEquals(args[3], ['package-creator.rb.rpath.com@factories:devel'])
            self.assertEquals(len(args), 4)
            self.assertEquals(kwargs, {})
            return 'real data'
        self.mock(packagecreator.DirectLibraryBackend, 'getCandidateBuildFactories', vacuum)
        try:
            factories = self.client.savePackage(projectId, self.id, '1', 'uploadfile', '')
        finally:
            packagecreator.DirectLibraryBackend = oldBackend
        self.assertEquals("real data", factories)


if __name__ == '__main__':
    testsuite.main()

