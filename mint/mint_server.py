#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import hmac
import os
import re
import string
import sys
import time
from urlparse import urlparse

import base64
import data
import database
import dbversion
import grouptrove
import jobs
import jobstatus
import news
import pkgindex
import projects
import releases
import reports
import requests
import sessiondb
import stats
import templates
import userlevels
import users

from mint_error import PermissionDenied, ReleasePublished, ReleaseMissing, \
     MintError
from reports import MintReport
from searcher import SearchTermsError

from conary import sqlite3
from conary import versions
from conary.repository.errors import TroveNotFound
from conary.repository import netclient
from conary.repository import shimclient
from conary.repository.netrepos import netserver
from conary.deps import deps
from conary import conarycfg
from conary import conaryclient


validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

dbConnection = None

class ParameterError(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "A required Parameter had an incorrect type"):
        self.reason = reason

class GroupTroveEmpty(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "Group Trove cannot be empty"):
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
                    if p_type in (int, long):
                        # allow ints and longs to be interchangeable
                        match = match or type(param) in (int, long)
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
        if paramType in (int, long):
            # make ints interchangeable with longs
            return type(param) in (int, long)
        return type(param) == paramType

def typeCheck(*paramTypes):
    """This decorator will be required on all functions callable over xmlrpc.
    This will force consistent calling conventions or explicit typecasting
    for all xmlrpc calls made to ensure extraneous calls won't be allowed."""
    def deco(func):
        def wrapper(self, *args):
            for i in range(len(args)):
                if (not checkParam(args[i],paramTypes[i])):
                    baseFunc = deriveBaseFunc(func)
                    raise ParameterError('%s was passed %s of type %s when '
                                         'expecting %s for parameter number '
                                         '%d' % \
                        (baseFunc.__name__, repr(args[i]), str(type(args[i])),
                         str(paramTypes[i]), i+1))
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
    d['userGroups'] = users.UserGroupsTable(db, cfg)
    d['userGroupMembers'] = users.UserGroupMembersTable(db, cfg)
    d['projectUsers'] = users.ProjectUsersTable(db)
    d['releases'] = releases.ReleasesTable(db)
    d['pkgIndex'] = pkgindex.PackageIndexTable(db)
    d['newsCache'] = news.NewsCacheTable(db, cfg)
    d['sessions'] = sessiondb.SessionsTable(db)
    d['membershipRequests'] = requests.MembershipRequestTable(db)
    d['commits'] = stats.CommitsTable(db)
    d['releaseData'] = data.ReleaseDataTable(db)
    d['groupTroves'] = grouptrove.GroupTroveTable(db)
    d['groupTroveItems'] = grouptrove.GroupTroveItemsTable(db)
    d['jobData'] = data.JobDataTable(db)
    d['releaseImageTypes'] = releases.ReleaseImageTypesTable(db)
    if not min([x.upToDate for x in d.values()]):
        d['version'].bumpVersion()
        return getTables(db, cfg)
    if d['version'].getDBVersion() != d['version'].schemaVersion:
        d['version'].bumpVersion()
    return d

