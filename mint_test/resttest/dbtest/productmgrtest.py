#!/usr/bin/python
import testsetup
from testutils import mock

from rpath_common.proddef import api1 as proddef

from conary.lib import cfgtypes

from mcp import client as mcpclient
from mcp import mcp_error

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint import userlevels
from mint.lib import data

from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import imagemgr

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
        self.createProduct('bar', owners=['user'], db=db)
        self.setDbUser(db, 'user')
        products = db.listProducts().products
        assert(len(products) == 1)
        assert(products[0].hostname == 'bar')
        self.setDbUser(db, 'admin')
        products = db.listProducts().products
        assert(len(products) == 2)

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
        productId = self.createProduct('foo', domainname='rpath.com', 
                                       db=db)
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
        productId = self.createProduct('foo', owners=['owner'], db=db)

        publisher.notify._mock.assertCalled('ProjectCreated', productId)
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
        self.setDbUser(db, 'admin')
        userId = db.getUser('user').userId
        ownerId = db.getUser('owner').userId
        publisher = mock.MockObject()
        db.productMgr.publisher = publisher
        reposMgr = db.productMgr.reposMgr
        productId = self.createProduct('foo', owners=['owner'], users=['user'],
                                       db=db)
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
        pass

    def testGetProductVersionDefinition(self):
        pass

    def testSetProductVersionDefinition(self):
        pass

    def testRebaseProductVersionDefinition(self):
        pass

    def testGetProductVersionForLabel(self):
        pass

testsetup.main()
