#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import re
import sqlite3
import sys

import projects
import users
import database
import userlevels

# exceptions
from mint_error import MintError
import repository.netrepos.netauth

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'www', 'web',
                 'rpath', 'wiki', 'conary']

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
            auth = self.users.checkAuth(authToken)
            self.authToken = authToken
            self.auth = users.Authorization(**auth)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            r = method(*args)
        except users.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
        except database.DuplicateItem, e:
            return (True, ("DuplicateItem", str(e)))
        except database.ItemNotFound, e:
            return (True, ("ItemNotFound", e.item))
#        except Exception, error:
#            exc_name = sys.exc_info()[0].__name__
#            return (True, (exc_name, error, ""))
        else:
            return (False, r)

    # project methods
    @requiresAuth
    def newProject(self, projectName, hostname, desc):
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in reservedHosts:
            raise projects.InvalidHostname
        hostname += "." + self.cfg.domainName
    
        projectId = self.projects.new(name = projectName, 
                                      ownerId = self.auth.userId,
                                      desc = desc,
                                      hostname = hostname,
                                      defaultBranch = "rpl:devel")
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)
        self.projects.createRepos(self.cfg.reposPath, hostname,
                                  self.authToken[0], self.authToken[1])
        

        return projectId

    def getProject(self, id):
        return self.projects.get(id)

    def getProjectIdByHostname(self, hostname):
        return self.projects.getProjectIdByHostname(hostname)

    def getProjectUsers(self, id):
        return self.projectUsers.getProjectUsers(id)

    @requiresAuth
    def addMember(self, projectId, userId, username, level):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()
        
        # XXX check for dups here
        if username and not userId:
            cu.execute("SELECT userId FROM Users WHERE username=?",
                       username)
            try:
                userId = cu.next()[0]
            except StopIteration:
                raise database.ItemNotFound("user")

        return self.projectUsers.new(projectId, userId, level)

    @requiresAuth
    def delMember(self, projectId, userId):
        return self.projectUsers.delete(projectId, userId)    

    # user methods
    def getUser(self, id):
        return self.users.get(id)

    def getUserLevel(self, userId, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT level FROM ProjectUsers WHERE userId=? and projectId=?",
                   userId, projectId)
        try:
            l = cu.next()[0]
            return l
        except StopIteration:
            raise database.ItemNotFound("membership")

    def registerNewUser(self, username, password, fullName, email, active):
        return self.users.registerNewUser(username, password, fullName, email, active)
       
    def checkAuth(self):
        return self.auth.__dict__

    def __init__(self, cfg):
        self.cfg = cfg
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        
        self.projects = projects.ProjectsTable(self.db)
        self.users = users.UsersTable(self.db, self.cfg)
        self.projectUsers = users.ProjectUsersTable(self.db)
