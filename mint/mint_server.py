#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import re
import sqlite3
import sys
import time

import projects
import users
import database
import userlevels
from mint_error import MintError

import repository.netrepos.netauth
from repository import netclient

from imagetool import imagetool

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
    _checkRepo = True
    def callWrapper(self, methodName, authToken, args):
        if methodName.startswith('_'):
            raise AttributeError
        try:
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            # check authorization
            auth = self.users.checkAuth(authToken, checkRepo = self._checkRepo)
            self.authToken = authToken
            self.auth = users.Authorization(**auth)
            if self.auth.authorized:
                self._checkRepo = False

            r = method(*args)
        except users.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
        except database.DuplicateItem, e:
            return (True, ("DuplicateItem", e.item))
        except database.ItemNotFound, e:
            return (True, ("ItemNotFound", e.item))
#        except Exception, error:
#            exc_name = sys.exc_info()[0].__name__
#            return (True, (exc_name, error, ""))
        else:
            return (False, r)

    def _getAuthRepo(self, project):
        authUrl = "http://%s:%s@%s/conary/" % (self.cfg.authUser, self.cfg.authPass,
                                               project.getHostname())
        authLabel = project.getLabel()

        authRepo = {authLabel: authUrl}
        repo = netclient.NetworkRepositoryClient(authRepo)
        return repo

    # project methods
    @requiresAuth
    def newProject(self, projectName, hostname, desc):
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in reservedHosts:
            raise projects.InvalidHostname
        hostname += "." + self.cfg.domainName

        # XXX this set of operations should be atomic if possible
        imagetoolUrl = self.cfg.imagetoolUrl % (self.authToken[0], self.authToken[1])
        itclient = imagetool.ImageToolClient(imagetoolUrl)
        itProject = itclient.newProject(projectName)
        itProject.addLabel(hostname + "@rpl:devel",
            "http://%s/conary/" % hostname, self.authToken[0], self.authToken[1])

        projectId = self.projects.new(name = projectName,
                                      creatorId = self.auth.userId,
                                      desc = desc,
                                      hostname = hostname,
                                      defaultBranch = "rpl:devel",
                                      itProjectId = itProject.getId(),
                                      timeModified = time.time(),
                                      timeCreated = time.time())
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

    def getProjectIdsByMember(self, userId):
        return self.projects.getProjectIdsByMember(userId)

    def getProjectUsers(self, id):
        return self.projectUsers.getProjectUsers(id)

    @requiresAuth
    def addMember(self, projectId, userId, username, level):
        assert(level in userlevels.LEVELS)
        project = projects.Project(self, projectId)

        cu = self.db.cursor()
        if username and not userId:
            cu.execute("SELECT userId FROM Users WHERE username=?",
                       username)
            try:
                userId = cu.next()[0]
            except StopIteration:
                raise database.ItemNotFound("user")

        self.projectUsers.new(projectId, userId, level)
        repos = self._getAuthRepo(project)
        repos.addUser(project.getLabel(), username, password)
        repos.addAcl(project.getLabel(), username, None, None, True, False, level == userlevels.OWNER)

        return True

    @requiresAuth
    def delMember(self, projectId, userId):
        return self.projectUsers.delete(projectId, userId)
        # XXX Need to delete the user from the repository

    @requiresAuth
    def setProjectDesc(self, projectId, desc):
        return self.projects.update(projectId, desc = desc)

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

    def getProjectsByUser(self, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT hostname, name, level FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=?
                      ORDER BY level, name""", userId)

        rows = []
        for r in cu.fetchall():
            rows.append([r[0], r[1], r[2]])
        return rows

    def registerNewUser(self, username, password, fullName, email, active):
        return self.users.registerNewUser(username, password, fullName, email, active)

    def checkAuth(self):
        return self.auth.getDict()

    @requiresAuth
    def setUserEmail(self, userId, email):
        return self.users.update(userId, email = email)

    @requiresAuth
    def setUserDisplayEmail(self, userId, displayEmail):
        return self.users.update(userId, displayEmail = displayEmail)

    @requiresAuth
    def setUserBlurb(self, userId, blurb):
        return self.users.update(userId, blurb = blurb)

    def confirmUser(self, confirmation):
        userId = self.users.confirm(confirmation)
        return userId

    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

    @requiresAuth
    def setPassword(self, userId, newPassword):
        username = self.users.get(userId)['username']

        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepo)
        authLabel = self.cfg.authRepo.keys()[0]
        authRepo.changePassword(authLabel, username, newPassword)

        for projectId in self.getProjectIdsByMember(userId):
            project = projects.Project(self, projectId)

            authRepo = self._getAuthRepo(project)
            authRepo.changePassword(project.getLabel(), username, newPassword)

        return True

    @requiresAuth
    def searchUsers(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param offset: Count at which to begin listing
        @param count:  Number of items to return
        @return:       dictionary of Items requested
        """
        return self.users.search(terms, limit, offset)

    @requiresAuth
    def searchProjects(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param offset: Count at which to begin listing
        @param count:  Number of items to return
        @return:       dictionary of Items requested
        """
        return self.projects.search(terms, limit, offset)



    def __init__(self, cfg):
        self.cfg = cfg
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)

        self.projects = projects.ProjectsTable(self.db, self.cfg)
        self.users = users.UsersTable(self.db, self.cfg)
        self.projectUsers = users.ProjectUsersTable(self.db)
