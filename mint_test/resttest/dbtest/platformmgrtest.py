#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from testutils import mock

from rpath_proddef import api1 as proddef

from conary.lib.http import request as req_mod
from mint.db import repository as reposdb
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import platformmgr
from mint.rest.db import reposmgr

from mint_test.resttest.apitest import restbase

class PlatformManagerTest(restbase.BaseRestTest):

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()
        self.setupPlatforms()
        self.db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(self.db, 'admin')
        from mint import config
        from mint.scripts import pkgindexer
        self.mock(pkgindexer.PackageIndexer, 'cfgPath', config.RBUILDER_CONFIG)

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
                            configurable=True,
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

    def _mockReposMgr(self):
        self.db.productMgr.reposMgr = mock.MockInstance(
                                       reposmgr.RepositoryManager)
        self.db.productMgr.reposMgr._mock.enableMethod('addIncomingMirror')
        self.db.productMgr.reposMgr._mock.enableMethod('addUserByMd5')
        self.db.productMgr.reposMgr._mock.enableMethod('_getFqdn')
        self.db.productMgr.reposMgr._mock.enableMethod('_getNextMirrorOrder')
        self.db.productMgr.reposMgr._mock.enableMethod('_isProductExternal')
        self.db.productMgr.reposMgr._mock.enableMethod('getIncomingMirrorUrlByLabel')
        self.db.productMgr.reposMgr._mock.enableByDefault()
        self.db.productMgr.reposMgr._mock.disable('createRepository')
        self.db.productMgr.reposMgr._mock.disable('getAdminClient')
        self.db.productMgr.reposMgr._mock.disable('_getRepositoryHandle')
        self.db.productMgr.reposMgr._mock.disable('_getRepositoryServer')
        self.db.productMgr.reposMgr._mock.disable('_getRoleForLevel')
        self.db.productMgr.reposMgr.db = self.db

    def testEnablePlatformNoProject(self):
        self._mockReposMgr()
        p = self._getPlatform()
        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p.platformId)

        # assert projectId was set for the platform
        self.assertTrue(plat['projectId'] is not None)
        # should be 2, i guess this could change if fixture data changes much
        self.assertEquals(plat['projectId'], 2)

    def testEnablePlatformProjectNoMirror(self):
        self._mockReposMgr()
        p = self._getPlatform()
        productId = self._getProductId()
        self.db.db.projects.update(productId, external=1)

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

    def testHidePlatform(self):
        self._mockReposMgr()
        p = self._getPlatform()
        p.hidden = True

        p2 = self.db.updatePlatform(p.platformId, p)
        plat = self.db.db.platforms.get(p2.platformId)

        self.failUnlessEqual(plat['hidden'], True)

    def testCreateDuplicatePlatform(self):
        p = self._getPlatform()
        p.platformId = 1
        p._sourceTypes = []

        mock.mock(platformmgr.log, 'error')
        
        self.db.platformMgr.platforms._create(p, None)
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
        mgr = self.db.platformMgr.platformCache.getReposMgr()
        mgr.db.isOffline._mock.setDefaultReturn(False)

        self.db.platformMgr.getPlatforms()

        self.assertEquals(
            len(platformmgr.PlatformDefCache._getPlatDef._mock.calls),
            3)

    def testPlatformsNoCfg(self):
        # Make sure that simply adding the platform to the DB will
        # successfully expose it
        plats = self.db.getPlatforms()
        self.failUnlessEqual(sorted(x.label for x in plats.platforms),
            ['localhost@rpath:plat-1', 'localhost@rpath:plat-2'])

        self.setupPlatform3()
        plats = self.db.getPlatforms()
        self.failUnlessEqual(sorted(x.label for x in plats.platforms),
            ['localhost@rpath:plat-1', 'localhost@rpath:plat-2',
            'localhost@rpath:plat-3'])
