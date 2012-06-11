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

from mint_test import fixtures
from mint_test import mint_rephelp

from conary import versions as conaryver
from conary.deps import deps as conarydeps
from conary import conaryclient

import pcreator
public = pcreator.common.public

from rpath_proddef import api1 as proddef

class MockedAppCreatorTest(fixtures.FixturedUnitTest):
    """ Unit Tests the MintClient and corresponding MintServer methods,
    but mocks out almost all pcreator methods."""

    def _setupMock(self, sessH = 'ses-123'):
        self.mock(pcreator.backend.BaseBackend, '_startApplianceSession',
                public(lambda *args, **kwargs:
                    (sessH, dict(isApplianceCreatorManged = True))))

    @fixtures.fixture('Full')
    def testStartApplianceSession(self, db, data):
        refSesH = 'ses-bogus'
        self._setupMock(refSesH)

        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        self.assertEquals(sesH, refSesH)

    @fixtures.fixture('Full')
    def testListApplianceTroves(self, db, data):
        self._setupMock()

        refTroveList = ['foo', 'bar']
        troveList = {'explicitTroves': ['foo', 'bar'],
                    'implicitTroves': ['not', 'listed']}
        self.mock(pcreator.backend.BaseBackend, '_listTroves',
                public(lambda *args, **kwargs: troveList))
        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        troveList = client.listApplianceTroves(data['projectId'], sesH)
        self.assertEquals(troveList, refTroveList)

    @fixtures.fixture('Full')
    def testSetApplianceTroves(self, db, data):
        self._setupMock()

        troveList = {'explicitTroves': ['foo', 'bar'],
                    'implicitTroves': ['not', 'listed']}
        self.mock(pcreator.backend.BaseBackend, '_listTroves',
                public(lambda *args, **kwargs: troveList))

        self.setCall = []

        @public
        def MockedSetTroves(x, sesH, explicitTroves, implicitTroves):
            self.setCall = (explicitTroves, implicitTroves)
            return True
        self.mock(pcreator.backend.BaseBackend, '_setTroves', MockedSetTroves)
        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        client.setApplianceTroves(sesH, ['test', 'list'])
        self.assertEquals(self.setCall, (['test', 'list'], ['not', 'listed']))

    @fixtures.fixture('Full')
    def testAddApplianceTrove(self, db, data):
        self._setupMock()

        self.addCall = []
        @public
        def MockedAddTrove(x, sesH, troveList, explicit):
            self.addCall = (troveList, explicit)
            return True
        self.mock(pcreator.backend.BaseBackend, '_addTrove', MockedAddTrove)
        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        client.addApplianceTrove(sesH, 'test')
        self.assertEquals(self.addCall, ('test', True))

    @fixtures.fixture('Full')
    def testMakeApplianceTrove(self, db, data):
        self._setupMock()
        self.called = False
        @public
        def MockedMakeTrove(x, sesH):
            self.called = True
            # bogus rMake jobId
            return 0
        self.mock(pcreator.backend.BaseBackend,
                '_makeApplianceTrove', MockedMakeTrove)
        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        client.makeApplianceTrove(sesH)
        self.failIf(not self.called, "Expected makeApplianceTrove to be called")

    @fixtures.fixture('Full')
    def testAddApplianceSearchPathsFail(self, db, data):
        self._setupMock()

        self.setCall = []

        @public
        def MockedAddApplianceSearchPaths(x, sesH, searchPaths):
            raise pcreator.backend.errors.TroveSpecError("teh 3rr0r")
        self.mock(pcreator.backend.BaseBackend,
                '_addSearchPaths', MockedAddApplianceSearchPaths)

        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        err = self.failUnlessRaises(mint_rephelp.mint_error.SearchPathError,
            client.addApplianceSearchPaths, sesH, ['test1==foo@bar:1'])
        self.failUnlessEqual(str(err), 'teh 3rr0r')


    @fixtures.fixture('Full')
    def testAddApplianceSearchPaths(self, db, data):
        self._setupMock()

        self.setCall = []

        @public
        def MockedAddApplianceSearchPaths(x, sesH, searchPaths):
            self.setCall.extend(searchPaths)
            return self.setCall
        self.mock(pcreator.backend.BaseBackend,
                '_addSearchPaths', MockedAddApplianceSearchPaths)
        @public
        def MockedListApplianceSearchPaths(x, sesH):
            return ['a', 'b', 'c']
        self.mock(pcreator.backend.BaseBackend,
                '_listSearchPaths', MockedListApplianceSearchPaths)

        client = self.getClient('owner')
        sesH, otherInfo = client.startApplianceCreatorSession(data['projectId'], 1, False)
        ret = client.addApplianceSearchPaths(sesH, ['test1=foo@bar:1'])
        self.failUnlessEqual(ret, ['test1=foo@bar:1'])

        ret = client.listApplianceSearchPaths(sesH)
        self.failUnlessEqual(ret, ['a', 'b', 'c'])

