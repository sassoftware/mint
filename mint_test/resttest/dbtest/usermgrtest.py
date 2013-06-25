#!/usr/bin/python

import os
import testsetup

from mint import buildtypes
from mint import mint_error
from mint.rest import errors
from mint_test import mint_rephelp

class UserManagerTest(mint_rephelp.MintDatabaseHelper):
    def setUp(self):
        mint_rephelp.MintDatabaseHelper.setUp(self)
        db = self.openMintDatabase(createRepos=False)
        cu = db.cursor()
        tbmap = [
            ('tType', buildtypes.RAW_HD_IMAGE),
        ]
        for ttype, buildTypeId in tbmap:
            cu.execute("INSERT INTO target_types (name, description, build_type_id) VALUES (?, ?, ?)",
                ttype, ttype + " description", buildTypeId)
        db.commit()

    def testMakeAdmin(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('other')
        assert(not db.userMgr._isUserAdmin('other'))
        db.userMgr.makeAdmin('other')
        assert(db.userMgr._isUserAdmin('other'))

    def testCreateUser(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
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
        #TODO: ensure algorithm is right.

    def testGetUsername(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('user')
        self.setDbUser(db, 'admin')
        adminId = db.getUser('admin').userId

    def testCancelUserAccount(self):
        userName = 'JeanValjean'
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser(userName, admin=False)
        self.createProduct('foo', owners=['admin', userName], db=db)

        targetType = 'tType'
        targetName = 'tName'
        targetData = dict(data = "abc")
        db.targetMgr.addTarget(targetType, targetName, targetData)

        db.targetMgr.setTargetCredentialsForUser(targetType, targetName,
                userName, dict(userData = "cde"))

        userId = db.userMgr.getUserId(userName)
        db.userMgr.cancelUserAccount(userName)

        # User no longer exists
        self.failUnlessRaises(errors.UserNotFound,
            db.userMgr.getUserId, userName)


testsetup.main()
