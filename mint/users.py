#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

global _dnspython_present

try:
    import dns.resolver
    _dnspython_present = True
except ImportError:
    _dnspython_present = False

from conary.lib.digestlib import md5
import os
import random
import smtplib
import socket
import time
from email import MIMEText

from mint import userlevels
from mint import templates
from mint import helperfuncs
from mint.templates import registerNewUser
from mint.templates import validateNewEmail
from mint import searcher
from mint import userlisting
from mint.mint_error import *
from mint import usertemplates
from mint.lib import database

from conary import repository
from conary.lib import sha1helper

from conary.repository.netrepos.netauth import nameCharacterSet

class ConfirmationsTable(database.KeyedTable):
    name = 'Confirmations'
    key = 'userId'
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

    fields = ['userId', 'username', 'fullName', 'salt', 'passwd', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'blurb']

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)
        self.confirm_table = ConfirmationsTable(db)
        # not passing a db object since a mint db isn't correct
        # and we're only using the _checkPassword function anyway
        self._userAuth = repository.netrepos.netauth.UserAuthorization(
            db = None, pwCheckUrl = self.cfg.externalPasswordURL,
            cacheTimeout = self.cfg.authCacheTimeout)

    def changePassword(self, username, password):
        salt, passwd = self._mungePassword(password)
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET salt=?, passwd=? WHERE username=?",
                   salt, passwd, username)
        self.db.commit()

    def _checkPassword(self, user, salt, password, challenge):
        return self._userAuth._checkPassword( \
                user, salt, password, challenge)

    def _mungePassword(self, password):
        m = md5()
        salt = os.urandom(4)
        m.update(salt)
        m.update(password)
        return salt, m.hexdigest()

    def _getUserGroups(self, authToken):
        user, challenge = authToken

        cu = self.db.cursor()
        cu.execute("SELECT salt, passwd FROM Users WHERE username=?", user)
        r = cu.fetchone()
        if r  and self._checkPassword(user, r[0], r[1], challenge):
            cu.execute("""SELECT UserGroups.userGroup
                          FROM UserGroups, Users, UserGroupMembers
                          WHERE UserGroups.userGroupId =
                                  UserGroupMembers.userGroupId AND
                                UserGroupMembers.userId = Users.userId AND
                                Users.username = ?""", user)
            return [row[0] for row in cu.fetchall()]
        else:
            return []

    def checkAuth(self, authToken):
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
            try:
                groups = self._getUserGroups(authToken)
            except repository.errors.OpenError:
                auth = noAuth

            if type(groups) != list:
                raise AuthRepoError

            if username in groups:
                auth = {'authorized':   True,
                        'userId':       int(r[0]),
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

        message = templates.write(templates.validateNewEmail, username = user['username'],
            cfg = self.cfg, confirm = confirm)

        sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, email,
                "Your %s account's email address must be confirmed" % self.cfg.productName, message)
        self.invalidateUser(userId, confirm)
        return True

    def invalidateUser(self, userId, confirm = None):
        if not confirm:
            confirm = confirmString()
        try:
            self.confirm_table.new(userId = userId,
                                   timeRequested = time.time(),
                                   confirmation = confirm)
        except DuplicateItem:
            self.confirm_table.update(userId, confirmation = confirm)

    def registerNewUser(self, username, password, fullName, email,
                        displayEmail, blurb, active):
        if self.cfg.sendNotificationEmails and not active:
            validateEmailDomain(email)
        if username.lower() == self.cfg.authUser.lower():
            raise IllegalUsername
        for letter in username:
            if letter not in nameCharacterSet:
                raise InvalidUsername

        confirm = confirmString()

        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(*) FROM UserGroups
                          WHERE UPPER(userGroup)=UPPER(?)""",
                   username)
        if cu.fetchone()[0]:
            raise UserAlreadyExists

        cu.execute("SELECT COUNT(*) FROM Users WHERE UPPER(username)=UPPER(?)",
                   username)
        if cu.fetchone()[0]:
            raise UserAlreadyExists

        salt, passwd = self._mungePassword(password)

        if self.cfg.sendNotificationEmails and not active:
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

        except DuplicateItem:
            self.db.rollback()
            raise UserAlreadyExists
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        if not active:
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
            self.db.commit()

            return r[0]

    def search(self, terms, limit, offset, includeInactive=False):
        """
        Returns a list of users matching L{terms} of length L{limit}
        starting with item L{offset}.
        @param terms: Search terms
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @param includeInactive: set True to include users needing confirmations
        @return:       a list of the requested items.
                       each entry will contain eight bits of data:
                        The userId for use in drilling down,
                        The user name,
                        The user's name
                        the display e-mail
                        the user's blurb
                        time created
                        time last accessed
                        account active flag
        """
        columns = ['userId', 'userName', 'fullName', 'displayEmail', 'blurb',
                   'timeCreated', 'timeAccessed', 'active']
        searchcols = ['userName', 'fullName', 'displayEmail', 'blurb']

        if includeInactive:
            whereClause = searcher.Searcher.where(terms, searchcols)
        else:
            whereClause = searcher.Searcher.where(terms, searchcols, "AND active=1")

        ids, count =  database.KeyedTable.search( \
            self, columns, 'Users', whereClause,
            searcher.Searcher.order(terms, searchcols, 'userName'), None,
            limit, offset)
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

        userConcat = database.concat(self.db, 'username', '" - "', 'fullName')
        SQL = """SELECT userId, %s, active
                FROM Users
                ORDER BY username""" % userConcat

        cu.execute(SQL)

        # results must be a built in type
        results = [tuple(x) for x in cu.fetchall()]
        for index, (userId, userName, active) in enumerate(results[:]):
            cu.execute("""SELECT COUNT(*) FROM UserGroupMembers
                              LEFT JOIN UserGroups
                                  ON UserGroupMembers.userGroupId=
                                          UserGroups.userGroupId
                              WHERE UserGroup = 'MintAdmin'
                              AND userId=?""", userId)
            if cu.fetchone()[0]:
                results[index] = userId, userName + " (admin)", active
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

    def getUsersWithAwsAccountNumber(self):
        """
        Returns a list of all users with Aws account numbers.
        """
        cu = self.db.cursor()
        SQL = """
            SELECT u.userId, ud.value
            FROM Users u
                JOIN UserData ud on u.userId = ud.userId
            WHERE ud.name = 'awsAccountNumber'
              AND ud.value is not NULL
            """
        cu.execute(SQL)
        results = cu.fetchall()
        return results

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

    def getAMIBuildsForUser(self, userId):
        cu = self.db.cursor()
        cu.execute("""\
            SELECT bd.value as amiId,
                   b.projectId,
                   COALESCE(pr.timePublished,0) != 0 as isPublished,
                   p.hidden as isPrivate,
                   pu.level
            FROM projectusers pu
              JOIN projects p USING (projectId)
              JOIN builds b USING (projectId)
              LEFT OUTER JOIN publishedReleases pr USING (pubReleaseId)
              JOIN buildData bd ON (bd.buildId = b.buildId)
            WHERE bd.name = 'amiId'
              AND b.deleted = 0
              AND pu.userId = ?""", userId)
        return cu.fetchall_dict()

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
        # NOTE: .strip done pre-insert for Kid's sake
        return self.server.setUserDisplayEmail(self.id, newEmail.strip())

    def setPassword(self, newPassword):
        self.server.setPassword(self.id, newPassword)

    def setBlurb(self, blurb):
        # NOTE: .strip done pre-insert for Kid's sake
        self.server.setUserBlurb(self.id, blurb.strip())

    def setFullName(self, fullName):
        self.server.setUserFullName(self.id, fullName)

    def cancelUserAccount(self):
        self.server.cancelUserAccount(self.id)

    def setDataValue(self, name, value):
        self.server.setUserDataValue(self.username, name, value)

    def getDataValue(self, name):
        return self.server.getUserDataValue(self.username, name)

    def getDefaultedData(self):
        return self.server.getUserDataDefaulted(self.username)

    def getDataTemplate(self):
        return usertemplates.userPrefsVisibleTemplate
    
    def getDefaultedDataAWS(self):
        return self.server.getUserDataDefaultedAWS(self.username)
    
    def getDataTemplateAWS(self):
        return usertemplates.userPrefsAWSTemplate

    def getDataDict(self, template = None):
        dataDict = self.server.getUserDataDict(self.username)
        if not template:
            template = self.getDataTemplate()
        for name in template:
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict


class ProjectUsersTable(database.DatabaseTable):
    name = "ProjectUsers"
    fields = ["projectId", "userId", "level"]

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

    def getUserlevelForProjectMember(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT level FROM ProjectUsers
                      WHERE projectId = ? AND userId = ?""",
                      projectId, userId)
        res = cu.fetchone()
        if res:
            return res[0]
        else:
            raise ItemNotFound()

    def getEC2AccountNumbersForProjectUsers(self, projectId):
        writers = []
        readers = []
        cu = self.db.cursor()
        cu.execute("""
            SELECT CASE WHEN MIN(pu.level) <= 1 THEN 1 ELSE 0 END AS isWriter,
                ud.value AS awsAccountNumber
            FROM projectUsers AS pu
                JOIN userData AS ud
                    ON ud.name = 'awsAccountNumber'
                       AND pu.userId = ud.userId
                       AND length(ud.value) > 0
            WHERE pu.projectId = ?
            GROUP BY ud.value""", projectId)
        for res in cu.fetchall():
            if res[0]:
                writers.append(res[1])
            else:
                readers.append(res[1])
        return writers, readers

    def new(self, projectId, userId, level, commit=True):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()

        cu.execute("SELECT * FROM ProjectUsers WHERE projectId=? AND userId = ?",
                   projectId, userId)
        if cu.fetchall():
            self.db.rollback()
            raise DuplicateItem("membership")

        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", projectId,
                   userId, level)
        if commit:
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

    def delete(self, projectId, userId, commit=True, force=False):
        if self.lastOwner(projectId, userId):
            if not force:
                raise LastOwner()
        cu = self.db.cursor()
        cu.execute("DELETE FROM ProjectUsers WHERE projectId=? AND userId=?", projectId, userId)
        if commit:
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
    fields = ['userGroupId', 'userGroup']

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)
        cu = self.db.cursor()
        cu.execute("""SELECT userGroupId FROM UserGroups
                          WHERE userGroup='public'""")
        if not cu.fetchall():
            cu.execute("INSERT INTO UserGroups (userGroup) VALUES('public')")

    def getMintAdminId(self):
        """
        Return the id of the MintAdmin user.

        NOTE: This will create the MintAdmin UserGroup if it doesn't
        already exist.
        """
        try:
            mintAdminId = self.getIdByColumn('userGroup', 'MintAdmin')
        except ItemNotFound:
            mintAdminId = self.new(userGroup = 'MintAdmin')
        except:
            raise
        return mintAdminId


class UserGroupMembersTable(database.DatabaseTable):
    name = "UserGroupMembers"
    fields = ['userGroupId', 'userId']

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.DatabaseTable.__init__(self, db)

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
    return helperfuncs.genPassword(length)

def sendMailWithChecks(fromEmail, fromEmailName, toEmail, subject, body):
    validateEmailDomain(toEmail)
    try:
        sendMail(fromEmail, fromEmailName, toEmail, subject, body)
    except smtplib.SMTPRecipientsRefused:
        raise MailError("Email could not be sent: Recipient refused by server.")
    except socket.error, e:
        raise MailError("Email could not be sent: %s" % str(e))


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
