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
import time

from conary.lib.digestlib import md5

from mint import mint_error
from mint.rest import errors
from mint.rest.db import manager

def _mungePassword(password):
    m = md5()
    salt = os.urandom(4)
    m.update(salt)
    m.update(password)
    return salt.encode('hex'), m.hexdigest()


class UserManager(manager.Manager):

    def getUserId(self, username):
        cu = self.db.cursor()
        cu.execute("""SELECT userId FROM Users WHERE username=?""", username)
        userId, = self.db._getOne(cu, errors.UserNotFound, username)
        return userId

    def makeAdmin(self, username):
        userId = self.getUserId(username)
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET is_admin = ? WHERE userId = ?", True,
                userId)

    def createUser(self, username, password, fullName, email, 
                   displayEmail, blurb, admin=False):
        # fixme - not for creating non-active users.  To do that we
        # need to do confirmations, which are too entwined.
        cu = self.db.cursor()
        cu.execute("SELECT COUNT(*) FROM Users WHERE UPPER(username)=UPPER(?)",
                   username)
        if cu.fetchone()[0]:
            raise mint_error.UserAlreadyExists
        salt, pw = _mungePassword(password)

        userValues = dict(username = username,
                          fullName = fullName,
                          salt = salt,
                          passwd = pw,
                          email = email,
                          displayEmail = displayEmail,
                          timeCreated = time.time(),
                          timeAccessed = 0,
                          blurb = blurb, 
                          active = 1)
        params = ', '.join(['?'] * len(userValues))
        values = userValues.values()
        keys = ', '.join(userValues.keys())
        sql = '''INSERT INTO Users (%s) VALUES (%s)'''% (keys, params)
        cu.execute(sql, values)
        userId = cu.lastrowid
        if admin:
            self.makeAdmin(username)
        return userId

    def _getPassword(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT passwd, salt from Users where userId=?', userId)
        passwd, salt = cu.next()
        return passwd, salt

    def _getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT username from Users where userId=?', userId)
        return self.db._getOne(cu, errors.UserNotFound, userId)[0]
