#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

import dns.resolver
import email
import md5
import os
import random
import re
import smtplib
import socket
import string
import sys
import time
from email import MIMEText

from conary import repository
from conary.lib import sha1helper
from conary import conaryclient

from mint_error import MintError
from mint_error import PermissionDenied
import database
import userlevels
import searcher
import userlisting
import templates
from conary import sqlite3

class MailError(MintError):
    def __str__(self):
        return self.context
    def __init__(self, context="there was a problem sending email"):
        self.context=context

class ConfirmError(MintError):
    def __str__(self):
        return "your registration could not be confirmed"

class AlreadyConfirmed(MintError):
    def __str__(self):
        return "registration already confirmed"

class UserAlreadyExists(MintError):
    def __str__(self):
        return "user already exists"

class GroupAlreadyExists(MintError):
    def __str__(self):
        return "group already exists"

class LastOwner(MintError):
    def __str__(self):
        return "attempted to orphan a project with developers"

class UserInduction(MintError):
    def __str__(self):
        return "Project owner attempted to manipulate a project user in an illegal fashion"

class AuthRepoError(MintError):
    def __str__(self):
        return "Authentication Token could not be manipulated."

class ConfirmationsTable(database.KeyedTable):
    name = 'Confirmations'
    key = 'userid'
    createSQL = """
                CREATE TABLE Confirmations (
                    userId          INTEGER PRIMARY KEY,
                    timeRequested   INT,
                    confirmation    STR
                )"""
    fields = ['userId', 'timeRequested', 'confirmation']

def digMX(hostname):
    try:
        answers = dns.resolver.query(hostname, 'MX')
    except dns.resolver.NoAnswer:
        return None
    return answers

