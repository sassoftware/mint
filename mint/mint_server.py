#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import re
import sqlite3
import sys
import os
import time
import string
from urlparse import urlparse

import database
import hmac
import jobs
import jobstatus
import news
import pkgindex
import projects
import requests
import releases
import sessiondb
import versions
import users
import userlevels
import dbversion
import stats
import releasedata
import grouptrove
from cache import TroveNamesCache
from mint_error import PermissionDenied, ReleasePublished, ReleaseMissing, MintError
from searcher import SearchTermsError

from repository import netclient
from repository import shimclient
from repository.netrepos import netserver

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

allTroveNames = TroveNamesCache()
dbConnection = None
authDbConnection = None

class ParameterError(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "A required Parameter had an incorrect type"):
        self.reason = reason

def deriveBaseFunc(func):
    r = func
    done = 0
    while not done:
        try:
            r = r.__wrapped_func__
        except AttributeError:
            done = 1
    return r

def requiresAdmin(func):
    def wrapper(self, *args):
        if self.authToken == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return func(self, *args)
        else:
            raise PermissionDenied
    wrapper.__wrapped_func__ = func
    return wrapper

def requiresAuth(func):
    def wrapper(self, *args):
        if not self.auth.authorized:
            raise PermissionDenied
        else:
            return func(self, *args)
    wrapper.__wrapped_func__ = func
    return wrapper

def private(func):
    """Mark a method as callable only if self._allowPrivate is set
    to mask out functions not callable via XMLRPC over the web."""
    def wrapper(self, *args):
        if self._allowPrivate:
            return func(self, *args)
        else:
            raise PermissionDenied
    trueFunc = deriveBaseFunc(func)
    trueFunc.__private_enforced__ = True
    wrapper.__wrapped_func__ = func
    return wrapper

# recursively type check a parameter list. allows one to type check nested
# containers if need be. returns true if param should be allowed through.
# Due to it's recursive nature, the behavior of this function is quite
# different from a simple isinstance call.
def checkParam(param, paramType):
    if type(paramType) == tuple:
        if len(paramType) == 1:
            # paramType[0] is a tuple of possible values
            match = False
            for p_type in paramType[0]:
                if type(p_type) is tuple:
                    match = match or checkParam(param, p_type)
                else:
                    match = match or (type(param) == p_type)
            return match
        else:
            # paramType[0] is the type of the container.
            # paramType[1] is the type of item the container contains.
            if type(param) != paramType[0]:
                return False
            for item in param:
                # remember to type check the value of a dict, not the key
                if isinstance(param, dict):
                    if not checkParam(param[item], paramType[1]):
                        return False
                else:
                    if not checkParam(item, paramType[1]):
                        return False
            return True
    else:
        # the paramType IS the type
        return type(param) == paramType

def typeCheck(*paramTypes):
    """This decorator will be required on all functions callable over xmlrpc.
    This will force consistent calling conventions or explicit typecasting
    for all xmlrpc calls made to ensure extraneous calls won't be allowed."""
    def deco(func):
        def wrapper(self, *args):
            # FIXME: enable this test in production mode once we are certain
            # that the web api honors all typeCheck conventions
            if not self.cfg.debugMode:
                return func(self, *args)
            for i in range(len(args)):
                if (not checkParam(args[i],paramTypes[i])):
                    baseFunc = deriveBaseFunc(func)
                    raise ParameterError('%s was passed %s of type %s when expecting %s for parameter number %d' %(baseFunc.__name__, repr(args[i]), str(type(args[i])), str(paramTypes[i]), i+1))
            return func(self, *args)
        trueFunc = deriveBaseFunc(func)
        trueFunc.__args_enforced__ = True
        wrapper.__wrapped_func__ = func
        return wrapper
    return deco

tables = {}
def getTables(db, cfg):
    d = {}
    d['version'] = dbversion.VersionTable(db)
    d['labels'] = projects.LabelsTable(db)
    d['projects'] = projects.ProjectsTable(db, cfg)
    d['jobs'] = jobs.JobsTable(db)
    d['images'] = jobs.ImageFilesTable(db)
    d['users'] = users.UsersTable(db, cfg)
    d['projectUsers'] = users.ProjectUsersTable(db)
    d['releases'] = releases.ReleasesTable(db)
    d['pkgIndex'] = pkgindex.PackageIndexTable(db)
    d['newsCache'] = news.NewsCacheTable(db, cfg)
    d['sessions'] = sessiondb.SessionsTable(db)
    d['membershipRequests'] = requests.MembershipRequestTable(db)
    d['commits'] = stats.CommitsTable(db)
    d['releaseData'] = releasedata.ReleaseDataTable(db)
    d['groupTroves'] = grouptrove.GroupTroveTable(db)
    d['groupTroveItems'] = grouptrove.GroupTroveItemsTable(db)
    return d

