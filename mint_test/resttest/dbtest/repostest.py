#!/usr/bin/python
import testsetup

from conary import versions
from conary.repository import errors as reposerrors
from conary_test import auth_helper

from mint.rest.api import models
from mint.rest import errors
from mint_test import mint_rephelp


class ReposManagerTest(mint_rephelp.MintDatabaseHelper, auth_helper.AuthHelper):
    def testCreateRepository(self):
        db = self.openMintDatabase()
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('developer')
        self.createUser('user')
        self.createUser('other')

        self.setDbUser(db, 'owner')
        self.createProduct('bar', developers=['developer'], users=['user'],
                           private=True)
        reposMgr = db.productMgr.reposMgr
        assert(not reposMgr._isProductExternal('bar'))
        repos = reposMgr.getUserClient().getRepos()
        # commit with this repos
        self.addComponent('foo:run=bar.rpath.local2@rpl:1', repos=repos)

        label = versions.Label("bar.rpath.local2@rpl:1")
        assert(repos.troveNames(label) == ['foo:run'])
        self.setDbUser(db, 'other')
        repos = reposMgr.getUserClient().getRepos()
        # hidden, so no access.
        self.assertRaises(errors.ProductNotFound, repos.troveNames, label)
        self.setDbUser(db, 'user')
        repos = reposMgr.getUserClient().getRepos()
        assert(repos.troveNames(label) == ['foo:run'])
        self.assertRaises(reposerrors.InsufficientPermission, self.addComponent,
                         'foo:dev=bar.rpath.local2@rpl:1', repos=repos)

    def testCreateRepositoryUnicode(self):
        db = self.openMintDatabase()
        reposMgr = db.productMgr.reposMgr
        self.createUser('owner')
        self.createUser('other')
        self.setDbUser(db, 'owner')
        description = u"Some desc with a non-ascii \u0163 character"
        productId = self.createProduct(u"bar", description = description,
            db = db)
        product = db.getProduct(u'bar')
        self.failUnless(isinstance(product.hostname, str))
        self.failUnlessEqual(product.hostname, "bar")
        self.failUnlessEqual(product.description,
            u'Some desc with a non-ascii \u0163 character')

    def testPublicCreateRepository(self):
        db = self.openMintDatabase()
        reposMgr = db.productMgr.reposMgr
        self.createUser('owner')
        self.createUser('other')
        self.setDbUser(db, 'owner')
        self.createProduct('bar', db=db)
        repos = reposMgr.getUserClient().getRepos()
        self.addComponent('foo:run=bar.rpath.local2@rpl:1', repos=repos)
        self.setDbUser(db, 'other')
        repos = reposMgr.getUserClient().repos
        label = versions.Label("bar.rpath.local2@rpl:1")
        assert(repos.troveNames(label) == ['foo:run'])


    def testExternalRepositoryEntitlementAccess(self):
        # s create an external repository that requires entitlement access 
        # and ensure that we can reach it.
        repos = self.openRepository()
        self.addComponent('foo:run=localhost@rpl:1')

        label = versions.Label("localhost@rpl:1")
        repos.deleteUserByName(label, 'anonymous')
        self.setupEntitlement(repos, "entGroup", "12345", label, None, None,
                              withClass = True)[0]
        db = self.openRestDatabase()
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        productMgr = db.productMgr
        reposMgr = productMgr.reposMgr
        productMgr.createExternalProduct('Local Host', 'localhost', '', 
                                 self.cfg.repositoryMap['localhost'],
                                 models.AuthInfo(authType='entitlement',
                                                 entitlement='12345'))
        db.commit()
        client = reposMgr.getUserClient().getRepos()
        assert(client.troveNames(label) == ['foo:run'])

    def testExternalRepositoryUserPassAccess(self):
        repos = self.openRepository()
        repos.setRoleCanMirror(self.cfg.buildLabel, 'test', True)
        self.addComponent('foo:run=localhost@rpl:1')
        label = versions.Label("localhost@rpl:1")
        repos.deleteUserByName(label, 'anonymous')
      
        db = self.openRestDatabase()
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        productMgr = db.productMgr
        reposMgr = productMgr.reposMgr
        userpass = self.cfg.user.find('localhost')
        productMgr.createExternalProduct('Local Host', 'localhost', '', 
                                 self.cfg.repositoryMap['localhost'],
                                 models.AuthInfo(authType='userpass',
                                                 username=userpass[0],
                                                 password=userpass[1]))
        client = reposMgr.getUserClient().getRepos()
        assert(client.troveNames(label) == ['foo:run'])
        assert(reposMgr._isProductExternal('localhost'))

    def testIncomingMirror(self):
        repos = self.openRepository()
        repos.setRoleCanMirror(self.cfg.buildLabel, 'test', True)
        self.addComponent('foo:run=localhost@rpl:1')
        label = versions.Label("localhost@rpl:1")
        repos.deleteUserByName(label, 'anonymous')
      
        db = self.openRestDatabase()
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        productMgr = db.productMgr
        reposMgr = productMgr.reposMgr
        userpass = self.cfg.user.find('localhost')
        productMgr.createExternalProduct('Local Host', 'localhost', 'abc', 
                                 self.cfg.repositoryMap['localhost'],
                                 models.AuthInfo(authType='userpass',
                                                 username=userpass[0],
                                                 password=userpass[1]),
                                                 mirror=True)

    def testIsProductExternal(self):
        db = self.openRestDatabase()
        self.assertRaises(errors.ProductNotFound,
                          db.productMgr.reposMgr._isProductExternal, 'foo')

    def testInternalProxy(self):
        pass

    def testOtherDomainNames(self):
        db = self.openRestDatabase()
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        self.createProduct('bar', domainname='rpath.com', db=db)

    def testAdminAccess(self):
        db = self.openRestDatabase()
        self.createUser('owner')
        self.createUser('other')
        self.setDbUser(db, 'owner')
        self.createProduct('bar', domainname='rpath.com', db=db)
        self.setDbUser(db, 'other')
        repos = db.productMgr.reposMgr.getAdminClient(write=True).repos
        self.addComponent('foo:bar=bar.rpath.com@rpl:1', repos=repos)

    def testCreateSourceTrove(self):
        db = self.openRestDatabase()
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        self.createProduct('bar', db=db)
        reposMgr = db.productMgr.reposMgr
        label = versions.Label("bar.rpath.local2@rpl:1")
        streamMap = {'foo.recipe' : 'hello world'}
        reposMgr.createSourceTrove('bar.rpath.local2', 'foo', 
                                   label, '1.0', streamMap, 'Changelog')
        repos = reposMgr.getUserClient().repos
        trv = self.findAndGetTrove(
                        'foo:source=bar.rpath.local2@rpl:1', repos=repos)
        assert(list(trv.iterFileList())[0][1] == 'foo.recipe')
        assert(trv.getChangeLog().getMessage() == 'Changelog\n')

testsetup.main()
