#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import os
import re

import conary
from lib import util
from repository.netrepos.netserver import NetworkRepositoryServer

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')

class DuplicateHostname(Exception):
    def __str__(self):
        return "hostname already exists"

# XXX sort of stolen from conary/server/server.py
class EmptyNetworkRepositoryServer(NetworkRepositoryServer):
    def reset(self, authToken, clientVersion):
        import shutil
        shutil.rmtree(self.repPath + '/contents')
        os.mkdir(self.repPath + '/contents')

        # cheap trick. sqlite3 doesn't mind zero byte files; just replace
        # the file with a zero byte one (to change the inode) and reopen
        open(self.repPath + '/sqldb.new', "w")
        os.rename(self.repPath + '/sqldb.new', self.repPath + '/sqldb')
        self.reopen()

        return 0

class ReposTable:
    def __init__(self, db):
        self.db = db

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
        
        tables = [ x[0] for x in cu ]
        if 'Repos' not in tables:
            cu.execute("""
                CREATE TABLE Repos (
                    reposId         INTEGER PRIMARY KEY,
                    projectId       INT,
                    hostname        STR UNIQUE
                );""")
                
    def createRepos(self, projectId, hostname, reposPath, username, password):
        assert(validHost.match(hostname) != None)
        cu = self.db.cursor()

        try:
            cu.execute("""INSERT INTO Repos VALUES (NULL, ?, ?)""",
                projectId, hostname)
        except sqlite3.ProgrammingError: # XXX make sure this is really a 'column name is not unique'
            raise DuplicateHostname
            
        path = os.path.join(reposPath, hostname)
        util.mkdirChain(reposPath)

        repos = EmptyNetworkRepositoryServer(path, None, None, None, {})
        repos.auth.addUser(username, password)
        repos.auth.addAcl(username, None, None, True, False, True)

        self.db.commit()
        return cu.lastrowid
