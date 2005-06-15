#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import random
import string
import sys
import time

import email
import smtplib

from repository import netclient
import repository.netrepos.netauth
from lib import sha1helper

from mint_error import MintError
import database
import userlevels

from imagetool import imagetool

class ConfirmError(MintError):
    def __str__(self):
        return "your registration could not be confirmed"

class AlreadyConfirmed(MintError):
    def __str__(self):
        return "registration already confirmed"

class UserAlreadyExists(MintError):
    def __str__(self):
        return "user already exists"

class UsersTable(database.KeyedTable):
    name = 'Users'
    key = 'userId'
    createSQL = """
                CREATE TABLE Users (
                    userId          INTEGER PRIMARY KEY,
                    username        STR UNIQUE,
                    fullName        STR,
                    email           STR,
                    displayEmail    STR,
                    timeCreated     INT,
                    timeAccessed    INT,
                    active          INT,
                    blurb           STR,
                    confirmation    STR
                );"""
    fields = ['userId', 'username', 'fullName', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'confirmation', 'blurb']
             
    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg
             
    def checkAuth(self, authToken, checkRepo = True):
        username, password = authToken
        cu = self.db.cursor()
        cu.execute("""SELECT userId, email, displayEmail, fullName, blurb FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()

        if r:
            groups = []
            if checkRepo:
                authUrl = self.cfg.authRepoUrl % (username, password)
                authLabel = self.cfg.authRepo.keys()[0]
                
                authRepo = {authLabel: authUrl}
                repo = netclient.NetworkRepositoryClient(authRepo)
                groups = repo.getUserGroups(authLabel)
                
            if username in groups or not checkRepo:
                return {'authorized':   True,
                        'userId':       r[0],
                        'username':     username,
                        'email':        r[1],
                        'displayEmail': r[2],
                        'fullName':     r[3],
                        'blurb':        r[4]}
            else:
                return {'authorized': False, 'userId': -1}
        else:
            return {'authorized': False, 'userId': -1}

    def registerNewUser(self, username, password, fullName, email, active):
        def confirmString():
            hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
            return sha1helper.sha1ToString(hash)

        # XXX this should be an atomic operation if possible:
        #     it would be nice to roll back previous operations
        #     if one in the chain fails
        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepo)
        confirm = confirmString()
        repoLabel = self.cfg.authRepo.keys()[0]

        try: 
            authRepo.addUser(repoLabel, username, password)
            authRepo.addAcl(repoLabel, username, None, None, False, False, False)
        except repository.netrepos.netauth.UserAlreadyExists:
            raise UserAlreadyExists

        imagetoolUrl = self.cfg.imagetoolUrl % (self.cfg.authUser, self.cfg.authPass)
        itclient = imagetool.ImageToolClient(imagetoolUrl)
        itclient.newUser(username, internalUser = False)

        if not active:
            message = "\n".join(["Thank you for registering for the rpath Linux customized",
                                 "distribution tool.",
                                 "",
                                 "Please follow the link below to confirm your registration:",
                                 "",
                                 "http://%s/confirm?id=%s" % (self.cfg.domainName, confirm),
                                 "",
                                 "Contact custom@rpath.com for help, or join the IRC channel #conary",
                                 "on the Freenode IRC network (http://www.freenode.net/) for live help."])

            sendMail(self.cfg.adminMail, "rpath.com", email, "rpath.com registration", message)
            
        try:
            userId = self.new(username = username,
                              fullName = fullName,
                              email = email,
                              active = active,
                              confirmation = confirm)
        except database.DuplicateItem:
            raise UserAlreadyExists

    def confirm(self, confirm):
        cu = self.db.cursor()

        cu.execute("SELECT active FROM Users WHERE confirmation=? AND active=1", confirm)
        if cu.fetchone():
            raise AlreadyConfirmed

        cu.execute("SELECT userId FROM Users WHERE confirmation=? AND active=0", confirm)
        if len(cu.fetchall()) != 1:
            raise ConfirmError
        else:
            cu.execute("UPDATE Users SET active=1 WHERE confirmation=?", confirm)
            self.db.commit()

            cu.execute("SELECT userId FROM Users WHERE confirmation=?", confirm)
            r = cu.fetchone()
            return r[0]

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

    def setDisplayEmail(self, newEmail):
        return self.server.setUserDisplayEmail(self.id, newEmail)

    def setPassword(self, newPassword):
        self.server.setPassword(self.id, newPassword)
    
    def setBlurb(self, blurb):
        self.server.setUserBlurb(self.id, blurb)

class ProjectUsersTable(database.DatabaseTable):
    name = "ProjectUsers"
    fields = ["projectId", "userId"]

    createSQL = """
                CREATE TABLE ProjectUsers (
                    projectId   INT,
                    userId      INT,
                    level       INT
                );"""

    def getProjectUsers(self, projectId):
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
                 'displayEmail', 'fullName', 'blurb')

    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key in kwargs:
                self.__setattr__(key, kwargs[key])
            else:
                self.__setattr__(key, None)

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
    msg = email.MIMEText.MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = '"%s" <%s>' % (fromEmailName, fromEmail)
    msg['To'] = toEmail

    s = smtplib.SMTP()
    s.connect()
    s.sendmail(fromEmail, [toEmail], msg.as_string())
    s.close()
