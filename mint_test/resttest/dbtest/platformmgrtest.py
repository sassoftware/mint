#!/usr/bin/python
import StringIO
import testsetup
from testutils import mock

from rpath_proddef import api1 as proddef

from mint import mint_error

from mint import userlevels
from mint.db import repository as reposdb
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import platformmgr
from mint.rest.db import reposmgr

from mint_test import mint_rephelp
from mint_test.resttest.apitest import restbase

class PlatformManagerTest(restbase.BaseRestTest):

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()
        self.setupPlatforms()
        self.db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(self.db, 'admin')
        mock.mock(platformmgr.Platforms, '_checkMirrorPermissions',
                        True)

    def _getPlatform(self):
        # Set up the platforms in the db before enabling it.
        self.db.getPlatforms()
        platformId = 1

        # This data should match what's setup in the cfg,
        # and platform defn
        p = models.Platform(platformName='Crowbar Linux 1',
                            label='localhost@rpath:plat-1',
                            mode='manual',
                            platformId=platformId,
                            enabled=1)
        return p                            

    def _getProductId(self):
        # Create an external project that matches the platform's label, but is
        # not external.
        product = models.Product(name='Crowbar Internal',
                    hostname='localhost', domainname='',
                    shortname='crowbar', hidden=0, projecturl='',)
        productId = self.db.productMgr.createProduct(product.name, 
                              product.description, product.hostname,
                              product.domainname, product.namespace,
                              product.projecturl,
                              product.shortname, product.prodtype,
                              product.version,
                              product.commitEmail, 
                              isPrivate=product.hidden)

        return productId

    def testEnablePlatformNoProject(self):
        p = self._getPlatform()
        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p.platformId)

        # assert projectId was set for the platform
        self.assertTrue(plat['projectId'] is not None)
        # should be 2, i guess this could change if fixture data changes much
        self.assertEquals(plat['projectId'], 2)

    def testEnablePlatformProjectNotExternal(self):
        p = self._getPlatform()
        productId = self._getProductId()

        mock.mockFunctionOnce(self.db.db.projects, 'getProjectIdByFQDN',
            productId)

        self.assertRaises(errors.InvalidProjectForPlatform, 
            self.db.updatePlatform, p.platformId, p)

    def testEnablePlatformProjectNoMirror(self):
        p = self._getPlatform()
        productId = self._getProductId()
        self.db.db.projects.update(productId, external=1)

        self.db.productMgr.reposMgr = mock.MockInstance(
                                       reposmgr.RepositoryManager)
        self.db.productMgr.reposMgr._mock.enableMethod('addIncomingMirror')
        self.db.productMgr.reposMgr._mock.enableMethod('_getFqdn')
        self.db.productMgr.reposMgr._mock.enableMethod('_getNextMirrorOrder')
        self.db.productMgr.reposMgr._mock.enableByDefault()
        self.db.productMgr.reposMgr._mock.disable('createRepository')
        self.db.productMgr.reposMgr._mock.disable('_generateConaryrcFile')
        self.db.productMgr.reposMgr.db = self.db

        mock.mockFunctionOnce(self.db.db.projects, 'getProjectIdByFQDN',
            productId)

        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p.platformId)

        # assert projectId was set for the platform
        self.assertTrue(plat['projectId'] is not None)
        # assert productId matches the product we created
        self.assertEquals(plat['projectId'], productId)

        mirrorId = self.db.db.inboundMirrors.getIdByColumn('targetProjectId',
                    productId)

        # should be the first mirror created
        self.assertEquals(mirrorId, 1)

    def testEnablePlatformProject(self):
        p = self._getPlatform()
        productId = self._getProductId()

        mirrorId = self.db.db.inboundMirrors.new(
                targetProjectId=productId,
                sourceLabels = 'label',
                sourceUrl = 'url', 
                sourceAuthType='entitlement',
                sourceUsername = 'username',
                sourcePassword = 'password',
                sourceEntitlement = 'entitlement',
                mirrorOrder = 0, allLabels = 1)

        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p.platformId)

        # assert projectId was set for the platform
        self.assertTrue(plat['projectId'] is not None)
        # assert productId matches the product we created
        self.assertEquals(plat['projectId'], productId)

    def testLoadPlatformProxy(self):
        # CNY-6002: make sure the whole config is passed to lookaside.FileFinder
        p = self._getPlatform()
        productId = self._getProductId()

        mirrorId = self.db.db.inboundMirrors.new(
                targetProjectId=productId,
                sourceLabels = 'label',
                sourceUrl = 'url', 
                sourceAuthType='entitlement',
                sourceUsername = 'username',
                sourcePassword = 'password',
                sourceEntitlement = 'entitlement',
                mirrorOrder = 0, allLabels = 1)

        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p.platformId)

        platformLoad = mock.MockObject()
        platformLoad._mock.set(uri = 'http://no.such.host/1234')

        from conary.build import lookaside
        lookasideClass = mock.MockObject()
        lookasideObj = mock.MockObject()
        lookasideClass._mock.setDefaultReturn(lookasideObj)
        self.mock(lookaside, 'FileFinder', lookasideClass)

        # We could work harder and return a real changeset here, but for the
        # purposes of this test, an exception is fine
        lookasideObj._fetchUrl._mock.setDefaultReturn(None)

        # Set a proxy
        self.db.platformMgr.cfg.proxy = dict(http = "httpProxy",
            https = "httpsProxy")
        err = self.failUnlessRaises(errors.PlatformLoadFileNotFound,
            self.db.platformMgr.platforms.load, p.platformId, platformLoad)
        called = lookasideClass._mock.popCall()
        self.failUnlessEqual(called,
            ((None, None), (('cfg', self.db.platformMgr.cfg), )))

    def testCreateDuplicatePlatform(self):
        p = self._getPlatform()
        p.platformId = 1
        p._sourceTypes = []

        mock.mock(platformmgr.log, 'error')
        
        self.db.platformMgr.platforms._create(p)
        platformmgr.log.error._mock.assertCalled('Error creating platform '
            'localhost@rpath:plat-1, it must already exist: Duplicate '
            'item in platforms')

    def testNoPlatDefLocalRepo(self):
        # simulate that a different platform source label was found
        mock.unmockAll()
        mock.mock(platformmgr.PlatformDefCache, '_getPlatDef')
        platformmgr.PlatformDefCache._getPlatDef._mock.raiseErrorOnAccess(
            proddef.ProductDefinitionTroveNotFoundError)
        platformmgr.PlatformDefCache._getPlatDef._mock.setDefaultReturn(None)
        mock.mock(reposmgr.RepositoryManager, 'getIncomingMirrorUrlByLabel')
        reposmgr.RepositoryManager.getIncomingMirrorUrlByLabel._mock.setReturn(
            'localhost@rpath:plat-1', 'localhost@rpath:plat-1')
        mock.mock(reposdb.RepositoryManager, 'getServerProxy')
        reposdb.RepositoryManager.getServerProxy._mock.setReturn(
            self.cclient.repos.c.cache['localhost'],
            'localhost', 'localhost@rpath:plat-1', None, [None])

        self.db.platformMgr.getPlatforms()

        self.assertEquals(3,
            len(platformmgr.PlatformDefCache._getPlatDef._mock.calls))

    def testProxySettingsPropagated(self):
        proxies = dict(http = "http://blah.com:1234",
                       https = "https://blah.com:12345")
        db = self.openRestDatabase()
        db.cfg.proxy.update(proxies)
        src = db.platformMgr.contentSourceTypes._getSourceTypeInstanceByName('RHN')
        self.failUnlessEqual(src.proxies, proxies)

    def testPlatformsLinkedToSources(self):
        # list platforms and sources so they're created
        plats = self.db.getPlatforms()
        sources = self.db.getSources('RHN')
        sources = self.db.getSources('satellite')

        # add a new platform
        platformId = 3
        self.mintCfg.availablePlatforms.append('localhost@rpath:plat-3')
        self.setupPlatform3()

        # get the new platform
        newPlatforms = self.db.getPlatforms()
        newPlatform = [x for x in newPlatforms.platforms \
            if x.label == 'localhost@rpath:plat-3'][0]
        newPlatSources = self.db.getSourcesByPlatform(newPlatform.platformId)
        
        # verify the added platform was linked to sources
        self.failUnlessEqual(len(newPlatSources.instance), 2)
        self.failUnlessEqual([x.contentSourceType \
            for x in newPlatSources.instance], ['RHN', 'RHN'])


if __name__ == "__main__":
        testsetup.main()

