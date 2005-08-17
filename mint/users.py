#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import random
import string
import re
import sys
import time

import email
from email import MIMEText
import smtplib
import socket
from string import find

from repository import netclient
from repository.repository import OpenError
import repository.netrepos.netauth
from lib import sha1helper

from mint_error import MintError
from mint_error import PermissionDenied
import database
import userlevels
import searcher
import userlisting

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

class UsersTable(database.KeyedTable):
    name = 'Users'
    key = 'userId'
    createSQL = """
                CREATE TABLE Users (
                    userId          INTEGER PRIMARY KEY,
                    username        STR UNIQUE,
                    fullName        STR,
                    email           STR,
                    displayEmail    STR DEFAULT "",
                    timeCreated     INT,
                    timeAccessed    INT,
                    active          INT,
                    blurb           STR DEFAULT ""
                )"""

    fields = ['userId', 'username', 'fullName', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'blurb']

    indexes = {"UsersUsernameIdx": "CREATE INDEX UsersUsernameIdx ON Users(username)",
               "UsersActiveIdx":   "CREATE INDEX UsersActiveIdx ON Users(username, active)"}

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg
        self.confirm_table = ConfirmationsTable(db)

    def checkAuth(self, authToken, checkRepo = True):
        username, password = authToken
        cu = self.db.cursor()
        cu.execute("""SELECT userId, email, displayEmail, fullName, blurb FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()
   
        noAuth = {'authorized': False, 'userId': -1}
        if r:
            groups = []
            if checkRepo:
                authUrl = self.cfg.authRepoUrl % (username, password)
                authLabel = self.cfg.authRepoMap.keys()[0]

                authRepo = {authLabel: authUrl}
                repo = netclient.NetworkRepositoryClient(authRepo)
                try:
                    groups = repo.getUserGroups(authLabel)
                except OpenError:
                    auth = noAuth

            if username in groups or not checkRepo:
                auth = {'authorized':   True,
                        'userId':       r[0],
                        'username':     username,
                        'email':        r[1],
                        'displayEmail': r[2],
                        'fullName':     r[3],
                        'blurb':        r[4],
                        'stagnant':     self.isUserStagnant(r[0])}
            else:
                auth = noAuth
        else:
            auth = noAuth
        return auth

    def validateNewEmail(self, userId, email):
        def confirmString():
            hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
            return sha1helper.sha1ToString(hash)

        confirm = confirmString()
        if self.cfg.hostName:
            confirmDomain = "%s.%s" % (self.cfg.hostName, self.cfg.domainName)
        else:
            confirmDomain = self.cfg.domainName
        message = "\n".join(["Thank you for updating your email address with the ",
                             "%s."%self.cfg.productName,
                             "",
                             "Please follow the link below to confirm your new address",
                             "",
                             "http://%s/confirm?id=%s" % (confirmDomain, confirm),
                             "",
                             "Contact %s"%self.cfg.supportContactTXT,
                             "if you need assistence."])
        try:
            socket.gethostbyname(email[find(email, '@')+1:])
            sendMail(self.cfg.adminMail, self.cfg.productName, email, "%s registration"%self.cfg.productName, message)
        except smtplib.SMTPRecipientsRefused:
            raise MailError("Email could not be sent: Recipient refused by server.")
        except socket.gaierror:
            raise MailError("Email could not be sent: Bad domain name.")
        try:
            self.confirm_table.new(userId = userId,
                                   timeRequested = time.time(),
                                   confirmation = confirm)
        except database.DuplicateItem:
            self.confirm_table.update(userId, confirmation = confirm)

    def registerNewUser(self, username, password, fullName, email, displayEmail, blurb, active):
        def confirmString():
            hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
            return sha1helper.sha1ToString(hash)

        # XXX this should be an atomic operation if possible:
        #     it would be nice to roll back previous operations
        #     if one in the chain fails
        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)
        confirm = confirmString()
        repoLabel = self.cfg.authRepoMap.keys()[0]

        try: 
            authRepo.addUser(repoLabel, username, password)
            authRepo.addAcl(repoLabel, username, None, None, False, False, False)
        except repository.netrepos.netauth.UserAlreadyExists:
            raise UserAlreadyExists
        except repository.netrepos.netauth.GroupAlreadyExists:
            raise GroupAlreadyExists

        if self.cfg.hostName:
            confirmDomain = "%s.%s" % (self.cfg.hostName, self.cfg.domainName)
        else:
            confirmDomain = self.cfg.domainName
            
        if not active:
            message = "\n".join(["Thank you for registering for %s"%self.cfg.productName,
                                 "",
                                 "Please follow the link below to confirm your registration",
                                 "for username %s:" % username,
                                 "",
                                 "http://%s/confirm?id=%s" % (confirmDomain, confirm),
                                 "",
                                 "Contact %s"%self.cfg.supportContactTXT,
                                 "if you need assistence."])
            try:
                socket.gethostbyname(email[find(email, '@')+1:])
                sendMail(self.cfg.adminMail, self.cfg.productName, email, "%s registration"%self.cfg.productName, message)
            except smtplib.SMTPRecipientsRefused:
                authRepo.deleteUserByName(repoLabel, username)
                raise MailError("Email could not be sent: Recipient refused by server.")
            except socket.gaierror:
                authRepo.deleteUserByName(repoLabel, username)
                raise MailError("Email could not be sent: Bad domain name.")
        try:
            userId = self.new(username = username,
                              fullName = fullName,
                              email = email,
                              displayEmail = displayEmail,
                              timeCreated = time.time(),
                              timeAccessed = 0,
                              blurb = blurb,
                              active = active)
        except database.DuplicateItem:
            raise UserAlreadyExists
        self.confirm_table.new(userId = userId,
                               timeRequested = time.time(),
                               confirmation = confirm)
        return userId

    def cancelUserAccount(self,userId):
        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)
        repoLabel = self.cfg.authRepoMap.keys()[0]

        cu = self.db.cursor()
        cu.execute("SELECT username FROM Users WHERE userId=?", userId)
        r = cu.fetchall()
        if not len(r):
            raise database.ItemNotFound("UserId: %d does not exist!"% userId)
        username = r[0][0]

        cu.execute("SELECT max(flagged) FROM (select A.projectId, COUNT(B.userId)*not(COUNT(C.userId)) AS flagged FROM ProjectUsers AS A LEFT JOIN ProjectUsers AS B ON A.projectId=B.projectId AND B.level=1 LEFT JOIN ProjectUsers AS C ON C.projectId=A.projectId AND C.level=0 AND C.userId<>A.userId WHERE A.userId=? GROUP BY A.projectId)", userId)
        r=cu.fetchall()
        if len(r):
            raise LastOwner

        authRepo.deleteUserByName(repoLabel, username)
        
        cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?", userId)
        cu.execute("UPDATE Jobs SET userId=NULL WHERE userId=?", userId)
        cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        cu.execute("DELETE FROM Users WHERE userId=?", userId)
        self.db.commit()

    def isUserStagnant(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT timeRequested FROM Confirmations WHERE userId=?", userId)
        results = cu.fetchall()
        if len(results) == 1:
            if ( time.time() - results[0][0]) > 172800:
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
            self.db.commit()

            cu.execute("DELETE FROM Confirmations WHERE userId=?", r[0])
            self.db.commit()

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
        columns = ['userId', 'userName', 'fullName', 'displayEmail', 'blurb']
        searchcols = ['userName', 'fullName', 'displayEmail', 'blurb']

        ids, count =  database.KeyedTable.search(self, columns, 'Users',
                                                 searcher.Searcher.where(terms, searchcols),
                                                 "userName", None, limit, offset)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][4] = searcher.Searcher.truncate(x[4], terms)

        return ids, count

    def getUsers(self, sortOrder, limit, offset):
        """
        Returns a list of users matching L{terms} of length L{limit}
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
        for x in cu:
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


        return cu.next()[0]

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
                      AND p.level=?""", projectname, userlevels.OWNER)
        data = []
        for r in cu.fetchall():
            data.append(list(r))
        return data

    def getMembersByProjectId(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT p.userId, u.username, p.level
                      FROM ProjectUsers p, Users u
                      WHERE p.userId=u.userId AND p.projectId=?""",
                   projectId)
        data = []
        for r in cu.fetchall():
            data.append( [r[0], r[1], r[2]] )
        return data

    def new(self, projectId, userId, level):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()

        cu.execute("SELECT * FROM ProjectUsers WHERE projectId=? AND userId=?",
                   projectId, userId)
        if cu.fetchall():
            raise database.DuplicateItem("membership")
        
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", projectId, userId, level)
        self.db.commit()
        return 0

    def delete(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM ProjectUsers WHERE projectId=? AND userId=?", projectId, userId)
        self.db.commit()
        return 0


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
    @cvar displayEmail: possibly obfuscated email address of the user
    @type displayEmail: str
    @cvar fullName: full name of the user
    @type fullName: str
    @cvar blurb: a short description about and written by the user
    @type blurb: str
    """
    __slots__ = ('authorized', 'userId', 'username', 'email',
                 'displayEmail', 'fullName', 'blurb', 'token', 'stagnant')

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

def newPassword(length = 6):
    """
    @param length: length of random password generated
    @returns: returns a character string of random letters and digits.
    @rtype: str
    """
    choices = string.letters + string.digits
    pw = "".join([random.choice(choices) for x in range(length)])
    return pw

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