class MintServer(object):
    _checkRepo = True
    _cachedGroups = []

    def callWrapper(self, methodName, authToken, args):
        # reopen the database if it's changed
        self.db.reopen()
        
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

            allowPrivate = self._allowPrivate
            r = method(*args)
            self._allowPrivate = allowPrivate
            if self.cfg.profiling:
                print >> sys.stderr, "Ending XMLRPC request:\t\t%-25s\t%.2f" % (methodName, (time.time() - startTime) * 1000)
                sys.stderr.flush()
        except users.UserAlreadyExists, e:
            self.db.rollback()
            return (True, ("UserAlreadyExists", str(e)))
        except database.DuplicateItem, e:
            self.db.rollback()
            return (True, ("DuplicateItem", e.item))
        except database.ItemNotFound, e:
            self.db.rollback()
            return (True, ("ItemNotFound", e.item))
        except SearchTermsError, e:
            self.db.rollback()
            return (True, ("SearchTermsError", str(e)))
        except users.AuthRepoError, e:
            self.db.rollback()
            return (True, ("AuthRepoError", str(e)))
        except jobs.DuplicateJob, e:
            self.db.rollback()
            return (True, ("DuplicateJob", str(e)))
        except:
            self.db.rollback()
            raise
        #except Exception, error:
        #    exc_name = sys.exc_info()[0].__name__
        #    return (True, (exc_name, error, str(error)))
        else:
            self.db.commit()
            return (False, r)

    def _getProjectRepo(self, project):
        # use a shimclient for mint-handled repositories; netclient if not
        if project.external:
            cfg = project.getConaryConfig()
            repo = conaryclient.ConaryClient(cfg).getRepos()
        else:
            if self.cfg.SSL:
                protocol = "https"
                port = 443
            else:
                protocol = "http"
                port = 80

            authUrl = "%s://%s:%s@%s/repos/%s/" % (protocol,
                                                   self.cfg.authUser,
                                                   self.cfg.authPass,
                                                   self.cfg.projectSiteHost,
                                                   project.getHostname())
            authLabel = project.getLabel()
            authRepo = {versions.Label(authLabel).getHost(): authUrl}

            reposPath = os.path.join(self.cfg.reposPath, project.getFQDN())
            tmpPath = os.path.join(reposPath, "tmp")

            # handle non-standard ports specified on cfg.projectDomainName,
            # most likely just used by the test suite
            if ":" in self.cfg.projectDomainName:
                port = int(self.cfg.projectDomainName.split(":")[1])

            name = project.getFQDN()
            cfg = netserver.ServerConfig()
            cfg.repositoryDB = self.projects.reposDB.getRepositoryDB(name)
            cfg.tmpDir = tmpPath
            cfg.serverName = project.getFQDN()
            cfg.contentsDir = reposPath + '/contents/'

            server = shimclient.NetworkRepositoryServer(cfg, '')

            cfg = conarycfg.ConaryConfiguration()
            cfg.repositoryMap = authRepo
            cfg.user.addServerGlob(versions.Label(authLabel).getHost(),
                                   self.cfg.authUser, self.cfg.authPass)
            repo = shimclient.ShimNetClient(server, protocol, port,
                (self.cfg.authUser, self.cfg.authPass, None, None), cfg.repositoryMap,
                                            cfg.user)
        return repo

    # unfortunately this function can't be a proper decorator because we
    # can't always know which param is the projectId.
    # We'll just call it at the begining of every function that needs it.
    def _filterProjectAccess(self, projectId):
        if self.authToken == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
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
        cu.execute("SELECT projectId FROM Releases WHERE releaseId = ?",
                   releaseId)
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
        cu.execute("""SELECT projectId FROM Jobs
                        JOIN Releases USING(releaseId)
                      WHERE jobId = ?
                        UNION SELECT projectId FROM Jobs
                               JOIN GroupTroves USING(groupTroveId)
                               WHERE jobId = ?
                                """, jobId, jobId)
        r = cu.fetchall()
        if len(r) and r[0][0]:
            self._filterProjectAccess(r[0][0])

    def _filterImageFileAccess(self, fileId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM ImageFiles
                          LEFT JOIN Releases
                              ON Releases.releaseId = ImageFiles.releaseId
                          WHERE fileId=?""", fileId)
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
        if self.auth.userId not in [x[0] for x in members]:
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


        project.addLabel(fqdn.split(':')[0] + "@%s" % self.cfg.defaultBranch,
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
        filter = (self.auth.userId != userId) and (not self.auth.admin)
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

                import templates.joinRequest
                message = templates.write(templates.joinRequest,
                    projectName = self.getProject(projectId)['name'],
                    comments = comments, cfg = self.cfg)
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
            cu.execute("""SELECT userId FROM Users
                              WHERE username=? AND active=1""", username)
            r = cu.fetchone()
            if not r:
                raise database.ItemNotFound("username")
            else:
                userId = r[0]
        elif userId and not username:
            cu.execute("""SELECT username FROM Users
                              WHERE userId=? AND active=1""", userId)
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
            password = ''
            salt = ''
            query = "SELECT salt, passwd FROM Users WHERE username=?"
            cu.execute(query, username)
            try:
                salt, password = cu.fetchone()
            except TypeError:
                raise database.ItemNotFound("username")
            repos = self._getProjectRepo(project)
            repos.addUserByMD5(project.getLabel(), username, salt, password)
            repos.addAcl(project.getLabel(), username, None, None,
                         level in userlevels.WRITERS, False,
                         level == userlevels.OWNER)

        self._notifyUser('Added', self.getUser(userId),
                         projects.Project(self,projectId), level)
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
            # FIXME Do we want to do some substitution in the subject/body?
            try:
                users.sendMailWithChecks(self.cfg.adminMail,
                                         self.cfg.productName,
                                         email, subject, body)
            except users.MailError, e:
                # Invalidate the user, so he/she must change his/her address at
                # the next login
                self.users.invalidateUser(user[0])

    @typeCheck(int, str, str, str)
    @requiresAuth
    @private
    def editProject(self, projectId, projecturl, desc, name):
        if projecturl and not (projecturl.startswith('https://') or \
                               projecturl.startswith('http://')):
            projecturl = "http://" + projecturl
        self._filterProjectAccess(projectId)
        return self.projects.update(projectId, projecturl=projecturl,
                                    description = desc, name = name)

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
        cu.execute("""SELECT level FROM ProjectUsers
                          WHERE userId=? and projectId=?""",
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
        if self.projectUsers.onlyOwner(projectId, userId) and \
               (level != userlevels.OWNER):
            raise users.LastOwner()
        #update the level on the project
        project = projects.Project(self, projectId)
        user = self.getUser(userId)
        if not project.external:
            repos = self._getProjectRepo(project)
            repos.editAcl(project.getLabel(), user['username'], "ALL", None,
                          None, None, level in userlevels.WRITERS, False,
                          level == userlevels.OWNER)

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
    def registerNewUser(self, username, password, fullName, email,
                        displayEmail, blurb, active):
        return self.users.registerNewUser(username, password, fullName, email,
                                          displayEmail, blurb, active)

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
        """ Checks to see if the the user to be deleted is leaving in a
            lurch developers of projects that would be left ownerless.
            Then deletes the user.
        """
        if (self.auth.userId != userId) and (not self.auth.admin):
            raise PermissionDenied()
        cu = self.db.cursor()
        username = self.users.getUsername(userId)

        # Find all projects of which userId is an owner, has no other owners, and/or
        # has developers.
        cu.execute("""SELECT MAX(D.flagged)
                        FROM (SELECT A.projectId,
                               COUNT(B.userId) * (NOT COUNT(C.userId)) AS flagged
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
        username = self.users.getUsername(userId)

        #Handle projects
        projectList = self.getProjectIdsByMember(userId)
        for (projectId, level) in projectList:
            self.delMember(projectId, userId, False)

        cu = self.db.transaction()
        try:
            cu.execute("""SELECT userGroupId FROM UserGroupMembers
                              WHERE userId=?""", userId)
            for userGroupId in [x[0] for x in cu.fetchall()]:
                cu.execute("""SELECT COUNT(*) FROM UserGroupMembers
                                  WHERE userGroupId=?""", userGroupId)
                if cu.fetchone()[0] == 1:
                    cu.execute("DELETE FROM UserGroups WHERE userGroupId=?",
                               userGroupId)
            cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?",
                       userId)
            cu.execute("UPDATE Jobs SET userId=0 WHERE userId=?", userId)
            cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
            cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
            cu.execute("DELETE FROM UserGroupMembers WHERE userId=?", userId)
            cu.execute("DELETE FROM Users WHERE userId=?", userId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    @typeCheck(str)
    @private
    def getConfirmation(self, username):
        # this function exists solely for server testing scripts and should
        # not be used for any other purpose. Never enable in production mode.
        if not self.cfg.debugMode:
            raise PermissionDenied
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM Users WHERE username=?", username)
        r = cu.fetchall()
        if not r:
            raise database.ItemNotFound
        cu.execute("SELECT confirmation FROM Confirmations WHERE userId=?",
                   r[0][0])
        if not r:
            raise database.ItemNotFound
        return cu.fetchall()[0][0]

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

            if not project.external:
                authRepo = self._getProjectRepo(project)
                authRepo.changePassword(project.getLabel(), username, newPassword)

        self.users.changePassword(username, newPassword)

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

    @typeCheck(int, bool, bool, ((str, type(None)),), ((str, type(None)),), ((bool, type(None)),))
    @private
    def getLabelsForProject(self, projectId, overrideSSL, overrideAuth, newUser, newPass, useSSL):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        self._filterProjectAccess(projectId)
        return self.labels.getLabelsForProject(projectId, overrideSSL, overrideAuth, useSSL, newUser, newPass)

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

    # release data calls
    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setReleaseDataValue(self, releaseId, name, value, dataType):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        return self.releaseData.setDataValue(releaseId, name, value, dataType)

    @typeCheck(int, str)
    @private
    def getReleaseDataValue(self, releaseId, name):
        self._filterReleaseAccess(releaseId)
        return self.releaseData.getDataValue(releaseId, name)

    @typeCheck(int)
    @private
    def getReleaseDataDict(self, releaseId):
        self._filterReleaseAccess(releaseId)
        return self.releaseData.getDataDict(releaseId)

    # job data calls
    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setJobDataValue(self, jobId, name, value, dataType):
        self._filterJobAccess(jobId)
        return self.jobData.setDataValue(jobId, name, value, dataType)

    @typeCheck(int, str)
    @private
    def getJobDataValue(self, jobId, name):
        self._filterJobAccess(jobId)
        return self.jobData.getDataValue(jobId, name)

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
        self.releases.update(releaseId, description = desc)
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
        self.releases.update(releaseId, published = int(published), timePublished = timeStamp)
        return True

    @typeCheck(int)
    @requiresAuth
    @private
    def getImageTypes(self, releaseId):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        cu = self.db.cursor()
        cu.execute('SELECT imageType from ReleaseImageTypes WHERE releaseId=?', releaseId)
        return [x[0] for x in cu.fetchall()]

    @typeCheck(int, list)
    @requiresAuth
    @private
    def setImageTypes(self, releaseId, imageTypes):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()
        cu = self.db.cursor()
        cu.execute("DELETE FROM ReleaseImageTypes WHERE releaseId=?", releaseId)
        for i in imageTypes:
            cu.execute("INSERT INTO ReleaseImageTypes (releaseId, imageType)"
                    "VALUES (?, ?)", releaseId, i)
        self.db.commit()
            
        #self.releases.update(releaseId, imageType = imageType)
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
        cu.execute("SELECT jobId, status FROM Jobs WHERE releaseId=? AND groupTroveId IS NULL",
                   releaseId)
        r = cu.fetchall()
        if len(r) == 0:
            retval = self.jobs.new(releaseId = releaseId, userId = self.auth.userId,
                status = jobstatus.WAITING, statusMessage = self.getJobWaitMessage(0),
                timeStarted = time.time(), timeFinished = 0)
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                msg = self.getJobWaitMessage(jobId)
                self.jobs.update(jobId, status = jobstatus.WAITING,
                    statusMessage = msg,
                    timeStarted = time.time(), timeFinished = 0)
                retval = jobId

        return retval

    @typeCheck(int, str)
    @private
    def startCookJob(self, groupTroveId, arch):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)

        if not self.listGroupTroveItemsByGroupTrove(groupTroveId):
            raise GroupTroveEmpty

        cu = self.db.cursor()
        cu.execute("""SELECT jobId, status FROM Jobs
                          WHERE groupTroveId=? AND releaseId IS NULL""",
                   groupTroveId)
        r = cu.fetchall()
        if len(r) == 0:
            retval = self.jobs.new(groupTroveId = groupTroveId,
                                   userId = self.auth.userId,
                                   status = jobstatus.WAITING,
                                   statusMessage = self.getJobWaitMessage(0),
                timeStarted = time.time(), timeFinished = 0)
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                msg = self.getJobWaitMessage(jobId)
                self.jobs.update(jobId, status = jobstatus.WAITING,
                    statusMessage = msg,
                    timeStarted = time.time(), timeFinished = 0)
                retval = jobId
        self.jobData.setDataValue(retval, "arch", arch, data.RDT_STRING)
        return retval

    @private
    @typeCheck(int)
    def getJobWaitMessage(self, jobId):
        queueLen = self._getJobQueueLength(jobId)
        msg = "Next in line for processing"
        if queueLen:
            msg = "Number %d in line for processing" % (queueLen+1)
        return msg

    @typeCheck(int)
    @private
    def getJob(self, jobId):
        self._filterJobAccess(jobId)
        cu = self.db.cursor()

        cu.execute("SELECT userId, releaseId, groupTroveId, status,"
                   "  statusMessage, timeStarted, "
                   "  timeFinished FROM Jobs "
                   " WHERE jobId=?", jobId)

        p = cu.fetchone()
        if not p:
            raise jobs.JobMissing

        dataKeys = ['userId', 'releaseId', 'groupTroveId', 'status',
                    'statusMessage', 'timeStarted', 'timeFinished']
        data = {}
        for i, key in enumerate(dataKeys):
            # these keys can be NULL from the db
            if key in ('releaseId', 'groupTroveId'):
                if p[i] is None:
                    data[key] = 0
                else:
                    data[key] = p[i]
            else:
                data[key] = p[i]
        return data

    @typeCheck()
    @requiresAuth
    @private
    def getJobIds(self):
        cu = self.db.cursor()

        cu.execute("SELECT jobId FROM Jobs ORDER BY timeStarted")

        return [x[0] for x in cu.fetchall()]

    @typeCheck(int)
    @requiresAuth
    @private
    def getJobIdsForRelease(self, releaseId):
        self._filterReleaseAccess(releaseId)
        cu = self.db.cursor()

        cu.execute("SELECT jobId FROM Jobs WHERE releaseId=?", releaseId)
        r = cu.fetchone()
        if r:
            return r[0]
        else:
            return 0

    @typeCheck(int)
    @requiresAuth
    @private
    def getJobIdForCook(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        self._requireProjectOwner(projectId)

        cu = self.db.cursor()

        cu.execute("SELECT jobId FROM Jobs WHERE groupTroveId=?", groupTroveId)
        r = cu.fetchone()
        if r:
            return r[0]
        else:
            return 0

    @typeCheck(int, int, str)
    @private
    def setJobStatus(self, jobId, newStatus, statusMessage):
        self._filterJobAccess(jobId)
        if newStatus == jobstatus.FINISHED:
            self.jobs.update(jobId, status = newStatus, statusMessage = statusMessage, timeFinished = time.time())
        else:
            self.jobs.update(jobId, status = newStatus, statusMessage = statusMessage)
        return True

    @typeCheck(int, (list, (list, str)))
    @requiresAuth
    @private
    def setImageFilenames(self, releaseId, filenames):
        self._filterReleaseAccess(releaseId)
        if not self.releases.releaseExists(releaseId):
            raise ReleaseMissing()
        if self.releases.getPublished(releaseId):
            raise ReleasePublished()

        cu = self.db.transaction()
        try:
            cu.execute("DELETE FROM ImageFiles WHERE releaseId=?", releaseId)
            for idx, file in enumerate(filenames):
                fileName, title = file
                cu.execute("INSERT INTO ImageFiles VALUES (NULL, ?, ?, ?, ?)",
                           releaseId, idx, fileName, title)
        except:
            self.db.rollback()
            raise
        else:
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
            l = []
            for x in results:
                try:
                    size = os.stat(x[1])[6]
                except OSError:
                    size = 0
                d = {'fileId':      x[0],
                     'filename':    os.path.basename(x[1]),
                     'title':       x[2],
                     'size':        size,
                    }
                l.append(d)
            return l

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
            troves = nc.troveNamesOnServer(versions.Label(label).getHost())
            troves = [x for x in troves if (x.startswith("group-") or\
                                            x.startswith("fileset-")) and\
                                            ":" not in x]
            troveDict[label] = troves
        return troveDict

    # XXX refactor to getJobStatus instead of two functions
    @typeCheck(int)
    @requiresAuth
    def getReleaseStatus(self, releaseId):
        self._filterReleaseAccess(releaseId)
        self._allowPrivate = True

        release = releases.Release(self, releaseId)
        job = release.getJob()

        if not job:
            return {'status'  : jobstatus.NOJOB,
                    'message' : jobstatus.statusNames[jobstatus.NOJOB],
                    'queueLen': 0}
        else:
            return {'status'  : job.getStatus(),
                    'message' : job.getStatusMessage(),
                    'queueLen': self._getJobQueueLength(job.getId())}

    @typeCheck(int)
    @requiresAuth
    def getJobStatus(self, jobId):
        self._filterJobAccess(jobId)
        self._allowPrivate = True

        job = jobs.Job(self, jobId)

        if not job:
            return {'status'  : jobstatus.NOJOB,
                    'message' : jobstatus.statusNames[jobstatus.NOJOB],
                    'queueLen': 0}
        else:
            return {'status'  : job.getStatus(),
                    'message' : job.getStatusMessage(),
                    'queueLen': self._getJobQueueLength(jobId)}

    def _getJobQueueLength(self, jobId):
        self._filterJobAccess(jobId)
        self._allowPrivate = True
        cu = self.db.cursor()
        if jobId:
            cu.execute("SELECT COUNT(*) FROM Jobs WHERE timeStarted < (SELECT timeStarted FROM Jobs WHERE jobId = ?) AND status = 0", jobId)
        else:
            cu.execute("SELECT COUNT(*) FROM Jobs WHERE status = 0")
        return cu.fetchone()[0]


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
    @private
    @typeCheck()
    def cleanupGroupTroves(self):
        self.groupTroves.cleanup()

    def _getRecipe(self, groupTroveId):
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
        recipeLabels = self.getGroupTroveLabelPath(groupTroveId)
        recipe += indent + "r.setLabelPath(%s)\n" % str(recipeLabels).split('[')[1].split(']')[0]

        for trv in groupTroveItems:
            if trv['versionLock']:
                ver = trv['trvVersion']
            else:
                ver = trv['trvLabel']

            # XXX HACK to use the "fancy-flavored" group troves from conary.rpath.com
            if trv['trvName'].startswith('group-') and trv['trvLabel'].startswith('conary.rpath.com@'):
                recipe += indent + "if Arch.x86_64:\n"
                recipe += (12 * " ") + "r.add('" + trv['trvName'] + "', '" + ver + "', 'is:x86(i486,i586,i686) x86_64', groupName = '" +trv['subGroup'] +"')\n"
                recipe += indent + "else:\n" + (4 * " ")
            recipe += indent + "r.add('" + trv['trvName'] + "', '" + ver + "', '" + trv['trvFlavor'] + "', groupName = '" +trv['subGroup'] +"')\n"
        return recipe

    @typeCheck(int)
    @private
    def getGroupTroveLabelPath(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)

        groupTrove = self.groupTroves.get(groupTroveId)
        groupTroveItems = self.groupTroveItems.listByGroupTroveId(groupTroveId)

        # build a dependency resolution scheme.
        # own project's labels come first.
        # the rest are sorted alphabetically.
        # this approach is definitely sub-optimal, but has the advantage of
        # consistent results.
        recipeLabels = list(set([x['trvLabel'] for x in groupTroveItems]))
        if not projectId:
            return recipeLabels
        projectLabels = self.labels.getLabelsForProject( \
            groupTrove['projectId'])[0].keys()
        for label in projectLabels:
            if label in recipeLabels:
                recipeLabels.remove(label)
        recipeLabels.sort()
        for label in projectLabels:
            recipeLabels.insert(0, label)
        return recipeLabels

    @typeCheck(int)
    @private
    def getRecipe(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self._getRecipe(groupTroveId)

    @private
    @typeCheck(int, bool)
    def setGroupTroveAutoResolve(self, groupTroveId, resolve):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
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
    def createGroupTrove(self, projectId, recipeName, upstreamVersion,
                         description, autoResolve):
        # projectId 0 indicates (public) transient group trove.
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
            creatorId = self.users.getIdByColumn("username", self.authToken[0])
        else:
            creatorId = 0
        return self.groupTroves.createGroupTrove(projectId, creatorId,
                                                 recipeName, upstreamVersion,
                                                 description, autoResolve)

    @private
    @typeCheck(int)
    def getGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        # projectId 0 indicates (public) transient group trove.
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self.groupTroves.get(groupTroveId)

    @private
    @typeCheck(int)
    def deleteGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self.groupTroves.delGroupTrove(groupTroveId)

    @private
    @typeCheck(int, str)
    def setGroupTroveDesc(self, groupTroveId, description):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroves.update(groupTroveId, description = description,
                                timeModified = time.time())

    @private
    @typeCheck(int, str)
    def setGroupTroveUpstreamVersion(self, groupTroveId, vers):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroves.setUpstreamVersion(groupTroveId, vers)

    #group trove item specific functions

    @private
    @typeCheck(int)
    def listGroupTroveItemsByGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self.groupTroveItems.listByGroupTroveId(groupTroveId)

    @typeCheck(int, bool)
    def setGroupTroveItemVersionLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroveItems.setVersionLock(groupTroveItemId, lock)
        return lock

    @private
    @typeCheck(int, bool)
    def setGroupTroveItemUseLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroveItems.setUseLock(groupTroveItemId, lock)
        return lock

    @private
    @typeCheck(int, bool)
    def setGroupTroveItemInstSetLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroveItems.setInstSetLock(groupTroveItemId, lock)
        return lock

    @typeCheck(int, str, str, str, str, bool, bool, bool)
    def addGroupTroveItem(self, groupTroveId, trvName, trvVersion, trvFlavor,
                     subGroup, versionLock, useLock, instSetLock):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
            creatorId = self.users.getIdByColumn("username", self.authToken[0])
        else:
            creatorId = 0
        return self.groupTroveItems.addTroveItem(groupTroveId, creatorId,
                                                 trvName, trvVersion,
                                                 trvFlavor, subGroup,
                                                 versionLock, useLock,
                                                 instSetLock)

    @typeCheck(int, str, str, str, str, bool, bool, bool)
    def addGroupTroveItemByProject(self, groupTroveId, trvName, projectName,
                                   trvFlavor, subGroup, versionLock, useLock,
                                   instSetLock):
        self._allowPrivate = True
        projectId = self.projects.getProjectIdByHostname(projectName)
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        groupTrove = grouptrove.GroupTrove(self, groupTroveId)
        leaves = None
        if groupTrove.projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(groupTrove.projectId)
            groupProject = projects.Project(self, groupTrove.projectId)
            affineLabel = project.getLabel().split('@')[0] + '@' + \
                          groupProject.getLabel().split('@')[1]
            # initial try. see if there's a trove affinite with branchName from
            # groupTroveId's project
            leaves = repos.getTroveVersionsByLabel(
                {trvName:{versions.Label(affineLabel):None}})
        # fallback 1. pick default branchName of that project
        if not leaves:
            leaves = repos.getTroveVersionsByLabel(
                {trvName:{versions.Label(project.getLabel()):None}})
        # fallback 2. find the first branchName match that we can...
        if not leaves:
            leaves = repos.getAllTroveLeaves(0, {trvName: None})
        if trvName not in leaves:
            raise TroveNotFound
        trvVersion = sorted(leaves[trvName].keys(),
                            reverse = True)[0].asString()

        groupTroveItemId = self.addGroupTroveItem(groupTroveId, trvName,
                                                  trvVersion, trvFlavor,
                                                  subGroup, versionLock,
                                                  useLock, instSetLock)
        return (groupTroveItemId, trvName, trvVersion)

    @typeCheck(int)
    def delGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self.groupTroveItems.delGroupTroveItem(groupTroveItemId)

    @private
    @typeCheck(int)
    def getGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        return self.groupTroveItems.get(groupTroveItemId)

    @private
    @typeCheck(int, str)
    def setGroupTroveItemSubGroup(self, groupTroveItemId, subGroup):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        if projectId:
            if not self.auth.authorized:
                raise PermissionDenied
            self._filterProjectAccess(projectId)
            self._requireProjectOwner(projectId)
        self.groupTroveItems.update(groupTroveItemId, subGroup = subGroup)

    ### Site reports ###
    @private
    @typeCheck()
    @requiresAdmin
    def listAvailableReports(self):
        reportNames = reports.getAvailableReports()
        res = {}
        for rep in reportNames:
            repObj = self._getReportObject(rep)
            if repObj is not None:
                res[rep] = repObj.title
        return res

    def _getReportObject(self, name):
        repModule = reports.__dict__[name]
        for objName in repModule.__dict__.keys():
            try:
                if objName != 'MintReport' and \
                       MintReport in repModule.__dict__[objName].__bases__:
                    return repModule.__dict__[objName](self.db)
            except AttributeError:
                pass
        return None

    @private
    @typeCheck(str)
    @requiresAdmin
    def getReport(self, name):
        if name not in reports.getAvailableReports():
            raise PermissionDenied
        return self._getReportObject(name).getReport()

    @private
    @typeCheck(str)
    @requiresAdmin
    def getReportPdf(self, name):
        if name not in reports.getAvailableReports():
            raise PermissionDenied
        return base64.b64encode(self._getReportObject(name).getPdf())

    def __init__(self, cfg, allowPrivate = False, alwaysReload = False):
        self.cfg = cfg

        # all methods are private (not callable via XMLRPC)
        # except the ones specifically decorated with @public.
        self._allowPrivate = allowPrivate

        from conary import dbstore
        global dbConnection
        if cfg.dbDriver in ["mysql", "postgresql"] and dbConnection and (not alwaysReload):
            self.db = dbConnection
        else:
            self.db = dbstore.connect(cfg.dbPath, driver=cfg.dbDriver)
            dbConnection = self.db

        try:
            #The database version object has a dummy check so that it always passes.
            #At the end of all database object creation, fix the version

            global tables
            if not tables or alwaysReload:
                self.db.loadSchema()
                tables = getTables(self.db, self.cfg)
            self.__dict__.update(tables)

            #Now it's safe to commit
            self.db.commit()

        except:
            #An error occurred during db creation or upgrading
            self.db.rollback()
            raise

        self.newsCache.refresh()
