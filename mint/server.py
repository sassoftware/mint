#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import base64
import hmac
import os
import re
import random
import simplejson
import string
import sys
import time
import tempfile
from urlparse import urlparse

from mint import data
from mint import database
from mint import dbversion
from mint import grouptrove
from mint import jobs
from mint import jobstatus
from mint import maintenance
from mint import mirror
from mint import news
from mint import pkgindex
from mint import profile
from mint import projects
from mint import builds
from mint import pubreleases
from mint import reports
from mint import requests
from mint import sessiondb
from mint import stats
from mint import templates
from mint import userlevels
from mint import users
from mint import usertemplates
from mint import spotlight
from mint import selections
from mint import useit
from mint import rmakebuild
from mint.distro import jsversion
from mint.distro.flavors import stockFlavors
from mint.mint_error import PermissionDenied, BuildPublished, \
     BuildMissing, MintError, BuildEmpty, UserAlreadyAdmin, \
     AdminSelfDemotion, JobserverVersionMismatch, LastAdmin, \
     MaintenanceMode, ParameterError, GroupTroveEmpty, rMakeBuildCollision, \
     rMakeBuildEmpty, rMakeBuildOrder, PublishedReleaseMissing, \
     PublishedReleaseEmpty, PublishedReleaseFinalized
from mint.reports import MintReport
from mint.searcher import SearchTermsError

from conary import conarycfg
from conary import conaryclient
from conary import sqlite3
from conary import versions
from conary.deps import deps
from conary.lib import util
from conary.repository.errors import TroveNotFound
from conary.repository import netclient
from conary.repository import shimclient
from conary.repository.netrepos import netserver, calllog
from conary import errors as conary_errors

from mint.rmakeconstants import buildjob
from mint.rmakeconstants import currentApi as currentrMakeApi

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

dbConnection = None

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
        if self.auth.admin or list(self.authToken) == [self.cfg.authUser, self.cfg.authPass]:
            return func(self, *args)
        else:
            raise PermissionDenied
    wrapper.__wrapped_func__ = func
    return wrapper

def requiresAuth(func):
    def wrapper(self, *args):
        if self.auth.authorized or list(self.authToken) == [self.cfg.authUser, self.cfg.authPass]:
            return func(self, *args)
        else:
            raise PermissionDenied
    wrapper.__wrapped_func__ = func
    return wrapper

def requiresCfgAdmin(cond):
    def deco(func):
        def wrapper(self, *args):
            if (list(self.authToken) == \
                [self.cfg.authUser, self.cfg.authPass]) or self.auth.admin or \
                 (not self.cfg.__getitem__(cond) and self.auth.authorized):
                    return func(self, *args)
            else:
                raise PermissionDenied
        wrapper.__wrapped_func__ = func
        return wrapper
    return deco

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
    d['labels'] = projects.LabelsTable(db, cfg)
    d['projects'] = projects.ProjectsTable(db, cfg)
    d['jobs'] = jobs.JobsTable(db)
    d['buildFiles'] = jobs.BuildFilesTable(db)
    d['users'] = users.UsersTable(db, cfg)
    d['userGroups'] = users.UserGroupsTable(db, cfg)
    d['userGroupMembers'] = users.UserGroupMembersTable(db, cfg)
    d['userData'] = data.UserDataTable(db)
    d['projectUsers'] = users.ProjectUsersTable(db)
    d['builds'] = builds.BuildsTable(db)
    d['pkgIndex'] = pkgindex.PackageIndexTable(db)
    d['newsCache'] = news.NewsCacheTable(db, cfg)
    d['sessions'] = sessiondb.SessionsTable(db)
    d['membershipRequests'] = requests.MembershipRequestTable(db)
    d['commits'] = stats.CommitsTable(db)
    d['buildData'] = data.BuildDataTable(db)
    d['groupTroves'] = grouptrove.GroupTroveTable(db, cfg)
    d['groupTroveItems'] = grouptrove.GroupTroveItemsTable(db, cfg)
    d['conaryComponents'] = grouptrove.ConaryComponentsTable(db)
    d['groupTroveRemovedComponents'] = grouptrove.GroupTroveRemovedComponentsTable(db)
    d['jobData'] = data.JobDataTable(db)
    d['inboundLabels'] = mirror.InboundLabelsTable(db)
    d['outboundLabels'] = mirror.OutboundLabelsTable(db)
    d['outboundMatchTroves'] = mirror.OutboundMatchTrovesTable(db)
    d['repNameMap'] = mirror.RepNameMapTable(db)
    d['spotlight'] = spotlight.ApplianceSpotlightTable(db, cfg)
    d['useit'] = useit.UseItTable(db, cfg)
    d['selections'] = selections.FrontPageSelectionsTable(db, cfg)
    d['rMakeBuild'] = rmakebuild.rMakeBuildTable(db)
    d['rMakeBuildItems'] = rmakebuild.rMakeBuildItemsTable(db)
    d['publishedReleases'] = pubreleases.PublishedReleasesTable(db)
    outDatedTables = [x for x in d.values() if not x.upToDate]
    while outDatedTables[:]:
        d['version'].bumpVersion()
        for table in outDatedTables:
            upToDate = table.versionCheck()
            if upToDate:
                outDatedTables.remove(table)
    if d['version'].getDBVersion() != d['version'].schemaVersion:
        d['version'].bumpVersion()
    return d

