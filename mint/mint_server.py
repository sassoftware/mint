#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import conary
import sqlite3
import sys

import projects
import repos
import users

# exceptions
from mint_error import MintError
import repository.netrepos.netauth

class MintServer(object):
    def callWrapper(self, methodName, authToken, args):
        if methodName.startswith('_'):
            raise AttributeError
        try:
            # try and get the method to see if it exists
            method = self.__getattribute__(methodName)

            # check authorization
            authTuple = self.users.checkAuth(authToken)
            self.authToken = authToken
            self.auth = users.Authorization(*authTuple)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            r = method(*args)
        except repository.netrepos.netauth.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
#        except Exception, error:
#            exc_name = sys.exc_info()[0].__name__
#            return (True, (exc_name, error, ""))
        else:
            return (False, r)

    def newProject(self, projectName, hostname, desc):
        projectId = self.projects.newProject(projectName, hostname, self.auth.userId, desc)
        reposId = self.repos.createRepos(projectId, hostname, self.cfg.reposPath,
                                         self.authToken[0], self.authToken[1])

        return (projectId, reposId)

    def checkAuth(self):
        return (self.auth.passwordOK, self.auth.userId)

    def __init__(self, cfg):
        self.cfg = cfg
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        
        self.projects = projects.ProjectsTable(self.db)
        self.repos = repos.ReposTable(self.db)
        self.users = users.UsersTable(self.db, self.cfg)
