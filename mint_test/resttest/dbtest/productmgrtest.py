#!/usr/bin/python
import testsetup
from testutils import mock

from conary.lib import cfgtypes

from mcp import client as mcpclient
from mcp import mcp_error

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint.lib import data

from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import imagemgr

import mint_rephelp

class ProductManagerTest(mint_rephelp.MintDatabaseHelper):
    def testGetProduct(self):
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
        self.createProductVersion(db, 'foo', '1', 'foo', 'desc', None)

    def testCreateProduct(self):
        pass

    def testIsMember(self):
        pass

    def testGetProductFQDN(self):
        pass

    def testGetUsername(self):
        pass

    def testGetPassword(self):
        pass

    def testSetMemberLevel(self):
        pass

    def testRemoveMember(self):
        pass

    def testCreateProductVersion(self):
        pass
    
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