class UsersTable(database.KeyedTable):
    name = 'Users'
    key = 'userId'

    createSQL = """
                CREATE TABLE Users (
                    userId          INTEGER PRIMARY KEY,
                    username        STR UNIQUE,
                    fullName        STR,
                    salt            %(BINARY4)s NOT NULL,
                    passwd          %(BINARY254)s NOT NULL,
                    email           STR,
                    displayEmail    STR DEFAULT '',
                    timeCreated     INT,
                    timeAccessed    INT,
                    active          INT,
                    blurb           STR DEFAULT ''
                    )"""

    fields = ['userId', 'username', 'fullName', 'salt', 'passwd', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'blurb']

    indexes = {"UsersUsernameIdx": """CREATE INDEX UsersUsernameIdx
                                          ON Users(username)""",
               "UsersActiveIdx":   """CREATE INDEX UsersActiveIdx
                                          ON Users(username, active)"""}

    def __init__(self, db, cfg):
        self.cfg = cfg
        if 'authDbPath' in cfg._options and cfg.authDbPath:
            self.authDb = sqlite3.connect(cfg.authDbPath)
        database.DatabaseTable.__init__(self, db)
        self.confirm_table = ConfirmationsTable(db)

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 8:
                # add the necessary columns to the Users table
                cu = self.db.cursor() 
                aCu = self.authDb.cursor()
                # add the mintauth user
                for userName in ('mintauth',):
                    cu.execute("""INSERT INTO Users (username, active)
                                  VALUES('%s', 1)""" % userName)
                if self.cfg.dbDriver == 'sqlite':
                    cu.execute("ALTER TABLE Users ADD COLUMN salt BINARY")
                    cu.execute("ALTER TABLE Users ADD COLUMN passwd STR")
                else:
                    cu.execute("""ALTER TABLE Users ADD COLUMN(
                                      salt   BINARY(4),
                                      passwd VARCHAR(255))""")
                # now go get each user's salt and pass from the authRepo
                aCu.execute('SELECT user, salt, password FROM Users')
                for username, salt, passwd in aCu.fetchall():
                    cu.execute("""UPDATE Users SET salt=?, passwd=?
                                      WHERE username=?""",
                               salt, passwd, username)
                return (dbversion + 1) == self.schemaVersion
        return True

    def changePassword(self, username, password):
        salt, passwd = self._mungePassword(password)
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET salt=?, passwd=? WHERE username=?",
                   salt, passwd, username)

    def _checkPassword(self, salt, password, challenge):
        m = md5.new()
        m.update(salt)
        m.update(challenge)

        return m.hexdigest() == password

    def _mungePassword(self, password):
        m = md5.new()
        salt = os.urandom(4)
        m.update(salt)
        m.update(password)
        return salt, m.hexdigest()

    def _getUserGroups(self, authToken):
        user, challenge = authToken

        cu = self.db.cursor()
        cu.execute("SELECT salt, passwd FROM Users WHERE username=?", user)
        r = cu.fetchone()
        if r  and self._checkPassword(r[0], r[1], challenge):
            cu.execute("""SELECT UserGroups.userGroup
                          FROM UserGroups, Users, UserGroupMembers 
                          WHERE UserGroups.userGroupId =
                                  UserGroupMembers.userGroupId AND
                                UserGroupMembers.userId = Users.userId AND
                                Users.username = ?""", user)
            return [row[0] for row in cu.fetchall()]
        else:
            return []

    def checkAuth(self, authToken, checkRepo = True, cachedGroups = []):
        noAuth = {'authorized': False, 'userId': -1}
        if authToken == ('anonymous', 'anonymous'):
            return noAuth

        username, password = authToken
        cu = self.db.cursor()
        cu.execute("""SELECT userId, email, displayEmail, fullName, blurb,
                        timeAccessed FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()
        
        if r:
            groups = cachedGroups
            if checkRepo:
                try:
                    groups = self._getUserGroups(authToken)
                except repository.errors.OpenError:
                    auth = noAuth

                if type(groups) != list:
                    raise AuthRepoError

            if username in groups or not checkRepo:
                auth = {'authorized':   True,
                        'userId':       r[0],
                        'username':     username,
                        'email':        r[1],
                        'displayEmail': r[2],
                        'fullName':     r[3],
                        'blurb':        r[4],
                        'timeAccessed': r[5],
                        'stagnant':     self.isUserStagnant(r[0]),
                        'groups':       groups}
                if 'MintAdmin' in groups:
                    auth['admin'] = True
                else:
                    auth['admin'] = False
            else:
                auth = noAuth
        else:
            auth = noAuth
        return auth

    def validateNewEmail(self, userId, email):
        user = self.get(userId)
        confirm = confirmString()

        import templates.validateNewEmail
        message = templates.write(templates.validateNewEmail, username = user['username'],
            cfg = self.cfg, confirm = confirm)

        sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, email,
                "Your %s account's email address must be confirmed" % self.cfg.productName, message)
        self.invalidateUser(userId, confirm)

    def invalidateUser(self, userId, confirm = None):
        if not confirm:
            confirm = confirmString()
        try:
            self.confirm_table.new(userId = userId,
                                   timeRequested = time.time(),
                                   confirmation = confirm)
        except database.DuplicateItem:
            self.confirm_table.update(userId, confirmation = confirm)

    def registerNewUser(self, username, password, fullName, email,
                        displayEmail, blurb, active):
        if self.cfg.sendNotificationEmails and not active:
            validateEmailDomain(email)

        confirm = confirmString()

        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(*) FROM UserGroups
                          WHERE UPPER(userGroup)=UPPER(?)""",
                   username)
        if cu.fetchone()[0]:
            raise GroupAlreadyExists
            
        cu.execute("SELECT COUNT(*) FROM Users WHERE UPPER(username)=UPPER(?)",
                   username)
        if cu.fetchone()[0]:
            raise UserAlreadyExists

        salt, passwd = self._mungePassword(password)

        if self.cfg.sendNotificationEmails and not active:
            import templates.registerNewUser
            message = templates.write(templates.registerNewUser,
                username = username, cfg = self.cfg, confirm = confirm)
            sendMailWithChecks(self.cfg.adminMail, self.cfg.productName,
                               email, "Welcome to %s!" % \
                               self.cfg.productName, message)
        try:
            cu.execute("INSERT INTO UserGroups (userGroup) VALUES(?)",
                       username)

            cu.execute("SELECT userGroupId FROM UserGroups WHERE userGroup=?",
                       username)
            userGroupId = cu.fetchone()[0]

            userId = self.new(username = username,
                              fullName = fullName,
                              salt = salt,
                              passwd = passwd,
                              email = email,
                              displayEmail = displayEmail,
                              timeCreated = time.time(),
                              timeAccessed = 0,
                              blurb = blurb,
                              active = int(active))

            cu.execute("INSERT INTO UserGroupMembers VALUES(?,?)", userGroupId,
                       userId)
            cu.execute("""SELECT userGroupId FROM UserGroups
                              WHERE userGroup='public'""")
            # FIXME, just skip the public group if it's not there.
            try:
                pubGroupId = cu.fetchone()[0]
            except:
                raise AssertionError("There's no public group!")
            cu.execute("INSERT INTO UserGroupMembers VALUES(?,?)", pubGroupId,
                       userId)

        except database.DuplicateItem:
            self.db.rollback()
            raise UserAlreadyExists
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        self.confirm_table.new(userId = userId,
                               timeRequested = time.time(),
                               confirmation = confirm)
        return userId

    def isUserStagnant(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT timeRequested FROM Confirmations WHERE userId=?", userId)
        results = cu.fetchall()
        if len(results) == 1:
            return True
        return False

    def confirm(self, confirm):
        cu = self.db.cursor()

        cu.execute("SELECT userId FROM Confirmations WHERE confirmation=?", confirm)
        if len(cu.fetchall()) != 1:
            raise AlreadyConfirmed
        else:
            cu.execute("SELECT userId FROM Confirmations WHERE confirmation=?", confirm)
            r = cu.fetchone()

            cu.execute("UPDATE Users SET active=1 WHERE userId=?", r[0])
            cu.execute("DELETE FROM Confirmations WHERE userId=?", r[0])

            return r[0]

    def search(self, terms, limit, offset):
        """
        Returns a list of users matching L{terms} of length L{limit}
        starting with item L{offset}.
        @param terms: Search terms
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @return:       a list of the requested items.
                       each entry will contain five bits of data:
                        The userId for use in drilling down,
                        The user name,
                        The user's name
                        the display e-mail
                        the user's blurb
        """
        columns = ['userId', 'userName', 'fullName', 'displayEmail', 'blurb',
                   'timeAccessed']
        searchcols = ['userName', 'fullName', 'displayEmail', 'blurb']

        ids, count =  database.KeyedTable.search( \
            self, columns, 'Users',
            searcher.Searcher.where(terms, searchcols, "AND active=1"),
            "userName", None, limit, offset)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][4] = searcher.Searcher.truncate(x[4], terms)

        return ids, count

    def getUsersList(self):
        """
        Returns a list of all users suitable for framing in a listbox or
        multi-select box.
        """
        cu = self.db.cursor()

        SQL = """SELECT userId, username || ' - ' || fullName, active
                FROM Users
                ORDER BY username"""

        cu.execute(SQL)

        results = cu.fetchall()
        return results

    def getUsersWithEmail(self):
        """
        Returns a list of all users suitable for sending e-mail
        """
        cu = self.db.cursor()
        SQL = """SELECT userId, fullName, email FROM Users"""

        cu.execute(SQL)

        results = cu.fetchall()
        return results

    def getUsers(self, sortOrder, limit, offset):
        """
        Returns a list of users for browsing limited by L{limit}
        starting with item L{offset}.
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       a list of the requested items.
        """
        cu = self.db.cursor()

        SQL = userlisting.sqlbase % (userlisting.ordersql[sortOrder],
            limit, offset)

        cu.execute(SQL)

        ids = []
        for x in cu.fetchall():
            ids.append(list(x))
            if len(ids[-1][userlisting.blurbindex]) > userlisting.blurbtrunclength:
                ids[-1][userlisting.blurbindex] = ids[-1][userlisting.blurbindex][:userlisting.blurbtrunclength] + "..."

        return ids

    def getNumUsers(self):
        """
        Returns the count of Users
        """
        cu = self.db.cursor()
        cu.execute( "SELECT count(userId) FROM Users WHERE active=1" )

        return cu.fetchone()[0]


    def getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute ( "SELECT username FROM Users WHERE userId = ?", userId)
        username = cu.fetchone()
        if not username:
            raise database.ItemNotFound("UserId: %d does not exist!"% userId)
        return username[0]

