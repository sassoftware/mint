#!/usr/bin/python
import testsetup
from testutils import mock

from mint import mint_error
from mint.rest import errors
from mint_test import mint_rephelp

class UserManagerTest(mint_rephelp.MintDatabaseHelper):
    def testCancelUserAccount(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('developer')
        self.assertRaises(mint_error.LastAdmin, db.cancelUserAccount, 'admin')
        self.createUser('owner')
        self.setDbUser(db, 'owner')
        self.createProduct('foo', db=db)
        self.createProduct('foo2', db=db)
        db.cancelUserAccount('owner')
        self.assertRaises(errors.UserNotFound, db.getUser, 'owner')
        self.createUser('owner')
        assert(not db.listMembershipsForUser('owner').members)
        self.setDbUser(db, 'owner')
        self.createProduct('foo3', developers=['developer'], db=db)
        self.assertRaises(mint_error.LastOwner, db.cancelUserAccount, 'owner')

    def testGetAdminGroupId(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        groupId = db.userMgr._getAdminGroupId()
        assert(groupId == db.userMgr._getAdminGroupId())

    def testMakeAdmin(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('other')
        assert(not db.userMgr._isUserAdmin('other'))
        db.userMgr.makeAdmin('other')
        groupId = db.userMgr._getAdminGroupId()
        assert(db.userMgr._isUserAdmin('other'))

    def testCreateUser(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.assertRaises(mint_error.UserAlreadyExists, self.createUser, 'mintadmin')
        self.assertRaises(mint_error.UserAlreadyExists, self.createUser, 'ADmIN')
        db.createUser('foo', 'bar', 'fullName', 'email', 
                      'displayEmail', 'blurb')
        foo = db.getUser('foo')
        assert(foo.displayEmail == 'displayEmail')
        assert(foo.blurb == 'blurb')
        assert(foo.fullName == 'fullName')
        assert(foo.email == 'email')
        assert(foo.displayEmail == 'displayEmail')

    def testGetPassword(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', password='foo', admin=True)
        self.setDbUser(db, 'admin')
        adminId = db.getUser('admin').userId
        passwd, salt = db.userMgr._getPassword(adminId)
        assert(len(salt) == 4)
        #TODO: ensure algorithm is right.

    def testGetUsername(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('user')
        self.setDbUser(db, 'admin')
        adminId = db.getUser('admin').userId

testsetup.main()
