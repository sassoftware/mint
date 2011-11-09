#!/usr/bin/python
#
# Copyright (c) 2008 rPath, Inc.
#

import os, sys
# SUB_LEVEL is the number of levels beneath the main test dir that we are
SUB_LEVEL = 1
mainPath = os.path.dirname(os.path.abspath(__file__))
for sub in range(SUB_LEVEL):
    mainPath = os.path.dirname(mainPath)
if mainPath not in sys.path: sys.path.append(mainPath)
import testsuite
testsuite.setup()

import os, signal
import json
import SimpleHTTPServer

import StringIO
import conary.lib.util
from conary.conaryclient import filetypes
from conary import changelog
from conary import versions

from mint_test import fixtures
from mint_test import mint_rephelp

from mint import packagecreator
from mint import helperfuncs
from mint.web import whizzyupload
from mint_rephelp import MINT_HOST, MINT_DOMAIN
from mint.server import deriveBaseFunc
from mint.django_rest.rbuilder.manager import rbuildermanager
import mint.mint_error
from conary import conaryclient
from factory_test.factorydatatest import basicXmlDef
import pcreator
from pcreator.factorydata import FactoryDefinition
from pcreator import server as pcreatorServer
from rpath_proddef import api1 as proddef

from testrunner import pathManager

