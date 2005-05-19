#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys
import conary
from repository import netclient

from mint_error import MintError
from database import DatabaseTable

class PermissionDenied(MintError):
    def __str__(self):
        return "permission denied from XMLRPC server"

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

    def registerNewUser(self, username, password, fullName, email):
        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepo)

        repoLabel = self.cfg.authRepo.keys()[0]
        authRepo.addUser(repoLabel, username, password)
        authRepo.addAcl(repoLabel, username, None, None, True, False, True)
        return self.new(username = username,
                        fullName = fullName,
                        email = email,
                        active = True)

class Authorization:
    __slots__ = ['authorized', 'userId', 'username']
    authorized = False
    userId = -1
    username = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
