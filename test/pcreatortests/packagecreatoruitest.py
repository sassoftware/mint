#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.
#

import sys
if '..' not in sys.path: sys.path.append('..')
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
import pcreator
from pcreator.factorydata import FactoryDefinition

class PkgCreatorTest(fixtures.FixturedUnitTest):
    """ Unit Tests the MintClient and corresponding MintServer methods, but mocks
    out certain pcreator.backend methods."""

    def _set_up_path(self):
        self.sesH = u'99999'
        conary.lib.util.mkdirChain(os.path.join(self.cfg.dataPath, 'tmp',
                'rb-pc-upload-%s' % self.sesH))
        self.client = self.getClient("owner")

    def tearDown(self):
        if hasattr(self, 'sesH') and self.sesH:
            conary.lib.util.rmtree(packagecreator.getWorkingDir(self.cfg, self.sesH))
            self.sesH = None
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

        assert cancelUploadProcess(self.client.server._server, self.sesH, ['some-fieldname'])

    @fixtures.fixture('Full')
    def testCreatePkgTmpDir(self, db, data):
        self.client = self.getClient('owner')
        self.sesH = self.client.createPackageTmpDir()

        #Check to see that the directory was in fact created
        wd = packagecreator.getWorkingDir(self.cfg, self.sesH)

        assert os.path.isdir(wd), "The working directory for createPackage was not created"

    @fixtures.fixture('Full')
    def testStartSessionDir(self, db, data):
        class MockProdDef(object):
            name = 'mock'
            getUpstreamSources = lambda *args, **kwargs: {}
            getFactorySources = lambda *args, **kwargs: {}
            getStages = lambda x: [x]
            getLabelForStage = lambda *args: 'localhost@rpl:linux'
        self.mock(pcreator.backend.BaseBackend, '_loadProductDefinitionFromProdDefDict', lambda *args: MockProdDef())
        self.client = self.getClient('owner')
        self.sesH = self.client.createPackageTmpDir()

        wd = packagecreator.getWorkingDir(self.cfg, self.sesH)

        pc = packagecreator.getPackageCreatorClient(wd, ('owner', "%dpass" % data['owner']))
        project = self.client.getProject(data['projectId'])
        cfg = project.getConaryConfig()
        cfg['name'] = 'owner'
        cfg['contact'] = ''
        mincfg = packagecreator.MinimalConaryConfiguration( cfg)

        pc.startSession({}, mincfg)
        # ensure we have a viable session
        self.assertEquals(os.listdir(os.path.join(wd, 'owner')), [self.sesH])
        self.assertEquals(wd.endswith(self.sesH), True)
        refKeys = ['develStageLabel', 'productDefinition', 'upstreamSources',
                'factorySources', 'mincfg']
        self.assertEquals(set(os.listdir(os.path.join(wd, 'owner', self.sesH))),
                set(refKeys))


    #
    ## Tests for the package creator client (ui backend)
    #

    def _setup_mocks(self, getPackageFactoriesMethod, writeManifest=True):
        self._set_up_path()

        #Create the manifest files
        wd = packagecreator.getWorkingDir(self.cfg, self.sesH)
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

        @pcreator.backend.public
        def startSession(s, *args, **kwargs):
            self.assertEquals(args[0], {'shortname': 'foo', 'version': 'FooV1', 'namespace': 'yournamespace', 'hostname': 'foo.rpath.local2'})
            self.assertEquals(len(args), 2)
            self.assertEquals(kwargs, {})
            return self.sesH

        if getPackageFactoriesMethod:
            getPackageFactoriesMethod._isPublic = True
        self.mock(pcreator.backend.BaseBackend,
                '_getCandidateBuildFactories', getPackageFactoriesMethod)
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)

    @fixtures.fixture('Full')
    def testCreatePackage(self, db, data):
        def getCandidateBuildFactories(s, sesH):
            self.assertEquals(sesH, self.sesH)
            return [('rpm', basicXmlDef, {'a': 'b'})]

        self._setup_mocks(getCandidateBuildFactories)
        projectId = data['projectId']
        factories = self.client.getPackageFactories(projectId, self.sesH, 1, 'uploadfile')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})

    @fixtures.fixture('Full')
    def testCreatePackageNoManifest(self, db, data):
        self._setup_mocks(None, writeManifest=False)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.sesH, 1, 'uploadfile')

    @fixtures.fixture('Full')
    def testCreatePackageFactoriesError(self, db, data):
        def raises(x, sesH):
            self.assertEquals(sesH, self.sesH)
            raise packagecreator.errors.UnsupportedFileFormat('bogus error')
        self._setup_mocks(raises)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.sesH, 1, 'uploadfile')


    @fixtures.fixture('Full')
    def testSavePackage(self, db, data):
        self.client = self.getClient('owner')
        self.sesH = self.client.createPackageTmpDir()
        refH = 'bogusFactoryHandle'
        self.validateCalled = False
        self.buildCalled = False
        try:
            @pcreator.backend.public
            def validateParams(x, sesH, factH, data):
                self.validateCalled = True
                self.assertEquals(sesH, self.sesH)
                self.assertEquals(factH, refH)
                return True
            self.mock(pcreator.backend.BaseBackend, '_makeSourceTrove',
                    validateParams)

            @pcreator.backend.public
            def buildParams(x, sesH, commit):
                self.buildCalled = True
                self.assertEquals(sesH, self.sesH)
                self.assertEquals(commit, True)
                return True
            self.mock(pcreator.backend.BaseBackend, '_build',
                    buildParams)

            self.client.savePackage(self.sesH, refH, {}, build = False)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failIf(self.buildCalled, "The Build method was called, but shouldn't have been")

            #Try again with build
            self.validateCalled = False
            self.client.savePackage(self.sesH, refH, {}, build = True)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failUnless(self.buildCalled, "The Build method was never called")
        finally:
            del self.validateCalled
            del self.buildCalled

    @fixtures.fixture('Full')
    def testGetPackageBuildStatusFailedBuild(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, self.sesH)
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            raise packagecreator.errors.BuildFailedError('fake build error')
        self.mock(pcreator.backend.BaseBackend, '_isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus(self.sesH), [True, -1, "fake build error"])

    @fixtures.fixture('Full')
    def testGetPackageBuildStatus(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, self.sesH)
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            return 'Some data'
        self.mock(pcreator.backend.BaseBackend, '_isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus(self.sesH), 'Some data')

    @fixtures.fixture('Full')
    def testGetPackageBuildLogsFailure(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH):
            self.assertEquals(sesH, self.sesH)
            raise packagecreator.errors.BuildFailedError('fake build error')
        self.mock(pcreator.backend.BaseBackend, '_getBuildLogs', validateParams)
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageBuildLogs, self.sesH)

    @fixtures.fixture('Full')
    def testGetPackageBuildLogs(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH):
            self.assertEquals(sesH, self.sesH)
            return 'Some Data'
        self.mock(pcreator.backend.BaseBackend, '_getBuildLogs', validateParams)
        self.assertEquals(self.client.getPackageBuildLogs(self.sesH), 'Some Data')

if __name__ == '__main__':
    testsuite.main()

