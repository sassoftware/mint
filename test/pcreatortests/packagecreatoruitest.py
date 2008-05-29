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
    """ Unit Tests the MintClient and corresponding MintServer methods, but mocks
    out certain pcreator.backend methods."""

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
    ## Tests for the package creator client (ui backend)
    #

    def _setup_mocks(self, getPackageFactoriesMethod, writeManifest=True):
        self._set_up_path()

        #Create the manifest files
        wd = packagecreator.getWorkingDir(self.cfg, self.id)
        if writeManifest:
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

        self.mock(packagecreator.DirectLibraryBackend, 'getCandidateBuildFactories', getPackageFactoriesMethod)
        self.mock(packagecreator.DirectLibraryBackend, 'startSession', startSession)

    @fixtures.fixture('Full')
    def testCreatePackage(self, db, data):
        def getCandidateBuildFactories(s, sesH):
            self.assertEquals(sesH, self.id)
            return [('rpm', StringIO.StringIO(basicXmlDef), {}, {'a': 'b'})]

        self._setup_mocks(getCandidateBuildFactories)
        projectId = data['projectId']
        factories = self.client.getPackageFactories(projectId, self.id, 1, 'uploadfile')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})

    @fixtures.fixture('Full')
    def testCreatePackageNoManifest(self, db, data):
        self._setup_mocks(None, writeManifest=False)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.id, 1, 'uploadfile')

    @fixtures.fixture('Full')
    def testCreatePackageFactoriesError(self, db, data):
        def raises(x, sesH):
            self.assertEquals(sesH, self.id)
            raise packagecreator.errors.UnsupportedFileFormat('bogus error')
        self._setup_mocks(raises)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.id, 1, 'uploadfile')


    @fixtures.fixture('Full')
    def testSavePackage(self, db, data):
        self.client = self.getClient('owner')
        self.id = self.client.createPackageTmpDir()
        refH = 'bogusFactoryHandle'
        self.validateCalled = False
        self.buildCalled = False
        try:
            def validateParams(x, sesH, factH, data):
                self.validateCalled = True
                self.assertEquals(sesH, self.id)
                self.assertEquals(factH, refH)
            self.mock(packagecreator.DirectLibraryBackend, 'makeSourceTrove',
                    validateParams)

            def buildParams(x, sesH, commit):
                self.buildCalled = True
                self.assertEquals(sesH, self.id)
                self.assertEquals(commit, True)
            self.mock(packagecreator.DirectLibraryBackend, 'build',
                    buildParams)

            self.client.savePackage(self.id, refH, {}, build = False)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failIf(self.buildCalled, "The Build method was called, but shouldn't have been")

            #Try again with build
            self.validateCalled = False
            self.client.savePackage(self.id, refH, {}, build = True)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failUnless(self.buildCalled, "The Build method was never called")
        finally:
            del self.validateCalled
            del self.buildCalled

    @fixtures.fixture('Full')
    def testGetPackageBuildStatusFailedBuild(self, db, data):
        self._set_up_path()
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, self.id)
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            raise packagecreator.errors.BuildFailedError('fake build error')
        self.mock(packagecreator.DirectLibraryBackend, 'isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus(self.id), [True, -1, "fake build error"])

    @fixtures.fixture('Full')
    def testGetPackageBuildStatus(self, db, data):
        self._set_up_path()
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, self.id)
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            return 'Some data'
        self.mock(packagecreator.DirectLibraryBackend, 'isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus(self.id), 'Some data')


if __name__ == '__main__':
    testsuite.main()

