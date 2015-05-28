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


from mint.rest import errors

from mint_test import mint_rephelp

class AuthenticationManagerTest(mint_rephelp.MintDatabaseHelper):
    def _checkPerms(self, db, method, param, userList, allowedUsers):
        allowedUsers = set(allowedUsers)
        funcName = method.im_func.func_name
        for username in userList:
            self.setDbUser(db, username)
            try:
                if param:
                    args = (param,)
                else:
                    args = ()
                method(*args)
            except (errors.PermissionDeniedError, errors.ItemNotFound), e:
                if username in allowedUsers:
                    raise RuntimeError('%s not allowed access to %s%s' % (username, funcName, args))
            else:
                if username not in allowedUsers:
                    raise RuntimeError('%s allowed access to %s%s' % (username, funcName, args))
                allowedUsers.remove(username)
        assert(not allowedUsers)
                

    
    def testPermissionsChecks(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('owner')
        self.createUser('owner2')
        self.createUser('developer')
        self.createUser('developer2')
        self.createUser('user')
        self.createUser('user2')
        self.createProduct('foo-private', owners=['owner2'], 
                           developers=['developer2'], users=['user2'], 
                           private=True, db=db)
        self.createProduct('foo', owners=['owner'], developers=['developer'],
                           users=['user'], db=db)
        userList = ['admin', 'owner', 'owner2', 'developer', 
                    'developer2', 'user', 'user2', None]
        auth = db.auth
        self._checkPerms(db, auth.requireProductReadAccess, 'foo', userList,
                         userList)
        self._checkPerms(db, auth.requireProductReadAccess, 'foo-private', 
                         userList, ['admin', 'owner2', 'developer2', 'user2'])
        self._checkPerms(db, auth.requireProductDeveloper, 'foo', userList,
                         ['admin', 'owner', 'developer'])
        self._checkPerms(db, auth.requireProductDeveloper, 'foo-private', 
                         userList, ['admin', 'owner2', 'developer2'])
        self._checkPerms(db, auth.requireProductOwner, 'foo', userList,
                         ['admin', 'owner'])
        self._checkPerms(db, auth.requireProductOwner, 'foo-private', userList,
                         ['admin', 'owner2'])
        self._checkPerms(db, auth.requireProductOwner, 'foo-private', userList,
                         ['admin', 'owner2'])
        self._checkPerms(db, auth.requireProductCreationRights, None, userList,
                         userList)
        self._checkPerms(db, auth.requireUserReadAccess, 'owner', userList,
                         ['admin', 'owner'])
        self._checkPerms(db, auth.requireUserAdmin, 'owner', userList,
                         ['admin', 'owner'])
        self._checkPerms(db, auth.requireAdmin, None, userList,
                         ['admin' ])
        self._checkPerms(db, auth.requireLogin, None, userList,
                         set(userList) - set([None]))


def log(x):
    import time
    print '\n%s: %s' % (time.time(), x)
