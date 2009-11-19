#!/usr/bin/python
import StringIO
import testsetup
from testutils import mock

from rpath_proddef import api1 as proddef

from mint import mint_error

from mint import userlevels
from mint.rest import errors
from mint.rest.api import models
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

    def _getPlatform(self):
        # Set up the platforms in the db before enabling it.
        self.db.getPlatforms()
        platformId = 1

        # This data should match what's setup in the cfg,
        # and platform defn
        p = models.Platform(platformName='Crowbar Linux 1',
                            hostname='localhost',
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