class AppCreatorTest(mint_rephelp.MintRepositoryHelper):
    """ Unit Tests the MintClient and corresponding MintServer methods,
    TroveBuilder is generally mocked out."""

    def _setupMock(self, sessH = 'ses-123'):
        self.mock(pcreator.backend.BaseBackend, '_startApplianceSession',
                public(lambda *args, **kwargs:
                    (sessH, dict(isApplianceCreatorManged = True))))

    def setUp(self):
        mint_rephelp.MintRepositoryHelper.setUp(self)

        self.mintClient, self.userId = self.quickMintUser('foouser', 'foopass')
        hostName = 'prodtest'
        fqdn = "%s.%s" % (hostName, mint_rephelp.MINT_PROJECT_DOMAIN)
        self.projectId = self.mintClient.newProject( \
                'Test Project', hostName, mint_rephelp.MINT_PROJECT_DOMAIN,
                shortname = hostName, namespace = hostName,
                prodtype="Appliance", version = '1')
        self.versionId = self.mintClient.addProductVersion( \
                self.projectId, hostName, '1')
        prodVersion = self.mintClient.getProductVersion(self.versionId)
        self.prodDef = proddef.ProductDefinition()

        self.prodDef.setConaryRepositoryHostname(fqdn)
        self.prodDef.setConaryNamespace(prodVersion['namespace'])
        self.prodDef.setProductShortname(hostName)
        self.prodDef.setProductVersion(prodVersion['name'])

        self.prodDef.setProductName("Test Product")
        self.prodDef.setProductDescription("Test Product")
        self.prodDef.setProductVersionDescription("Test Product 1.0")
        self.prodDef.setImageGroup("group-%s" % prodVersion['namespace'])
        self.prodDef.setBaseFlavor('')
        self.prodDef.addStage(name = "Development", labelSuffix = "-devel")
        self.prodDef.addStage(name = "QA", labelSuffix = "-qa")
        self.prodDef.addStage(name = "Release", labelSuffix = "")

        self.prodDef.addArchitecture('x86', '32 bit', 'is: x86')
        self.prodDef.addArchitecture('x86_64', '64 bit', 'is: x86_64')

        self.prodDef.addBuildDefinition(name = "'x86 Installable ISO Build",
            architectureRef = 'x86',
            image = self.prodDef.imageType('installableIsoImage'),
            stages = ['Development', 'QA', 'Release'])

        self.prodDef.addBuildDefinition(name = "'x86_64 Installable ISO Build",
            architectureRef = 'x86_64',
            image = self.prodDef.imageType('installableIsoImage'),
            stages = ['Development', 'QA', 'Release'])

        project = self.mintClient.getProject(self.projectId)
        cfg = project.getConaryConfig()
        cClient = conaryclient.ConaryClient(cfg)
        self.prodDef.saveToRepository(cClient)

        self.productDefinitionDict = \
                {'hostname': fqdn,
                'namespace': prodVersion['namespace'],
                'shortname': hostName,
                'version': prodVersion['name']}

        # we're going to mock some of the deeper functionality becuase we're
        # trying to test compatibility with the public interface
        # mostly factory and build related functions will be mocked.
        self.mock(pcreator.backend.BaseBackend, '_getApplianceFactoryName',
                public(lambda *args, **kwargs: 'factory-group-base'))

        self.mock(pcreator.backend.BaseBackend, '_buildableFactorySource',
                public(lambda *args, **kwargs: True))

        # mock the actual building because rMake probably isn't present
        self.mock(pcreator.backend.TroveBuilder, 'build',
                lambda *args, **kwargs: 0)

    def testTroveManipulation(self):
        sesH, otherInfo = self.mintClient.startApplianceCreatorSession( \
                self.projectId, self.versionId, False)
        self.mintClient.addApplianceTrove(sesH, 'foo')
        trvs = self.mintClient.listApplianceTroves(self.projectId, sesH)
        self.assertEquals(trvs, ['foo'])
        trvs = self.mintClient.listApplianceTroves(self.projectId, sesH)
        ['foo', 'test=localhost@rpl:1']
        refTrvList = ['widd', 'biff', 'pinko', 'fwee']
        self.mintClient.setApplianceTroves(sesH, refTrvList)
        trvs = self.mintClient.listApplianceTroves(self.projectId, sesH)
        self.assertEquals(trvs, refTrvList)

    def testFilterApplianceTroveFailedBuilds(self):
        recipeStr = """
class TestRecipe(PackageRecipe):
    name="testpkg%s"
    version="1.0"
    clearBuildReqs()
    def setup(r):
        r.Create('/srv/foo%s', contents="jack sprat")
"""
        sesH, otherInfo = self.mintClient.startApplianceCreatorSession( \
                self.projectId, self.versionId, False)
        project = self.mintClient.getProject(self.projectId)
        repos = self.mintClient.server._server._getProjectRepo(project)
        bar = self.addComponent('testpkgzero:runtime', '%s/1.0' % 
            self.prodDef.getDefaultLabel(), repos=repos)
        self.mintClient.addApplianceTrove(sesH, bar.getName())
        fooone = self.addComponent('testpkgone:source', '%s/1.0' %
            self.prodDef.getDefaultLabel(), fileContents= [ ('testpkgone.recipe',
                recipeStr % ('one', 'one')) ], repos = repos)
        self.mintClient.addApplianceTrove(sesH, '='.join((fooone.getName(), fooone.getVersion().asString())))
        footwo = self.addComponent('testpkgtwo:source', '%s/1.0' %
            self.prodDef.getDefaultLabel(), fileContents= [ ('testpkgtwo.recipe',
                recipeStr % ('two', 'two')) ], repos = repos)
        self.mintClient.addApplianceTrove(sesH, '='.join((footwo.getName(), footwo.getVersion().asString())))
        self.cookFromRepository('testpkgtwo', conaryver.Label(self.prodDef.getDefaultLabel()), repos=repos)
        l = self.mintClient.listApplianceTroves(self.projectId, sesH)
        self.assertEquals(set(l), set(['testpkgtwo', 'testpkgzero:runtime']))

    def _makeApplianceTrove(self, rebuild, troveName, troveList, label):
        sesH, otherInfo = self.mintClient.startApplianceCreatorSession( \
                self.projectId, self.versionId, rebuild, label)
        self.mintClient.addApplianceTrove(sesH, troveName)
        self.mintClient.makeApplianceTrove(sesH)
        project = self.mintClient.getProject(self.projectId)
        cfg = project.getConaryConfig()
        cClient = conaryclient.ConaryClient(cfg)
        repos = cClient.getRepos()
        nvf = repos.findTrove(None, ("%s:source" % self.prodDef.getImageGroup(),
            label, None))
        fileDict = cClient.getFilesFromTrove(*nvf[0])
        self.assertEquals(sorted(fileDict.keys()),
                ['appliance-manifest.xml', 'group-prodtest.recipe'])
        manifestFileObj = fileDict['appliance-manifest.xml']
        manifestData = manifestFileObj.read()
        for refTrvName in troveList:
            assert ('<trove>%s</trove>' % refTrvName) in manifestData
        manifest = pcreator.appmanifest.ApplianceManifest( \
                fromStream = manifestData)
        self.assertEquals([x for x in manifest.iterTroves(explicit = True)],
                troveList)
        self.assertEquals([x for x in manifest.iterTroves(implicit = True)], [])

    def testMakeApplianceTrove(self):
        self._makeApplianceTrove(False, 'foo', ['foo'], 'prodtest.rpath.local2@prodtest:prodtest-1-qa')

    def testRebuildApplianceTrove(self):
        self._makeApplianceTrove(True, 'bar', ['bar'], 'prodtest.rpath.local2@prodtest:prodtest-1-devel')

    def testRebuildApplianceTrove2(self):
        self._makeApplianceTrove(False, 'foo', ['foo'], 'prodtest.rpath.local2@prodtest:prodtest-1')

    def testGetAvailablePackages(self):
        self._setupMock()

        retTroveList = \
            [
                [
                    ('foo-package', '/foo@foo:foo/0.000:1.0.1-1-1', '1#x86')
                    #Frozen strings since this is how the server returns them
                ]
            ]
        refTroveList = []
        for label in retTroveList:
            refTroveList.append([(x[0], conaryver.ThawVersion(x[1]), conarydeps.ThawFlavor(x[2])) for x in label])
        self.avail_called = False
        def _getAvailPackages(s, sesH, refresh):
            self.avail_called = True
            return retTroveList
        self.mock(pcreator.backend.BaseBackend, '_getAvailablePackages',
                public(_getAvailPackages))
        sesH, otherInfo = self.mintClient.startApplianceCreatorSession(self.projectId, 1, False)
        troveList = self.mintClient.getAvailablePackages(sesH)
        self.assertEquals(troveList, refTroveList)
        self.failUnless(self.avail_called)

        #call again to test built in caching
        self.avail_called=False
        troveList = self.mintClient.getAvailablePackages(sesH)
        self.assertEquals(troveList, refTroveList)


if __name__ == '__main__':
    testsuite.main()