class PkgCreatorTest(fixtures.FixturedUnitTest):
    """ Unit Tests the MintClient and corresponding MintServer methods, but mocks
    out certain pcreator.backend methods."""

    def _set_up_path(self):
        self.uploadSes = u'99999'
        conary.lib.util.mkdirChain(os.path.join(self.cfg.dataPath, 'tmp',
                'rb-pc-upload-%s' % self.uploadSes))
        self.client = self.getClient("owner")

    def tearDown(self):
        if hasattr(self, 'uploadSes') and self.uploadSes:
            conary.lib.util.rmtree(packagecreator.getUploadDir(self.cfg, self.uploadSes))
            self.uploadSes = None
        fixtures.FixturedUnitTest.tearDown(self)

    @fixtures.fixture('Full')
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
    def testCancelUpload(self, db, data):
        self._set_up_path()
        # Have to bypass the auth checks
        cancelUploadProcess = deriveBaseFunc(self.client.server._server.cancelUploadProcess)    

        assert not cancelUploadProcess(self.client.server._server, '99998', [])

        assert cancelUploadProcess(self.client.server._server, self.uploadSes, ['some-fieldname'])

    @fixtures.fixture('Full')
    def testCreatePkgTmpDir(self, db, data):
        self.client = self.getClient('owner')
        self.uploadSes = self.client.createPackageTmpDir()

        #Check to see that the directory was in fact created
        wd = packagecreator.getUploadDir(self.cfg, self.uploadSes)

        assert os.path.isdir(wd), "The working directory for createPackage was not created"

    @fixtures.fixture('Full')
    def testStartSessionDir(self, db, data):
        raise testsuite.SkipTestException('session dir has been broken out from upload dir. this test needs to be corrected')
        class MockProdDef(object):
            name = 'mock'
            getSearchPaths = lambda *args, **kwargs: {}
            getFactorySources = lambda *args, **kwargs: {}
            getStages = lambda x: [x]
            getLabelForStage = lambda *args: 'localhost@rpl:linux'
        self.mock(pcreator.backend.BaseBackend, '_loadProductDefinitionFromProdDefDict', lambda *args: MockProdDef())
        self.client = self.getClient('owner')
        self.uploadSes = self.client.createPackageTmpDir()

        wd = packagecreator.getUploadDir(self.cfg, self.uploadSes)

        pc = packagecreator.getPackageCreatorClient(self.cfg, ('owner', "%dpass" % data['owner']), 
            djangoManager=rbuildermanager.RbuilderManager())
        project = self.client.getProject(data['projectId'])
        cfg = project.getConaryConfig()
        cfg['name'] = 'owner'
        cfg['contact'] = ''
        mincfg = packagecreator.MinimalConaryConfiguration( cfg)

        pc.startSession({}, mincfg)
        # ensure we have a viable session
        self.assertEquals(os.listdir(os.path.join(wd, 'owner')), [self.uploadSes])
        self.assertEquals(wd.endswith(self.uploadSes), True)
        refKeys = ['stageLabel', 'productDefinition', 'searchPath',
                'factorySources', 'mincfg']
        assert(set(refKeys).issubset(set(os.listdir(os.path.join(wd, 'owner', self.uploadSes)))))


    #
    ## Tests for the package creator client (ui backend)
    #

    def _setup_mocks(self, getPackageFactoriesMethod, writeManifest=True):
        self._set_up_path()

        #Create the manifest files
        wd = packagecreator.getUploadDir(self.cfg, self.uploadSes)
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
            self.assertEquals(args[0], {'shortname': 'foo', 'version': 'FooV1', 'namespace': 'ns', 'hostname': 'foo.rpath.local2'})
            self.assertEquals(len(args), 4, "The number of arguments to saveSession has changed")
            self.assertEquals(kwargs, {})
            return '88889'

        if getPackageFactoriesMethod:
            getPackageFactoriesMethod._isPublic = True
        self.mock(pcreator.backend.BaseBackend,
                '_getCandidateBuildFactories', getPackageFactoriesMethod)
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)

    @fixtures.fixture('Full')
    def testCreatePackage(self, db, data):
        def getCandidateBuildFactories(s, sesH):
            self.assertEquals(sesH, '88889')
            return [('rpm', basicXmlDef, {'a': 'b'})]

        self._setup_mocks(getCandidateBuildFactories)
        projectId = data['projectId']
        sesH, factories, data = self.client.getPackageFactories(projectId, self.uploadSes, 1)
        self.assertEquals(sesH, '88889')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})

    @fixtures.fixture('Full')
    def testCreatPackagePreexistingTrove(self, db, data):
        def getCandidateBuildFactories(s, sesH):
            self.assertEquals(sesH, 'session-88889')
            return [('rpm', basicXmlDef, {'a': 'b'})]
        self._setup_mocks(getCandidateBuildFactories)
        @pcreator.backend.public
        def startSession(*args):
            return 'session-88889'
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)
        projectId = data['projectId']
        sesH, factories, data = self.client.getPackageFactoriesFromRepoArchive(projectId, 1, 'gina', 'foobar', 'barrage.rpath.com@gina:sdi-1-devel')
        self.assertEquals(sesH, 'session-88889')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})
 
    @fixtures.fixture('Full')
    def testCreatePackagePreExistSession(self, db, data):
        def getCandidateBuildFactories(s, sesH):
            self.assertEquals(sesH, 'session_handle_test')
            return [('rpm', basicXmlDef, {'a': 'b'})]
        self._setup_mocks(getCandidateBuildFactories)
        projectId = data['projectId']
        sesH, factories, data = self.client.getPackageFactories(projectId, self.uploadSes, 1, 'session_handle_test')
        self.assertEquals(sesH, 'session_handle_test')
        self.assertEquals(factories[0][0], 'rpm')
        assert isinstance(factories[0][1], FactoryDefinition)
        self.assertEquals(factories[0][2], {'a': 'b'})

    @fixtures.fixture('Full')
    def testCreatePackageNoManifest(self, db, data):
        self._setup_mocks(None, writeManifest=False)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.uploadSes, 1)

    @fixtures.fixture('Full')
    def testCreatePackageFactoriesError(self, db, data):
        def raises(x, sesH):
            self.assertEquals(sesH, '88889')
            raise packagecreator.errors.UnsupportedFileFormat('bogus error')
        self._setup_mocks(raises)
        projectId = data['projectId']
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageFactories, projectId, self.uploadSes, 1)

    @fixtures.fixture('Full')
    def testStartPackageCreatorSession(self, db, data):
        @pcreator.backend.public
        def startSession(*args):
            return 'asdfasdfasdfasdfsdf'
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)
        self.client = self.getClient('owner')
        sesH = self.client.startPackageCreatorSession(1, '3', 'yournamespace', 'foo', 'bar.baz.com@yournamespace:baz-3-devel')
        self.assertEquals(sesH, 'asdfasdfasdfasdfsdf')

    @fixtures.fixture('Full')
    def testStartPackageCreatorSessionFail(self, db, data):
        @pcreator.backend.public
        def startSession(*args):
            raise packagecreator.errors.ProductDefinitionTroveNotFound()
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)
        self.client = self.getClient('owner')
        self.assertRaises(mint.mint_error.PackageCreatorError,
            self.client.startPackageCreatorSession,1, '3', 'yournamespace', 'foo',
            'bar.baz.com@yournamespace:baz-3-devel')

    @fixtures.fixture('Full')
    def testSavePackage(self, db, data):
        self.client = self.getClient('owner')
        self.uploadSes = self.client.createPackageTmpDir()
        refH = 'bogusFactoryHandle'
        self.validateCalled = False
        self.buildCalled = False
        try:
            @pcreator.backend.public
            def validateParams(x, sesH, factH, data):
                self.validateCalled = True
                self.assertEquals(sesH, '88889')
                self.assertEquals(factH, refH)
                return True
            self.mock(pcreator.backend.BaseBackend, '_makeSourceTrove',
                    validateParams)

            @pcreator.backend.public
            def buildParams(x, sesH, commit):
                self.buildCalled = True
                self.assertEquals(sesH, '88889')
                self.assertEquals(commit, True)
                return True
            self.mock(pcreator.backend.BaseBackend, '_build',
                    buildParams)

            def goodgfdfdd(*args):
                return StringIO.StringIO('blah blah blah')
            self.mock(packagecreator, 'getFactoryDataFromDataDict', goodgfdfdd)
            self.client.savePackage('88889', refH, {}, build = False)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failIf(self.buildCalled, "The Build method was called, but shouldn't have been")

            #Try again with build
            self.validateCalled = False
            self.client.savePackage('88889', refH, {}, build = True)
            self.failUnless(self.validateCalled, "The validate method was never called")
            self.failUnless(self.buildCalled, "The Build method was never called")

            # test FAIL cases
            @pcreator.backend.public
            def badvalidateparams(*args):
                raise pcreator.errors.ConstraintsValidationError(['blah', 'bleh', 'blih'])
            self.mock(pcreator.backend.BaseBackend, '_makeSourceTrove',
                    badvalidateparams)
            self.validateCalled = False
            self.buildCalled = False
            try:
                self.client.savePackage('88889', refH, {}, build=True)
            except mint.mint_error.PackageCreatorValidationError, err:
                self.assertEquals(err.reasons, ['blah', 'bleh', 'blih'])
                self.assertEquals(str(err), 'Field validation failed: blah, bleh, blih')

        finally:
            del self.validateCalled
            del self.buildCalled

    @fixtures.fixture('Full')
    def testSavePackageBadArgs(self, db, data):
        self.client = self.getClient('owner')
        self.uploadSes = self.client.createPackageTmpDir()
        refH = 'bogusFactoryHandle'
        @pcreator.backend.public
        def raiseError(x, sesH, factH, data):
            raise packagecreator.errors.PackageCreationFailedError("deliberately raised")
        self.mock(pcreator.backend.BaseBackend, '_makeSourceTrove',
                raiseError)

        def goodgfdfdd(*args):
            return StringIO.StringIO('blah blah blah')
        self.mock(packagecreator, 'getFactoryDataFromDataDict', goodgfdfdd)
        err = self.assertRaises(mint.mint_error.PackageCreatorError,
                self.client.savePackage, '88889', refH, {}, build = False)
        self.assertEquals(str(err),
                'Error attempting to create source trove: deliberately raised')

    @fixtures.fixture('Full')
    def testBuildPackageUnbuildable(self, db, data):
        self.client = self.getClient('owner')
        self.sesH = self.client.createPackageTmpDir()
        refH = 'bogusFactoryHandle'
        @pcreator.backend.public
        def passThru(*args, **kwargs):
            return "slide"
        self.mock(pcreator.backend.BaseBackend, '_makeSourceTrove', passThru)

        @pcreator.backend.public
        def raiseError(*args, **kwargs):
            raise packagecreator.errors.UnbuildablePackage
        self.mock(pcreator.backend.BaseBackend, '_build', raiseError)

        def goodgfdfdd(*args):
            return StringIO.StringIO('blah blah blah')
        self.mock(packagecreator, 'getFactoryDataFromDataDict', goodgfdfdd)

        # prove the build param is honored
        self.client.savePackage(self.sesH, refH, {}, build = False)
        err = self.assertRaises(mint.mint_error.PackageCreatorError,
                self.client.savePackage, self.sesH, refH, {}, build = True)
        self.assertEquals(str(err),
                'Error attempting to build package: '
                'Raised when a package cannot be built')

    @fixtures.fixture('Full')
    def testGetPackageBuildStatusFailedBuild(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, '88889')
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            raise packagecreator.errors.BuildFailedError('fake build error')
        self.mock(pcreator.backend.BaseBackend, '_isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus('88889'), [True, -1, "fake build error", []])

    @fixtures.fixture('Full')
    def testBuildSourcePackage(self, db, data):
        projectId = data['projectId']
        self.client = self.getClient('owner')

        @pcreator.backend.public
        def startSession(s, *args, **kwargs):
            self.assertEquals(args[0], {'shortname': 'foo', 'version': 'FooV1', 'namespace': 'ns', 'hostname': 'foo.rpath.local2'})
            self.assertEquals(args[2], 'foo:source=testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')
            self.assertEquals(len(args), 4, "The number of arguments to saveSession has changed")
            self.assertEquals(kwargs, {})
            return '88889'
        self.mock(pcreator.backend.BaseBackend, '_startPackagingSession', startSession)

        @pcreator.backend.public
        def buildParams(x, sesH, commit):
            self.buildCalled = True
            self.assertEquals(sesH, '88889')
            self.assertEquals(commit, True)
            return True

        self.mock(pcreator.backend.BaseBackend, '_build',
                buildParams)
        sesH = self.client.buildSourcePackage(projectId, 1, 'foo:source', 'testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')
        self.assertEquals(sesH, '88889')

    @fixtures.fixture('Full')
    def testBuildSourcePackageBuildFail(self, db, data):
        projectId = data['projectId']
        self.client = self.getClient('owner')

        @pcreator.backend.public
        def startSession(s, *args, **kwargs):
            self.assertEquals(args[0], {'shortname': 'foo', 'version': 'FooV1', 'namespace': 'ns', 'hostname': 'foo.rpath.local2'})
            self.assertEquals(args[2], 'foo:source=testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')
            self.assertEquals(len(args), 4, "The number of arguments to saveSession has changed")
            self.assertEquals(kwargs, {})
            return '88889'
        self.mock(pcreator.backend.BaseBackend, '_startPackagingSession', startSession)

        @pcreator.backend.public
        def buildParams(x, sesH, commit):
            raise packagecreator.errors.ProductDefinitionTroveNotFound()

        self.mock(pcreator.backend.BaseBackend, '_build',
                buildParams)
        self.assertRaises(mint.mint_error.PackageCreatorError,
                self.client.buildSourcePackage, projectId, 1, 'foo:source',
                'testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')

    @fixtures.fixture('Full')
    def testBuildSourcePackageErrStart(self, db, data):
        projectId = data['projectId']
        self.client = self.getClient('owner')

        @pcreator.backend.public
        def startSession(s, *args, **kwargs):
            raise packagecreator.errors.ProductDefinitionTroveNotFound()
        self.mock(pcreator.backend.BaseBackend, '_startPackagingSession', startSession)

        self.assertRaises(mint.mint_error.PackageCreatorError,
                self.client.buildSourcePackage, projectId, 1, 'foo:source',
                'testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')

    @fixtures.fixture('Full')
    def testGetPackageBuildStatus(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH, commit):
            self.assertEquals(sesH, '88889')
            self.failUnless(commit, 'True should have been passed as the commit parameter')
            return 'Some data'
        self.mock(pcreator.backend.BaseBackend, '_isBuildFinished', validateParams)
        self.assertEquals(self.client.server.getPackageBuildStatus('88889'), 'Some data')

    @fixtures.fixture('Full')
    def testGetPackageBuildLogsFailure(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH):
            self.assertEquals(sesH, '88889')
            raise packagecreator.errors.BuildFailedError('fake build error')
        self.mock(pcreator.backend.BaseBackend, '_getBuildLogs', validateParams)
        self.assertRaises(mint.mint_error.PackageCreatorError, self.client.getPackageBuildLogs, '88889')

    @fixtures.fixture('Full')
    def testGetPackageBuildLogs(self, db, data):
        self._set_up_path()
        @pcreator.backend.public
        def validateParams(x, sesH):
            self.assertEquals(sesH, '88889')
            return 'Some Data'
        self.mock(pcreator.backend.BaseBackend, '_getBuildLogs', validateParams)
        self.assertEquals(self.client.getPackageBuildLogs('88889'), 'Some Data')

    @fixtures.fixture('Full')
    def testMinCfgData(self, db, data):
        @pcreator.backend.public
        def startSession(*args):
            cfgArgs = json.loads(args[2])
            proxyLines = [x for x in cfgArgs if x.startswith('conaryProxy')]
            self.failUnless(proxyLines, "Local conary proxy was not set")
            return 'asdfasdfasdfasdfsdf'
        self.mock(pcreator.backend.BaseBackend, '_startSession', startSession)
        client = self.getClient('owner')
        sesH = client.startPackageCreatorSession(1, '3', 'yournamespace', 'foo', 'bar.baz.com@yournamespace:baz-3-devel')

class PkgCreatorReposTest(mint_rephelp.MintRepositoryHelper):
    def _createProductVersion(self, mintclient, project, version, namespace, description=''):
        versionId = mintclient.addProductVersion(project.id, namespace, version, description)
        pd = helperfuncs.sanitizeProductDefinition(project.name,
                    project.description, project.hostname + '.' + project.domainname,
                    project.shortname, version, description, namespace)
        mintclient.setProductDefinitionForVersion(versionId, pd)
        return versionId

    def testGetSourcePackages(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        cclient = conaryclient.ConaryClient(cfg)
        repos = cclient.getRepos()

        versionId = self._createProductVersion(client, project, 'vs1', 'ns1', 'bogus description')

        self.assertEquals([], client.getProductVersionSourcePackages(projectId, versionId))

        #Now write some troves
        self.addComponent('foo:source', '/testproject.rpath.local2@ns1:testproject-vs1-devel/1.0-1')
        self.addComponent('foo:source', '/testproject.rpath.local2@ns1:testproject-vs1-devel/2.0-1')
        self.addComponent('bar:source', '/testproject.rpath.local2@ns1:testproject-vs1-devel/2.0-1')
        self.addComponent('bar:source', '/testproject.rpath.local2@ns2:testproject-vs1-devel/2.0-1')
        self.addComponent('bar:source', '/testproject.rpath.local2@ns1:testproject-vs2-devel/2.0-1')
        self.addComponent('bar:runtime', '/testproject.rpath.local2@ns1:testproject-vs2-devel/2.0-1-1')
        self.addCollection('bar', ['bar:runtime'], '/testproject.rpath.local2@ns1:testproject-vs2-devel/2.0-1-1')
        ret = client.getProductVersionSourcePackages(projectId, versionId)
        ret = set([(x[0], str(versions.ThawVersion(x[1]))) for x in ret]) # Gets rid of the timestamp in the return value
        self.assertEquals(set([
                        ('bar:source', '/testproject.rpath.local2@ns1:testproject-vs1-devel/2.0-1'),
                        ('foo:source', '/testproject.rpath.local2@ns1:testproject-vs1-devel/2.0-1')]), ret)

    def testGetPackageCreatorPackages(self):
        self.startMintServer()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)
        cfg = project.getConaryConfig()
        cclient = conaryclient.ConaryClient(cfg)
        repos = cclient.getRepos()

        self.assertEquals({}, client.getPackageCreatorPackages(projectId))

        #add some troves
        hostname = project.getFQDN()
        labeltemplate = "%s@%%s:%s-%%s-devel" % (hostname, project.getShortname())
        ns1, vs1 = 'ns1', 'vs1'
        label1 = labeltemplate % (ns1, vs1)
        vs2 = 'vs2'
        label2 = labeltemplate % (ns1, vs2)
        ns2 = 'ns2'
        label3 = labeltemplate % (ns2, vs2)
        cs = cclient.createSourceTrove('grnotify:source', label1, '0.4.4', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs1, namespace=ns1, hostname=hostname,
                    shortname=project.getShortname(), label=label1))
        repos.commitChangeSet(cs)
        cs = cclient.createSourceTrove('zope:source', label1, '2.7.8', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs1, namespace=ns1, hostname=hostname,
                    shortname=project.getShortname(), label=label1))
        repos.commitChangeSet(cs)
        cs = cclient.createSourceTrove('grnotify:source', label1, '0.4.5', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs1, namespace=ns1, hostname=hostname,
                    shortname=project.getShortname(), label=label1))
        repos.commitChangeSet(cs)
        cs = cclient.createSourceTrove('grnotify:source', label2, '0.4.4', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs2, namespace=ns1, hostname=hostname,
                    shortname=project.getShortname(), label=label2))
        repos.commitChangeSet(cs)
        cs = cclient.createSourceTrove('grnotify:source', label3, '0.4.4', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs2, namespace=ns2, hostname=hostname,
                    shortname=project.getShortname(), label=label3))
        repos.commitChangeSet(cs)
        #This one should not be returned
        cs = cclient.createSourceTrove('zope:source', label1, '2.7.9', {},
            changelog.ChangeLog(name='test', contact=''),
            pkgCreatorData='{"stageLabel": "%(label)s", "productDefinition": {"shortname": "%(shortname)s", "version": "%(version)s", "namespace": "%(namespace)s", "hostname": "%(hostname)s"}}' %
                dict(version=vs2, namespace=ns2, hostname=hostname,
                    shortname=project.getShortname(), label=label3))
        repos.commitChangeSet(cs)
        
        res = client.getPackageCreatorPackages(projectId)
        self.assertEquals(res, getPackageCreatorFactoriesData1)

