#!/usr/bin/python
import testsetup
from testutils import mock

import mint_rephelp

class UserManagerTest(mint_rephelp.MintDatabaseHelper):
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
