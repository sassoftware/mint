#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import os
import re
import sys

import conary
from lib import util
from server.server import ResetableNetworkRepositoryServer

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')

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
                    hostname        STR
                );""")
                
    def createRepos(self, projectId, hostname, reposPath, username, password):
        assert(validHost.match(hostname) != None)
        cu = self.db.cursor()

        cu.execute("""INSERT INTO Repos VALUES (NULL, ?, ?)""",
            projectId, hostname)

        path = os.path.join(reposPath, hostname)
        util.mkdirChain(reposPath)

        repos = ResetableNetworkRepositoryServer(path, None, None, None, {})
        repos.auth.addUser(username, password)
        repos.auth.addAcl(username, None, None, True, False, True)

        self.db.commit()
        return cu.lastrowid