getPackageCreatorFactoriesData1 = {u'vs1': {u'ns1': {'grnotify:source': {u'stageLabel': u'testproject.rpath.local2@ns1:testproject-vs1-devel/0.4.5-1',
                                       u'productDefinition': {u'hostname': u'testproject.rpath.local2',
                                                              u'namespace': u'ns1',
                                                              u'shortname': u'testproject',
                                                              u'version': u'vs1'}},
                   'zope:source': {u'stageLabel': u'testproject.rpath.local2@ns1:testproject-vs1-devel/2.7.8-1',
                                   u'productDefinition': {u'hostname': u'testproject.rpath.local2',
                                                          u'namespace': u'ns1',
                                                          u'shortname': u'testproject',
                                                          u'version': u'vs1'}}}},
 u'vs2': {u'ns1': {'grnotify:source': {u'stageLabel': u'testproject.rpath.local2@ns1:testproject-vs2-devel/0.4.4-1',
                                       u'productDefinition': {u'hostname': u'testproject.rpath.local2',
                                                              u'namespace': u'ns1',
                                                              u'shortname': u'testproject',
                                                              u'version': u'vs2'}}},
          u'ns2': {'grnotify:source': {u'stageLabel': u'testproject.rpath.local2@ns2:testproject-vs2-devel/0.4.4-1',
                                       u'productDefinition': {u'hostname': u'testproject.rpath.local2',
                                                              u'namespace': u'ns2',
                                                              u'shortname': u'testproject',
                                                              u'version': u'vs2'}}}}}

