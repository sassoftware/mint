#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import random
import sys
import time

import email
from email import MIMEText
import smtplib

from repository import netclient
import repository.netrepos.netauth
from lib import sha1helper

from mint_error import MintError
import database
import userlevels

class PermissionDenied(MintError):
    def __str__(self):
        return "permission denied from XMLRPC server"

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
                    confirmation    STR
                );"""
    fields = ['userId', 'username', 'fullName', 'email',
              'displayEmail', 'timeCreated', 'timeAccessed',
              'active', 'confirmation']
             
    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg
             
    def checkAuth(self, authToken):
        username, password = authToken

        cu = self.db.cursor()
        cu.execute("""SELECT userId, email, displayEmail, fullName FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()

        if r:
            authUrl = self.cfg.authRepoUrl % (username, password)
            authLabel = self.cfg.authRepo.keys()[0]
            
            authRepo = {authLabel: authUrl}
            repo = netclient.NetworkRepositoryClient(authRepo)
            
            groups = repo.getUserGroups(authLabel)
            if username in groups:
                return {'authorized':   True,
                        'userId':       r[0],
                        'username':     username,
                        'email':        r[1],
                        'displayEmail': r[2],
                        'fullName':     r[3]}
        else:
            return {'authorized': False, 'userId': -1}

    def registerNewUser(self, username, password, fullName, email, active):
        def confirmString():
            hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
            return sha1helper.sha1ToString(hash)

        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepo)

        confirm = confirmString()
        repoLabel = self.cfg.authRepo.keys()[0]
        try: 
            authRepo.addUser(repoLabel, username, password)
            authRepo.addAcl(repoLabel, username, None, None, False, False, False)
        except repository.netrepos.netauth.UserAlreadyExists:
            raise UserAlreadyExists

        if not active:
            message = """Thank you for registering for the rpath Linux customized
distribution tool.

Please follow the link below to confirm your registration:

%sconfirm?id=%s

Contact custom@rpath.com for help, or join the IRC channel #conary
on the Freenode IRC network (http://www.freenode.net/) for live help.
""" % (self.cfg.domainName, confirm)

            msg = MIMEText.MIMEText(message)
            msg['Subject'] = "rpath Linux Mint Registration"
            msg['From'] = "\"rpath Linux\" <%s>" % self.cfg.adminMail
            msg['To'] = email

            s = smtplib.SMTP()
            s.connect()
            s.sendmail(self.cfg.adminMail, [email], msg.as_string())
            s.close()
    
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

        cu.execute("SELECT userId FROM Users WHERE active=0 AND confirmation=?", confirm)
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

    def setEmail(self, newEmail):
        return self.server.users.update(self.id, email = newEmail)

    def setDisplayEmail(self, newEmail):
        return self.server.users.update(self.id, displayEmail = newEmail)

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
        cu.execute("""SELECT p.userId, u.username
                      FROM ProjectUsers p, Users u
                      WHERE p.userId=u.userId AND p.projectId=?""",
                   projectId)
        data = []
        for r in cu.fetchall():
            data.append( [r[0], r[1]] )
        return data

    def new(self, projectId, userId, level):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", projectId, userId, level)
        self.db.commit()
        return 0

class Authorization:
    __slots__ = ['authorized', 'userId', 'username', 'email', 'fullName']
    authorized = False
    userId = -1
    username = None
    email = None
    fullName = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
