#!/usr/bin/python
import testsetup
from testutils import mock

from rpath_common.proddef import api1 as proddef

from mint import mint_error

from mint import userlevels
from mint.rest import errors
from mint.rest.api import models

import mint_rephelp

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
        assert(foo.isAppliance)
        assert(bar.isAppliance)
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
        self.createUser('user', admin=False)
        self.createProduct('foo', owners=['admin'], db=db, private=True)
        self.createProduct('bar', owners=['user'], db=db, private=True)

        # User can't see other hidden projects
        self.setDbUser(db, 'user')
        products = db.listProducts().products
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].shortname, 'bar')

        # Admin can see all projects; check sorting.
        self.setDbUser(db, 'admin')
        products = db.listProducts().products
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].shortname, 'bar')
        self.assertEqual(products[1].shortname, 'foo')

        # List by role
        products = db.listProducts(role='Owner').products
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].shortname, 'foo')

        # Query limits; check sorting
        products = db.listProducts(limit=1).products
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].shortname, 'bar')

    def testGetProductVersion(self):
        db = self.openMintDatabase(createRepos=False)
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
                                       write=False, mirror=False, admin=False)
        publisher.notify._mock.assertCalled('UserProductAdded', 
                                            otherId, productId, 
                                            userlevels.USER)
        db.setMemberLevel('foo', 'other', 'developer')
        reposMgr.editUser._mock.assertCalled('foo.rpath.local2', 'other', 
                                             write=True, mirror=False,
                                             admin=False)
        publisher.notify._mock.assertCalled('UserProductChanged', 
                                            otherId, productId, 
                                    userlevels.USER, userlevels.DEVELOPER)
        membership, = db.listMembershipsForUser('other').members
        assert(membership.level == 'Developer' and membership.hostname == 'foo')
        self.assertRaises(mint_error.LastOwner,
                          db.setMemberLevel, 'foo', 'owner', 'developer')
        db.setMemberLevel('foo', 'other', 'owner')
        reposMgr.editUser._mock.assertCalled('foo.rpath.local2', 'other', 
                                             write=True, mirror=True,
                                             admin=True)
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
        db = self.openMintDatabase(createRepos=False)
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
                                    reposMgr.getConaryClientForProduct())
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
                                reposMgr.getConaryClientForProduct(),
                                 'Product Definition commit from rBuilder\n')

    def testRebaseProductVersionDefinition(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', description='desc', 
                                  platformLabel=None)
        reposMgr = db.productMgr.reposMgr
        cclient = reposMgr.getConaryClientForProduct()
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
        pass

testsetup.main()
