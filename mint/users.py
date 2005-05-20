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

import conary
from repository import netclient

from mint_error import MintError
from database import DatabaseTable

class PermissionDenied(MintError):
    def __str__(self):
        return "permission denied from XMLRPC server"

class ConfirmError(MintError):
    def __str__(self):
        return "your registration could not be confirmed"

class AlreadyConfirmed(MintError):
    def __str__(self):
        return "registration already confirmed"

class UsersTable(DatabaseTable):
    name = 'Users'
    key = 'userId'
    createSQL = """
                CREATE TABLE Users (
                    userId          INTEGER PRIMARY KEY,
                    username        STR UNIQUE,
                    fullName        STR,
                    email           STR,
                    timeCreated     INT,
                    timeAccessed    INT,
                    active          INT,
                    confirmation    STR
                );"""
    fields = ['userId', 'username', 'fullName', 'email',
              'timeCreated', 'timeAccessed',
              'active', 'confirmation']
             
    def __init__(self, db, cfg):
        DatabaseTable.__init__(self, db)
        self.cfg = cfg
             
    def checkAuth(self, authToken):
        username, password = authToken

        cu = self.db.cursor()
        cu.execute("""SELECT userId FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()

        if r:
            authUrl = self.cfg.authRepoUrl % (username, password)
            authLabel = self.cfg.authRepo.keys()[0]
            
            authRepo = {authLabel: authUrl}
            repo = netclient.NetworkRepositoryClient(authRepo)
            
            groups = repo.getUserGroups(authLabel)
            if username in groups:
                return (True, r[0], username)
        return (False, -1, None)

    def registerNewUser(self, username, password, fullName, email, active):
        def confirmString():
            hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
            return sha1helper.sha1ToString(hash)

        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepo)

        repoLabel = self.cfg.authRepo.keys()[0]
        authRepo.addUser(repoLabel, username, password)
        authRepo.addAcl(repoLabel, username, None, None, False, False, False)

        if not active:
            message = """Thank you for registering for the rpath Linux customized
distribution tool.

Please follow the link below to confirm your registration:

%sconfirm?id=%s

Contact custom@rpath.com for help, or join the IRC channel #conary
on the Freenode IRC network (http://www.freenode.net/) for live help.
""" % (self.cfg.domain, confirm)

            msg = MIMEText.MIMEText(message)
            msg['Subject'] = "rpath Linux Mint Registration"
            msg['From'] = "\"rpath Linux\" <%s>" % self.cfg.adminMail
            msg['To'] = email

            s = smtplib.SMTP()
            s.connect()
            s.sendmail(self.cfg.adminMail, [email], msg.as_string())
            s.close()
    
        
        return self.new(username = username,
                        fullName = fullName,
                        email = email,
                        active = activeNow,
                        confirmation = confirmString())

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



class Authorization:
    __slots__ = ['authorized', 'userId', 'username']
    authorized = False
    userId = -1
    username = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