prodDef1 = """\
<?xml version="1.0" encoding="UTF-8"?>
<productDefinition version="2.0" xmlns="http://www.rpath.com/permanent/rpd-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd">
   <productName>My Awesome Appliance</productName>
   <productShortname>awesome</productShortname>
   <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
   </productDescription>
   <productVersion>1.0</productVersion>
   <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   </productVersionDescription>
   <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
   <conaryNamespace>mycompany</conaryNamespace>
   <imageGroup>group-foo</imageGroup>
   <baseFlavor>
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,
      ~!xen, ~!xfce, ~!xorg-x11.xprint
   </baseFlavor>
   <stages>
      <stage labelSuffix="-devel" name="devel"/>
      <stage labelSuffix="-qa" name="qa"/>
      <stage labelSuffix="" name="release"/>
   </stages>
   <searchPaths>
      <searchPath label="localhost@rpath:factories"
troveName="group-rap-standard"/>
troveName="group-postgres"/>
   </searchPaths>
   <factorySources>
      <factorySource label="localhost@rpath:factories"
troveName="group-factories"/>
troveName="group-postgres"/>
   </factorySources>
   <architectures>
      <architecture name="x86" displayName="32 bit" flavor="is: x86"/>
      <architecture name="x86_64" displayName="64 bit" flavor="is: x86_64"/>
      <architecture name="biarch" displayName="biarch" flavor="is: x86 x86_64"/>
   </architectures>
   <flavorSets>
      <flavorSet name="xen" displayName="xen" flavor="~xen,~domU"/>
      <flavorSet name="vmware" displayName="vmware" flavor="~vmware"/>
   </flavorSets>
   <containerTemplates>
     <image architectureRef="x86" containerTemplateRef="installableIsoImage"/>
     <image architectureRef="x86_64" containerTemplateRef="installableIsoImage"/>
     <image architectureRef="x86" containerTemplateRef="rawFsImage" flavorSetRef="xen" freespace="1234"/>
     <image architectureRef="biarch" containerTemplateRef="rawHdImage" flavorSetRef="xen" autoResolve="true" baseFileName="proc-foo-moo"/>
     <image architectureRef="biarch" containerTemplateRef="vmwareImage" flavorSetRef="vmware" autoResolve="true" baseFileName="foobar"/>
     <image architectureRef="biarch" containerTemplateRef="virtualIronImage"/>
   </containerTemplates>
   <buildDefinition>
      <build architectureRef="x86" name="x86 installableIso" containerTemplateRef="installableIsoImage">
         <stage ref="devel"/>
         <stage ref="qa"/>
         <stage ref="release"/>
         <imageGroup>group-os</imageGroup>
      </build>
      <build architectureRef="x86_64" name="x86_64 installableIso" containerTemplateRef="installableIsoImage">
         <stage ref="release"/>
      </build>
      <build architectureRef="x86" flavorSetRef="xen" name="x86 rawFs" containerTemplateRef="rawFsImage">
      </build>
      <build architectureRef="biarch" flavorSetRef="xen" name="x86_64 rawHd" containerTemplateRef="rawHdImage">
         <stage ref="devel"/>
         <stage ref="qa"/>
         <stage ref="release"/>
         <imageGroup>group-os</imageGroup>
      </build>
      <build architectureRef="biarch" flavorSetRef="vmware" name="x86_64 vmware" containerTemplateRef="vmwareImage">
         <stage ref="release"/>
         <imageGroup>group-bar</imageGroup>
      </build>
      <build architectureRef="biarch" name="Virtual Iron Image" containerTemplateRef="virtualIronImage">
         <stage ref="release"/>
         <imageGroup>group-bar</imageGroup>
      </build>
   </buildDefinition>
</productDefinition>
"""

class FileHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kw):
        pass

    def do_GET(self):
        fname = os.path.basename(self.path)
        # Do we have this file?
        fPath = os.path.join(pathManager.getPath('PACKAGE_CREATOR_SERVICE_ARCHIVE_PATH'), 'rpms',
                             fname)
        if not os.path.exists(fPath):
            self.send_response(404)
            self.end_headers()
            return
        # Get the file length
        s = os.stat(fPath)
        fileSize = s.st_size
        del s
        self.send_response(200)
        self.send_header("Content-Type", "application/x-rpm")
        self.send_header("Content-Length", fileSize)
        self.end_headers()
        util.copyStream(open(fPath), self.wfile)

class ReposTests(mint_rephelp.MintRepositoryHelper):
    def startHTTPServer(self):
        httpServer = mint_rephelp.rephelp.HTTPServerController(FileHandler)
        return httpServer

    def setUp(self):
        mint_rephelp.MintRepositoryHelper.setUp(self)
        self.setUpProductDefinition()
        self.httpServer = self.startHTTPServer()

    def tearDown(self):
        self.httpServer.close()
        self.httpServer = None
        mint_rephelp.MintRepositoryHelper.tearDown(self)

    def _saveProdDef(self):
        prodDefDict = dict(hostname = 'localhost', shortname = 'myprod',
                 namespace = 'mycompany', version = '1.0')

        self.startMintServer(1)
        client = conaryclient.ConaryClient(self.cfg)

        # OK, we need to save the product definition first
        pd = pcreator.backend.proddef.ProductDefinition(fromStream = prodDef1)
        pd.setConaryRepositoryHostname('localhost')
        pd.setConaryNamespace('mycompany')
        pd.setProductShortname('myprod')
        pd.setProductVersion('1.0')

        pd.saveToRepository(client)
        return prodDefDict

    def _createFactories(self, recipesToBuild = ['factory-rpm']):
        fakedTroves = [
        'bash:runtime',
        'bzip2:runtime',
        'conary-build:lib',
        'conary-build:python',
        'conary-build:runtime',
        'conary:python',
        'conary:runtime',
        'coreutils:runtime',
        'cpio:runtime',
        'dev:runtime',
        'filesystem:runtime',
        'findutils:runtime',
        'gawk:runtime',
        'grep:runtime',
        'gzip:runtime',
        'patch:runtime',
        'python:lib',
        'python:runtime',
        'sed:runtime',
        'setup:runtime',
        'sqlite:lib',
        'tar:runtime',
    ]
        recipedir = pathManager.getPath('PACKAGE_CREATOR_SERVICE_FACTORY_PATH')

        if 'factory-base-packagecreator' not in recipesToBuild:
            recipesToBuild.insert(0, 'factory-base-packagecreator')
        client = self.getConaryClient()
        repos = client.getRepos()
        factoryLabel = versions.Label('localhost@rpath:factories')
        for i, ft in enumerate(fakedTroves):
            self.addComponent(ft, filePrimer = 1000 + i)
        self.updatePkg(fakedTroves, noRestart = True)

        # We need to change baseClassDir, otherwise the recipe lives in /tmp
        # and doesn't get packaged
        oldBaseClassDir = self.cfg.baseClassDir

        oldBuildLabel = self.cfg.buildLabel
        try:
            self.cfg.baseClassDir = "/usr/share/conary/baseclasses"
            self.cfg.buildLabel = factoryLabel

            superclassContents = file(os.path.join(recipedir, 'rpm-import',
                    "rpm-import.recipe")).read()
            superclassContents = superclassContents.replace(
                                "rpmUrl = ''",
                                "rpmUrl = 'http://localhost:%s/some/path'" %
                                            self.httpServer.port)

            self.makeSourceTrove('rpm-import', superclassContents)

            cookedFactories = []
            for recipe in recipesToBuild:
                recipePath = os.path.join(recipedir, recipe)
                pathDict = {}
                for fn in os.listdir(recipePath):
                    fileObj = filetypes.RegularFile( \
                            contents = open(os.path.join(recipePath, fn)))
                    pathDict[fn] = fileObj
                chLog = changelog.ChangeLog(name = 'test', contact = '')
                factory = recipe.startswith('factory-') and 'factory' or None
                cs = client.createSourceTrove('%s:source' % recipe,
                        factoryLabel, '1.0', pathDict, chLog,
                        factory = factory)
                repos.commitChangeSet(cs)
                built = self.cookFromRepository(recipe, logBuild = True)
                # Grab the :recipe component
                cookedFactories.append((recipe, built[0][1], built[0][2]))

            # Now cook the group
            trv = self.addCollection('group-factories', '1.0',
                    cookedFactories)
        finally:
            self.cfg.buildLabel = oldBuildLabel
            self.cfg.baseClassDir = oldBaseClassDir

    def testUploadFileXMLRPC(self):
        self.startMintServer()
        repos = self.openRepository()
        pDefDict = self._saveProdDef()
        self._createFactories(['factory-archive'])

        packageCreatorURL = self.mintCfg.packageCreatorURL
        pid = 0
        try:
            pccfg = pcreator.config.PackageCreatorServiceConfiguration()
            pccfg.storagePath =  os.path.join(self.workDir,
                    'pcreator', 'storagePath')
            pccfg.tmpFileStorage = os.path.join(self.workDir,
                    'pcreator', 'tmpFileStorage')
            hostname = '%s.%s' %(MINT_HOST, MINT_DOMAIN)
            port, pid = pcreator.server.getServer(pccfg, hostname)
            url = 'http://%s:%s' % (hostname, port)
            self.mintCfg.packageCreatorURL = url
            client, userId = self.quickMintUser('testuser', 'testpass')
            pClient = packagecreator.getPackageCreatorClient(self.mintCfg,
                    ('testuser', 'testpass'),
                    djangoManager=rbuildermanager.RbuilderManager())
            mincfg = packagecreator.MinimalConaryConfiguration(self.cfg)
            sesH = pClient.startSession(pDefDict, mincfg)
            tarFile = 'logrotate-3.7.1.tar.gz'
            filePath = os.path.join(pathManager.getPath('CONARY_ARCHIVE_PATH'), tarFile)
            pClient.uploadData(sesH, tarFile, filePath, 'application/x-rpm')
            res = pClient.getCandidateBuildFactories(sesH)
            self.assertEquals([x[0] for x in res],
                    ['archive=/localhost@rpath:factories/1.0-1-1'])
        finally:
            if pid:
                os.kill(pid, signal.SIGKILL)
            self.mintCfg.packageCreatorURL = packageCreatorURL

class RecipeManipulationTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testRecipeManipulation(self, data, db):
        client = self.getClient('owner')
        # Fake a session handle
        sesH = "Blah-blah-blah"
        dataPath = os.path.join(self.cfg.dataPath, 'tmp', 'users', 'owner', sesH)
        conary.lib.util.mkdirChain(dataPath)
        modePath = os.path.join(dataPath, 'mode')
        for mode in ('package-creator', 'appliance-creator'):
            f = open(modePath, 'w')
            f.write(json.dumps(mode))
            f.close()
            isDefault, recipe = client.getPackageCreatorRecipe(sesH)
            self.failUnless('asserts no copyright claim on this interface' \
                    in recipe)
            self.assertEquals(isDefault, True)

            refRecipe = 'completely busted\n'
            client.savePackageCreatorRecipe(sesH, refRecipe)
            isDefault, newRecipe = client.getPackageCreatorRecipe(sesH)
            self.assertEquals(newRecipe, refRecipe)
            self.assertEquals(isDefault, False)

            # now prove that submitting an empty recipe restores the defaults
            client.savePackageCreatorRecipe(sesH, '')
            isDefault, newRecipe = client.getPackageCreatorRecipe(sesH)
            self.assertEquals(newRecipe, recipe)
            self.assertEquals(isDefault, True)


if __name__ == '__main__':
    testsuite.main()

