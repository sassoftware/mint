#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import conary
import re
import sqlite3
import sys

import projects
import repos
import users
import database

# exceptions
from mint_error import MintError
import repository.netrepos.netauth

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'www', 'web']

class PermissionDenied(MintError):
    def __str__(self):
        return "permission denied"

def requiresAuth(func):
    def wrapper(self, *args):
        if not self.auth.authorized:
            raise PermissionDenied
        else:
            return func(self, *args)
    return wrapper

class MintServer(object):
    def callWrapper(self, methodName, authToken, args):
        if methodName.startswith('_'):
            raise AttributeError
        try:
            # try and get the method to see if it exists
            method = self.__getattribute__(methodName)

            # check authorization
            authTuple= self.users.checkAuth(authToken)
            self.authToken = authToken
            self.auth = users.Authorization(authorized = authTuple[0],
                                            userId = authTuple[1],
                                            username = authTuple[2])
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            r = method(*args)
        except users.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
        except projects.DuplicateProjectName, e:
            return (True, ("DuplicateItem", str(e)))
        except database.DuplicateItem, e:
            return (True, ("DuplicateHostname", str(e)))
        except database.ItemNotFound, e:
            return (True, ("ItemNotFound", str(e)))
#        except Exception, error:
#            exc_name = sys.exc_info()[0].__name__
#            return (True, (exc_name, error, ""))
        else:
            return (False, r)

    @requiresAuth
    def newProject(self, projectName, hostname, desc):
        if validHost.match(hostname) == None:
            raise repos.InvalidHostname
        if hostname in reservedHosts:
            raise repos.InvalidHostname
        hostname += "." + self.cfg.domainName
    
        projectId = self.projects.new(name = projectName, userId = self.auth.userId, desc = desc)
        reposId = self.repos.createRepos(projectId, hostname, self.cfg.reposPath,
                                         self.authToken[0], self.authToken[1])

        return (projectId, reposId)

    def getProject(self, id):
        return self.projects.get(id)

    def registerNewUser(self, username, password, fullName, email, active):
        return self.users.registerNewUser(username, password, fullName, email, active)

    def getProjectIdByHostname(self, hostname):
        return self.projects.getProjectIdByHostname(hostname)

    def checkAuth(self):
        return {'authorized': self.auth.authorized,
                'userId':     self.auth.userId,
                'username':   self.auth.username } 

    def __init__(self, cfg):
        self.cfg = cfg
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        
        self.projects = projects.ProjectsTable(self.db)
        self.repos = repos.ReposTable(self.db)
        self.users = users.UsersTable(self.db, self.cfg)
