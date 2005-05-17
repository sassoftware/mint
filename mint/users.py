#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys
import conary
from repository import netclient

class UsersTable:
    def __init__(self, db, cfg):
        self.db = db
        self.cfg = cfg

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
        
        tables = [ x[0] for x in cu ]
        if 'Users' not in tables:
            cu.execute("""
                CREATE TABLE Users (
                    userId          INTEGER PRIMARY KEY,
                    username        STR,
                    fullName        STR,
                    email           STR,
                    timeCreated     INT,
                    timeAccessed    INT,
                    active          INT,
                    confirmation    STR
                );""")
        self.db.commit()

    def checkAuth(self, authToken):
        username, password = authToken

        cu = self.db.cursor()
        cu.execute("""SELECT userId FROM Users 
                      WHERE username=? AND active=1""", username)
        r = cu.fetchone()

        if r:
            authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)
            
            if 'mint' in authRepo.getUserGroups():
                return (True, r[0])
        return (False, -1)

class Authorization:
    def __init__(self, passwordOK = False, userId = -1):
        self.passwordOK = passwordOK
        self.userId = userId
