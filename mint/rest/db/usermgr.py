#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
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
    return salt, m.hexdigest()


class UserManager(manager.Manager):

    def cancelUserAccount(self, username):
        """Removes the user account from the authrepo and mint databases.
        Also removes the user from each project listed in projects.
        """
        userId = self.getUserId(username)
        # NOTE: this check is duplicated by the check when deleting
        # each project membership.
        self._ensureNoOrphans(userId)
        self.db.db.membershipRequests.userAccountCanceled(userId)
        self.filterLastAdmin(username)

        #Handle projects
        projectList = self.db.listMembershipsForUser(username).members
        for membership in projectList:
            productId = self.db.getProductId(membership.hostname)
            self.db.productMgr.deleteMember(productId, userId, notify=False)

        cu = self.db.cursor()
        cu.execute("""SELECT userGroupId FROM UserGroupMembers
                          WHERE userId=?""", userId)
        for userGroupId in [x[0] for x in cu.fetchall()]:
            cu.execute("""SELECT COUNT(*) FROM UserGroupMembers
                              WHERE userGroupId=?""", userGroupId)
            if cu.fetchone()[0] == 1:
                cu.execute("DELETE FROM UserGroups WHERE userGroupId=?",
                           userGroupId)
        cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?",
                   userId)
        cu.execute("UPDATE Jobs SET userId=0 WHERE userId=?", userId)
        cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        cu.execute("DELETE FROM UserGroupMembers WHERE userId=?", userId)
        cu.execute("DELETE FROM Users WHERE userId=?", userId)
        cu.execute("DELETE FROM UserData where userId=?", userId)
        self.publisher.notify('UserCancelled', userId)
        return True

 
    def _ensureNoOrphans(self, userId):
        """
        Make sure there won't be any orphans
        """
        cu = self.db.cursor()

        # Find all projects of which userId is an owner, has no other owners,
        # and/or has developers.
        cu.execute("""
        SELECT MAX(D.flagged)
    FROM (SELECT A.projectId,
           COUNT(B.userId) * (NOT COUNT(C.userId)) AS flagged
     FROM ProjectUsers AS A
       LEFT JOIN ProjectUsers AS B ON A.projectId=B.projectId AND B.level=1
       LEFT JOIN ProjectUsers AS C ON C.projectId=A.projectId AND
                                      C.level = 0 AND
                                      C.userId <> A.userId AND
                                      A.level = 0
           WHERE A.userId=? GROUP BY A.projectId) AS D
                   """, userId)

        r = cu.fetchone()
        if r and r[0]:
            raise mint_error.LastOwner
        
        return True

    def filterLastAdmin(self, username):
        """Raises an exception if the last site admin attempts to cancel their
        account, to protect against not having any admins at all."""
        if not self._isUserAdmin(username):
            return
        cu = self.db.cursor()
        cu.execute("""SELECT username
                          FROM UserGroups
                          JOIN UserGroupMembers USING(userGroupId)
                          JOIN Users USING(userId)
                          WHERE userGroup='MintAdmin'""")
        if [x[0] for x in cu.fetchall()] == [username]:
            # userId is admin, and there is only one admin => last admin
            raise mint_error.LastAdmin(
                        "There are no more admin accounts. Your request "
                        "to close your account has been rejected to "
                        "ensure that at least one account is admin.")


    def getUserId(self, username):
        cu = self.db.cursor()
        cu.execute("""SELECT userId FROM Users WHERE username=?""", username)
        userId, = self.db._getOne(cu, errors.UserNotFound, username)
        return userId

    def _getAdminGroupId(self):
        cu = self.db.cursor()
        cu.execute('SELECT userGroupId'
                   ' FROM UserGroups WHERE userGroup=?', 'MintAdmin')
        groupIds = cu.fetchall()
        if groupIds:
            return groupIds[0][0]
        cu.execute('INSERT INTO UserGroups (userGroup) VALUES (?)''',
                   'MintAdmin')
        return cu.lastrowid

    def _isUserAdmin(self, username):
        cu = self.db.cursor()
        cu.execute('''SELECT userGroup FROM Users
                    JOIN UserGroupMembers USING(userId)
                    JOIN UserGroups USING(userGroupId)
                    WHERE userGroup=? AND username=?''', 'MintAdmin', username)
        return bool(cu.fetchall())

    def makeAdmin(self, username):
        userId = self.getUserId(username)
        cu = self.db.cursor()
        if not self._isUserAdmin(username):
            groupId = self._getAdminGroupId()
            cu.execute('INSERT INTO UserGroupMembers (userGroupId, userId)'
                       ' VALUES (?, ?)', groupId, userId)

    def createUser(self, username, password, fullName, email, 
                   displayEmail, blurb, admin=False):
        # fixme - not for creating non-active users.  To do that we
        # need to do confirmations, which are too entwined.
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(*) FROM UserGroups
                      WHERE UPPER(userGroup)=UPPER(?)""",
                   username)
        if cu.fetchone()[0]:
            raise mint_error.UserAlreadyExists
        cu.execute("SELECT COUNT(*) FROM Users WHERE UPPER(username)=UPPER(?)",
                   username)
        if cu.fetchone()[0]:
            raise mint_error.UserAlreadyExists
        # NOTE: I don't add users to their own usergroups.
        # as far as I can tell the only use for usergroups is for
        # MintAdmin.
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
        return cu.next()

    def _getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT username from Users where userId=?', userId)
        return self.db._getOne(cu, errors.UserNotFound, userId)[0]

