#!/usr/bin/python
import StringIO
import testsetup
from testutils import mock

from rpath_proddef import api1 as proddef

from mint import mint_error

from mint import userlevels
from mint.rest import errors
from mint.rest.api import models

from mint_test import mint_rephelp

class ProductManagerTest(mint_rephelp.MintDatabaseHelper):
    def testGetAndCreateProductVersion(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        prd = models.Product(name='Project foo',
                             hostname='foo',
                             shortname='foo', prodtype='Appliance',
                             description='desc1', 
                             domainname='foo.bar.com', 
                             namespace='foons',
                             projectUrl='http://myproject1',
                             commitEmail='commitEmail1', 
                             backupExternal=False,
                             hidden=False)
        db.createProduct(prd)
        prd = models.Product(name='Project bar',
                             hostname='bar',
                             shortname='bar', prodtype='Appliance',
                             description='desc1', 
                             domainname='bar.bar.com', 
                             projectUrl='http://myproject2',
                             commitEmail='commitEmail2', 
                             backupExternal=True,
                             hidden=True)
        db.createProduct(prd)
        foo = db.getProduct('foo')
        bar = db.getProduct('bar')
        assert(foo.productId == 1)
        assert(bar.productId == 2)
        assert(foo.hostname == 'foo')
        assert(bar.hostname == 'bar')
        assert(foo.shortname == 'foo')
        assert(bar.shortname == 'bar')
        assert(foo.name == 'Project foo')
        assert(bar.name == 'Project bar')
        assert(foo.prodtype == 'Appliance')
        assert(bar.prodtype == 'Appliance')
        assert(not foo.hidden)
        assert(bar.hidden)
        assert(foo.repositoryHostname == 'foo.foo.bar.com')
        assert(bar.repositoryHostname == 'bar.bar.bar.com')
        assert(foo.timeCreated == foo.timeModified)
        assert(foo.namespace == 'foons')
        assert(bar.namespace == self.mintCfg.namespace)
        # TODO: test notify
        # TODO: test errors - make sure repository is not left in bad state.
        # make sure error in notify plugin does the right thing.
        # test creation of label map.

    def testListProducts(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('user1', admin=False)
        self.createUser('user2', admin=False)
        # One public product from an admin user
        self.createProduct('foo0', owners=['admin'], db=db, private=False)
        # One private product from an admin user
        self.createProduct('foo1', owners=['admin'], db=db, private=True)
        # One public product from a non-admin user
        self.createProduct('bar0', owners=['user1'], db=db, private=False)
        # One private product with developer access for user2
        self.createProduct('bar1', owners=['user1'], developers=['user2'],
            db=db, private=True)
        # One private product with user access for user2
        self.createProduct('bar2', owners=['user1'], users=['user2'],
            db=db, private=True)
        # One private product
        self.createProduct('bar3', owners=['user1'], db=db, private=True)
        # Product owned by user2
        self.createProduct('baz', owners=['user2'], db=db, private=True)

        # User can't see other hidden projects
        self.setDbUser(db, 'user1')
        products = db.listProducts().products
        self.assertEqual([ x.shortname for x in products ],
            ['bar0', 'bar1', 'bar2', 'bar3', 'foo0', ])
        self.assertEqual([ x.role for x in products ],
            ['Owner', 'Owner', 'Owner', 'Owner', 'User', ])

        self.setDbUser(db, 'user2')
        products = db.listProducts().products
        self.assertEqual([ x.shortname for x in products ],
            ['bar0', 'bar1', 'bar2', 'baz', 'foo0', ])
        self.assertEqual([ x.role for x in products ],
            ['User', 'Developer', 'User', 'Owner', 'User', ])

        products = db.listProducts(roles=['Owner',]).products
        self.assertEqual([ x.shortname for x in products ],
            ['baz', ])

        products = db.listProducts(roles=['Developer',]).products
        self.assertEqual([ x.shortname for x in products ],
            ['bar1', ])

        products = db.listProducts(roles=['User',]).products
        self.assertEqual([ x.shortname for x in products ],
            ['bar0', 'bar2', 'foo0', ])

        products = db.listProducts(
                roles=['Owner', 'Developer', 'User']).products

        # Admin can see all projects; check sorting.
        self.setDbUser(db, 'admin')
        products = db.listProducts().products
        self.assertEqual([ x.shortname for x in products],
            [ 'bar0', 'bar1', 'bar2', 'bar3', 'baz', 'foo0', 'foo1', ])
        self.assertEqual([ x.role for x in products ],
            ['User', 'User', 'User', 'User', 'User', 'Owner', 'Owner', ])

        # List by role
        products = db.listProducts(roles=('Owner',)).products
        self.assertEqual([ x.shortname for x in products ],
            [ 'foo0', 'foo1', ])

        products = db.listProducts(
                roles=['Owner', 'Developer', 'User']).products
        self.assertEqual([ x.shortname for x in products ],
            [ 'bar0', 'bar1', 'bar2', 'bar3', 'baz', 'foo0', 'foo1', ])

        # Query limits; check sorting
        products = db.listProducts(limit=1).products
        self.assertEqual([ x.shortname for x in products ], [ 'bar0', ])

        # Query prodtype
        self.createProduct('bloop', owners=['user1'], db=db, private=True,
                           prodtype='Repository')

        products = db.listProducts(prodtype='repository').products
        self.assertEqual([ x.shortname for x in products ], [ 'bloop', ])

        products = db.listProducts(prodtype='appliance').products
        self.assertEqual([ x.shortname for x in products ],
            [ 'bar0', 'bar1', 'bar2', 'bar3', 'baz', 'foo0', 'foo1', ])

        products = db.listProducts(prodtype='foo').products
        self.assertEqual(len(products), 0)

    def testUpdateProduct(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db, private=True)
        product = db.getProduct('foo')
        assert(product.prodtype == 'Appliance')
        product.prodtype = 'Component'
        product.description = 'new desc'
        product.namespace = 'spiffynamespace'
        self.setDbUser(db, 'admin')
        db.updateProduct('foo', product)
        product = db.getProduct('foo')
        self.failUnlessEqual(product.namespace, 'spiffynamespace')
        assert(product.prodtype == 'Component')
        assert(product.description == 'new desc')

    def testGetProductVersion(self):
        db = self.openMintDatabase(createRepos=True)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', namespace='ns', 
                                  description='desc', platformLabel=None)
        pv = db.getProductVersion('foo', '1')
        assert(str(pv) == "models.ProductVersion(1, 'foo', '1')")
        assert(pv.description == 'desc')
        assert(pv.namespace == 'ns')

    def testGetMemberLevel(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        ownerId = self.createUser('owner')
        devUserId = self.createUser('devuser')
        userId = self.createUser('user')
        otherId = self.createUser('other')
        prdId = self.createProduct('foo', owners=['owner'], 
                                 developers=['devuser'], users=['user'], db=db)

        adminId = db.getUser('admin').userId
        ownerId = db.getUser('owner').userId
        devUserId = db.getUser('devuser').userId
        userId = db.getUser('user').userId
        otherId = db.getUser('other').userId
        getMemberLevel = db.productMgr._getMemberLevel
        assert(not getMemberLevel(prdId, otherId)[0])
        assert(getMemberLevel(prdId, userId) == (True, userlevels.USER))
        assert(getMemberLevel(prdId, devUserId) == (True, userlevels.DEVELOPER))
        assert(getMemberLevel(prdId, ownerId) == (True, userlevels.OWNER))
        assert(not getMemberLevel(prdId, adminId)[0])


    def testGetProductFQDN(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        productId = self.createProduct('foo', domainname='rpath.com', db=db)
        fqdn = db.productMgr._getProductFQDN(productId)
        self.assertEquals(fqdn, 'foo.rpath.com')
        
    def testSetMemberLevel(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('other')
        self.setDbUser(db, 'admin')
        otherId = db.getUser('other').userId
        ownerId = db.getUser('owner').userId
        publisher = mock.MockObject()
        db.productMgr.publisher = publisher
        reposMgr = db.productMgr.reposMgr
        reposMgr._isProductExternal._mock.setDefaultReturn(False)
        productId = self.createProduct('foo', owners=['owner'], db=db)

        publisher.notify._mock.assertCalled('ProductCreated', productId)
        # calling list is empty after that.
        # not call to notify when the owner was added as a user.
        publisher.notify._mock.assertNotCalled()
        membership, = db.listMembershipsForUser('owner').members
        assert(membership.level == 'Owner' and membership.hostname == 'foo')

        db.setMemberLevel('foo', 'other', 'user')
        membership, = db.listMembershipsForUser('other').members
        assert(membership.level == 'User' and membership.hostname == 'foo')
        salt, password = db.userMgr._getPassword(otherId)

        reposMgr.addUserByMd5._mock.assertCalled(
                                      'foo.rpath.local2', 'other',
                                       password, salt,
                                       userlevels.USER)
        publisher.notify._mock.assertCalled('UserProductAdded', 
                                            otherId, productId, 
                                            None, userlevels.USER)
        db.setMemberLevel('foo', 'other', 'developer')
        reposMgr.editUser._mock.assertCalled('foo.rpath.local2', 'other', 
                                             userlevels.DEVELOPER)
        publisher.notify._mock.assertCalled('UserProductChanged', 
                                            otherId, productId, 
                                    userlevels.USER, userlevels.DEVELOPER)
        membership, = db.listMembershipsForUser('other').members
        assert(membership.level == 'Developer' and membership.hostname == 'foo')
        self.assertRaises(mint_error.LastOwner,
                          db.setMemberLevel, 'foo', 'owner', 'developer')
        db.setMemberLevel('foo', 'other', 'owner')
        reposMgr.editUser._mock.assertCalled('foo.rpath.local2', 'other', 
                                             userlevels.OWNER)
        publisher.notify._mock.assertCalled('UserProductChanged', 
                                            otherId, productId, 
                                    userlevels.DEVELOPER, userlevels.OWNER)

    def testRemoveMember(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('user')
        self.createUser('developer')
        self.setDbUser(db, 'admin')
        userId = db.getUser('user').userId
        ownerId = db.getUser('owner').userId
        publisher = mock.MockObject()
        db.productMgr.publisher = publisher
        reposMgr = db.productMgr.reposMgr
        productId = self.createProduct('foo', owners=['owner'], users=['user'],
                                       developers=['developer'], db=db)
        self.assertRaises(mint_error.LastOwner, db.deleteMember, 
                          'foo', 'owner')
        db.deleteMember('foo', 'user')
        assert(not db.listMembershipsForUser('user').members)
        publisher.notify._mock.assertCalled('UserProductRemoved', userId, 
                                            productId)
        reposMgr.deleteUser._mock.assertCalled('foo.rpath.local2', 'user')

    def testCreateProductVersion(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.assertRaises(mint_error.ProductVersionInvalid,
                          self.createProductVersion, db, 'foo', '/',
                                  description='desc', platformLabel=None)
        self.assertRaises(mint_error.InvalidLabel,
                          self.createProductVersion, db, 'foo', '1', 
                          namespace='/',
                          description='desc', platformLabel=None)
        self.assertRaises(mint_error.InvalidNamespace,
                          self.createProductVersion, db, 'foo', '1', 
                          namespace='1'*20,
                          description='desc', platformLabel=None)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        args, kw = db.productMgr.reposMgr.createSourceTrove._mock.popCall()

        assert(not kw)
        assert(len(args) == 6)
        assert(args[0:4] == ('foo', 'group-foo-appliance', 
                             'foo.rpath.local2@rpl:foo-1-devel', '1'))
        assert(args[4].keys() == ['group-foo-appliance.recipe'])
        assert(args[5] == 'Initial appliance image group template')
        self.assertRaises(mint_error.DuplicateProductVersion,
                          self.createProductVersion, 
                          db, 'foo', '1')
        mock.mock(proddef.ProductDefinition, 'rebase')
        self.createProductVersion(db, 'foo', '2', 
                                  platformLabel='conary.rpath.com@rpl:1')
        args, kw = proddef.ProductDefinition.rebase._mock.popCall()
        assert(args[1] == 'conary.rpath.com@rpl:1')

    def testUpdateProductVersion(self):
        db = self.openMintDatabase(createRepos=True)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        assert(db.getProductVersion('foo', '1').description == 'desc')
        db.updateProductVersion('foo', '1', 
                                models.ProductVersion(description='desc2'))
        assert(db.getProductVersion('foo', '1').description == 'desc2')
        self.assertRaises(errors.ProductVersionNotFound,
                          db.updateProductVersion,'foo', '2', 
                                models.ProductVersion(description='desc2'))


    def testGetProductVersionDefinition(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        mock.mock(proddef.ProductDefinition, 'loadFromRepository')
        pd = db.getProductVersionDefinition('foo', '1')
        reposMgr = db.productMgr.reposMgr
        pd.loadFromRepository._mock.assertCalled(
                reposMgr.getAdminClient(write=False))
        pd.loadFromRepository._mock.raiseErrorOnAccess(RuntimeError)
        self.assertRaises(mint_error.ProductDefinitionVersionNotFound,
                          db.getProductVersionDefinition,'foo', '1')

    def testSetProductVersionDefinition(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        pd = mock.MockObject()
        # NOTE, since we're not creating repositories,  we've mocked out 
        # setProductDefinition and renamed it with the underscore.
        db.productMgr._setProductVersionDefinition('foo', '1', pd)
        reposMgr = db.productMgr.reposMgr
        pd.saveToRepository._mock.assertCalled(
                                reposMgr.getUserClient(),
                                 'Product Definition commit from rBuilder\n')

    def testRebaseProductVersionDefinition(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        reposMgr = db.productMgr.reposMgr
        cclient = reposMgr.getUserClient()
        mock.mock(proddef.ProductDefinition, 'saveToRepository')
        mock.mock(proddef.ProductDefinition, 'loadFromRepository')
        mock.mock(proddef.ProductDefinition, 'rebase')
        db.rebaseProductVersionPlatform('foo', '1', 'conary.rpath.com@rpl:1') 
        proddef.ProductDefinition.rebase._mock.assertCalled(cclient,
                                'conary.rpath.com@rpl:1')
        proddef.ProductDefinition.saveToRepository._mock.assertCalled(cclient,
                                 'Product Definition commit from rBuilder\n')


    def testGetProductVersionForLabel(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        mock.mock(proddef.ProductDefinition, 'loadFromRepository')

        version, stage = db.productMgr.getProductVersionForLabel('foo',
                                            'foo.rpath.local2@rpl:foo-1-devel')
        assert(version == 1 and stage == None)
        mock.mock(proddef.ProductDefinition, 'getStages')
        stages = [mock.MockObject(name='devel')]
        proddef.ProductDefinition.getStages._mock.setReturn(stages)
        mock.mock(proddef.ProductDefinition, 'getLabelForStage')
        proddef.ProductDefinition.getLabelForStage._mock.setReturn('foo.rpath.local2@rpl:foo-1-devel', 'devel')
        version, stage = db.productMgr.getProductVersionForLabel('foo',
                                            'foo.rpath.local2@rpl:foo-1-devel')
        assert(version == 1 and stage == 'devel')
        # FIXME: why doesn't this happen automatically?
        version, stage = db.productMgr.getProductVersionForLabel('foo',
                                            'foo.rpath.local2@rpl:foo-2-devel')
        assert((version, stage) == (None, None))
        proddef.ProductDefinition.loadFromRepository._mock.raiseErrorOnAccess(RuntimeError)
        version, stage = db.productMgr.getProductVersionForLabel('foo',
                                            'foo.rpath.local2@rpl:foo-1-devel')
        assert(version == 1 and stage == None)

    def testSetProductVersionBuildDefinitions(self):
        db = self.openMintDatabase(createRepos=False)
        fqdn = 'foo'
        version = '1'
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, fqdn, version, description='desc', 
                                  platformLabel=None)
        def fakeLoadFromRepository(slf, client):
            slf.parseStream(StringIO.StringIO(refProductDefintion1))
        self.mock(proddef.ProductDefinition, 'loadFromRepository',
            fakeLoadFromRepository)
        platform = proddef.PlatformDefinition()
        proddef.ProductDefinition.platform = platform
        tests = [
            ('Build name missing', {}),
        ]
        # Missing architecture
        params = dict(name = "Build name")
        tests.append(('Architecture missing', params.copy()))
        # Missing architecture ID
        params['architecture'] = models.Architecture(name = "blip")
        tests.append(('Architecture missing', params.copy()))
        # Missing container
        params['architecture'] = models.Architecture(id = "blip")
        tests.append(('Container missing', params.copy()))
        # Missing container ID
        params['container'] = models.ContainerFormat(name = "blah")
        tests.append(('Container missing', params.copy()))
        # Flavor set too
        params['container'] = models.ContainerFormat(id = "blah")
        params['flavorSet'] = models.FlavorSet(id = "bloop")
        msg = 'Invalid combination of container template, architecture and flavor set (blah, blip, bloop)'
        tests.append((msg, params.copy()))

        for errMsg, params in tests:
            model = models.BuildDefinitions()
            model.buildDefinitions.append(models.BuildDefinition(**params))
            resp = self.failUnlessRaises(errors.InvalidItem,
                db.productMgr.setProductVersionBuildDefinitions,
                fqdn, version, model)
            self.failUnlessEqual(str(resp), errMsg)

refProductDefintion1 = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-2.0.xsd" xmlns:xsi=
"http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd rpd-2.0.xsd" version="2.0">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>Awesome</productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>Awesome Version</productVersionDescription>
  <conaryRepositoryHostname>product.example.com</conaryRepositoryHostname>
  <conaryNamespace>exm</conaryNamespace>
  <imageGroup>group-awesome-dist</imageGroup>
  <baseFlavor>is: x86 x86_64</baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths/>
</productDefinition>
"""


testsetup.main()
