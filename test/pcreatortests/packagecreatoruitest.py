#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import os

import StringIO
import conary.lib.util

import fixtures

from mint import packagecreator
from mint.web import whizzyupload
from mint.server import deriveBaseFunc
import mint.mint_error
from conary.conarycfg import ConaryConfiguration
from factory_test.factorydatatest import basicXmlDef
from pcreator.factorydata import FactoryDefinition

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
        fixtures.FixturedUnitTest.tearDown(self)

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

    #
    ## Tests for the package creator backend
    #

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

        def startSession(s, *args, **kwargs):
            self.assertEquals(args[0], {'shortname': 'foo', 'version': 'FooV1', 'namespace': 'yournamespace', 'hostname': 'foo.rpath.local2'})
            self.assertEquals(len(args), 2)
            self.assertEquals(kwargs, {})
            return self.id

        def vacuum(s, *args, **kwargs):
            self.assertEquals(args[0], self.id)
            self.assertEquals(len(args), 1)
            self.assertEquals(kwargs, {})
            return [('rpm', StringIO.StringIO(basicXmlDef), {}, {'a': 'b'})]
        self.mock(packagecreator.DirectLibraryBackend, 'getCandidateBuildFactories', vacuum)
        self.mock(packagecreator.DirectLibraryBackend, 'startSession', startSession)

        factories = self.client.getPackageFactories(projectId, self.id, 1, 'uploadfile')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})


if __name__ == '__main__':
    testsuite.main()

