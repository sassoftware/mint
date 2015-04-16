#
# Copyright (c) SAS Institute Inc.
#

import os
import time

from conary import repository
from conary.lib.digestlib import md5

from conary.repository.netrepos.netauth import nameCharacterSet
from conary.repository.netrepos.auth_tokens import ValidPasswordToken

from mint import userlisting
from mint.mint_error import (DuplicateItem, InvalidUsername,
        IllegalUsername, UserAlreadyExists, ItemNotFound)
from mint.lib import auth_client
from mint.lib import data
from mint.lib import database


class UsersTable(database.KeyedTable):
    name = 'Users'
    key = 'userId'

    fields = ['userId', 'username', 'fullName', 'salt', 'passwd', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'blurb', 'is_admin']

    # Not the ideal place to put these, but I wanted to easily find them later
    # --misa
    EC2TargetType = 'ec2'
    EC2TargetName = 'aws'

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)
        self.authClient = auth_client.getClient(cfg.authSocket)

    def changePassword(self, username, password):
        if username == self.cfg.authUser:
            raise ValueError
        salt, passwd = self._mungePassword(password)
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET salt=?, passwd=? WHERE username=?",
                   salt, passwd, username)
        self.db.commit()

    def _checkPassword(self, user, salt, password, challenge):
        if salt and password:
            m = md5(salt.decode('hex') + challenge)
            if m.hexdigest() == password:
                return True
        else:
            if self.authClient.checkPassword(user, challenge):
                return True
        return False

    def _mungePassword(self, password):
        if password is None or password == '':
            return None, None
        m = md5()
        salt = os.urandom(4)
        m.update(salt)
        m.update(password)
        return salt.encode('hex'), m.hexdigest()

    def _checkToken(self, userId, token):
        # Don't send the token to the database, if it's actually a user
        # password it might end up in the DB logs.
        cu = self.db.cursor()
        cu.execute("""
            SELECT token FROM auth_tokens
            WHERE user_id = ?  AND expires_date >= now()
            """, userId)
        tokens = [x[0] for x in cu]
        return token in tokens

    def checkAuth(self, authToken, useToken=False):
        username, password = authToken[:2]
        noAuth = {'authorized': False, 'userId': -1}
        if username == 'anonymous':
            return noAuth
        elif username == self.cfg.authUser and password == self.cfg.authPass:
            return {
                    'authorized': True,
                    'userId': -1,
                    'username': username,
                    'admin': True,
                    }

        cu = self.db.cursor()
        cu.execute("""SELECT userId, email, displayEmail, fullName, blurb,
                        timeAccessed, salt, passwd, is_admin FROM Users
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()
        if not r:
            # No matching uer
            return noAuth
        (userId, email, displayEmail, fullName, blurb, timeAccessed, salt,
                digest, isAdmin) = r
        if password is ValidPasswordToken:
            # Pre-authenticated session
            pass
        elif useToken and self._checkToken(userId, password):
            # Repository token
            pass
        else:
            try:
                if not self._checkPassword(username, salt, digest, password):
                    # Password failed
                    return noAuth
            except repository.errors.OpenError:
                # External (HTTP) auth failed
                return noAuth

        return {
                'authorized':   True,
                'userId':       int(userId),
                'username':     username,
                'email':        email,
                'displayEmail': displayEmail,
                'fullName':     fullName,
                'blurb':        blurb,
                'timeAccessed': timeAccessed,
                'stagnant':     False,
                'groups':       [],
                'admin':        isAdmin,
                }

    def validateUsername(self, username):
        if username.lower() == self.cfg.authUser.lower():
            raise IllegalUsername
        for letter in username:
            if letter not in nameCharacterSet:
                raise InvalidUsername

        cu = self.db.cursor()
        cu.execute("SELECT COUNT(*) FROM Users WHERE UPPER(username)=UPPER(?)",
                   username)
        if cu.fetchone()[0]:
            raise UserAlreadyExists

    def registerNewUser(self, username, password, fullName, email,
                        displayEmail, blurb, active):
        self.validateUsername(username)

        salt, passwd = self._mungePassword(password)

        self.db.transaction()
        try:
            userId = self.new(username = username,
                              fullName = fullName,
                              salt = salt,
                              passwd = passwd,
                              email = email,
                              displayEmail = displayEmail,
                              timeCreated = time.time(),
                              timeAccessed = 0,
                              blurb = blurb,
                              active=1,
                              )

        except DuplicateItem:
            self.db.rollback()
            raise UserAlreadyExists
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return userId

    def getUsersWithEmail(self):
        """
        Returns a list of all users suitable for sending e-mail
        """
        cu = self.db.cursor()
        SQL = """SELECT userId, fullName, email FROM Users"""

        cu.execute(SQL)

        results = cu.fetchall()
        return results

    def getUsersWithAwsAccountNumber(self):
        """
        Returns a list of all users with Aws account numbers.
        """
        cu = self.db.cursor()
        SQL = """
            SELECT u.userId, tc.credentials AS creds
              FROM Users u
              JOIN TargetUserCredentials AS tuc USING (userId)
              JOIN TargetCredentials AS tc USING (targetCredentialsId)
              JOIN Targets AS t ON (t.targetId=tuc.targetId)
              JOIN target_types AS tt ON (t.target_type_id = t.target_type_id)
             WHERE tt.name = ?
               AND t.name = ?
            """
        cu.execute(SQL, self.EC2TargetType, self.EC2TargetName)
        results = cu.fetchall()
        return [ (x[0], data.unmarshalTargetUserCredentials(self.cfg, x[1]
            ).get('accountId')) for x in results ]

    def getUsers(self, sortOrder, limit, offset, includeInactive=False):
        """
        Returns a list of users for browsing limited by L{limit}
        starting with item L{offset}.
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @param includeInactive: set True to include users needing confirmations
        @return:       a list of the requested items.
        """
        cu = self.db.cursor()

        if not includeInactive:
            whereClause = "WHERE active=1"
        else:
            whereClause = ""

        SQL = userlisting.sqlbase % (whereClause,
                userlisting.ordersql[sortOrder], limit, offset)

        cu.execute(SQL)

        ids = []
        for x in cu.fetchall():
            ids.append(list(x))
            if len(ids[-1][userlisting.blurbindex]) > userlisting.blurbtrunclength:
                ids[-1][userlisting.blurbindex] = ids[-1][userlisting.blurbindex][:userlisting.blurbtrunclength] + "..."

        return ids

    def getNumUsers(self, includeInactive=False):
        """
        Returns the count of Users
        """
        cu = self.db.cursor()
        if not includeInactive:
            whereClause = "WHERE active=1"
        else:
            whereClause = ""
        cu.execute( "SELECT count(userId) FROM Users " + whereClause )
        return cu.fetchone()[0]


    def getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute ( "SELECT username FROM Users WHERE userId = ?", userId)
        username = cu.fetchone()
        if not username:
            raise ItemNotFound("UserId: %d does not exist!"% userId)
        return username[0]


class UserDataTable(data.GenericDataTable):
    name = "UserData"