class User(database.TableObject):
    __slots__ = [UsersTable.key] + UsersTable.fields

    def getItem(self, id):
        return self.server.getUser(id)

    def getUsername(self):
        return self.username

    def getFullName(self):
        return self.fullName

    def getEmail(self):
        return self.email

    def getDisplayEmail(self):
        return self.displayEmail

    def getBlurb(self):
        return self.blurb

    def setEmail(self, newEmail):
        return self.server.setUserEmail(self.id, newEmail)

    def validateNewEmail(self, newEmail):
        return self.server.validateNewEmail(self.id,newEmail)

    def setDisplayEmail(self, newEmail):
        return self.server.setUserDisplayEmail(self.id, newEmail)

    def setPassword(self, newPassword):
        self.server.setPassword(self.id, newPassword)

    def setBlurb(self, blurb):
        self.server.setUserBlurb(self.id, blurb)

    def setFullName(self, fullName):
        self.server.setUserFullName(self.id, fullName)

    def cancelUserAccount(self):
        self.server.cancelUserAccount(self.id)

class ProjectUsersTable(database.DatabaseTable):
    name = "ProjectUsers"
    fields = ["projectId", "userId"]
    indexes = {'ProjectUsersIdx': "CREATE UNIQUE INDEX ProjectUsersIdx ON ProjectUsers(projectId, userId)",
               'ProjectUsersProjectIdx': "CREATE INDEX ProjectUsersProjectIdx ON ProjectUsers(projectId)",
               'ProjectUsersUserIdx': "CREATE INDEX ProjectUsersUserIdx ON ProjectUsers(userId)",
              }

    createSQL = """
                CREATE TABLE ProjectUsers (
                    projectId   INT,
                    userId      INT,
                    level       INT
                );"""

    def getOwnersByProjectName(self, projectname):
        cu = self.db.cursor()
        cu.execute("""SELECT u.username, u.email
                      FROM Projects pr, ProjectUsers p, Users u
                      WHERE pr.projectId=p.projectId AND p.userId=u.userId
                      AND pr.hostname=?
                      AND p.level=? AND pr.disabled=0""", projectname,
                   userlevels.OWNER)
        data = []
        for r in cu.fetchall():
            data.append(list(r))
        return data

    def getMembersByProjectId(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT p.userId, u.username, p.level
                      FROM ProjectUsers p, Users u
                      WHERE p.userId=u.userId AND p.projectId=?
                      ORDER BY p.level, u.username""",
                   projectId)
        data = []
        for r in cu.fetchall():
            data.append( [r[0], r[1], r[2]] )
        return data

    def new(self, projectId, userId, level):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()

        cu.execute("SELECT * FROM ProjectUsers WHERE projectId=? AND userId = ?",
                   projectId, userId)
        if cu.fetchall():
            self.db.rollback()
            raise database.DuplicateItem("membership")
        
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", projectId,
                   userId, level)
        self.db.commit()

    def onlyOwner(self, projectId, userId):
        cu = self.db.cursor()
        # verify userId is an owner of the project.
        cu.execute("SELECT level from ProjectUsers where projectId=? and userId = ?", projectId, userId)
        res = cu.fetchall()
        if (not bool(res)) or (res[0][0] != userlevels.OWNER):
            return False
        cu.execute("SELECT count(userId) FROM ProjectUsers WHERE projectId=? AND userId<>? and LEVEL = ?", projectId, userId, userlevels.OWNER)
        return not cu.fetchone()[0]

    def lastOwner(self, projectId, userId):
        cu = self.db.cursor()
        # check that there are developers
        cu.execute("SELECT count(userId) FROM ProjectUsers WHERE projectId=? AND userId<>? and LEVEL = ?", projectId, userId, userlevels.DEVELOPER)
        if not cu.fetchone()[0]:
            return False
        return self.onlyOwner(projectId, userId)

    def delete(self, projectId, userId):
        if self.lastOwner(projectId, userId):
            raise LastOwner()
        cu = self.db.cursor()
        cu.execute("DELETE FROM ProjectUsers WHERE projectId=? AND userId=?", projectId, userId)
        self.db.commit()


class Authorization(object):
    """
    Object describing a logged in user
    @cvar authorized: True if this user is authorized with a good password, False if not.
    @type authorized: bool
    @cvar userId: database id of the user represented by this object
    @type userId: int
    @cvar username: username of the user
    @type username: str
    @cvar email: email address of the user
    @type email: str
    @cvar displayEmail: email address of user provided for public display
    @type displayEmail: str
    @cvar fullName: full name of the user
    @type fullName: str
    @cvar blurb: a short description about and written by the user
    @type blurb: str
    @cvar timeAccessed: The time that the user last logged in
    @type timeAccessed: float
    @cvar groups: a list dictionaries containing the groups to which the user belongs
    @type groups: list
    """
    __slots__ = ('authorized', 'userId', 'username', 'email',
                 'displayEmail', 'fullName', 'blurb', 'token', 'stagnant',
                 'groups', 'admin', 'timeAccessed')

    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key in kwargs:
                self.__setattr__(key, kwargs[key])
            else:
                self.__setattr__(key, None)

    def setToken(self, authToken):
        self.token = authToken

    def getToken(self):
        return self.token

    def getDict(self):
        d = {}
        for slot in self.__slots__:
            d[slot] = self.__getattribute__(slot)
        return d

class UserGroupsTable(database.KeyedTable):
    name = "UserGroups"
    key = "userGroupId"

    createSQL = """CREATE TABLE UserGroups (
                       userGroupId     INTEGER PRIMARY KEY,
                       userGroup       STR)"""

    indexes = {"UserGroupsIndex" : """CREATE UNIQUE INDEX UserGroupsIndex
                                         ON UserGroups(userGroupId)"""}

    fields = ['userGroupId', 'userGroup']

    def __init__(self, db, cfg):
        self.cfg = cfg
        if 'authDbPath' in cfg._options and cfg.authDbPath:
            self.authDb = sqlite3.connect(cfg.authDbPath)
        database.DatabaseTable.__init__(self, db)
        cu = self.db.cursor()
        cu.execute("""SELECT userGroupId FROM UserGroups
                          WHERE userGroup='public'""")
        if not cu.fetchall():
            cu.execute("INSERT INTO UserGroups (userGroup) VALUES('public')")

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 9:
                # this schema version lineal is used to stock the
                # user groups table from the authrepo
                cu = self.db.cursor()
                aCu = self.authDb.cursor()
                aCu.execute('SELECT * FROM UserGroups')
                for userId, userName in aCu.fetchall():
                    cu.execute("""INSERT INTO UserGroups (userGroup)
                                      VALUES('%s')""" % userName)
                return (dbversion + 1) == self.schemaVersion
        return True

class UserGroupMembersTable(database.KeyedTable):
    name = "UserGroupMembers"
    key = "userGroupMemberId"

    createSQL = """CREATE TABLE UserGroupMembers (
                        userGroupId     INTEGER,
                        userId          INTEGER)"""

    indexes = {"UserGroupMembers_userId_fk":
                   """CREATE INDEX UserGroupMembers_userId_fk
                          FOREIGN KEY (userId) REFERENCES Users(userId)
                          ON DELETE CASCADE ON UPDATE CASCADE""",
               "UserGroupMembers_userGroupId_fk":
                   """CREATE INDEX UserGroupMembers_userGroupId_fk
                          FOREIGN KEY (userGroupId) REFERENCES
                          UserGroups(userGroupId)
                          ON DELETE RESTRICT ON UPDATE CASCADE"""}

    indexes = {}

    fields = ['userGroupId', 'userId']

    def __init__(self, db, cfg):
        self.cfg = cfg
        if 'authDbPath' in cfg._options and cfg.authDbPath:
            self.authDb = sqlite3.connect(cfg.authDbPath)
        database.DatabaseTable.__init__(self, db)

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 10:
                # this schema version lineal is used to stock the
                # user group members table from the authrepo. it must happen
                # subsequent to user groups table being stocked.
                cu = self.db.cursor()
                aCu = self.authDb.cursor()
                cu.execute("DELETE FROM UserGroupMembers")
                aCu.execute("""SELECT Users.user, UserGroups.usergroup
                                   FROM UserGroupMembers
                                   LEFT JOIN Users
                                       ON Users.userId=UserGroupMembers.userId
                                   LEFT JOIN UserGroups
                                   ON UserGroups.userGroupId=
                                           UserGroupMembers.userGroupId""")
                for username, groupname in [(x[0], x[1]) for x in \
                                            aCu.fetchall() if x[0]]:

                    cu.execute("SELECT userId from Users WHERE username=?",
                               username)
                    # Type errors indicate a user in authrepo that's not
                    # in mintdb. there shouldn't be any but that's no reason
                    # to fail horribly, so we'll just ignore them.
                    try:
                        userId = cu.fetchone()[0]
                    except TypeError:
                        continue
                    cu.execute("""SELECT userGroupId from UserGroups
                                      WHERE userGroup=?""", groupname)
                    try:
                        userGroupId = cu.fetchone()[0]
                    except TypeError:
                        continue
                    cu.execute("""INSERT INTO UserGroupMembers
                                      VALUES(%d, '%s')""" % (userGroupId,
                                                             userId))
                cu.execute("""SELECT userGroupId FROM UserGroups
                                  WHERE userGroup='public'""")
                groupId = cu.fetchone()[0]
                cu.execute("SELECT userId from Users")
                for userId in [x[0] for x in cu.fetchall()]:
                    cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                               groupId, userId)
                return (dbversion + 1) == self.schemaVersion
        return True

    def getGroupsForUser(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT userGroupId FROM UserGroupMembers WHERE userId=?",
                   userId)
        return [x[0] for x in cu.fetchall()]

def confirmString():
    """
    Generate a confirmation string
    """
    hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
    return sha1helper.sha1ToString(hash)
        
        
def newPassword(length = 6):
    """
    @param length: length of random password generated
    @returns: returns a character string of random letters and digits.
    @rtype: str
    """
    choices = string.letters + string.digits
    pw = "".join([random.choice(choices) for x in range(length)])
    return pw


def sendMailWithChecks(fromEmail, fromEmailName, toEmail, subject, body):
    validateEmailDomain(toEmail)
    try:
        sendMail(fromEmail, fromEmailName, toEmail, subject, body)
    except smtplib.SMTPRecipientsRefused:
        raise MailError("Email could not be sent: Recipient refused by server.")


def validateEmailDomain(toEmail):
    toDomain = smtplib.quoteaddr(toEmail).split('@')[-1][0:-1]
    VALIDATED_DOMAINS = ('localhost', 'localhost.localdomain')
    # basically if we don't implicitly know this domain,
    # and we can't look up the DNS entry of the MX
    # use gethostbyname to validate the email address
    try:
        if not ((toDomain in VALIDATED_DOMAINS) or digMX(toDomain)):
            socket.gethostbyname(toDomain)
    except (socket.gaierror, dns.resolver.NXDOMAIN):
        raise MailError("Email could not be sent: Bad domain name.")


def sendMail(fromEmail, fromEmailName, toEmail, subject, body):
    """
    @param fromEmail: email address for the From: header 
    @type fromEmail: str
    @param fromEmailName: name for the From: header
    @type fromEmailName: str
    @param toEmail: recipient's email address
    @type toEmail: str
    @param subject: Email subject
    @type subject: str
    @param body: Email body text
    @type body: str
    """
    
    msg = MIMEText.MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = '"%s" <%s>' % (fromEmailName, fromEmail)
    msg['To'] = toEmail

    s = smtplib.SMTP()
    s.connect()
    s.sendmail(fromEmail, [toEmail], msg.as_string())
    s.close()
