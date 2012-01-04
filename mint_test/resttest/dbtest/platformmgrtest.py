#!/usr/bin/python
import testsetup
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
        self.db.productMgr.reposMgr._mock.enableByDefault()
        self.db.productMgr.reposMgr._mock.disable('createRepository')
        self.db.productMgr.reposMgr._mock.disable('_generateConaryrcFile')
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
        plat = self.db.db.platforms.get(p.platformId)

        self.failUnlessEqual(plat['hidden'], True)


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
        uri = mock.MockObject()
        uri.encode._mock.setDefaultReturn(u'http://no.such.host/1234')
        platformLoad._mock.set(loadUri=uri)

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

        called = lookasideObj._fetchUrl._mock.popCall()
        self.failUnlessEqual(called,
            (('http://no.such.host/1234', {}), ()))
        # And make sure it's unicode
        self.failUnless(isinstance(called[0][0], unicode))

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

        self.db.platformMgr.getPlatforms()

        self.assertEquals(
            len(platformmgr.PlatformDefCache._getPlatDef._mock.calls),
            2)

    def testProxySettingsPropagated(self):
        proxies = dict(http = "https://blah.com:12345",
                       https = "https://blah.com:12345")
        db = self.openRestDatabase()
        db.cfg.proxy.update(proxies)
        src = db.platformMgr.contentSourceTypes._getSourceTypeInstanceByName('RHN')
        self.assertEqual(src.proxyMap.filterList[0][1],
                [req_mod.URL('https://blah.com:12345')])
        self.assertEqual(src.proxyMap.filterList[1][1],
                [req_mod.URL('https://blah.com:12345')])

    def testPlatformsLinkedToSources(self):
        # list platforms and sources so they're created
        plats = self.db.getPlatforms()
        # This adds the sources
        self.db.getSources('RHN')
        self.db.getSources('satellite')

        # add a new platform
        platformId = 3
        self.setupPlatform3()

        # get the new platform
        newPlatforms = self.db.getPlatforms()
        newPlatform = [x for x in newPlatforms.platforms \
            if x.label == 'localhost@rpath:plat-3'][0]
        newPlatSources = self.db.getSourcesByPlatform(newPlatform.platformId)
        
        # verify the added platform was linked to sources
        self.failUnlessEqual([x.contentSourceType \
            for x in newPlatSources.instance], ['RHN', 'RHN'])

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

    def testGetDescriptor(self):
        rc = self.getRestClient()
        for cst in platformmgr.contentsources.contentSourceTypes:
            if cst not in self.Descriptors:
                self.fail("Missing descriptor test for %s" % cst)
            descr = self.db.getSourceTypeDescriptor(cst)
            xml = rc.convert('xml', None, descr)
            self.assertXMLEquals(xml, self.Descriptors[cst])

    Descriptors = dict(
        RHN = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Red Hat Network</displayName>
    <descriptions>
      <desc>Red Hat Network Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
  </dataFields>
</configDescriptor>
""",
        satellite = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Red Hat Satellite</displayName>
    <descriptions>
      <desc>Red Hat Satellite Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
    <field>
      <name>sourceUrl</name>
      <required>true</required>
      <descriptions>
        <desc>Source URL</desc>
      </descriptions>
      <prompt>
        <desc>Source URL</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
      <constraints>
        <descriptions>
          <desc>URL must begin with ftp://, http://, or https://</desc>
        </descriptions>
        <regexp>^(http|https|ftp):\/\/.*</regexp>
      </constraints>
    </field>
  </dataFields>
</configDescriptor>
""",
        proxy = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Red Hat Proxy</displayName>
    <descriptions>
      <desc>Red Hat Proxy Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
    <field>
      <name>sourceUrl</name>
      <required>true</required>
      <descriptions>
        <desc>Source URL</desc>
      </descriptions>
      <prompt>
        <desc>Source URL</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
      <constraints>
        <descriptions>
          <desc>URL must begin with ftp://, http://, or https://</desc>
        </descriptions>
        <regexp>^(http|https|ftp):\/\/.*</regexp>
      </constraints>
    </field>
  </dataFields>
</configDescriptor>
""",
        nu = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Novell Update Service</displayName>
    <descriptions>
      <desc>Novell Update Service Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
  </dataFields>
</configDescriptor>
""",
        SMT = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Subscription Management Tool</displayName>
    <descriptions>
      <desc>Subscription Management Tool Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>false</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>false</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
    <field>
      <name>sourceUrl</name>
      <required>true</required>
      <descriptions>
        <desc>Source URL</desc>
      </descriptions>
      <prompt>
        <desc>Source URL</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
      <constraints>
        <descriptions>
          <desc>URL must begin with ftp://, http://, or https://</desc>
        </descriptions>
        <regexp>^(http|https|ftp):\/\/.*</regexp>
      </constraints>
    </field>
  </dataFields>
</configDescriptor>
""",
    repomd = """\
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Yum Repository</displayName>
    <descriptions>
      <desc>Yum Repository Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>false</required>
      <descriptions>
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>false</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
    <field>
      <name>sourceUrl</name>
      <required>true</required>
      <descriptions>
        <desc>Source URL</desc>
      </descriptions>
      <prompt>
        <desc>Source URL</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
      <constraints>
        <descriptions>
          <desc>URL must begin with ftp://, http://, or https://</desc>
        </descriptions>
        <regexp>^(http|https|ftp):\/\/.*</regexp>
      </constraints>
    </field>
  </dataFields>
</configDescriptor>
""",
)

if __name__ == "__main__":
        testsetup.main()