class MintServer(object):
    def callWrapper(self, methodName, authToken, args):
        # reopen the database if it's changed
        self.db.reopen()

        prof = profile.Profile(self.cfg)

        try:
            if methodName.startswith('_'):
                raise AttributeError
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))

        # start profile
        prof.startXml(methodName)

        try:
            try:
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

                auth = self.users.checkAuth(authToken)
                self.authToken = authToken
                self.auth = users.Authorization(**auth)

                try:
                    maintenance.enforceMaintenanceMode(self.cfg, self.auth)
                except MaintenanceMode:
                    # supress exceptions for certain critical methods.
                    if methodName not in self.maintenanceMethods:
                        raise

                # let inner private-only calls pass
                self._allowPrivate = True

                r = method(*args)
                if self.callLog:
                    self.callLog.log(self.remoteIp, list(authToken) + [None, None], methodName, args)

            except users.UserAlreadyExists, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("UserAlreadyExists", str(e)))
            except database.DuplicateItem, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("DuplicateItem", e.item))
            except database.ItemNotFound, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("ItemNotFound", e.item))
            except SearchTermsError, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("SearchTermsError", str(e)))
            except users.AuthRepoError, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("AuthRepoError", str(e)))
            except jobs.DuplicateJob, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("DuplicateJob", str(e)))
            except UserAlreadyAdmin, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("UserAlreadyAdmin", str(e)))
            except AdminSelfDemotion, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("AdminSelfDemotion" , str(e)))
            except JobserverVersionMismatch, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("JobserverVersionMismatch", str(e)))
            except MaintenanceMode, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("MaintenanceMode", str(e)))
            except users.LastOwner, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("LastOwner", str(e)))
            except ParameterError, e:
                self._handleError(e, authToken, methodName, args)
                return (True, ("ParameterError", str(e)))
            except Exception, e:
                self._handleError(e, authToken, methodName, args)
                raise
            #except Exception, error:
            #   exc_name = sys.exc_info()[0].__name__
            #   return (True, (exc_name, error, str(error)))
            else:
                self.db.commit()
                return (False, r)
        finally:
            prof.stopXml(methodName)

    def _handleError(self, e, authToken, methodName, args):
        self.db.rollback()
        if self.callLog:
            self.callLog.log(self.remoteIp, list(authToken) + [None, None],
                methodName, args, exception = e)

    def _getProjectRepo(self, project):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")
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
            cfg.externalPasswordURL = self.cfg.externalPasswordURL
            cfg.authCacheTimeout = self.cfg.authCacheTimeout

            server = shimclient.NetworkRepositoryServer(cfg, '')

            cfg = conarycfg.ConaryConfiguration()
            conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
            if os.path.exists(conarycfgFile):
                cfg.read(conarycfgFile)
            cfg.repositoryMap.update(authRepo)
            cfg.user.addServerGlob(versions.Label(authLabel).getHost(),
                                   self.cfg.authUser, self.cfg.authPass)
            repo = shimclient.ShimNetClient(server, protocol, port,
                (self.cfg.authUser, self.cfg.authPass, None, None),
                cfg.repositoryMap, cfg.user)
        return repo

    # unfortunately this function can't be a proper decorator because we
    # can't always know which param is the projectId.
    # We'll just call it at the begining of every function that needs it.
    def _filterProjectAccess(self, projectId):
        if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return
        if not self.projects.isHidden(projectId):
            return
        if (self.projectUsers.getUserlevelForProjectMember(projectId,
            self.auth.userId) in userlevels.WRITERS):
                return
        raise database.ItemNotFound()

    def _filterBuildAccess(self, buildId):
        try:
            buildRow = self.builds.get(buildId, fields=['projectId'])
        except database.ItemNotFound:
            return

        self._filterProjectAccess(buildRow['projectId'])


    def _filterPublishedReleaseAccess(self, pubReleaseId):
        try:
            pubReleaseRow = self.publishedReleases.get(pubReleaseId,
                    fields=['projectId'])
        except database.ItemNotFound:
            return

        isFinal = self.publishedReleases.isPublishedReleaseFinalized(pubReleaseId)
        # if the release is not finalized, then only project members 
        # with write access can see the published release
        if not isFinal and not self._checkProjectAccess(pubReleaseRow['projectId'], userlevels.WRITERS):
            raise database.ItemNotFound()
        # if the published release is finalized, then anyone can see it
        # unless the project is hidden and the user is not an admin
        else:
            self._filterProjectAccess(pubReleaseRow['projectId'])

    def _filterLabelAccess(self, labelId):
        try:
            labelRow = self.labels.get(labelId, fields=['projectId'])
        except database.ItemNotFound:
            return

        self._filterProjectAccess(labelRow['projectId'])


    def _filterJobAccess(self, jobId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM Jobs
                        JOIN Builds USING(buildId)
                      WHERE jobId = ?
                        UNION SELECT projectId FROM Jobs
                               JOIN GroupTroves USING(groupTroveId)
                               WHERE jobId = ?
                                """, jobId, jobId)
        r = cu.fetchall()
        if len(r) and r[0][0]:
            self._filterProjectAccess(r[0][0])

    def _filterBuildFileAccess(self, fileId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM BuildFiles 
                          LEFT JOIN Builds
                              ON Builds.buildId = BuildFiles.buildId
                          WHERE fileId=?""", fileId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _filterrMakeBuildAccess(self, rMakeBuildId):
        cu = self.db.cursor()
        cu.execute("SELECT UserId FROM rMakeBuild WHERE rMakeBuildId=?",
                   rMakeBuildId)
        res = cu.fetchone()
        if not res or res[0] != self.auth.userId:
            raise database.ItemNotFound

    def _filterrMakeBuildItemAccess(self, rMakeBuildItemId):
        cu = self.db.cursor()
        cu.execute("""SELECT rMakeBuildId
                          FROM rMakeBuildItems
                          WHERE rMakeBuildItemId=?""",
                   rMakeBuildItemId)
        res = cu.fetchone()
        if not res:
            raise database.ItemNotFound
        return self._filterrMakeBuildAccess(res[0])

    def _checkProjectAccess(self, projectId, allowedUserlevels):
        if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return True
        try:
            if (self.projectUsers.getUserlevelForProjectMember(projectId,
                    self.auth.userId) in allowedUserlevels):
                return True
        except database.ItemNotFound:
            pass
        return False

    def _isUserAdmin(self, userId):
        mintAdminId = self.userGroups.getMintAdminId()
        try:
            if mintAdminId in self.userGroupMembers.getGroupsForUser(userId):
                return True
        except database.ItemNotFound:
            pass
        return False

    # project methods
    @typeCheck(str, str, str, str, str)
    @requiresCfgAdmin('adminNewProjects')
    @private
    def newProject(self, projectName, hostname, domainname, projecturl, desc):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")
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

        # add to RepNameMap if projectDomainName != domainname
        projectDomainName = self.cfg.projectDomainName.split(':')[0]
        if (domainname != projectDomainName):
            self._addRemappedRepository('%s.%s' % \
                                        (hostname, projectDomainName), fqdn)

        project = projects.Project(self, projectId)

        project.addLabel(fqdn.split(':')[0] + "@%s" % self.cfg.defaultBranch,
            "http://%s%srepos/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname),
            self.cfg.authUser, self.cfg.authPass)

        self.projects.createRepos(self.cfg.reposPath, self.cfg.reposContentsDir,
                                  hostname, domainname, self.authToken[0],
                                  self.authToken[1])

        if self.cfg.createConaryRcFile:
            self._generateConaryRcFile()
        return projectId

    @typeCheck(str, str, str, str, str, bool)
    @requiresAdmin
    @private
    def newExternalProject(self, name, hostname, domainname, label, url, mirrored):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")

        from conary import versions
        # ensure that the label we were passed is valid
        try:
            versions.Label(label)
        except conary_errors.ParseError:
            raise ParameterError("Not a valid Label")

        if not url:
            url = 'http://' + label.split('@')[0] + '/conary/'

        # create the project entry
        projectId = self.projects.new(name = name,
                                      creatorId = self.auth.userId,
                                      description = '',
                                      hostname = hostname,
                                      domainname = domainname,
                                      projecturl = '',
                                      external = 1,
                                      timeModified = time.time(),
                                      timeCreated = time.time())

        # create the projectUsers entry
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)

        project = projects.Project(self, projectId)

        # create the labels entry
        project.addLabel(label, url, 'anonymous', 'anonymous')

        # create the target repository if needed
        if mirrored:
            parts = versions.Label(label).getHost().split(".")
            hostname, domainname = parts[0], ".".join(parts[1:])
            self.projects.createRepos(self.cfg.reposPath, self.cfg.reposContentsDir,
                hostname, domainname, None, None)

        self._generateConaryRcFile()
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
        self.membershipRequests.deleteRequest(projectId, userId)
        return True

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
                return False
        if self.cfg.sendNotificationEmails and \
               not self.membershipRequests.userHasRequested(projectId, userId):
            projectName = self.getProject(projectId)['hostname']
            owners = self.projectUsers.getOwnersByProjectName(projectName)
            for name, email in owners:
                projectName = self.getProject(projectId)['name']
                subject = projectName + " Membership Request"

                if self.auth.fullName:
                    name = "%s (%s)" % (self.auth.username, self.auth.fullName)
                else:
                    name = self.auth.username
                from mint.templates import joinRequest
                message = templates.write(joinRequest,
                                          projectName = projectName, 
                                          comments = comments, cfg = self.cfg,
                                          displayEmail = self.auth.displayEmail,
                                          name = name)
                users.sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, email, subject, message)
        self.membershipRequests.setComments(projectId, userId, comments)
        return True

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

        if level != userlevels.USER:
            self.membershipRequests.deleteRequest(projectId, userId)
        try:
            self.projectUsers.new(projectId, userId, level)
        except database.DuplicateItem:
            project.updateUserLevel(userId, level)
            # only attempt to modify acl's of local projects.
            if not project.external:
                repos = self._getProjectRepo(project)
                # edit vice/drop+add is intentional to honor acl tweaks by
                # admins.
                repos.editAcl(project.getLabel(), username, None, None, None,
                              None, level in userlevels.WRITERS, False,
                              self.cfg.projectAdmin and \
                              level == userlevels.OWNER)
                repos.setUserGroupCanMirror(project.getLabel(), username,
                                            int(level == userlevels.OWNER))
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
                         self.cfg.projectAdmin and level == userlevels.OWNER)
            repos.setUserGroupCanMirror(project.getLabel(), username,
                                        int(level == userlevels.OWNER))

        self._notifyUser('Added', self.getUser(userId),
                         projects.Project(self,projectId), level)
        return True

    typeCheck(int, int)
    @private
    def projectAdmin(self, projectId, userName):
        """Check for admin ACL in a given project repo."""
        from conary import dbstore
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)
        if project.external:
            return False
        if self.auth.admin:
            return True
        repositoryDB = self.projects.reposDB.getRepositoryDB(project.getFQDN())
        db = dbstore.connect(repositoryDB[1], repositoryDB[0])
        cu = db.cursor()
        # id's guaranteed by schema definition.
        labelId = itemId = 0
        # aggregate with MAX in case user is member of multiple groups
        cu.execute("""SELECT MAX(admin)
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN Permissions ON Permissions.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=? AND itemId=? and labelId=?""",
                   userName, itemId, labelId)
        res = cu.fetchone()
        # acl in question can be non-existent
        db.close()
        return res and res[0] or False

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
        return True

    def _notifyUser(self, action, user, project, userlevel=None):
        userlevelname = ((userlevel >=0) and userlevels.names[userlevel] or\
                                             'Unknown')
        projectUrl = 'http://%s.%s%sproject/%s/' %\
                      (self.cfg.hostName, project.getDomainname(),
                       self.cfg.basePath, project.getHostname())

        greeting = "Hello,"

        actionText = {'Removed':'has been removed from the "%s" project'%\
                       project.getName(),

                      'Added':'has been added to the "%s" project as %s %s' % (project.getName(), userlevelname == 'Developer' and 'a' or 'an', userlevelname),

                      'Changed':'has had its current access level changed to "%s" on the "%s" project' % (userlevelname, project.getName())
                     }

        helpLink = "\n\nInstructions on how to set up your build environment for this project can be found at %sconaryDevelCfg\n\nIf you would not like to be %s %s of this project, you may resign from this project at %smembers" % (projectUrl, userlevelname == 'Developer' and 'a' or 'an', userlevelname, projectUrl)

        closing = 'If you have questions about the project, please contact the project owners.'

        adminHelpText = {'Removed':'',
         
                         'Added':'\n\nIf you would not like this account to be %s %s of this project, you may remove them from the project at %smembers' %\
                         (userlevelname == 'Developer' and 'a' or 'an', 
                          userlevelname, projectUrl),

                         'Changed':'\n\nIf you would not like this account to be %s %s of this project, you may change their access level at %smembers' %\
                         (userlevelname == 'Developer' and 'a' or 'an',
                          userlevelname, projectUrl)
                        }

        message = adminMessage = None
        if self.auth.userId != user['userId']:
            message = 'Your %s account "%s" ' % (self.cfg.productName, 
                                              user['username'])
            message += actionText[action] + '.'
            if action == "Added":
                message += helpLink

            adminMessage = 'The %s account "%s" ' % (self.cfg.productName,
                                                   user['username'])
            adminMessage += actionText[action] + ' by the project owner "%s".' % (self.auth.username)
            adminMessage += adminHelpText[action]
        else:
            if action == 'Removed':
                message = 'You have resigned from the %s project "%s".' %\
                          (self.cfg.productName, project.getName())
                adminMessage = 'The %s account "%s" has resigned from the "%s" project.' % (self.cfg.productName, user['username'], project.getName())
            elif action == 'Changed':
                message = 'You have changed your access level from Owner to Developer on the %s project "%s".' % (self.cfg.productName, project.getName())
                adminMessage = 'The %s account "%s" ' % (self.cfg.productName,
                                                         user['username'])
                adminMessage += actionText[action] + ' by the project owner "%s".' % (self.auth.username)
                adminMessage += adminHelpText[action]

        if self.cfg.sendNotificationEmails:
            if message:
                users.sendMail(self.cfg.adminMail, self.cfg.productName,
                               user['email'],
                               "Your %s account" % \
                               self.cfg.productName,
                               '\n\n'.join((greeting, message, closing)))
            if adminMessage:
                members = project.getMembers()
                adminUsers = []
                for level in [userlevels.OWNER]:
                    for admnUsr in [self.getUser(x[0]) for x in members \
                                 if x[2] == level]:
                        adminUsers.append(admnUsr)
                for usr in adminUsers:
                    if usr['username'] != user['username']:
                        users.sendMail(self.cfg.adminMail, self.cfg.productName,
                                       usr['email'],
                                       "%s project membership modification" % \
                                       self.cfg.productName,
                                       '\n\n'.join((greeting, adminMessage)))

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
        # record the MintAdmin userGroupId
        cu = self.db.cursor()
        cu.execute("""SELECT userGroupId
                          FROM UserGroups
                          WHERE userGroup='MintAdmin'""");
        adminGroupId = cu.fetchone()[0]

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
                cu.execute("""SELECT COUNT(*)
                                  FROM UserGroupMembers
                                  WHERE userId=? and userGroupId=?""",
                           user[0], adminGroupId)
                if not (cu.fetchone()[0] or user[2].endswith('@localhost')):
                    self.users.invalidateUser(user[0])
        return True

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

        self.projects.hide(projectId)
        self._generateConaryRcFile()
        return True

    @typeCheck(int)
    @requiresAdmin
    @private
    def unhideProject(self, projectId):
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        userId = repos.addUser(project.getLabel(), 'anonymous', 'anonymous')
        repos.addAcl(project.getLabel(), 'anonymous', None, None, False, False, False)

        self.projects.unhide(projectId)
        self._generateConaryRcFile()
        return True

    @typeCheck(int)
    @requiresAdmin
    @private
    def disableProject(self, projectId):
        self.projects.disable(projectId, self.cfg.reposPath)
        self._generateConaryRcFile()
        return True

    @typeCheck(int)
    @requiresAdmin
    @private
    def enableProject(self, projectId):
        self.projects.enable(projectId, self.cfg.reposPath)
        self._generateConaryRcFile()
        return True

    # user methods
    @typeCheck(int)
    @private
    def getUser(self, id):
        return self.users.get(id)

    @typeCheck(int)
    def getUserPublic(self, id):
        """Public version of getUser which takes out the private bits."""
        u = self.users.get(id)
        u['salt'] = ""
        u['passwd'] = ""
        return u

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
    def setUserLevel(self, userId, projectId, level):
        self._filterProjectAccess(projectId)
        if (self.auth.userId != userId) and (level == userlevels.USER):
            raise users.UserInduction()
        if self.projectUsers.onlyOwner(projectId, userId) and \
               (level != userlevels.OWNER):
            raise users.LastOwner
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
        return True

    @typeCheck(int)
    @private
    def getProjectsByUser(self, userId):
        cu = self.db.cursor()

        fqdnConcat = database.concat(self.db, "hostname", "'.'", "domainname")
        # audited for SQL injection.
        cu.execute("""SELECT %s, name, level
                      FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=?
                      ORDER BY level, name""" % fqdnConcat, userId)

        rows = []
        for r in cu.fetchall():
            rows.append([r[0], r[1], r[2]])
        return rows

    @typeCheck(str, str, str, str, str, str, bool)
    @private
    def registerNewUser(self, username, password, fullName, email,
                        displayEmail, blurb, active):
        if not ((list(self.authToken) == \
                [self.cfg.authUser, self.cfg.authPass]) or self.auth.admin \
                 or not self.cfg.adminNewUsers):
            raise PermissionDenied
        if active and not (list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin):
            raise PermissionDenied
        return self.users.registerNewUser(username, password, fullName, email,
                                          displayEmail, blurb, active)

    @typeCheck()
    @private
    def checkAuth(self):
        res = self.auth.getDict()
        # we can't marshall None, but Auth objects are smart enough to cope
        for key, val in self.auth.getDict().iteritems():
            if val is None:
                del res[key]
        return res

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
        repos.addNewAsciiPGPKey(project.getLabel(), username, keydata)
        return True

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

        self.removeUserAccount(userId)
        return True

    @typeCheck(int)
    @requiresAuth
    @private
    def filterLastAdmin(self, userId):
        """Raises an exception if the last site admin attempts to cancel their
        account, to protect against not having any admins at all."""
        if not self._isUserAdmin(userId):
            return
        cu = self.db.cursor()
        cu.execute("""SELECT userId
                          FROM UserGroups
                          LEFT JOIN UserGroupMembers
                          ON UserGroups.userGroupId =
                                 UserGroupMembers.userGroupId
                          WHERE userGroup='MintAdmin'""")
        if [x[0] for x in cu.fetchall()] == [userId]:
            # userId is admin, and there is only one admin => last admin
            raise LastAdmin("There are no more admin accounts. Your request "
                            "to close your account has been rejected to "
                            "ensure that at least one account is admin.")

    @typeCheck(int)
    @requiresAuth
    @private
    def removeUserAccount(self, userId):
        """Removes the user account from the authrepo and mint databases.
        Also removes the user from each project listed in projects.
        """
        if not self.auth.admin and userId != self.auth.userId:
            raise PermissionDenied
        self.filterLastAdmin(userId)
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
            cu.execute("DELETE FROM UserData where userId=?", userId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    @typeCheck(int)
    @requiresAuth
    @private
    def isUserAdmin(self, userId):
        return self._isUserAdmin(userId)

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
        r = cu.fetchall()
        if not r:
            raise database.ItemNotFound
        return r[0][0]

    @typeCheck(str)
    @private
    def confirmUser(self, confirmation):
        userId = self.users.confirm(confirmation)
        return userId

    @typeCheck(str)
    @private
    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

    @typeCheck(str, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setUserDataValue(self, username, name, value):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise PermissionDenied
        if name not in usertemplates.userPrefsTemplate:
            raise ParameterError("Undefined data entry")
        dataType = usertemplates.userPrefsTemplate[name][0]
        self.userData.setDataValue(userId, name, value, dataType)
        return True

    @typeCheck(str, str)
    @requiresAuth
    @private
    def getUserDataValue(self, username, name):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise PermissionDenied
        found, res = self.userData.getDataValue(userId, name)
        if found:
            return res
        return usertemplates.userPrefsTemplate[name][1]

    @typeCheck(str)
    @requiresAuth
    @private
    def getUserDataDefaulted(self, username):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise PermissionDenied

        cu = self.db.cursor()
        cu.execute("SELECT name FROM UserData WHERE userId=?", userId)
        res = usertemplates.userPrefsAttTemplate.keys()
        for ent in [x[0] for x in cu.fetchall() if x[0] in res]:
            res.remove(ent)
        return res

    @typeCheck(str)
    @requiresAuth
    @private
    def getUserDataDict(self, username):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise PermissionDenied
        return self.userData.getDataDict(userId)

    @typeCheck(int, str)
    @private
    def setPassword(self, userId, newPassword):
        if self.auth.admin or list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.userId == userId:
            username = self.users.get(userId)['username']

            for projectId, level in self.getProjectIdsByMember(userId):
                project = projects.Project(self, projectId)

                if not project.external:
                    authRepo = self._getProjectRepo(project)
                    authRepo.changePassword(project.getLabel(), username, newPassword)

            self.users.changePassword(username, newPassword)

            return True
        else:
            raise PermissionDenied

    @typeCheck(str, int, int)
    @requiresAuth
    @private
    def searchUsers(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms.
        NOTE: admins can see everything including unconfirmed users.
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        if self.auth and self.auth.admin:
            includeInactive = True
        else:
            includeInactive = False
        return self.users.search(terms, limit, offset, includeInactive)

    @typeCheck(str, int, int, int)
    @private
    def searchProjects(self, terms, modified, limit, offset):
        """
        Collect the results as requested by the search terms.
        NOTE: admins can see everything including hidden and fledgling
        projects regardless of the value of self.cfg.hideFledgling.
        @param terms: Search terms
        @param modified: Code for the lastModified filter
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        if self.auth and self.auth.admin:
            includeInactive = True
        else:
            includeInactive = False
        return self.projects.search(terms, modified, limit, offset, includeInactive)

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
    @requiresAdmin
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
        Collect a list of projects.
        NOTE: admins can see everything including hidden and fledgling
        projects regardless of the value of self.cfg.hideFledgling.
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return: a 2-tuple (list of projects, total number of projects)
        """
        if self.auth and self.auth.admin:
            includeInactive = True
        else:
            includeInactive = False
        return self.projects.getProjects(sortOrder, limit, offset, includeInactive), self.projects.getNumProjects(includeInactive)

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
        Collect a list of users.
        NOTE: admins can see everything including unconfirmed users.
        @param sortOrder: Order the users by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        if self.auth and self.auth.admin:
            includeInactive = True
        else:
            includeInactive = False
        return self.users.getUsers(sortOrder, limit, offset, includeInactive), self.users.getNumUsers(includeInactive)

    @typeCheck(int)
    @requiresAdmin
    @private
    def promoteUserToAdmin(self, userId):
        """
        Given a userId, will attempt to promote that user to an
        administrator (i.e. make a member of the MintAdmin User Group).

        NOTE: if the MintAdmin UserGroup doesn't exist, it will be created
        as a side effect.

        @param userId: the userId to promote
        """
        mintAdminId = self.userGroups.getMintAdminId()
        if self._isUserAdmin(userId):
            raise UserAlreadyAdmin

        cu = self.db.cursor()
        cu.execute('INSERT INTO UserGroupMembers VALUES(?, ?)',
                mintAdminId, userId)
        self.db.commit()
        return True

    @typeCheck(int)
    @requiresAdmin
    @private
    def demoteUserFromAdmin(self, userId):
        """
        Given a userId, will attempt to demote that user from administrator
        If this user is the last administrator, this function will balk.
        @param userId: the userId to promote
        """
        # refuse to demote self. this ensures there will always be at least one
        if userId == self.auth.userId:
            raise AdminSelfDemotion

        mintAdminId = self.userGroups.getMintAdminId()
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM UserGroupMembers WHERE userGroupId=?",
                   mintAdminId)

        cu.execute("""DELETE FROM UserGroupMembers WHERE userId=?
                          AND userGroupId=?""", userId, mintAdminId)
        self.db.commit()
        return True

    @typeCheck()
    @private
    def getNews(self):
        return self.newsCache.getNews()

    @typeCheck()
    @private
    def getNewsLink(self):
        return self.newsCache.getNewsLink()

    @typeCheck()
    @private
    def getUseItIcons(self):
        return self.useit.getIcons()

    @typeCheck(int)
    @private
    @requiresAdmin
    def deleteUseItIcon(self, itemId):
        return self.useit.deleteIcon(itemId)

    @typeCheck(int, str, str)
    @private
    @requiresAdmin
    def addUseItIcon(self, itemId, name, link):
        if name and link:
            return self.useit.addIcon(itemId, name, link)
        else:
            return False

    @typeCheck(str, str, str, str, int, str, str)
    @requiresAdmin
    @private
    def addSpotlightItem(self, title, text, link, logo, showArchive, startDate,
                         endDate):
         return self.spotlight.addItem(title, text, link, logo,
                                               showArchive, startDate, endDate)

    @typeCheck()
    @private
    def getSpotlightAll(self):
        return self.spotlight.getAll()

    @typeCheck()
    @private
    def getCurrentSpotlight(self):
        return self.spotlight.getCurrent()

    @typeCheck(int)
    @private
    @requiresAdmin
    def deleteSpotlightItem(self, itemId):
        return self.spotlight.deleteItem(itemId)

    @typeCheck(str, str, int)
    @private
    @requiresAdmin
    def addFrontPageSelection(self, name, link, rank):
        return self.selections.addItem(name, link, rank)

    @typeCheck(int)
    @private
    @requiresAdmin
    def deleteFrontPageSelection(self, itemId):
        return self.selections.deleteItem(itemId)

    @typeCheck()
    @private
    def getFrontPageSelection(self):
        return self.selections.getAll()
    #
    # LABEL STUFF
    #
    @typeCheck(int)
    @private
    def getDefaultProjectLabel(self, projectId):
        self._filterProjectAccess(projectId)
        return self.labels.getDefaultProjectLabel(projectId)

    @typeCheck(int, bool, ((str, type(None)),), ((str, type(None)),))
    @private
    def getLabelsForProject(self, projectId, overrideAuth, newUser, newPass):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        self._filterProjectAccess(projectId)
        return self.labels.getLabelsForProject(projectId, overrideAuth, newUser, newPass)

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
        self.labels.editLabel(labelId, label, url, username, password)
        if self.cfg.createConaryRcFile:
            self._generateConaryRcFile()

        return True

    @typeCheck(int, int)
    @requiresAuth
    @private
    def removeLabel(self, projectId, labelId):
        self._filterProjectAccess(projectId)
        return self.labels.removeLabel(projectId, labelId)

    @typeCheck(str)
    @private
    def versionIsExternal(self, versionStr):
        cu = self.db.cursor()

        try:
            hostname = ('/' + versionStr.split('/')[1]).split('@')[0]
        except:
            # All exceptions at this point will be string parsing errors.
            raise ItemNotFound

        cu.execute("SELECT projectId FROM Labels WHERE label LIKE ?",
                   "%s%%" % hostname)

        res = cu.fetchone()

        if not res:
            # FIXME: this needs to be an exception condition to prevent
            # rBO making non-hosted content appear as part of the site.
            return True

        projectId = res[0]

        # remember to filter access to hidden projects
        # we couldn't do it right away because we didn't have the projectId
        self._filterProjectAccess(projectId)

        cu.execute("SELECT external FROM Projects WHERE projectId=?",
                   projectId)

        res = cu.fetchone()

        if not res:
            return True

        return bool(res[0])

    def _generateConaryRcFile(self):
        if not self.cfg.createConaryRcFile:
            return
        cu = self.db.cursor()
        res = cu.execute("""SELECT ProjectId from Projects 
                            WHERE hidden=0 AND disabled=0""")
        projs = cu.fetchall()
        repoMaps = {}
        for x in projs:
            repoMaps.update(self.labels.getLabelsForProject(x[0])[1])
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        f = open(fname, 'w')
        for host, url in repoMaps.iteritems():
            f.write('repositoryMap %s %s\n' % (host, url))
        f.close()
        util.mkdirChain(os.path.join(self.cfg.dataPath, 'run'))
        util.copyfile(fname, self.cfg.conaryRcFile)
        os.unlink(fname)
        os.chmod(self.cfg.conaryRcFile, 0644)

    #
    # BUILD STUFF
    #
    @typeCheck(int)
    @private
    def getBuildsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return [x for x in self.builds.iterBuildsForProject(projectId)]

    @typeCheck(int, int)
    @private
    def getPublishedReleaseList(self, limit, offset):
        return self.publishedReleases.getPublishedReleaseList(limit, offset)

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
    def getBuild(self, buildId):
        self._filterBuildAccess(buildId)
        return self.builds.get(buildId)

    @typeCheck(int, str, bool)
    @requiresAuth
    @private
    def newBuild(self, projectId, productName):
        self._filterProjectAccess(projectId)
        buildId = self.builds.new(projectId = projectId,
                                      name = productName)

        self.buildData.setDataValue(buildId, 'jsversion',
                                      jsversion.getDefaultVersion(),
                                      data.RDT_STRING)

        return buildId

    @typeCheck(int)
    @requiresAuth
    def deleteBuild(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        cu = self.db.cursor()
        cu.execute("SELECT filename FROM BuildFiles WHERE buildId=?",
                   buildId)
        for fileName in [x[0] for x in cu.fetchall()]:
            try:
                os.unlink(fileName)
            except:
                print >> sys.stderr, "Couldn't delete related file: %s" % \
                      fileName
                sys.stderr.flush()
        self.builds.deleteBuild(buildId)
        return True

    @typeCheck(int, dict)
    @requiresAuth
    @private
    def updateBuild(self, buildId, valDict):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        if len(valDict):
            valDict.update({'timeUpdated': time.time(),
                            'updatedBy':   self.auth.userId})
            return self.builds.update(buildId, **valDict)

    # build data calls
    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setBuildDataValue(self, buildId, name, value, dataType):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        return self.buildData.setDataValue(buildId, name, value, dataType)

    @typeCheck(int, str)
    @private
    def getBuildDataValue(self, buildId, name):
        self._filterBuildAccess(buildId)
        return self.buildData.getDataValue(buildId, name)

    @typeCheck(int)
    @private
    def getBuildDataDict(self, buildId):
        self._filterBuildAccess(buildId)
        return self.buildData.getDataDict(buildId)

    #
    # published releases 
    #
    @typeCheck(int)
    @requiresAuth
    def newPublishedRelease(self, projectId):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        timeCreated = time.time()
        createdBy = self.auth.userId
        return self.publishedReleases.new(projectId = projectId,
                timeCreated = timeCreated, createdBy = createdBy)

    @typeCheck(int)
    def getPublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        return self.publishedReleases.get(pubReleaseId)

    @typeCheck(int, dict)
    @requiresAuth
    @private
    def updatePublishedRelease(self, pubReleaseId, valDict):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        if self.publishedReleases.isPublishedReleaseFinalized(pubReleaseId):
            raise PublishedReleaseFinalized
        if len(valDict):
            valDict.update({'timeUpdated': time.time(),
                            'updatedBy': self.auth.userId})
            return self.publishedReleases.update(pubReleaseId, **valDict)

    @typeCheck(int, dict)
    @requiresAuth
    @private
    def finalizePublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        if not len(self.publishedReleases.getBuilds(pubReleaseId)):
            raise PublishedReleaseEmpty
        if self.publishedReleases.isPublishedReleaseFinalized(pubReleaseId):
            raise PublishedReleaseFinalized
        valDict = {'timePublished': time.time(),
                   'publishedBy': self.auth.userId}
        return self.publishedReleases.update(pubReleaseId, **valDict)

    @typeCheck(int)
    @requiresAuth
    def deletePublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        self.publishedReleases.delete(pubReleaseId)
        return True

    @typeCheck(int)
    @private
    def isPublishedReleaseFinalized(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        return self.publishedReleases.isPublishedReleaseFinalized(pubReleaseId)

    @typeCheck(int)
    @requiresAuth
    @private
    def getUnpublishedBuildsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.builds.getUnpublishedBuilds(projectId)

    @typeCheck(int)
    @private
    def getBuildsForPublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        return self.publishedReleases.getBuilds(pubReleaseId)

    @typeCheck(int)
    @private
    def getPublishedReleasesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        finalizedOnly = False
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            finalizedOnly = True
        return self.publishedReleases.getPublishedReleasesByProject(projectId,
                finalizedOnly)

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
    def getBuildTrove(self, buildId):
        self._filterBuildAccess(buildId)
        return self.builds.getTrove(buildId)

    @typeCheck(int, str, str, str)
    @requiresAuth
    @private
    def setBuildTrove(self, buildId, troveName, troveVersion, troveFlavor):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        return self.builds.setTrove(buildId, troveName,
                                                 troveVersion,
                                                 troveFlavor)

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setBuildDesc(self, buildId, desc):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        self.builds.update(buildId, description = desc)
        return True

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setBuildName(self, buildId, name):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        self.builds.update(buildId, name = name)
        return True

    @typeCheck(int, int, bool)
    @requiresAuth
    @private
    def setBuildPublished(self, buildId, pubReleaseId, published):
        self._filterBuildAccess(buildId)
        buildData = self.builds.get(buildId, fields=['projectId'])
        if not self._checkProjectAccess(buildData['projectId'],
                [userlevels.OWNER]):
            raise PermissionDenied()
        if not self.publishedReleases.publishedReleaseExists(pubReleaseId):
            raise PublishedReleaseMissing()
        if self.isPublishedReleaseFinalized(pubReleaseId):
            raise PublishedReleaseFinalized()
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if published and not self.getBuildFilenames(buildId):
            raise BuildEmpty()
        if published and self.builds.getPublished(buildId):
            raise BuildPublished()
        pubReleaseId = published and pubReleaseId or None
        return self.updateBuild(buildId, {'pubReleaseId': pubReleaseId })

    @typeCheck(int)
    @private
    def getBuildPublished(self, buildId):
        return self.builds.getPublished(buildId)

    @typeCheck(int)
    @private
    def getBuildType(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        cu = self.db.cursor()
        cu.execute("SELECT buildType FROM Builds WHERE buildId = ?",
                buildId)
        return cu.fetchone()[0]

    @typeCheck(int, int)
    @requiresAuth
    @private
    def setBuildType(self, buildId, buildType):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        cu = self.db.cursor()
        cu.execute("UPDATE Builds SET buildType = ? WHERE buildId = ?",
                buildType, buildId)
        self.db.commit()
        return True

    @typeCheck()
    @private
    def getAvailableBuildTypes(self):
        if self.cfg.visibleBuildTypes:
            return self.cfg.visibleBuildTypes
        else:
            return []

    @typeCheck(int)
    @requiresAuth
    def startImageJob(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        found, jsVer = self.buildData.getDataValue(buildId, 'jsversion')
        if not found:
            raise JobserverVersionMismatch('No job server version available.')
        if jsVer not in jsversion.getVersions():
            raise JobserverVersionMismatch

        cu = self.db.cursor()

        cu.execute("""SELECT jobId, status FROM Jobs
                          WHERE buildId=? AND groupTroveId IS NULL""",
                   buildId)
        r = cu.fetchall()
        if len(r) == 0:
            retval = self.jobs.new(buildId = buildId,
                                   userId = self.auth.userId,
                                   status = jobstatus.WAITING,
                                   statusMessage = self.getJobWaitMessage(0),
                                   timeSubmitted = time.time(),
                                   timeStarted = 0,
                                   timeFinished = 0)
            cu.execute('SELECT troveFlavor FROM Builds WHERE buildId=?',
                       buildId)
            flavorString = cu.fetchone()[0]
            flavor = deps.ThawFlavor(flavorString)
            arch = "1#" + flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
            cu.execute("INSERT INTO JobData VALUES(?, 'arch', ?, 0)", retval,
                       arch)
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                # delete any files in the BuildFiles table prior to regeneration
                cu.execute("DELETE FROM BuildFiles WHERE buildId = ?",
                        buildId)

                # getJobWaitMessage orders by timeSubmitted, so update must
                # occur in two steps
                self.jobs.update(jobId, status = jobstatus.WAITING,
                                 timeSubmitted= time.time(), timeStarted = 0,
                                 timeFinished = 0,
                                 owner = None)
                msg = self.getJobWaitMessage(jobId)
                self.jobs.update(jobId, statusMessage = msg)
                retval = jobId

        return retval

    @typeCheck(int, str)
    @private
    @requiresAuth
    def startCookJob(self, groupTroveId, arch):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        if not self.listGroupTroveItemsByGroupTrove(groupTroveId):
            raise GroupTroveEmpty

        cu = self.db.cursor()
        cu.execute("""SELECT jobId, status FROM Jobs
                          WHERE groupTroveId=? AND buildId IS NULL""",
                   groupTroveId)
        r = cu.fetchall()
        if len(r) == 0:
            retval = self.jobs.new(groupTroveId = groupTroveId,
                                   userId = self.auth.userId,
                                   status = jobstatus.WAITING,
                                   statusMessage = self.getJobWaitMessage(0),
                                   timeSubmitted = time.time(),
                                   timeStarted = 0,
                                   timeFinished = 0)
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                # getJobWaitMessage orders by timeStarted, so update must
                # occur in two steps
                self.jobs.update(jobId, status = jobstatus.WAITING,
                                 timeSubmitted = time.time(),
                                 timeStarted = 0,
                                 timeFinished = 0,
                                 owner = None)
                msg = self.getJobWaitMessage(jobId)
                self.jobs.update(jobId, statusMessage = msg)
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

        cu.execute("SELECT userId, buildId, groupTroveId, status,"
                   "  statusMessage, timeSubmitted, timeStarted, "
                   "  timeFinished FROM Jobs "
                   " WHERE jobId=?", jobId)

        p = cu.fetchone()
        if not p:
            raise jobs.JobMissing

        dataKeys = ['userId', 'buildId', 'groupTroveId', 'status',
                    'statusMessage', 'timeSubmitted', 'timeStarted',
                    'timeFinished']
        data = {}
        for i, key in enumerate(dataKeys):
            # these keys can be NULL from the db
            if key in ('buildId', 'groupTroveId'):
                if p[i] is None:
                    data[key] = 0
                else:
                    data[key] = p[i]
            else:
                data[key] = p[i]
        # ensure waiting job messages get updated
        if data['status'] == jobstatus.WAITING:
            data['statusMessage'] = self.getJobWaitMessage(jobId)
        return data

    @typeCheck()
    @requiresAuth
    @private
    def getJobIds(self):
        cu = self.db.cursor()

        cu.execute("SELECT jobId FROM Jobs ORDER BY timeSubmitted")

        return [x[0] for x in cu.fetchall()]

    @typeCheck(bool)
    @requiresAuth
    def listActiveJobs(self, filter):
        """List the jobs in the job queue.
        @param filter: If True it will only show running or waiting jobs.
          If False it will show all jobs for past 24 hours plus waiting jobs.
        @return: list of jobIds"""
        cu = self.db.cursor()

        if filter:
            cu.execute("""SELECT jobId FROM Jobs
                              WHERE status IN (?, ?) ORDER BY timeSubmitted""",
                       jobstatus.WAITING, jobstatus.RUNNING)
        else:
            cu.execute("""SELECT jobId FROM Jobs WHERE timeSubmitted > ?
                              OR status IN (?, ?) ORDER BY timeSubmitted""",
                       time.time() - 86400, jobstatus.WAITING,
                       jobstatus.RUNNING)

        ret = []
        for x in cu.fetchall():
            job = self.jobs.get(x[0])
            hostname = self.getJobDataValue(x[0], 'hostname')
            if hostname[0]:
                job['hostname'] = hostname[1]
            else:
                job['hostname'] = "None"
            ret.append(job)
        return ret

    @typeCheck((list, str), (dict, (list, int)), str)
    @requiresAuth
    @private
    def startNextJob(self, archTypes, jobTypes, jobserverVersion):
        """Select a job to execute from the list of pending jobs
        @param archTypes: list of frozen flavors. only specify arch flags.
        @param jobTypes: dict. keys are the kinds of jobs.
          values are lists of valid types for that job.
        @param jobserverVersion: string. version of the job server.
        @return: jobId of job to execute, or 0 for no job.
        """
        from mint import cooktypes
        from mint import buildtypes
        # scrub archTypes and jobTypes.
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")
        for arch in archTypes:
            if arch not in ("1#x86", "1#x86_64"):
                raise ParameterError("Not a legal architecture")

        buildTypes = jobTypes.get('buildTypes', [])
        cookTypes = jobTypes.get('cookTypes', [])

        if sum([(x not in buildtypes.TYPES) \
                for x in buildTypes]):
            raise ParameterError("Not a legal Build Type")

        if sum([(x != cooktypes.GROUP_BUILDER) for x in cookTypes]):
            raise ParameterError("Not a legal Cook Type")

        if jobserverVersion not in jsversion.getVersions():
            raise ParameterError("Not a legal job server version: %s" % jobserverVersion)
        # client asked for nothing, client gets nothing.
        if not (buildTypes or cookTypes) or (not archTypes):
            return 0

        # the pid would suffice, except that fails to be good enough
        # if multiple web servers use one database backend.
        ownerId = (os.getpid() << 47) + random.randint(0, (2 << 47) - 1)

        cu = self.db.transaction()

        cu.execute("""UPDATE Jobs SET owner=?
                          WHERE owner IS NULL AND status=?""",
                   ownerId, jobstatus.WAITING)

        self.db.commit()

        archTypeQuery = archTypes and "(%s)" % \
                        ', '.join(['?' for x in archTypes]) or ''

        buildTypeQuery = buildTypes and "(%s)" % \
                        ', '.join(['?' for x in buildTypes]) or ''

        # at least one of buildTypes or cookTypes will be defined,
        # or this code would have already bailed out.
        if not buildTypes:
            #client wants only cooks
            query = """SELECT Jobs.jobId FROM Jobs
                       LEFT JOIN JobData
                           ON Jobs.jobId=JobData.jobId
                       WHERE status=? AND JobData.name='arch'
                           AND Jobs.buildId IS NULL
                           AND owner=?
                           AND JobData.value IN %s
                       ORDER BY timeSubmitted
                       LIMIT 1""" % archTypeQuery
            cu.execute(query, jobstatus.WAITING, ownerId, *archTypes)
        elif not cookTypes:
            # client wants only image jobs
            query = """SELECT Jobs.jobId FROM Jobs
                       LEFT JOIN JobData
                           ON Jobs.jobId=JobData.jobId
                               AND JobData.name='arch'
                       LEFT JOIN Builds
                           ON Builds.buildId=Jobs.buildId
                       LEFT JOIN BuildData
                           ON BuildData.buildId=Jobs.buildId
                               AND BuildData.name='jsversion'
                       WHERE status=?
                           AND Jobs.groupTroveId IS NULL
                           AND owner=?
                           AND BuildData.value=?
                           AND JobData.value IN %s
                           AND Builds.buildType IN %s
                       ORDER BY timeSubmitted
                       LIMIT 1""" % (archTypeQuery, buildTypeQuery)
            cu.execute(query, jobstatus.WAITING, ownerId, jobserverVersion,
                       *(archTypes + buildTypes))
        else:
            # client wants both cook and image jobs
            query = """SELECT Jobs.jobId FROM Jobs
                       LEFT JOIN JobData
                           ON Jobs.jobId=JobData.jobId AND JobData.name='arch'
                       LEFT JOIN Builds
                           ON Builds.buildId=Jobs.buildId
                       LEFT JOIN BuildData
                           ON BuildData.buildId=Jobs.buildId
                               AND BuildData.name='jsversion'
                       WHERE status=? AND owner=?
                           AND ((BuildData.value=? AND
                               Builds.buildType IN %s) OR
                                (groupTroveId IS NOT NULL))
                           AND JobData.value IN %s
                       ORDER BY timeSubmitted
                       LIMIT 1""" % (buildTypeQuery, archTypeQuery)

            cu.execute(query, jobstatus.WAITING, ownerId, jobserverVersion,
                       *(buildTypes + archTypes))

        res = cu.fetchone()

        if not res:
            jobId = 0
        else:
            jobId = res[0]
            cu.execute("""UPDATE Jobs
                              SET status=?, statusMessage=?, timeStarted=?
                              WHERE jobId=?""",
                       jobstatus.RUNNING, 'Starting', time.time(), jobId)
            if self.req:
                self.jobData.setDataValue(jobId, "hostname", self.req.connection.remote_ip, data.RDT_STRING)
            cu.execute("SELECT jobId FROM Jobs WHERE status=?",
                       jobstatus.WAITING)
            # this is done inside the job lock. there is a small chance of race
            # condition, but the consequence would be that jobs might not
            # reflect the correct number on admin page. if this proves to be
            # too costly, move it outside the lock
            for ordJobId in [x[0] for x in cu.fetchall()]:
                cu.execute("UPDATE Jobs SET statusMessage=? WHERE jobId=?",
                           self.getJobWaitMessage(ordJobId), ordJobId)

        cu.execute("UPDATE Jobs SET owner=NULL WHERE owner=? AND status=?",
                   ownerId, jobstatus.WAITING)
        self.db.commit()

        return jobId


    @typeCheck(int)
    @requiresAuth
    @private
    def getJobIdForBuild(self, buildId):
        self._filterBuildAccess(buildId)
        cu = self.db.cursor()

        cu.execute("SELECT jobId FROM Jobs WHERE buildId=?", buildId)
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
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied

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

    @typeCheck()
    @private
    @requiresAdmin
    def getJobServerStatus(self):
        # Handling the job server in this manner is temporary
        # This is only useful in an appliance context at this time.
        pipeFD = os.popen("sudo /sbin/service multi-jobserver status")
        res = pipeFD.read()
        pipeFD.close()
        return res

    @typeCheck(int, (list, (list, str)))
    @requiresAuth
    @private
    def setBuildFilenames(self, buildId, filenames):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()

        cu = self.db.transaction()
        try:
            cu.execute("DELETE FROM BuildFiles WHERE buildId=?", buildId)
            for idx, file in enumerate(filenames):
                fileName, title = file
                cu.execute("INSERT INTO BuildFiles VALUES (NULL, ?, ?, ?, ?)",
                           buildId, idx, fileName, title)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    @typeCheck(int)
    @private
    def getBuildFilenames(self, buildId):
        self._filterBuildAccess(buildId)
        cu = self.db.cursor()
        cu.execute("SELECT fileId, filename, title FROM BuildFiles WHERE buildId=? ORDER BY idx", buildId)

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
        self._filterBuildFileAccess(fileId)
        cu = self.db.cursor()
        cu.execute("SELECT buildId, idx, filename, title FROM BuildFiles WHERE fileId=?", fileId)

        r = cu.fetchone()
        if r:
            return r[0], r[1], r[2], r[3]
        else:
            raise jobs.FileMissing

    @typeCheck(int, ((str, unicode),))
    @requiresAuth
    def getTroveVersionsByArch(self, projectId, troveNameWithLabel):
        self._filterProjectAccess(projectId)

        def dictByArch(versionList, trove):
            archMap = {}
            for v, flavors in reversed(sorted(versionList[trove].items())):
                for f in flavors:
                    # skip broken groups that don't have an instruction set
                    if deps.DEP_CLASS_IS not in f.members:
                        continue
                    arch = f.members[deps.DEP_CLASS_IS].members.keys()[0]

                    l = archMap.setdefault(arch, [])
                    l.append((v.asString(), v.freeze(), f.freeze()))
            return archMap

        project = projects.Project(self, projectId)
        trove, label = troveNameWithLabel.split('=')
        label = versions.Label(label)
        version = None
        flavor = None

        cfg = project.getConaryConfig()

        nc = conaryclient.ConaryClient(cfg).getRepos()
        versionList = nc.getTroveVersionList(cfg.repositoryMap.keys()[0], {trove: None})

        # group trove by major architecture
        return dictByArch(versionList, trove)

    def _getConaryClient(self):
        cfg = conarycfg.ConaryConfiguration(readConfigFiles = False)
        if os.path.exists(os.path.join(self.cfg.dataPath, "config", "conaryrc")):
            cfg.read(os.path.join(self.cfg.dataPath, "config", "conaryrc"))
        return conaryclient.ConaryClient(cfg)

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getAllTroveLabels(self, projectId, serverName, troveName):
        self._filterProjectAccess(projectId)

        project = projects.Project(self, projectId)
        cfg = project.getConaryConfig()
        nc = conaryclient.ConaryClient(cfg).getRepos()

        troves = nc.getAllTroveLeaves(str(serverName), {str(troveName): None})[troveName]
        return list(set(str(x.branch().label()) for x in troves))

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getTroveVersions(self, projectId, labelStr, troveName):
        self._filterProjectAccess(projectId)

        project = projects.Project(self, projectId)
        cfg = project.getConaryConfig()
        nc = conaryclient.ConaryClient(cfg).getRepos()

        troves = nc.getTroveVersionsByLabel({str(troveName): {versions.Label(str(labelStr)): None}})[troveName]
        versionDict = dict((x.freeze(), [y for y in troves[x]]) for x in troves)
        versionList = sorted(versionDict.keys(), reverse = True)

        # insert a tuple of (flavor differences, full flavor) into versionDict
        strFlavor = lambda x: str(x) and str(x) or '(no flavor)'
        for v, fList in versionDict.items():
            diffDict = deps.flavorDifferences(fList)
            versionDict[v] = [(not diffDict[x].isEmpty() and str(diffDict[x]) or strFlavor(x), str(x)) for x in fList]

        return [versionDict, versionList]

    @typeCheck(int)
    @requiresAuth
    def getGroupTroves(self, projectId):
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)

        nc = self._getProjectRepo(project)
        label = versions.Label(project.getLabel())
        troves = nc.troveNamesOnServer(label.getHost())

        troves = sorted(trove for trove in troves if 
            (trove.startswith('group-') or 
             trove.startswith('fileset-')) and
            not trove.endswith(':source'))
        return troves

    # XXX refactor to getJobStatus instead of two functions
    @typeCheck(int)
    @requiresAuth
    def getBuildStatus(self, buildId):
        self._filterBuildAccess(buildId)

        build = builds.Build(self, buildId)
        job = build.getJob()

        if not job:
            return {'status'  : jobstatus.NOJOB,
                    'message' : jobstatus.statusNames[jobstatus.NOJOB],
                    'queueLen': 0}
        else:
            status = job.getStatus()
            return {'status'  : job.getStatus(),
                    'message' : (status == jobstatus.WAITING \
                                 and self.getJobWaitMessage(job.id) \
                                 or  job.getStatusMessage()),
                    'queueLen': self._getJobQueueLength(job.getId())}

    @typeCheck(int)
    @requiresAuth
    def getJobStatus(self, jobId):
        self._filterJobAccess(jobId)

        job = jobs.Job(self, jobId)

        if not job:
            return {'status'  : jobstatus.NOJOB,
                    'message' : jobstatus.statusNames[jobstatus.NOJOB],
                    'queueLen': 0}
        else:
            status = job.getStatus()
            return {'status'  : job.getStatus(),
                    'message' : (status == jobstatus.WAITING \
                                 and self.getJobWaitMessage(job.id) \
                                 or  job.getStatusMessage()),
                    'queueLen': self._getJobQueueLength(jobId)}

    def _getJobQueueLength(self, jobId):
        self._filterJobAccess(jobId)
        cu = self.db.cursor()
        if jobId:
            cu.execute("SELECT status FROM Jobs WHERE jobId=?", jobId)
            res = cu.fetchall()
            if not res:
                raise Database.ItemNotFound("No job with that Id")
            # job is not in the queue
            if res[0][0] != jobstatus.WAITING:
                return 0
            cu.execute("""SELECT COUNT(*) FROM Jobs
                              WHERE timeSubmitted <
                                  (SELECT timeSubmitted FROM Jobs
                                      WHERE jobId = ?)
                              AND status = ?""", jobId, jobstatus.WAITING)
        else:
            cu.execute("SELECT COUNT(*) FROM Jobs WHERE status = ?",
                       jobstatus.WAITING)
        return cu.fetchone()[0]


    # session management
    @private
    def loadSession(self, sid):
        return self.sessions.load(sid)

    @private
    def saveSession(self, sid, data):
        self.sessions.save(sid, data)
        return True

    @private
    def deleteSession(self, sid):
        self.sessions.delete(sid)
        return True

    @private
    def cleanupSessions(self):
        self.sessions.cleanup()
        return True

    # group trove specific functions
    @private
    @typeCheck()
    def cleanupGroupTroves(self):
        self.groupTroves.cleanup()

    def _resolveRedirects(self, groupTroveId, trvName, trvVersion, trvFlavor):
        # get the repo object
        projectId = self.getGroupTrove(groupTroveId)['projectId']
        project = projects.Project(self, projectId)

        # external projects follow what's in the labels table,
        # internal projects follow the configuration:
        cfg = project.getConaryConfig()

        res = {}
        for arch, flavor in stockFlavors.items():
            flavor = deps.ThawFlavor(arch)

            cfg.flavor = [flavor]
            cfg.buildFlavor = flavor

            cfg.root = cfg.dbPath = ":memory:"
            cfg.initializeFlavors()

            conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
            if os.path.exists(conarycfgFile):
                cfg.read(conarycfgFile)

            cclient = conaryclient.ConaryClient(cfg)
            repos = cclient.getRepos()

            try:
                trvList = repos.findTrove(\
                    None, (trvName, trvVersion, deps.parseFlavor(trvFlavor)),
                    cfg.buildFlavor, bestFlavor=True)

                res[arch] = []
                for lName, lVer, lFlav in trvList:
                    trv = repos.getTrove(lName, lVer, lFlav)

                    if trv.isRedirect():
                        uJob = cclient.updateChangeSet(\
                            [(lName, (None, None),
                              (lVer, lFlav), True)], resolveDeps = False)[0]
                        res[arch].extend([(x[0], str(x[2][0]), str(x[2][1])) \
                                    for x in uJob.getJobs()[0]])
            except TroveNotFound:
                pass
        return res

    def _getRecipe(self, groupTroveId):
        groupTrove = self.groupTroves.get(groupTroveId)
        groupTroveItems = self.groupTroveItems.listByGroupTroveId(groupTroveId)
        removedComponents = self.groupTroveRemovedComponents.list(groupTroveId)

        recipe = ""
        name = ''.join((string.capwords(
            ' '.join(groupTrove['recipeName'].split('-')))).split(' '))
        indent = 4 * " "

        recipe += "class " + name + "(GroupRecipe):\n"
        recipe += indent + "name = '%s'\n" % groupTrove['recipeName']
        recipe += indent + "version = '%s'\n\n" % groupTrove['upstreamVersion']
        recipe += indent + "autoResolve = %s\n\n" % \
                  str(groupTrove['autoResolve'])
        recipe += indent + 'def setup(r):\n'

        indent = 8 * " "
        recipeLabels = self.getGroupTroveLabelPath(groupTroveId)
        recipe += indent + "r.setLabelPath(%s)\n" % \
                  str(recipeLabels).split('[')[1].split(']')[0]

        if removedComponents:
            recipe += indent + "r.removeComponents(('" + \
                      "', '".join(removedComponents) + "'))\n"

        for trv in groupTroveItems:
            ver = trv['versionLock'] and trv['trvVersion'] or trv['trvLabel']

            # XXX HACK to use the "fancy-flavored" group troves from
            # conary.rpath.com
            if trv['trvName'].startswith('group-') and \
                   trv['trvLabel'].startswith('conary.rpath.com@'):
                recipe += indent + "if Arch.x86_64:\n"
                recipe += (12 * " ") + "r.add('" + trv['trvName'] + "', '" + \
                          ver + "', 'is:x86(i486,i586,i686) x86_64', " + \
                          "groupName = '" + trv['subGroup'] +"')\n"
                recipe += indent + "else:\n" + (4 * " ")
            recipe += indent + "r.add('" + trv['trvName'] + "', '" + ver \
                      + "', '" + trv['trvFlavor'] + "', groupName = '" + \
                      trv['subGroup'] +"')\n"

            # properly support redirected troves, by explicitly including them
            for arch, redirList in self._resolveRedirects(groupTroveId, trv['trvName'], ver, trv['trvFlavor']).iteritems():
                if redirList:
                    recipe += indent + "if Arch.%s:\n" % arch.split("#")[1]
                    for rName, rVer, rFlav in redirList:
                        recipe += (12 * " ") + "r.add('%s', '%s', '%s', groupName = '%s')\n" % \
                            (rName, rVer, rFlav, trv['subGroup'])
        return recipe

    @typeCheck(int)
    @private
    @requiresAuth
    def getGroupTroveLabelPath(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied

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
    @requiresAuth
    def getRecipe(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self._getRecipe(groupTroveId)

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveAutoResolve(self, groupTroveId, resolve):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroves.setAutoResolve(groupTroveId, resolve)
        return True

    @private
    @requiresAuth
    @typeCheck(int)
    def listGroupTrovesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroves.listGroupTrovesByProject(projectId)

    @private
    @typeCheck(int, str, str, str, bool)
    @requiresAuth
    def createGroupTrove(self, projectId, recipeName, upstreamVersion,
                         description, autoResolve):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        creatorId = self.users.getIdByColumn("username", self.authToken[0])
        return self.groupTroves.createGroupTrove(projectId, creatorId,
                                                 recipeName, upstreamVersion,
                                                 description, autoResolve)

    @typeCheck(int)
    @requiresAuth
    def getGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroves.get(groupTroveId)

    @private
    @typeCheck(int)
    @requiresAuth
    def deleteGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroves.delGroupTrove(groupTroveId)

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveDesc(self, groupTroveId, description):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroves.update(groupTroveId, description = description,
                                timeModified = time.time())
        return True

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveUpstreamVersion(self, groupTroveId, vers):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroves.setUpstreamVersion(groupTroveId, vers)
        return True

    #group trove component reomval specific functions
    @private
    @typeCheck(int)
    @requiresAuth
    def listGroupTroveRemovedComponents(self, groupTroveId):
        return self.groupTroveRemovedComponents.list(groupTroveId)

    @private
    @typeCheck(int, (list, str))
    @requiresAuth
    def removeGroupTroveComponents(self, groupTroveId, components):
        self.groupTroveRemovedComponents.removeComponents(groupTroveId,
                                                          components)
        return True

    @private
    @typeCheck(int, (list, str))
    @requiresAuth
    def allowGroupTroveComponents(self, groupTroveId, components):
        self.groupTroveRemovedComponents.allowComponents(groupTroveId,
                                                         components)
        return True

    @private
    @typeCheck(int, (list, str))
    @requiresAuth
    def setGroupTroveRemovedComponents(self, groupTroveId, components):
        self.groupTroveRemovedComponents.setRemovedComponents(groupTroveId,
                                                              components)
        return True

    #group trove item specific functions

    @private
    @typeCheck(int)
    @requiresAuth
    def listGroupTroveItemsByGroupTrove(self, groupTroveId):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroveItems.listByGroupTroveId(groupTroveId)

    @private
    @typeCheck(int, str, str, str)
    @requiresAuth
    def troveInGroupTroveItems(self, groupTroveId, name, version, flavor):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroveItems.troveInGroupTroveItems( \
            groupTroveId, name, version, flavor)

    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemVersionLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroveItems.setVersionLock(groupTroveItemId, lock)
        return self.groupTroveItems.get(groupTroveItemId)

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemUseLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroveItems.setUseLock(groupTroveItemId, lock)
        return lock

    @private
    @typeCheck(int, bool)
    @requiresAuth
    def setGroupTroveItemInstSetLock(self, groupTroveItemId, lock):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroveItems.setInstSetLock(groupTroveItemId, lock)
        return lock

    @typeCheck(int, str, str, str, str, bool, bool, bool)
    @requiresAuth
    def addGroupTroveItem(self, groupTroveId, trvName, trvVersion, trvFlavor,
                     subGroup, versionLock, useLock, instSetLock):
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        creatorId = self.users.getIdByColumn("username", self.authToken[0])
        return self.groupTroveItems.addTroveItem(groupTroveId, creatorId,
                                                 trvName, trvVersion,
                                                 trvFlavor, subGroup,
                                                 versionLock, useLock,
                                                 instSetLock)

    @requiresAuth
    @typeCheck(int, str, str, str, str, bool, bool, bool)
    @requiresAuth
    def addGroupTroveItemByProject(self, groupTroveId, trvName, projectName,
                                   trvFlavor, subGroup, versionLock, useLock,
                                   instSetLock):
        projectId = self.projects.getProjectIdByHostname(projectName)
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        groupTrove = grouptrove.GroupTrove(self, groupTroveId)
        leaves = None
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
            leaves = repos.getAllTroveLeaves( \
                versions.Label(project.getLabel()).host, {trvName: None})
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
    @requiresAuth
    def delGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroveItems.delGroupTroveItem(groupTroveItemId)

    @private
    @typeCheck(int)
    @requiresAuth
    def getGroupTroveItem(self, groupTroveItemId):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        return self.groupTroveItems.get(groupTroveItemId)

    @private
    @typeCheck(int, str)
    @requiresAuth
    def setGroupTroveItemSubGroup(self, groupTroveItemId, subGroup):
        projectId = self.groupTroveItems.getProjectId(groupTroveItemId)
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise PermissionDenied
        self.groupTroveItems.update(groupTroveItemId, subGroup = subGroup)
        return True

    ### rMake Build functions ###
    def _checkrMakeBuildTitle(self, title):
        if not re.match("[a-zA-Z0-9\-_ ]+$", title):
            raise ParameterError('Bad rMake Build name: %s' % title)

    @private
    @typeCheck(int)
    @requiresAuth
    def getrMakeBuild(self, rMakeBuildId):
        self._filterrMakeBuildAccess(rMakeBuildId)
        return self.rMakeBuild.get(rMakeBuildId)

    @private
    @typeCheck(str)
    @requiresAuth
    def createrMakeBuild(self, title):
        self._checkrMakeBuildTitle(title)
        return self.rMakeBuild.new(userId = self.auth.userId, title = title)

    @private
    @typeCheck(int, str)
    @requiresAuth
    def renamerMakeBuild(self, rMakeBuildId, title):
        self._filterrMakeBuildAccess(rMakeBuildId)
        self._checkrMakeBuildTitle(title)
        self.rMakeBuild.update(rMakeBuildId, title = title)
        return True

    @private
    @typeCheck(int)
    @requiresAuth
    def listrMakeBuilds(self):
        return self.rMakeBuild.listByUser(self.auth.userId)

    @private
    @typeCheck(int)
    @requiresAuth
    def delrMakeBuild(self, rMakeBuildId):
        self._filterrMakeBuildAccess(rMakeBuildId)
        self.rMakeBuild.delete(rMakeBuildId)
        return True

    @private
    @typeCheck(int)
    @requiresAuth
    def listrMakeBuildTroves(self, rMakeBuildId):
        self._filterrMakeBuildAccess(rMakeBuildId)
        return [self.rMakeBuildItems.get(x) for x in \
                self.rMakeBuild.listTrovesById(rMakeBuildId)]

    @private
    @typeCheck(int, str)
    @requiresAuth
    def getrMakeBuildXML(self, rMakeBuildId, command):
        def makeOption(name, val):
            return "<option><name>%s</name><value>%s</value></option>" % \
                   (name, val)

        def makeTroveSpec(trvName, trvVersion):
            ret = "<trove><troveName>%s</troveName>" % trvName
            ret += "<troveVersion>%s</troveVersion>" % trvVersion
            ret += "<troveFlavor></troveFlavor></trove>"
            return ret

        self._filterrMakeBuildAccess(rMakeBuildId)
        if command not in ('build', 'stop', 'commit'):
            raise ParameterError("Invalid rMake Command: %s" % command)
        trvList = self.listrMakeBuildTroves(rMakeBuildId)
        if not trvList:
            raise rMakeBuildEmpty
        rMakeBuildDict = self.rMakeBuild.get(rMakeBuildId)
        if (command == 'stop' and rMakeBuildDict['status'] == 0) or \
               (command == 'commit' and rMakeBuildDict['status'] \
                not in (buildjob.JOB_STATE_BUILT, buildjob.JOB_STATE_COMMITTING)):
            raise rMakeBuildOrder
        UUID = rMakeBuildDict['UUID']
        if command == 'build':
            if UUID:
                raise rMakeBuildCollision
            else:
                UUID = self.rMakeBuild.randomizeUUID(rMakeBuildId)
        res = "<rmake><version>1</version><buildConfig>"
        res += makeOption('includeConfigFile',
                          'http://' + self.cfg.siteHost + self.cfg.basePath + \
                          'conaryrc')
        res += makeOption('subscribe', 'rBuilder xmlrpc ' \
                          'http://' + self.cfg.siteHost + self.cfg.basePath + \
                          'rmakesubscribe/' + UUID)
        res += makeOption('subscribe', 'rBuilder apiVersion %d' % \
                          currentrMakeApi)
        res += makeOption('uuid', UUID)
        res += "</buildConfig><command><name>%s</name>" % command
        if command == "build":
            for rMakeBuildItem in trvList:
                res += makeTroveSpec(rMakeBuildItem['trvName'],
                                     rMakeBuildItem['trvLabel'])
            self.rMakeBuild.startBuild(rMakeBuildId)
        elif command == 'stop':
            self.rMakeBuild.reset(rMakeBuildId)
        elif command == 'commit':
            self.rMakeBuild.commitBuild(rMakeBuildId)
        res += "</command></rmake>"
        return res

    @private
    @typeCheck(int)
    def resetrMakeBuildStatus(self, rMakeBuildId):
        self._filterrMakeBuildAccess(rMakeBuildId)
        self.rMakeBuild.reset(rMakeBuildId)
        return True

    @private
    @typeCheck(str, int, str)
    def setrMakeBuildStatus(self, UUID, status, statusMessage):
        self.rMakeBuild.setStatus(UUID, status, statusMessage)
        return True

    @private
    @typeCheck(str, int)
    def setrMakeBuildJobId(self, UUID, jobId):
        self.rMakeBuild.setJobId(UUID, jobId)
        return True

    ### rMake Build trove functions ###
    @private
    @typeCheck(int, ((unicode, str),), ((unicode, str),))
    @requiresAuth
    def addrMakeBuildTrove(self, rMakeBuildId, trvName, trvLabel):
        self._filterrMakeBuildAccess(rMakeBuildId)
        trvName = str(trvName)
        trvLabel = str(trvLabel)
        rMakeBuildDict = self.rMakeBuild.get(rMakeBuildId)
        if rMakeBuildDict['status']:
            raise rMakeBuildOrder('Cannot add troves at this time.')
        if ':' in trvName and not trvName.endswith(':source'):
            raise ParameterError('Cannot add components to rMake Build')
        rMakeBuildItemId = self.rMakeBuildItems.new( \
            rMakeBuildId = rMakeBuildId, trvName = trvName,
            trvLabel = trvLabel)
        return self.rMakeBuildItems.get(rMakeBuildItemId)

    @private
    @typeCheck(int, ((unicode, str),), ((unicode, str),))
    @requiresAuth
    def addrMakeBuildTroveByProject(self, rMakeBuildId, trvName, projectName):
        self._filterrMakeBuildAccess(rMakeBuildId)
        trvName = str(trvName)
        projectname = str(projectName)
        projectId = self.projects.getProjectIdByHostname(projectName)
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        leaves = None
        leaves = repos.getTroveVersionsByLabel(
            {trvName:{versions.Label(project.getLabel()):None}})
        if not leaves:
            leaves = repos.getAllTroveLeaves( \
                versions.Label(project.getLabel()).host,{trvName: None})
        if trvName not in leaves:
            raise TroveNotFound
        trvVersion = sorted(leaves[trvName].keys(),
                            reverse = True)[0].asString()
        trvLabel = str(versions.VersionFromString(trvVersion).branch().label())

        return self.addrMakeBuildTrove(rMakeBuildId, trvName, trvLabel)

    @private
    @typeCheck(int)
    @requiresAuth
    def delrMakeBuildTrove(self, rMakeBuildItemId):
        self._filterrMakeBuildItemAccess(rMakeBuildItemId)
        rMakeBuildItemDict = self.rMakeBuildItems.get(rMakeBuildItemId)
        rMakeBuildDict = self.rMakeBuild.get( \
            rMakeBuildItemDict['rMakeBuildId'])
        if rMakeBuildDict['status']:
            raise rMakeBuildOrder('Cannot delete troves at this time.')
        self.rMakeBuildItems.delete(rMakeBuildItemId)
        return rMakeBuildItemId

    @private
    @typeCheck(int)
    @requiresAuth
    def getrMakeBuildTrove(self, rMakeBuildItemId):
        self._filterrMakeBuildItemAccess(rMakeBuildItemId)
        return self.rMakeBuildItems.get(rMakeBuildItemId)

    @private
    @typeCheck(str, str, str, int, str)
    def setrMakeBuildTroveStatus(self, UUID, trvName, trvVersion,
                                 status, statusMessage):
        self.rMakeBuildItems.setStatus(UUID, trvName, trvVersion,
                                       status, statusMessage)
        return True

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

    # mirrored labels
    @private
    @typeCheck(int, int, str, str, str)
    @requiresAdmin
    def addInboundLabel(self, projectId, labelId, url, username, password):
        return self.inboundLabels.new(projectId = projectId, labelId = labelId,
                                      url = url, username = username,
                                      password = password)

    @private
    @typeCheck()
    @requiresAdmin
    def getInboundLabels(self):
        cu = self.db.cursor()

        cu.execute("""SELECT projectId, labelId, url, username, password
                          FROM InboundLabels""")
        return [list(x) for x in cu.fetchall()]

    @private
    @typeCheck(int, int, str, str, str, bool, bool)
    @requiresAdmin
    def addOutboundLabel(self, projectId, labelId, url, username, password, allLabels, recurse):
        return self.outboundLabels.new(projectId = projectId,
                                       labelId = labelId, url = url,
                                       username = username,
                                       password = password,
                                       allLabels = allLabels,
                                       recurse = recurse)

    @private
    @typeCheck(int, str)
    @requiresAdmin
    def delOutboundLabel(self, labelId, url):
        self.outboundLabels.delete(labelId, url)
        return True

    @private
    @typeCheck(int, int, (list, str))
    @requiresAdmin
    def setOutboundMatchTroves(self, projectId, labelId, matchList):
        if [x for x in matchList if x[0] not in ('-', '+')]:
            raise ParameterError("First character of matchStr must be + or -")
        self.outboundMatchTroves.set(projectId, labelId, matchList)
        return True

    @private
    @typeCheck(int)
    @requiresAdmin
    def getOutboundMatchTroves(self, labelId):
        return self.outboundMatchTroves.listMatches(labelId)

    @private
    @typeCheck()
    @requiresAdmin
    def getOutboundLabels(self):
        cu = self.db.cursor()

        cu.execute("""SELECT projectId, labelId, url, username, password,
                             allLabels, recurse
                          FROM OutboundLabels""")
        return [list(x[:5]) + [bool(x[5]), bool(x[6])] for x in cu.fetchall()]

    @private
    @typeCheck(str, str)
    @requiresAdmin
    def addRemappedRepository(self, fromName, toName):
        return self._addRemappedRepository(fromName, toName)

    def _addRemappedRepository(self, fromName, toName):
        return self.repNameMap.new(fromName = fromName, toName = toName)

    def __init__(self, cfg, allowPrivate = False, alwaysReload = False, db = None, req = None):
        self.cfg = cfg
        self.req = req
        self.callLog = None

        if self.cfg.xmlrpcLogFile:
            self.callLog = calllog.CallLogger(self.cfg.xmlrpcLogFile, [self.cfg.siteHost])
        if self.req:
            self.remoteIp = self.req.connection.remote_ip
        else:
            self.remoteIp = "0.0.0.0"

        # all methods are private (not callable via XMLRPC)
        # except the ones specifically decorated with @public.
        self._allowPrivate = allowPrivate

        self.maintenanceMethods = ('checkAuth', 'loadSession', 'saveSession',
                                   'deleteSession')

        from conary import dbstore
        global dbConnection
        if db:
            dbConnection = db

        if cfg.dbDriver in ["mysql", "postgresql"] and dbConnection and (not alwaysReload):
            self.db = dbConnection
        else:
            self.db = dbstore.connect(cfg.dbPath, driver=cfg.dbDriver)
            dbConnection = self.db

        # reopen a dead database
        if self.db.reopen():
            print >> sys.stderr, "reopened dead database connection in mint server"
            sys.stderr.flush()

        try:
            #The database version object has a dummy check so that it always passes.
            #At the end of all database object creation, fix the version

            global tables
            if not tables or alwaysReload:
                self.db.loadSchema()
                tables = getTables(self.db, self.cfg)

            for table in tables:
                tables[table].db = self.db
                tables[table].cfg = self.cfg
                self.__dict__[table] = tables[table]

            self.users.confirm_table.db = self.db
            self.newsCache.ageTable.db = self.db
            self.projects.reposDB.cfg = self.cfg

            #Now it's safe to commit
            self.db.commit()

        except:
            #An error occurred during db creation or upgrading
            self.db.rollback()
            raise

        self.newsCache.refresh()