class MintServer(object):
    _checkRepo = True 
    _cachedGroups = []

    def callWrapper(self, methodName, authToken, args):
        try:
            if methodName.startswith('_'):
                raise AttributeError
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            startTime = time.time()
            # check authorization

            # grab authToken from a session id if passed a session id
            # the session id from the client is a hmac-signed string
            # containing the actual session id.
            if type(authToken) == str:
                if len(authToken) == 64: # signed cookie
                    sig, val = authToken[:32], authToken[32:]
                
                    mac = hmac.new(self.cfg.cookieSecretKey, 'pysid')
                    mac.update(val)
                    if mac.hexdigest() != sig:
                        raise PermissionDenied

                    sid = val
                elif len(authToken) == 32: # unsigned cookie
                    sid = authToken
                else:
                    raise PermissionDenied

                d = self.sessions.load(sid)
                authToken = d['_data']['authToken']
            
            auth = self.users.checkAuth(authToken,
                checkRepo = self._checkRepo,
                cachedGroups = self._cachedGroups)
            self.authToken = authToken
            self.auth = users.Authorization(**auth)
            self._cachedGroups = self.auth.groups
            
            if self.auth.authorized:
                self._checkRepo = False

            r = method(*args)
            if self.cfg.profiling:
                print >> sys.stderr, "Ending XMLRPC request:\t\t%-25s\t%.2f" % (methodName, (time.time() - startTime) * 1000)
                sys.stderr.flush()
        except users.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
        except database.DuplicateItem, e:
            return (True, ("DuplicateItem", e.item))
        except database.ItemNotFound, e:
            return (True, ("ItemNotFound", e.item))
        except SearchTermsError, e:
            return (True, ("SearchTermsError", str(e)))
        except users.AuthRepoError, e:
            return (True, ("AuthRepoError", str(e)))
        #except Exception, error:
        #    exc_name = sys.exc_info()[0].__name__
        #    return (True, (exc_name, error, str(error)))
        else:
            return (False, r)

    def _getAuthRepo(self):
        authRepoPath = os.path.dirname(self.cfg.authDbPath)
        server = netserver.NetworkRepositoryServer(authRepoPath,
            os.path.join(authRepoPath, "tmp"), '', self.cfg.authRepoMap.keys()[0],
            self.cfg.authRepoMap)

        repoUrl = urlparse(self.cfg.authRepoMap.values()[0])
        # too bad urlparse doesn't split foo:bar@foo.com:80
        if "@" in repoUrl[1]:
            host = repoUrl[1].split("@")
        else:
            host = repoUrl
        if ":" in host[0]:
            port = host[1].split(":")
        else:
            port = 80
    
        repo = shimclient.ShimNetClient(
            server, repoUrl[0], port,
            (self.cfg.authUser, self.cfg.authPass),
            self.cfg.authRepoMap)
        return repo

    def _getProjectRepo(self, project):
        # use a shimclient for mint-handled repositories; netclient if not
        if project.external:
            cfg = project.getConaryConfig()
            repo = netclient.NetworkRepositoryClient(cfg.repositoryMap)
        else:
            if self.cfg.SSL:
                protocol = "https"
                port = 443
            else:
                protocol = "http"
                port = 80

            authUrl = "%s://%s:%s@%s/repos/%s/" % (protocol, self.cfg.authUser, self.cfg.authPass,
                                                   self.cfg.projectSiteHost, project.getHostname())
            authLabel = project.getLabel()
            authRepo = {versions.Label(authLabel).getHost(): authUrl}

            reposPath = os.path.join(self.cfg.reposPath, project.getFQDN())
            tmpPath = os.path.join(reposPath, "tmp")
            
            # handle non-standard ports specified on cfg.projectDomainName,
            # most likely just used by the test suite
            if ":" in self.cfg.projectDomainName:
                port = int(self.cfg.projectDomainName.split(":")[1])
     
            server = netserver.NetworkRepositoryServer(reposPath, tmpPath, '', project.getFQDN(), authRepo)
            repo = shimclient.ShimNetClient(server, protocol, port, (self.cfg.authUser, self.cfg.authPass), authRepo)
        return repo

    # unfortunately this function can't be a proper decorator because we
    # can't always know which param is the projectId.
    # We'll just call it at the begining of every function that needs it.
    def _filterProjectAccess(self, projectId):
        if self.auth.admin:
            return
        if self.projects.isDisabled(projectId):
            raise database.ItemNotFound()
        if not self.projects.isHidden(projectId):
            return
        members = self.projectUsers.getMembersByProjectId(projectId)
        for userId, username, level in members:
            if (userId == self.auth.userId) and (level in userlevels.WRITERS):
                return
        raise database.ItemNotFound()

    def _filterReleaseAccess(self, releaseId):
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM Releases WHERE releaseId = ?", releaseId)
        res = cu.fetchall()
        if len(res):
            self._filterProjectAccess(res[0][0])

    def _filterLabelAccess(self, labelId):
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM Labels WHERE labelId = ?", labelId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _filterJobAccess(self, jobId):
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM Jobs LEFT JOIN Releases ON Releases.releaseId = Jobs.releaseId WHERE jobId = ?", jobId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _filterImageFileAccess(self, fileId):
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM ImageFiles LEFT JOIN Releases ON Releases.releaseId = ImageFiles.releaseId WHERE fileId = ?", fileId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _requireProjectOwner(self, projectId):
        if self.auth.admin:
            return
        members = self.projectUsers.getMembersByProjectId(projectId)
        for userId, username, level in members:
            if (userId == self.auth.userId) and (level != userlevels.OWNER):
                raise PermissionDenied

    @typeCheck(str, str, str, str, str)
    # project methods
    @requiresAuth
    @private
    def newProject(self, projectName, hostname, domainname, projecturl, desc):
        if not hostname:
            raise projects.InvalidHostname
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in reservedHosts:
            raise projects.InvalidHostname
        fqdn = ".".join((hostname, domainname))
        if projecturl and not (projecturl.startswith('https://') or projecturl.startswith('http://')):
            projecturl = "http://" + projecturl

        # XXX this set of operations should be atomic if possible
        projectId = self.projects.new(name = projectName,
                                      creatorId = self.auth.userId,
                                      description = desc,
                                      hostname = hostname,
                                      domainname = domainname,
                                      projecturl = projecturl,
                                      timeModified = time.time(),
                                      timeCreated = time.time())
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)
        
        project = projects.Project(self, projectId)
        
        
        project.addLabel(fqdn + "@%s" % self.cfg.defaultBranch,
            "http://%s%srepos/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname),
            self.cfg.authUser, self.cfg.authPass)

        self.projects.createRepos(self.cfg.reposPath, self.cfg.reposContentsPath,
                                  hostname, domainname, self.authToken[0],
                                  self.authToken[1])

        return projectId

    @typeCheck(int)
    @private
    def getProject(self, id):
        self._filterProjectAccess(id)
        return self.projects.get(id)

    @typeCheck(str)
    @private
    def getProjectIdByFQDN(self, fqdn):
        projectId = self.projects.getProjectIdByFQDN(fqdn)
        self._filterProjectAccess(projectId)
        return projectId

    @typeCheck(str)
    @private
    def getProjectIdByHostname(self, hostname):
        projectId = self.projects.getProjectIdByHostname(hostname)
        self._filterProjectAccess(projectId)
        return projectId

    @typeCheck(int)
    @private
    def getProjectIdsByMember(self, userId):
        filter = (self.auth.userId != userId) or (self.auth.admin)
        return self.projects.getProjectIdsByMember(userId, filter)

    @typeCheck(int)
    @private
    def getMembersByProjectId(self, id):
        self._filterProjectAccess(id)
        return self.projectUsers.getMembersByProjectId(id)

    @typeCheck(int, int)
    @private
    def userHasRequested(self, projectId, userId):
        self._filterProjectAccess(projectId)
        return self.membershipRequests.userHasRequested(projectId, userId)

    @typeCheck(int, int)
    @private
    @requiresAuth
    def deleteJoinRequest(self, projectId, userId):
        self._filterProjectAccess(projectId)
        return self.membershipRequests.deleteRequest(projectId, userId)

    @typeCheck(int)
    @private
    @requiresAuth
    def listJoinRequests(self, projectId):
        self._filterProjectAccess(projectId)
        reqList = self.membershipRequests.listRequests(projectId)
        return [ (x, self.users.getUsername(x)) for x in reqList]

    @typeCheck(int, str)
    @private
    @requiresAuth
    def setJoinReqComments(self, projectId, comments):
        self._filterProjectAccess(projectId)
        # only add if user is already a member of project
        userId = self.auth.userId
        memberList = self.getMembersByProjectId(projectId)
        if userId in [x[0] for x in memberList]:
            # in other words, filter emails for alterations to a join request
            if (userId, userlevels.USER) not in [(x[0], x[2]) for x in memberList]:
                return
        if self.cfg.sendNotificationEmails and \
               not self.membershipRequests.userHasRequested(projectId, userId):
            projectName = self.getProject(projectId)['hostname']
            owners = self.projectUsers.getOwnersByProjectName(projectName)
            for name, email in owners:
                subject = "Project Membership Request"
                message = "A user of %s would like to join a project you own.\n\n" %self.cfg.productName
                message += "Project: %s\n" %self.getProject(projectId)['name']
                message += "Username: %s\n\n" %self.users.getUsername(userId)
                if comments:
                    message += "Comments:\n%s" %comments
                else:
                    message += "No comments were supplied"
                message += "\n\nTo respond to this request:\n\n"
                message += "  o Login to %s\n\n" % self.cfg.productName
                message += "  o Click on the 'Requests Pending' link under the 'My Projects' sidebar\n"
                message += "    (Note: This link will not be present if the user retracted their request or another project owner has already responded to it.)\n\n"
                message += "  o You can find all outstanding requests under the 'Requestors' heading at the bottom of the page\n"
                users.sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, email, subject, message)
        return self.membershipRequests.setComments(projectId, userId, comments)

    @typeCheck(int, int)
    @private
    @requiresAuth
    def getJoinReqComments(self, projectId, userId):
        self._filterProjectAccess(projectId)
        return self.membershipRequests.getComments(projectId, userId)

    @typeCheck(str)
    @requiresAdmin
    @private
    def getOwnersByProjectName(self, name):
        return self.projectUsers.getOwnersByProjectName(name)

    @typeCheck(int, ((int, type(None)),), ((str, type(None)),), int)
    @requiresAuth
    @private
    def addMember(self, projectId, userId, username, level):
        self._filterProjectAccess(projectId)
        assert(level in userlevels.LEVELS)

        project = projects.Project(self, projectId)

        cu = self.db.cursor()
        if username and not userId:
            cu.execute("SELECT userId FROM Users WHERE username=? AND active=1", username)
            r = cu.fetchone()
            if not r:
                raise database.ItemNotFound("username")
            else:
                userId = r[0]
        elif userId and not username:
            cu.execute("SELECT username FROM Users WHERE userId=? AND active=1", userId)
            r = cu.fetchone()
            if not r:
                raise database.ItemNotFound("userId")
            else:
                username = r[0]

        if (self.auth.userId != userId) and level == userlevels.USER:
            raise users.UserInduction()

        self.membershipRequests.deleteRequest(projectId, userId)
        try:
            self.projectUsers.new(projectId, userId, level)
        except database.DuplicateItem:
            project.updateUserLevel(userId, level)
            return True

        if not project.external:
            acu = self.authDb.cursor()
            password = ''
            salt = ''
            query = "SELECT salt, password FROM Users WHERE user=?"
            acu.execute(query, username)
            try:
                salt, password = acu.fetchone()
            except TypeError:
                raise database.ItemNotFound("user")
            repos = self._getProjectRepo(project)
            repos.addUserByMD5(project.getLabel(), username, salt, password)
            repos.addAcl(project.getLabel(), username, None, None, level in userlevels.WRITERS, False, level == userlevels.OWNER)

        self._notifyUser('Added', self.getUser(userId), projects.Project(self,projectId), level)
        return True

    @typeCheck(int, int)
    @private
    def lastOwner(self, projectId, userId):
        self._filterProjectAccess(projectId)
        return self.projectUsers.lastOwner(projectId, userId)

    @typeCheck(int, int)
    @private
    def onlyOwner(self, projectId, userId):
        self._filterProjectAccess(projectId)
        return self.projectUsers.onlyOwner(projectId, userId)

    @typeCheck(int, int, bool)
    @requiresAuth
    @private
    def delMember(self, projectId, userId, notify=True):
        self._filterProjectAccess(projectId)
        #XXX Make this atomic
        try:
            userLevel = self.getUserLevel(userId, projectId)
        except database.ItemNotFound:
            raise netclient.UserNotFound()
        if (self.auth.userId != userId) and userLevel == userlevels.USER:
            raise users.UserInduction()

        project = projects.Project(self, projectId)
        self.projectUsers.delete(projectId, userId)
        repos = self._getProjectRepo(project)
        user = self.getUser(userId)

        if not project.external:
            repos.deleteUserByName(project.getLabel(), user['username'])
        if notify:
            self._notifyUser('Removed', user, project)

    def _notifyUser(self, action, user, project, userlevel=None):
        if self.auth.userId == user['userId']:
            return
        userlevelname = ((userlevel >=0) and userlevels.names[userlevel] or 'Unknown')
        actionText = {'Removed': "has been removed from the following project:",
            'Added': "has been added to the following project as %s:" % userlevelname,
            'Changed': "has had its current access level changed to %s on the following project:" % \
                userlevelname
        }
        greeting = "Hello,"
        message = "Your %s account: %s\n" % (self.cfg.productName, user['username'])
        message += actionText[action]
        message += "\n%s\n" % project.getName()
        closing = 'Please contact the project owner(s) with any questions.'

        if self.cfg.sendNotificationEmails:
            users.sendMail(self.cfg.adminMail, self.cfg.productName,
                        user['email'],
                        "%s user account modification" % self.cfg.productName,
                        '\n\n'.join((greeting, message, closing)))

    @typeCheck(str, str)
    @requiresAdmin
    @private
    def notifyUsers(self, subject, body):
        """
        Send an e-mail message to all registered members.
        XXX Should we store these notifications somehow?
        """
        #First get a list of the users
        userlist = self.users.getUsersWithEmail()
        for user in userlist:
            #Figure out the user's full name and e-mail address
            email = "%s<%s>" % (user[1], user[2])
            # XXX Do we want to do some substitution in the subject/body?
            try:
                users.sendMailWithChecks(self.cfg.adminMail, self.cfg.productName,
                        email, subject, body)
            except users.MailError, e:
                # Invalidate the user, so he/she must change his/her address at the next login
                self.users.invalidateUser(user[0])

    @typeCheck(int, str, str, str)
    @requiresAuth
    @private
    def editProject(self, projectId, projecturl, desc, name):
        if projecturl and not (projecturl.startswith('https://') or projecturl.startswith('http://')):
            projecturl = "http://" + projecturl
        self._filterProjectAccess(projectId)
        return self.projects.update(projectId, projecturl=projecturl, description = desc, name = name)

    @typeCheck(int)
    @requiresAdmin
    @private
    def hideProject(self, projectId):
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        repos.deleteUserByName(project.getLabel(), 'anonymous')

        return self.projects.hide(projectId)

    @typeCheck(int)
    @requiresAdmin
    @private
    def unhideProject(self, projectId):
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        userId = repos.addUser(project.getLabel(), 'anonymous', 'anonymous')
        repos.addAcl(project.getLabel(), 'anonymous', None, None, False, False, False)

        return self.projects.unhide(projectId)

    @typeCheck(int)
    @requiresAdmin
    @private
    def disableProject(self, projectId):
        return self.projects.disable(projectId, self.cfg.reposPath)

    @typeCheck(int)
    @requiresAdmin
    @private
    def enableProject(self, projectId):
        return self.projects.enable(projectId, self.cfg.reposPath)

    # user methods
    @typeCheck(int)
    @private
    def getUser(self, id):
        return self.users.get(id)

    @typeCheck(int, int)
    @private
    def getUserLevel(self, userId, projectId):
        self._filterProjectAccess(projectId)
        cu = self.db.cursor()
        cu.execute("SELECT level FROM ProjectUsers WHERE userId=? and projectId=?",
                   userId, projectId)

        r = cu.fetchone()
        if not r:
            raise database.ItemNotFound("membership")
        else:
            return r[0]

    @typeCheck(int, int, int)
    @requiresAuth
    @private
    def setUserLevel(self, userId, projectId, level):
        self._filterProjectAccess(projectId)
        if (self.auth.userId != userId) and (level == userlevels.USER):
            raise users.UserInduction()
        if self.projectUsers.onlyOwner(projectId, userId) and (level != userlevels.OWNER):
            raise users.LastOwner()
        #update the level on the project
        project = projects.Project(self, projectId)
        user = self.getUser(userId)
        if not project.external:
            repos = self._getProjectRepo(project)
            repos.editAcl(project.getLabel(), user['username'], "ALL", None, None, None, level in userlevels.WRITERS, False, level == userlevels.OWNER)

        #Ok, now update the mint db
        if level in userlevels.WRITERS:
            self.deleteJoinRequest(projectId, userId)
        cu = self.db.cursor()
        cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and 
            projectId=?""", level, userId, projectId)

        self.db.commit()
        self._notifyUser('Changed', user, project, level)

    @typeCheck(int)
    @private
    def getProjectsByUser(self, userId):
        cu = self.db.cursor()
       
        fqdnConcat = database.concat(self.db, "hostname", "'.'", "domainname")
        cu.execute("""SELECT %s, name, level
                      FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=? AND Projects.disabled=0
                      ORDER BY level, name""" % fqdnConcat, userId)

        rows = []
        for r in cu.fetchall():
            rows.append([r[0], r[1], r[2]])
        return rows

    @typeCheck(str, str, str, str, str, str, bool)
    @private
    def registerNewUser(self, username, password, fullName, email, displayEmail, blurb, active):
        return self.users.registerNewUser(username, password, fullName, email, displayEmail, blurb, active)

    @typeCheck()
    @private
    def checkAuth(self):
        return self.auth.getDict()
        
    @typeCheck(int)
    @requiresAuth
    @private
    def updateAccessedTime(self, userId):
        return self.users.update(userId, timeAccessed = time.time())

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setUserEmail(self, userId, email):
        return self.users.update(userId, email = email)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def validateNewEmail(self, userId, email):
        return self.users.validateNewEmail(userId, email)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setUserDisplayEmail(self, userId, displayEmail):
        return self.users.update(userId, displayEmail = displayEmail)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setUserBlurb(self, userId, blurb):
        return self.users.update(userId, blurb = blurb)

    @typeCheck(int, str, str)
    @requiresAuth
    @private
    def addUserKey(self, projectId, username, keydata):
        self._filterProjectAccess(projectId)
        #find the project repository
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)

        #Call the repository's addKey function
        return repos.addNewAsciiPGPKey(project.getLabel(), username, keydata)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setUserFullName(self, userId, fullName):
        return self.users.update(userId, fullName = fullName)

    @typeCheck(int)
    @requiresAuth
    @private
    def cancelUserAccount(self, userId):
        """ Checks to see if the the user to be deleted is leaving in a lurch developers of projects that would be left ownerless.  Then deletes the user.
        """
        if (self.auth.userId != userId) and (not self.auth.admin):
            raise PermissionDenied()
        cu = self.db.cursor()
        username = self.users.getUsername(userId)

        # Find all projects of which userId is an owner, has no other owners, and/or
        # has developers.
        cu.execute("""SELECT MAX(D.flagged)
                        FROM (SELECT A.projectId,
                               COUNT(B.userId)*not(COUNT(C.userId)) AS flagged
                                 FROM ProjectUsers AS A
                                   LEFT JOIN ProjectUsers AS B ON A.projectId=B.projectId AND B.level=1
                                   LEFT JOIN ProjectUsers AS C ON C.projectId=A.projectId AND
                                                                  C.level = 0 AND
                                                                  C.userId <> A.userId AND
                                                                  A.level = 0
                                       WHERE A.userId=? GROUP BY A.projectId) AS D
                   """, userId)

        r = cu.fetchone()
        if r and r[0]:
            raise users.LastOwner

        self.membershipRequests.userAccountCanceled(userId)

        return self.removeUserAccount(userId)

    @typeCheck(int)
    @requiresAuth
    @private
    def removeUserAccount(self, userId):
        """Removes the user account from the authrepo and mint databases.
        Also removes the user from each project listed in projects.
        """
        if not self.auth.admin and userId != self.auth.userId:
            raise PermissionDenied
        repoLabel = self.cfg.authRepoMap.keys()[0]
        username = self.users.getUsername(userId)
        cu = self.db.cursor()
        authRepo = self._getAuthRepo()

        #Handle projects
        projectList = self.getProjectIdsByMember(userId)
        for (projectId, level) in projectList:
            self.delMember(projectId, userId, False)

        authRepo.deleteUserByName(repoLabel, username)

        cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?", userId)
        cu.execute("UPDATE Jobs SET userId=NULL WHERE userId=?", userId)
        cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        cu.execute("DELETE FROM Users WHERE userId=?", userId)

        self.db.commit()

    @typeCheck(str)
    @private
    def confirmUser(self, confirmation):
        userId = self.users.confirm(confirmation)
        return userId

    @typeCheck(str)
    @private
    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

    @typeCheck(int, str)
    @private
    def setPassword(self, userId, newPassword):
        username = self.users.get(userId)['username']

        for projectId, level in self.getProjectIdsByMember(userId):
            project = projects.Project(self, projectId)

            authRepo = self._getProjectRepo(project)
            authRepo.changePassword(project.getLabel(), username, newPassword)

        authRepo = self._getAuthRepo()
        authLabel = self.cfg.authRepoMap.keys()[0]
        authRepo.changePassword(authLabel, username, newPassword)

        return True

    @typeCheck(str, int, int)
    @requiresAuth
    @private
    def searchUsers(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.users.search(terms, limit, offset)

    @typeCheck(str, int, int, int)
    @private
    def searchProjects(self, terms, modified, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param modified: Code for the lastModified filter
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.projects.search(terms, modified, limit, offset)

    @typeCheck(str, int, int)
    @private
    def searchPackages(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.pkgIndex.search(terms, limit, offset)

    @typeCheck()
    @private
    def getProjectsList(self):
        """
        Collect a list of all projects suitable for creating a select box
        """
        return self.projects.getProjectsList()

    @typeCheck(int, int, int)
    @private
    def getProjects(self, sortOrder, limit, offset):
        """
        Collect a list of projects
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        return self.projects.getProjects(sortOrder, limit, offset), self.projects.getNumProjects()

    @typeCheck()
    @requiresAdmin
    @private
    def getUsersList(self):
        """
        Collect a list of users suitable for creating a select box
        """
        return self.users.getUsersList()

    @typeCheck(int, int, int)
    @requiresAdmin
    @private
    def getUsers(self, sortOrder, limit, offset):
        """
        Collect a list of users
        @param sortOrder: Order the users by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        return self.users.getUsers(sortOrder, limit, offset), self.users.getNumUsers()

    @typeCheck()
    @private
    def getNews(self):
        return self.newsCache.getNews()

    @typeCheck()
    @private
    def getNewsLink(self):
        return self.newsCache.getNewsLink()

    #
    # LABEL STUFF
    #
    @typeCheck(int)
    @private
    def getDefaultProjectLabel(self, projectId):
        self._filterProjectAccess(projectId)
        return self.labels.getDefaultProjectLabel(projectId)

    @typeCheck(int, ((str, type(None)),), ((str, type(None)),), ((bool, type(None)),))
    @private
    def getLabelsForProject(self, projectId, newUser, newPass, useSSL):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        self._filterProjectAccess(projectId)
        return self.labels.getLabelsForProject(projectId, useSSL, newUser, newPass)

    @typeCheck(int, str, str, str, str)
    @requiresAuth
    @private
    def addLabel(self, projectId, label, url, username, password):
        self._filterProjectAccess(projectId)
        return self.labels.addLabel(projectId, label, url, username, password)

    @typeCheck(int)
    @requiresAuth
    @private
    def getLabel(self, labelId):
        self._filterLabelAccess(labelId)
        return self.labels.getLabel(labelId)

    @typeCheck(int, str, str, str, str)
    @requiresAuth
    @private
    def editLabel(self, labelId, label, url, username, password):
        self._filterLabelAccess(labelId)
        return self.labels.editLabel(labelId, label, url, username, password)

    @typeCheck(int, int)
    @requiresAuth
    @private
    def removeLabel(self, projectId, labelId):
        self._filterProjectAccess(projectId)
        return self.labels.removeLabel(projectId, labelId)

    #
    # RELEASE STUFF
    #
    @typeCheck(int, bool)
    @private
    def getReleasesForProject(self, projectId, showUnpublished = False):
        self._filterProjectAccess(projectId)
        return [releases.Release(self, x) for x in self.releases.iterReleasesForProject(projectId, showUnpublished)]

    @typeCheck(int, int)
    @private
    def getReleaseList(self, limit, offset):
        cu = self.db.cursor()
        cu.execute("""SELECT Projects.name, Projects.hostname, releaseId 
                         FROM Releases LEFT JOIN Projects ON Projects.projectId = Releases.projectId 
                         WHERE Projects.hidden=0 AND Projects.disabled=0 and published=1 
                         ORDER BY timePublished DESC LIMIT ? OFFSET ?""", limit, offset)
        return [(x[0], x[1], releases.Release(self, x[2])) for x in cu.fetchall()]

    @typeCheck(str, str, str, str)
    @private
    def registerCommit(self, hostname, username, name, version):
        projectId = self.getProjectIdByFQDN(hostname)
        self._filterProjectAccess(projectId)
        try:
            userId = self.getUserIdByName(username)
        except database.ItemNotFound:
            userId = 0
        self.commits.new(projectId, time.time(), name, version, userId)
        return True

    @typeCheck(int)
    @private
    def getCommitsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.commits.getCommitsByProject(projectId)

    @typeCheck(int)
    @private
    def getRelease(self, releaseId):
        self._filterReleaseAccess(releaseId)
        return self.releases.get(releaseId)

    @typeCheck(int, str, bool)
    @requiresAuth
    @private
    def newRelease(self, projectId, releaseName, published):
        self._filterProjectAccess(projectId)
        return self.releases.new(projectId = projectId,
                                 name = releaseName,
                                 published = published)

    @typeCheck(int)
    @requiresAuth
    @private
    def deleteRelease(self, releaseId):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        return self.releases.deleteRelease(releaseId)

    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setReleaseDataValue(self, releaseId, name, value, dataType):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        return self.releaseData.setReleaseDataValue(releaseId, name, value, dataType)

    @typeCheck(int, str)
    @private
    def getReleaseDataValue(self, releaseId, name):
        self._filterReleaseAccess(releaseId)
        return self.releaseData.getReleaseDataValue(releaseId, name)

    @typeCheck(int)
    @private
    def getReleaseDataDict(self, releaseId):
        self._filterReleaseAccess(releaseId)
        return self.releaseData.getReleaseDataDict(releaseId)

    @typeCheck(int)
    @private
    def getReleaseTrove(self, releaseId):
        self._filterReleaseAccess(releaseId)
        return self.releases.getTrove(releaseId)

    @typeCheck(int, str, str, str)
    @requiresAuth
    @private
    def setReleaseTrove(self, releaseId, troveName, troveVersion, troveFlavor):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        return self.releases.setTrove(releaseId, troveName,
                                                 troveVersion,
                                                 troveFlavor)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setReleaseDesc(self, releaseId, desc):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET description=? WHERE releaseId=?",
                   desc, releaseId)
        self.db.commit()
        return True

    @typeCheck(int)
    @private
    def incReleaseDownloads(self, releaseId):
        self._filterReleaseAccess(releaseId)
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET downloads = downloads + 1 WHERE releaseId=?",
            releaseId)
        self.db.commit()
        return True

    @typeCheck(int, bool)
    @requiresAuth
    @private
    def setReleasePublished(self, releaseId, published):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        timeStamp = time.time()
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET published=?, timePublished=? WHERE releaseId=?",
            int(published), timeStamp, releaseId)
        self.db.commit()
        return True

    @typeCheck(int, int)
    @requiresAuth
    @private
    def setImageType(self, releaseId, imageType):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET imageType=? WHERE releaseId=?",
                   imageType, releaseId)
        self.db.commit()
        return True

    @typeCheck(int)
    @requiresAuth
    @private
    def startImageJob(self, releaseId):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        cu = self.db.cursor()

        cu.execute("SELECT jobId, status FROM Jobs WHERE releaseId=?",
                   releaseId)
        r = cu.fetchall()
        if len(r) == 0:
            cu.execute("INSERT INTO Jobs VALUES (NULL, ?, ?, ?, ?, ?, 0)",
                       releaseId, self.auth.userId, jobstatus.WAITING,
                       jobstatus.statusNames[jobstatus.WAITING],
                       time.time())
            if self.db.type == "native_sqlite":
                retval = cu.lastrowid
            else:
                retval = cu._cursor.lastrowid
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                cu.execute("""UPDATE Jobs SET status=?, statusMessage='Waiting',
                                              timeStarted=?, timeFinished=0
                              WHERE jobId=?""", jobstatus.WAITING, time.time(),
                                                jobId)
                retval = jobId

        self.db.commit()
        return retval

    @typeCheck(int)
    @requiresAuth
    @private
    def getJob(self, jobId):
        self._filterJobAccess(jobId)
        cu = self.db.cursor()

        cu.execute("SELECT userId, releaseId, status,"
                   "  statusMessage, timeStarted, "
                   "  timeFinished FROM Jobs "
                   " WHERE jobId=?", jobId)

        p = cu.fetchone()
        if not p:
            raise jobs.JobMissing

        dataKeys = ['userId', 'releaseId', 'status',
                    'statusMessage', 'timeStarted', 'timeFinished']
        data = {}
        for i, key in enumerate(dataKeys):
            data[key] = p[i]
        return data

    @typeCheck(int)
    @requiresAuth
    @private
    def getJobIds(self, releaseId):
        self._filterReleaseAccess(releaseId)
        cu = self.db.cursor()

        stmt = """SELECT jobId FROM Jobs"""
        if releaseId != -1:
            stmt += " WHERE releaseId=?"
            cu.execute(stmt, releaseId)
        else:
            cu.execute(stmt)

        p = cu.fetchall()
        rows = []
        for row in p:
            rows.append(row[0])
        return rows

    @typeCheck(int, int, str)
    @requiresAuth
    @private
    def setJobStatus(self, jobId, newStatus, statusMessage):
        self._filterJobAccess(jobId)
        cu = self.db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage=? WHERE jobId=?",
                   newStatus, statusMessage, jobId)
        if newStatus == jobstatus.FINISHED:
            cu.execute("UPDATE Jobs SET timeFinished=? WHERE jobId=?",
                       time.time(), jobId)
        self.db.commit()
        return True

    @typeCheck(int, (list, (tuple, str)))
    @requiresAuth
    @private
    def setImageFilenames(self, releaseId, filenames):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        cu = self.db.cursor()
        cu.execute("DELETE FROM ImageFiles WHERE releaseId=?", releaseId)
        for idx, file in enumerate(sorted(filenames)):
            fileName, title = file
            cu.execute("INSERT INTO ImageFiles VALUES (NULL, ?, ?, ?, ?)",
                       releaseId, idx, fileName, title)
        self.db.commit()
        return True

    @typeCheck(int)
    @private
    def getImageFilenames(self, releaseId):
        self._filterReleaseAccess(releaseId)
        cu = self.db.cursor()
        cu.execute("SELECT fileId, filename, title FROM ImageFiles WHERE releaseId=? ORDER BY idx", releaseId)

        results = cu.fetchall()
        if len(results) < 1:
            return []
        else:
            return [(x[0], os.path.basename(x[1]), x[2]) for x in results]
   
    @typeCheck(int)
    @private
    def getFileInfo(self, fileId):
        self._filterImageFileAccess(fileId)
        cu = self.db.cursor()
        cu.execute("SELECT releaseId, idx, filename, title FROM ImageFiles WHERE fileId=?", fileId)

        r = cu.fetchone()
        if r:
            return r[0], r[1], r[2], r[3]
        else:
            raise jobs.FileMissing

    @typeCheck(int)
    @requiresAuth
    def getGroupTroves(self, projectId):
        self._filterProjectAccess(projectId)
        # enable internal methods so that public methods can make 
        # private calls; this is safe because only one instance
        # of MintServer is instantiated per call.
        self._allowPrivate = True

        project = projects.Project(self, projectId)

        labelIdMap = project.getLabelIdMap()
        nc = self._getProjectRepo(project)

        troveDict = {}
        for label in labelIdMap.keys():
            troves = allTroveNames.getTroveNames(versions.Label(label), nc)
            troves = [x for x in troves if (x.startswith("group-") or\
                                            x.startswith("fileset-")) and\
                                            ":" not in x]
            troveDict[label] = troves
        return troveDict

    @typeCheck(int)
    @requiresAuth
    def getReleaseStatus(self, releaseId):
        self._filterReleaseAccess(releaseId)
        self._allowPrivate = True

        release = releases.Release(self, releaseId)
        job = release.getJob()

        if not job:
            return {'status': jobstatus.NOJOB,
                    'message': jobstatus.statusNames[jobstatus.NOJOB]}
        else:
            return {'status':  job.getStatus(),
                    'message': job.getStatusMessage()}

    # session management
    @private
    def loadSession(self, sid):
        return self.sessions.load(sid)

    @private
    def saveSession(self, sid, data):
        self.sessions.save(sid, data)

    @private
    def deleteSession(self, sid):
        self.sessions.delete(sid)

    @private
    def cleanupSessions(self):
        self.sessions.cleanup()

    # group trove specific functions
    @typeCheck(int)
    @private
    @requiresAuth
    def getRecipe(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)

        groupTrove = self.groupTroves.get(groupTroveId)
        groupTroveItems = self.groupTroveItems.listByGroupTroveId(groupTroveId)

        recipe = ""
        name = ''.join((string.capwords(' '.join(groupTrove['recipeName'].split('-')))).split(' '))
        indent = 4 * " "

        recipe += "class " + name + "(GroupRecipe):\n"
        recipe += indent + "name = '%s'\n" % groupTrove['recipeName']
        recipe += indent + "version = '%s'\n\n" % groupTrove['upstreamVersion']
        recipe += indent + "autoResolve = %s\n\n" % str(groupTrove['autoResolve'])
        recipe += indent + 'def setup(r):\n'

        indent = 8 * " "

        for trv in groupTroveItems:
            recipe += indent + "r.add('" + trv['trvName'] + "', '" + trv['trvVersion'] + "', '" + trv['trvFlavor'] + "', groupName = '" +trv['subGroup'] +"')\n"
        return recipe

    @private
    @requiresAuth
    @typeCheck(int, bool)
    def setGroupTroveAutoResolve(self, groupTroveId, resolve):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroves.setAutoResolve(groupTroveId, resolve)

    @private
    @requiresAuth
    @typeCheck(int)
    def listGroupTrovesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        return self.groupTroves.listGroupTrovesByProject(projectId)

    @private
    @typeCheck(int, str, str, str, bool)
    @requiresAuth
    def createGroupTrove(self, projectId, recipeName, upstreamVersion,
                         description, autoResolve):
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        creatorId = self.users.getIdByColumn("username", self.authToken[0])
        return self.groupTroves.createGroupTrove(projectId, creatorId,
                                                 recipeName, upstreamVersion,
                                                 description, autoResolve)

    @private
    @typeCheck(int)
    @requiresAuth
    def getGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        return self.groupTroves.get(groupTroveId)

    @private
    @typeCheck(int)
    @requiresAuth
    def deleteGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroves.delGroupTrove(groupTroveId)

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveDesc(self, groupTroveId, description):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroves.update(groupTroveId, description = description, timeModified = time.time())

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveUpstreamVersion(self, groupTroveId, vers):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroves.setUpstreamVersion(groupTroveId, vers)

    #group trove item specific functions

    @private
    @typeCheck(int)
    @requiresAuth
    def listGroupTroveItemsByGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        return self.groupTroveItems.listByGroupTroveId(groupTroveId)

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemVersionLocked(self, groupTroveItemId, locked):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroveItems.setVersionLocked(groupTroveItemId, locked)

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemUseLocked(self, groupTroveItemId, locked):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroveItems.setUseLocked(groupTroveItemId, locked)

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemInstSetLocked(self, groupTroveItemId, locked):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroveItems.setInstSetLocked(groupTroveItemId, locked)

    @private
    @typeCheck(int, str, str, str, str, bool, bool, bool)
    @requiresAuth
    def addGroupTroveItem(self, groupTroveId, trvname, trvVersion, trvFlavor,
                     subGroup, versionLock, useLock, instSetLock):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        creatorId = self.users.getIdByColumn("username", self.authToken[0])
        return self.groupTroveItems.addTroveItem(groupTroveId, creatorId, trvname, trvVersion, trvFlavor, subGroup, versionLock, useLock, instSetLock)

    @private
    @typeCheck(int)
    @requiresAuth
    def delGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroveItems.delGroupTroveItem(groupTroveItemId)

    @private
    @typeCheck(int)
    @requiresAuth
    def getGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        return self.groupTroveItems.get(groupTroveItemId)

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveItemSubGroup(self, groupTroveItemId, subGroup):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)
        self.groupTroveItems.update(groupTroveItemId, subGroup = subGroup)

    def __init__(self, cfg, allowPrivate = False, alwaysReload = False):
        self.cfg = cfg
     
        # all methods are private (not callable via XMLRPC)
        # except the ones specifically decorated with @public.
        self._allowPrivate = allowPrivate

        if cfg.dbDriver == "native_sqlite":
            self.db = sqlite3.connect(cfg.dbPath)
            self.db.type = "native_sqlite"
            cu = self.db.cursor()
            
            cu.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
            self.db.tables = [ x[0] for x in cu.fetchall() ]
        elif cfg.dbDriver == "sqlite":
            from dbstore import sqlite_drv
            self.db = sqlite_drv.Database(cfg.dbPath)
            self.db.connect()
        elif cfg.dbDriver == "mysql":
            global dbConnection 
            if not dbConnection:
                from dbstore import mysql_drv
                self.db = mysql_drv.Database(cfg.dbPath)
                self.db.connect()
                dbConnection = self.db
            else:
                self.db = dbConnection
        else:
            assert("invalid SQL driver specified: %s" % cfg.dbDriver)

        self.authDb = sqlite3.connect(cfg.authDbPath)

        #An explicit transaction.  Make sure you don't have any implicit
        #commits until the database version has been asserted
        if self.db.type == "native_sqlite":
            self.db.cursor().execute("BEGIN")
        else:
            self.db.transaction(None)
        try:
            #The database version object has a dummy check so that it always passes.
            #At the end of all database object creation, fix the version

            global tables           
            if not tables or alwaysReload:
                if self.db.type != "native_sqlite":
                    self.db._getSchema()
                tables = getTables(self.db, self.cfg)
            self.__dict__.update(tables)
           
            #now fix the version
            self.version.fixVersion()

            #Now it's safe to commit
            self.db.commit()

        except:
            #An error occurred during db creation or upgrading
            self.db.rollback()
            raise

        self.newsCache.refresh()


