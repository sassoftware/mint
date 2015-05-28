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


import os

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
        db.userMgr.makeAdmin('other')

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
