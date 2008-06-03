#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import base64
import hmac
import os
import re
import random
import simplejson
import socket
import stat
import string
import sys
import time
import tempfile
import urllib
from urlparse import urlparse
import StringIO

from mint import buildtypes
from mint import charts
from mint import communityids
from mint import data
from mint import database
from mint import ec2
from mint import grouptrove
from mint import helperfuncs
from mint import jobs
from mint import jobstatus
from mint import maintenance
from mint import mirror
from mint import news
from mint import pkgindex
from mint import profile
from mint import projects
from mint import builds
from mint import buildtemplates
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
from mint import urltypes
from mint import useit
from mint import constants
from mint.flavors import stockFlavors, getStockFlavor, getStockFlavorPath
from mint.mint_error import *
from mint.reports import MintReport
from mint.helperfuncs import toDatabaseTimestamp, fromDatabaseTimestamp, getUrlHost

from mcp import client as mcpClient
from mcp import mcp_error

from conary import changelog
from conary import conarycfg
from conary import conaryclient
from conary import sqlite3
from conary import versions
from conary.conaryclient import filetypes
from conary.deps import deps
from conary.lib.cfgtypes import CfgEnvironmentError
from conary.lib import sha1helper
from conary.lib import util
from conary.repository.errors import TroveNotFound, RoleAlreadyExists, UserAlreadyExists
from conary.repository import netclient
from conary.repository import shimclient
from conary.repository.netrepos import netserver
from conary import errors as conary_errors
from conary.dbstore import sqlerrors, sqllib
from conary import checkin
from conary.build import use

from rpath_common.proddef import api1 as proddef

try:
    # Conary 2
    from conary.repository.netrepos.reposlog \
        import RepositoryCallLogger as CallLogger
except ImportError:
    # Conary 1
    from conary.repository.netrepos.calllog import CallLogger


import gettext
gettext.install('rBuilder')

SERVER_VERSIONS = [6]
# XMLRPC Schema History
# Version 6
#  * Reworked exception marshalling API. All exceptions derived from MintError
#    are now marshalled automatically.

# first argument needs to be fairly unique so that we can detect
# detect old (unversioned) clients.
VERSION_STRINGS = ["RBUILDER_CLIENT:%d" % x for x in SERVER_VERSIONS]

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']
reservedExtHosts = ['admin', 'mail', 'mint', 'www', 'web', 'wiki', 'conary', 'lists']
# XXX do we need to reserve localhost?
# XXX reserve proxy hostname (see cfg.proxyHostname) if it's not
#     localhost
validLabel = re.compile('^[a-zA-Z][a-zA-Z0-9\-\@\.\:]*$')

# valid product version
validProductVersion = re.compile('^[a-zA-Z0-9\.]*$')

dbConnection = None
callLog = None

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

    # check to make sure the schema version is correct
    from mint import schema
    try:
        schema.checkVersion(db)
    except sqlerrors.SchemaVersionError, e:
        raise DatabaseVersionMismatch(e.args[0])

    d = {}
    d['labels'] = projects.LabelsTable(db, cfg)
    d['projects'] = projects.ProjectsTable(db, cfg)
    d['jobs'] = jobs.JobsTable(db)
    d['buildFiles'] = jobs.BuildFilesTable(db)
    d['filesUrls'] = jobs.FilesUrlsTable(db)
    d['buildFilesUrlsMap'] = jobs.BuildFilesUrlsMapTable(db)
    d['urlDownloads'] = builds.UrlDownloadsTable(db)
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
    d['inboundMirrors'] = mirror.InboundMirrorsTable(db)
    d['outboundMirrors'] = mirror.OutboundMirrorsTable(db, cfg)
    d['updateServices'] = mirror.UpdateServicesTable(db, cfg)
    d['outboundMirrorsUpdateServices'] = mirror.OutboundMirrorsUpdateServicesTable(db)
    d['repNameMap'] = mirror.RepNameMapTable(db)
    d['spotlight'] = spotlight.ApplianceSpotlightTable(db, cfg)
    d['useit'] = useit.UseItTable(db, cfg)
    d['selections'] = selections.FrontPageSelectionsTable(db, cfg)
    d['topProjects'] = selections.TopProjectsTable(db)
    d['popularProjects'] = selections.PopularProjectsTable(db)
    d['latestCommit'] = selections.LatestCommitTable(db)
    d['publishedReleases'] = pubreleases.PublishedReleasesTable(db)
    d['blessedAMIs'] = ec2.BlessedAMIsTable(db)
    d['launchedAMIs'] = ec2.LaunchedAMIsTable(db)
    d['communityIds'] = communityids.CommunityIdsTable(db)
    d['productVersions'] = projects.ProductVersionsTable(db, cfg)

    # tables for per-project repository db connections
    d['projectDatabase'] = projects.ProjectDatabase(db)
    d['databases'] = projects.Databases(db)

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

                if args and type(args[0]) == str and args[0].startswith("RBUILDER_CLIENT:"):
                    clientVer = int(args[0].split(":")[1])
                    args = args[1:]
                else:
                    clientVer = 1

                self.clientVer = clientVer
                r = method(*args)
                if self.callLog:
                    # We mustn't try to pickle flavors or versions, so just
                    # stringify everything except numbers. This could be
                    # better, but it is an undocumented feature after all.
                    str_args = [isinstance(x, (int, long)) and x or str(x)
                        for x in args]
                    self.callLog.log(self.remoteIp,
                        list(authToken) + [None, None], methodName, str_args)

            except MintError, e:
                self._handleError(e, authToken, methodName, args)
                frozen = (e.__class__.__name__, e.freeze())
                return (True, frozen)
            except:
                e_type, e_value, e_tb = sys.exc_info()
                self._handleError(e_value, authToken, methodName, args)
                raise
            else:
                self.db.commit()
                return (False, r)
        finally:
            prof.stopXml(methodName)

    def _handleError(self, e, authToken, methodName, args):
        self.db.rollback()
        if self.callLog:
            # See above for rant about pickling args
            str_args = [isinstance(x, (int, long)) and x or str(x)
                for x in args]
            self.callLog.log(self.remoteIp, list(authToken) + [None, None],
                methodName, str_args, exception = e)

    @typeCheck(str)
    @requiresAdmin
    @private
    def translateProjectFQDN(self, fqdn):
        return self._translateProjectFQDN(fqdn)

    def _translateProjectFQDN(self, fqdn):
        cu = self.db.cursor()
        cu.execute('SELECT toName FROM RepNameMap WHERE fromName=?', fqdn)
        res = cu.fetchone()
        return res and res[0] or fqdn

    def _getProjectRepo(self, project):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")
        # use a shimclient for mint-handled repositories; netclient if not
        if project.external and not self.isLocalMirror(project.id):
            cfg = project.getConaryConfig()
            conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
            if os.path.exists(conarycfgFile):
                cfg.read(conarycfgFile)

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

            fqdn = self._translateProjectFQDN(project.getFQDN())
            reposPath = os.path.join(self.cfg.reposPath, fqdn)
            tmpPath = os.path.join(reposPath, "tmp")

            # handle non-standard ports specified on cfg.projectDomainName,
            # most likely just used by the test suite
            if ":" in self.cfg.projectDomainName:
                port = int(self.cfg.projectDomainName.split(":")[1])

            cfg = netserver.ServerConfig()
            cfg.repositoryDB = self.projects.reposDB.getRepositoryDB(fqdn, db = self.db)
            cfg.tmpDir = tmpPath
            cfg.serverName = fqdn
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

            cfg = helperfuncs.configureClientProxies(cfg, self.cfg.useInternalConaryProxy, self.cfg.proxy)

            repo = shimclient.ShimNetClient(server, protocol, port,
                (self.cfg.authUser, self.cfg.authPass, None, None),
                cfg.repositoryMap, cfg.user,
                conaryProxies=conarycfg.getProxyFromConfig(cfg))
        return repo

    def _createSourceTrove(self, project, trovename, buildLabel, upstreamVersion, streamMap, changeLogMessage, cclient=None):

        # Get repository + client
        # XXX: Make this use a shimclient for rBuilder-managed
        #      repositories so we can run web-based functional tests
        #      against a single-threaded Apache server.
        #      Until the shimclient can commit, we cannot do that
        #      (see CNY-2545)

        if not cclient:
            projectCfg = project.getConaryConfig()
            projectCfg['buildLabel'] = buildLabel
            client = conaryclient.ConaryClient(projectCfg)
        else:
            client = cclient

        repos = client.getRepos()

        projectCfg = project.getConaryConfig()
        projectCfg.buildLabel = buildLabel
        client = conaryclient.ConaryClient(projectCfg)
        repos = client.getRepos()

        # ensure that the changelog message ends with a newline
        if not changeLogMessage.endswith('\n'):
            changeLogMessage += '\n'

        # create a pathdict out of the streamMap
        pathDict = {}
        for filename, filestream in streamMap.iteritems():
            pathDict[filename] = filetypes.RegularFile(contents=filestream,
                config=True)

        # create the changelog message using the currently
        # logged-on user's username and fullname, if available
        newchangelog = changelog.ChangeLog(self.auth.username,
                             self.auth.fullName or '',
                             changeLogMessage)

        # create a change set object from our source data
        changeSet = client.createSourceTrove('%s:source' % trovename,
                        projectCfg.buildLabel,
                        upstreamVersion, pathDict, newchangelog)

        # commit the change set to the repository
        repos.commitChangeSet(changeSet)

        if not cclient:
            del client

    def _getProductDefinitionForVersionObj(self, versionId):
        version = projects.ProductVersions(self, versionId)
        project = projects.Project(self, version.projectId)
        projectCfg = project.getConaryConfig()
        cclient = conaryclient.ConaryClient(projectCfg)

        pd = proddef.ProductDefinition()
        pd.setProductShortname(project.shortname)
        pd.setConaryRepositoryHostname(project.getFQDN())
        pd.setConaryNamespace(self.cfg.namespace)
        pd.setProductVersion(version.name)
        try:
            pd.loadFromRepository(cclient)
        except Exception, e:
            raise ProductDefinitionVersionNotFound
        return pd

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
        raise ItemNotFound()

    def _filterBuildAccess(self, buildId):
        try:
            buildRow = self.builds.get(buildId, fields=['projectId'])
        except ItemNotFound:
            return

        self._filterProjectAccess(buildRow['projectId'])


    def _filterPublishedReleaseAccess(self, pubReleaseId):
        try:
            pubReleaseRow = self.publishedReleases.get(pubReleaseId,
                    fields=['projectId'])
        except ItemNotFound:
            return

        isFinal = self.publishedReleases.isPublishedReleasePublished(pubReleaseId)
        # if the release is not published, then only project members
        # with write access can see the published release
        if not isFinal and not self._checkProjectAccess(pubReleaseRow['projectId'], userlevels.WRITERS):
            raise ItemNotFound()
        # if the published release is published, then anyone can see it
        # unless the project is hidden and the user is not an admin
        else:
            self._filterProjectAccess(pubReleaseRow['projectId'])

    def _filterLabelAccess(self, labelId):
        try:
            labelRow = self.labels.get(labelId, fields=['projectId'])
        except ItemNotFound:
            return

        self._filterProjectAccess(labelRow['projectId'])


    def _filterJobAccess(self, jobId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM Jobs
                        JOIN BuildsView USING(buildId)
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
                          LEFT JOIN BuildsView AS Builds
                              ON Builds.buildId = BuildFiles.buildId
                          WHERE fileId=?""", fileId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _checkProjectAccess(self, projectId, allowedUserlevels):
        if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return True
        try:
            if (self.projectUsers.getUserlevelForProjectMember(projectId,
                    self.auth.userId) in allowedUserlevels):
                return True
        except ItemNotFound:
            pass
        return False

    def _isUserAdmin(self, userId):
        mintAdminId = self.userGroups.getMintAdminId()
        try:
            if mintAdminId in self.userGroupMembers.getGroupsForUser(userId):
                return True
        except ItemNotFound:
            pass
        return False

    def _getProxies(self):
        useInternalConaryProxy = self.cfg.useInternalConaryProxy
        if useInternalConaryProxy:
            httpProxies = {}
        else:
            httpProxies = self.cfg.proxy or {}
        return [ useInternalConaryProxy, httpProxies ]

    def _configureUpdateService(self, hostname, adminUser, adminPassword):
        import xmlrpclib
        from mint.proxiedtransport import ProxiedTransport
        mirrorUser = ''
        try:
            # Make sure that we deal with any HTTP proxies
            proxy_host = self.cfg.proxy.get('https') or \
                            self.cfg.proxy.get('http')
            if proxy_host:
                transport = ProxiedTransport(proxy_host)
            else:
                transport = None

            # Connect to the rUS via XML-RPC
            urlhostname = hostname
            if ':' not in urlhostname:
                urlhostname += ':8003'
                protocol = 'https'
            else:
                # Hack to allow testsuite, which passes 'hostname:port'
                # and isn't using HTTPS
                protocol = 'http'
            url = "%s://%s:%s@%s/rAA/xmlrpc/" % \
                    (protocol, adminUser, adminPassword, urlhostname)
            sp = xmlrpclib.ServerProxy(url, transport=transport)

            mirrorUser = helperfuncs.generateMirrorUserName("%s.%s" % \
                    (self.cfg.hostName, self.cfg.siteDomainName), hostname)

            # Add a user to the update service with mirror permissions
            mirrorPassword = \
                    sp.mirrorusers.MirrorUsers.addRandomUser(mirrorUser)
        except xmlrpclib.ProtocolError, e:
            if e.errcode == 403:
                raise UpdateServiceAuthError(urlhostname)
            else:
                raise UpdateServiceConnectionFailed(urlhostname, \
                        "%d %s" % (e.errcode, e.errmsg))
        except socket.error, e:
            raise UpdateServiceConnectionFailed(urlhostname, str(e[1]))
        else:
            if not mirrorPassword:
                raise UpdateServiceUnknownError(urlhostname)

        return (mirrorUser, mirrorPassword)

    def _createGroupTemplate(self, project, buildLabel, version, groupName=None):
        if groupName is None:
            groupName = helperfuncs.getDefaultImageGroupName(project.shortname)

        label = versions.Label(buildLabel)

        projectCfg = project.getConaryConfig()
        projectCfg.buildLabel = buildLabel
        client = conaryclient.ConaryClient(projectCfg)
        repos = client.getRepos()

        trvLeaves = repos.getTroveLeavesByLabel(\
                {groupName: {label: None} }).get(groupName, [])
        if trvLeaves:
            raise GroupTroveTemplateExists

        from mint.templates import groupTemplate
        recipeStream = StringIO.StringIO()
        recipeStream.write(templates.write(groupTemplate,
                    cfg = self.cfg,
                    groupApplianceLabel=self.cfg.groupApplianceLabel,
                    groupName=groupName,
                    recipeClassName=util.convertPackageNameToClassName(groupName),
                    version=version))
        recipeStream.write('\n')
        self._createSourceTrove(project, groupName,
                buildLabel, version,
                {'%s.recipe' % groupName: recipeStream},
                'Initial appliance image group template',
                client)
        recipeStream.close()
        return True

    def checkVersion(self):
        if self.clientVer < SERVER_VERSIONS[0]:
            raise InvalidClientVersion('Invalid client version %s. Server '
                'accepts client versions %s' % (self.clientVer,
                    ', '.join(str(x) for x in SERVER_VERSIONS)))
        return SERVER_VERSIONS

    # project methods
    def _validateHostname(self, hostname, domainname, resHosts):
        if not hostname:
            raise projects.InvalidHostname
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in resHosts:
            raise projects.InvalidHostname
        if (hostname + "." + domainname) == socket.gethostname():
            raise projects.InvalidHostname
        return None

    def _validateShortname(self, shortname, domainname, resHosts):
        if not shortname:
            raise InvalidShortname
        if validHost.match(shortname) == None:
            raise InvalidShortname
        if shortname in resHosts:
            raise InvalidShortname
        if (shortname + "." + domainname) == socket.gethostname():
            raise InvalidShortname
        return None

    def _validateProductVersion(self, version):
        if not version:
            raise ProductVersionInvalid
        if not validProductVersion.match(version):
            raise ProductVersionInvalid
        return None

    @typeCheck(str, str, str, str, str, str, str, str, str, str)
    @requiresCfgAdmin('adminNewProjects')
    @private
    def newProject(self, projectName, hostname, domainname, projecturl, desc, appliance, shortname, prodtype, version, commitEmail):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")

        # make sure the shortname, version, and prodtype are valid, and
        # validate the hostname also in case it ever splits from being
        # the same as the short name
        self._validateShortname(shortname, domainname, reservedHosts)
        self._validateHostname(hostname, domainname, reservedHosts)
        self._validateProductVersion(version)
        if not prodtype or (prodtype != 'Appliance' and prodtype != 'Component'):
            raise projects.InvalidProdType

        fqdn = ".".join((hostname, domainname))
        if projecturl and not (projecturl.startswith('https://') or projecturl.startswith('http://')):
            projecturl = "http://" + projecturl

        if prodtype == 'Appliance':
            appliance = "yes"
            applianceValue = 1
        else:
            appliance = "no"
            applianceValue = 0

        # initial product definition
        pd = helperfuncs.sanitizeProductDefinition(projectName,
                desc, hostname, domainname, shortname, version,
                '', self.cfg.namespace)

        label = pd.getDefaultLabel()

        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if validLabel.match(label) == None:
            raise projects.InvalidLabel(label)

        # XXX this set of operations should be atomic if possible
        projectId = self.projects.new(name = projectName,
                                      creatorId = self.auth.userId,
                                      description = desc,
                                      hostname = hostname,
                                      domainname = domainname,
                                      isAppliance = applianceValue,
                                      projecturl = projecturl,
                                      timeModified = time.time(),
                                      timeCreated = time.time(),
                                      shortname = shortname,
                                      prodtype = prodtype, 
                                      version = version)
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)

        # add to RepNameMap if projectDomainName != domainname
        projectDomainName = self.cfg.projectDomainName.split(':')[0]
        if (domainname != projectDomainName):
            self._addRemappedRepository('%s.%s' % \
                                        (hostname, projectDomainName), fqdn)

        project = projects.Project(self, projectId)

        project.addLabel(label,
                         "http://%s%srepos/%s/" % (self.cfg.projectSiteHost, 
                         self.cfg.basePath, hostname), 'userpass', 
                         self.cfg.authUser, self.cfg.authPass)

        self.projects.createRepos(self.cfg.reposPath, self.cfg.reposContentsDir,
                                  hostname, domainname, self.authToken[0],
                                  self.authToken[1])

        if commitEmail:
            project.setCommitEmail(commitEmail)

        if applianceValue:
            try:
                self._createGroupTemplate(project, label, version)
            except GroupTroveTemplateExists:
                pass # really, this is OK -- and even if it weren't,
                     # there's nothing you can do about it, anyway

        if self.cfg.hideNewProjects:
            repos = self._getProjectRepo(project)
            repos.deleteUserByName(project.getLabel(), 'anonymous')
            self.projects.hide(projectId)

        if self.cfg.createConaryRcFile:
            self._generateConaryRcFile()
        return projectId

    @typeCheck(str, str, str, str, str, bool)
    @requiresAdmin
    @private
    def newExternalProject(self, name, hostname, domainname, label, url, mirrored):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")

        # make sure the hostname is valid
        self._validateHostname(hostname, domainname, reservedExtHosts)

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
        project.addLabel(label, url, 'none')

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
        project = self.projects.get(id)

        if self.clientVer < 3:
            del project['isAppliance']

        if self.clientVer < 4:
            del project['commitEmail']

        return project


    @typeCheck(str)
    @private
    def getProjectIdByFQDN(self, fqdn):
        fqdn = self._translateProjectFQDN(fqdn)
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
        label = versions.Label(project.getLabel())

        cu = self.db.cursor()
        if username and not userId:
            cu.execute("""SELECT userId FROM Users
                              WHERE username=? AND active=1""", username)
            r = cu.fetchone()
            if not r:
                raise ItemNotFound("username")
            else:
                userId = r[0]
        elif userId and not username:
            cu.execute("""SELECT username FROM Users
                              WHERE userId=? AND active=1""", userId)
            r = cu.fetchone()
            if not r:
                raise ItemNotFound("userId")
            else:
                username = r[0]

        if (self.auth.userId != userId) and level == userlevels.USER:
            raise users.UserInduction()

        if level != userlevels.USER:
            self.membershipRequests.deleteRequest(projectId, userId)
        try:
            self.projectUsers.new(projectId, userId, level)
        except DuplicateItem:
            project.updateUserLevel(userId, level)
            # only attempt to modify acl's of local projects.
            if not project.external:
                repos = self._getProjectRepo(project)
                # edit vice/drop+add is intentional to honor acl tweaks by
                # admins.
                repos.editAcl(label, username, None, None, None,
                              None, write=level in userlevels.WRITERS,
                              canRemove=False)
                repos.setRoleIsAdmin(label, username,
                                     self.cfg.projectAdmin and
                                     level == userlevels.OWNER)
                repos.setRoleCanMirror(label, username,
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
                raise ItemNotFound("username")
            repos = self._getProjectRepo(project)
            helperfuncs.addUserByMD5ToRepository(repos, username, password, salt, 
                username, label)
            repos.addAcl(label, username, None, None,
                         write=(level in userlevels.WRITERS),
                         remove=False)
            repos.setRoleIsAdmin(label, username,
                                 self.cfg.projectAdmin and level == userlevels.OWNER)
            repos.setRoleCanMirror(label, username,
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
        repositoryDB = self.projects.reposDB.getRepositoryDB( \
            self._translateProjectFQDN(project.getFQDN()), db = self.db)
        db = dbstore.connect(repositoryDB[1], repositoryDB[0])
        cu = db.cursor()
        # aggregate with MAX in case user is member of multiple groups
        cu.execute("""SELECT MAX(admin) FROM Users
                      JOIN UserGroupMembers ON
                          Users.userId = UserGroupMembers.userId
                      JOIN UserGroups ON
                          UserGroups.userGroupId = UserGroupMembers.userGroupId
                      WHERE Users.username=?""", userName)
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
        except ItemNotFound:
            raise netclient.UserNotFound()
        if (self.auth.userId != userId) and userLevel == userlevels.USER:
            raise users.UserInduction()

        project = projects.Project(self, projectId)
        self.projectUsers.delete(projectId, userId)
        repos = self._getProjectRepo(project)
        user = self.getUser(userId)

        if not project.external:
            repos.deleteUserByName(versions.Label(project.getLabel()), user['username'])
        if notify:
            self._notifyUser('Removed', user, project)
        return True

    def _notifyUser(self, action, user, project, userlevel=None):
        userlevelname = ((userlevel >=0) and userlevels.names[userlevel] or\
                                             'Unknown')
        projectUrl = 'http://%s%sproject/%s/' %\
                      (self.cfg.projectSiteHost,
                       self.cfg.basePath,
                       project.getHostname())

        greeting = "Hello,"

        actionText = {'Removed':'has been removed from the "%s" project'%\
                       project.getName(),

                      'Added':'has been added to the "%s" project as %s %s' % (project.getName(), userlevelname == 'Developer' and 'a' or 'an', userlevelname),

                      'Changed':'has had its current access level changed to "%s" on the "%s" project' % (userlevelname, project.getName())
                     }

        helpLink = """

Instructions on how to set up your build environment for this project can be found at http://wiki.rpath.com/

If you would not like to be %s %s of this project, you may resign from this project at %smembers""" % \
        (userlevelname == 'Developer' and 'a' or 'an',
            userlevelname, projectUrl)

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

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setProjectCommitEmail(self, projectId, commitEmail):
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied

        return self.projects.update(projectId, commitEmail = commitEmail)

    @typeCheck(int)
    @requiresAdmin
    @private
    def hideProject(self, projectId):
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        repos.deleteUserByName(versions.Label(project.getLabel()), 'anonymous')

        self.projects.hide(projectId)
        self._generateConaryRcFile()
        return True

    @typeCheck(int, bool)
    @requiresAdmin
    @private
    def setBackupExternal(self, projectId, backupExternal):
        return self.projects.update(projectId, backupExternal=backupExternal)

    @typeCheck(int)
    @requiresAdmin
    @private
    def unhideProject(self, projectId):
        project = projects.Project(self, projectId)
        repos = self._getProjectRepo(project)
        label = versions.Label(project.getLabel())
        username = 'anonymous'
        helperfuncs.addUserToRepository(repos, username, username, username, 
            label)
        repos.addAcl(label, username, None, None, write=False, remove=False)

        self.projects.unhide(projectId)
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
            raise ItemNotFound("membership")
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
            label = versions.Label(project.getLabel())
            repos.editAcl(label, user['username'], "ALL", None,
                          None, None, write=(level in userlevels.WRITERS),
                          canRemove=False)
            repos.setRoleIsAdmin(label, user['username'],
                                 level == userlevels.OWNER)
            repos.setRoleCanMirror(label, user['username'], int(level == userlevels.OWNER))

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

    @private
    @typeCheck(str, str)
    def pwCheck(self, user, password):
        return self.users.checkAuth((user, password))['authorized']

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
        repos.addNewAsciiPGPKey(versions.Label(project.getLabel()), username, keydata)
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
            raise ItemNotFound
        cu.execute("SELECT confirmation FROM Confirmations WHERE userId=?",
                   r[0][0])
        r = cu.fetchall()
        if not r:
            raise ItemNotFound
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
                    authRepo.changePassword(versions.Label(project.getLabel()), username, newPassword)

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

    @typeCheck(str, int, int, int, bool, bool)
    @private
    def searchProjects(self, terms, modified, limit, offset, byPopularity, filterNoDownloads):
        """
        Collect the results as requested by the search terms.
        NOTE: admins can see everything including hidden and fledgling
        projects regardless of the value of self.cfg.hideFledgling.
        @param terms: Search terms
        @param modified: Code for the lastModified filter
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @param byPopularity: if True, order items by popularity metric
        @return:       dictionary of Items requested
        """
        if self.auth and self.auth.admin:
            includeInactive = True
        else:
            includeInactive = False
        return self.projects.search(terms, modified, limit, offset, includeInactive, byPopularity, filterNoDownloads)

    @typeCheck(str, int, int)
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

    @typeCheck(int, bool)
    @private
    def getNewProjects(self, limit, showFledgling):
        """
        Collect a list of projects.
        NOTE: admins can see everything including hidden and fledgling
        projects regardless of the value of self.cfg.hideFledgling.
        @param limit:  Number of items to return
        @param showFledgling:  Boolean to show fledgling (empty) projects or not
        @return: a list of projects
        """
        return self.projects.getNewProjects(limit, showFledgling)

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
        # includeInactive *must* be set to false for non-admins if user browse
        # is ever opened up to non-admins
        includeInactive = True
        return self.users.getUsers(sortOrder, limit, offset, includeInactive),\
               self.users.getNumUsers(includeInactive)

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

    @typeCheck()
    @private
    def getPopularProjects(self):
        return self.popularProjects.getList()

    @typeCheck()
    @private
    def getTopProjects(self):
        return self.topProjects.getList()

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

    @typeCheck(bool, ((str, type(None)),), ((str, type(None)),))
    @private
    @requiresAuth
    def getAllLabelsForProjects(self, overrideAuth, newUser, newPass):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        return self.labels.getAllLabelsForProjects(overrideAuth, newUser, newPass)

    @typeCheck(int, str, str, str, str, str, str)
    @requiresAuth
    @private
    def addLabel(self, projectId, label, url, authType, username, password, entitlement):
        self._filterProjectAccess(projectId)
        return self.labels.addLabel(projectId, label, url, authType, username, password, entitlement)

    @typeCheck(int)
    @requiresAuth
    @private
    def getLabel(self, labelId):
        self._filterLabelAccess(labelId)
        return self.labels.getLabel(labelId)

    @typeCheck(int, str, str, str, str, str, str)
    @requiresAuth
    @private
    def editLabel(self, labelId, label, url, authType, username, password,
            entitlement):
        self._filterLabelAccess(labelId)
        self.labels.editLabel(labelId, label, url, authType, username,
            password, entitlement)
        if self.cfg.createConaryRcFile:
            self._generateConaryRcFile()

        return True

    @typeCheck(int, int)
    @requiresAuth
    @private
    def removeLabel(self, projectId, labelId):
        self._filterProjectAccess(projectId)
        return self.labels.removeLabel(projectId, labelId)

    def _getFullRepositoryMap(self):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM Projects
                            WHERE hidden=0 AND disabled=0 AND
                                (external=0 OR projectId IN (SELECT targetProjectId FROM InboundMirrors))""")
        projs = cu.fetchall()
        repoMap = {}
        for x in projs:
            repoMap.update(self.labels.getLabelsForProject(x[0])[1])

        # for external projects where rBuilder isn't using the default
        # repositoryMap, put this in conaryrc.generated too:
        cu.execute("""SELECT projectId FROM Projects WHERE external=1
            AND NOT (projectId IN (SELECT targetProjectId FROM InboundMirrors))""")
        projs = cu.fetchall()
        for x in projs:
            l = self.labels.getLabelsForProject(x[0])
            label = versions.Label(l[0].keys()[0])
            host = getUrlHost(l[1].values()[0])

            if label.getHost() != host:
                repoMap.update(l[1])

        return repoMap

    def _generateConaryRcFile(self):
        if not self.cfg.createConaryRcFile:
            return False

        repoMaps = self._getFullRepositoryMap()

        try:
            fd, fname = tempfile.mkstemp()
            os.close(fd)
            f = open(fname, 'w')
            for host, url in repoMaps.iteritems():
                f.write('repositoryMap %s %s\n' % (host, url))
            f.close()
            util.mkdirChain(os.path.join(self.cfg.dataPath, 'run'))
            util.copyfile(fname, self.cfg.conaryRcFile)
            os.chmod(self.cfg.conaryRcFile, 0644)

            # add proxy stuff for version 1 config clients
            v1config = self.cfg.conaryRcFile + "-v1"
            f = open(fname, 'a+')
            
            # add conaryProxy if we have it enabled
            if self.cfg.useInternalConaryProxy:
                for proto in ['http', 'https']:
                    stringMap = { 'proto': proto,
                                  'host': self.cfg.hostName,
                                  'domain': self.cfg.siteDomainName }
                    f.write("conaryProxy %(proto)s %(proto)s://%(host)s.%(domain)s\n" % stringMap)

            self.cfg.displayKey('proxy', out=f)
            f.close()
            util.copyfile(fname, v1config)
            os.chmod(v1config, 0644)

        finally:
            os.unlink(fname)

    @requiresAuth
    @private
    def getFullRepositoryMap(self):
        return self._getFullRepositoryMap()

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
        except ItemNotFound:
            userId = 0
        self.commits.new(projectId, time.time(), name, version, userId)
        return True

    @typeCheck(int)
    @private
    def getCommitsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.commits.getCommitsByProject(projectId)

    @typeCheck(int)
    def getRelease(self, releaseId):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        self._filterBuildAccess(buildId)
        build = self.builds.get(buildId)
        # add some things that the old jobserver will expect
        build['releaseId'] = build['buildId']
        build['imageTypes'] = [build['buildType']]
        build['downloads'] = 0
        build['timePublished'] = 0
        build['published'] = 0
        # remove things that will confuse old jobservers
        del build['buildId']
        del build['buildType']
        del build['timeCreated']
        del build['createdBy']
        del build['timeUpdated']
        del build['updatedBy']
        del build['pubReleaseId']
        del build['deleted']
        return build

    @typeCheck(int)
    def getBuild(self, buildId):
        if not self.builds.buildExists(buildId):
            raise ItemNotFound
        self._filterBuildAccess(buildId)
        build = self.builds.get(buildId)

        if self.clientVer == 1:
            del build['deleted']

        return build

    @typeCheck(int, str, bool)
    @requiresAuth
    @private
    def newBuild(self, projectId, productName):
        self._filterProjectAccess(projectId)
        buildId = self.builds.new(projectId = projectId,
                                      name = productName,
                                      timeCreated = time.time(),
                                      buildCount = 0)

        mc = self._getMcpClient()

        try:
            self.buildData.setDataValue(buildId, 'jsversion',
                str(mc.getJSVersion()),
                data.RDT_STRING)
        except mcp_error.NotEntitledError:
            raise NotEntitledError()
        return buildId

    @typeCheck(int, ((str, unicode),), bool)
    @requiresAuth
    @private
    def newBuildsFromProductDefinition(self, versionId, stageName, force):
        """
        Launch the image builds defined in the product definition for the
        given version id and stage.  If provided, use troveSpec as the top
        level group for the image, otherwise use the top level group defined
        in the
        product defintion.
        """
        version = projects.ProductVersions(self, versionId)
        project = projects.Project(self, version.projectId)
        projectId = version.projectId

        # Read build definition from product definition.
        pd = self._getProductDefinitionForVersionObj(versionId)

        # Look up the label for the stage name that was passed in.
        try:
            stageLabel = str(pd.getLabelForStage(stageName))
        except proddef.StageNotFoundError, snfe:
            raise ProductDefinitionError("Stage %s was not found in the product definition" % stageName)
        except proddef.MissingInformationError, mie:
            raise ProductDefinitionError("Cannot determine the product label as the product definition is incomplete")

        # Filter builds by stage
        builds = pd.getBuildsForStage(stageName)
        if not builds:
            raise NoBuildsDefinedInBuildDefinition

        # Create build data for each defined build so we can create the builds
        # later
        filteredBuilds = []
        buildErrors = []
        for build in builds:
            buildFlavor = deps.parseFlavor(str(build.getBuildBaseFlavor()))
            buildGroup = str(build.getBuildImageGroup())

            # Returns a list of troves that satisfy buildFlavor.
            nvfs = self._resolveTrove(projectId, buildGroup,
                                      stageLabel, buildFlavor)

            if nvfs:
                # Store a build with options for each trove found.
                for nvf in nvfs:
                    filteredBuilds.append((build, nvf))
            else:
                # No troves were found, save the error.
                buildErrors.append(str(conary_errors.TroveNotFound(
                    "Trove '%s' has no matching flavors for '%s'" % \
                    (buildGroup, buildFlavor))))

        if buildErrors and not force:
            raise TroveNotFoundForBuildDefinition(buildErrors)

        # Create/start each build.
        buildIds = []
        for buildDefinition, nvf in filteredBuilds:
            buildId = self._createBuildDefBuild(projectId, buildDefinition,
                    nvf, project.getName())
            buildIds.append(buildId)
            self.startImageJob(buildId)

        return buildIds

    def _createBuildDefBuild(self, projectId, buildDefinition, nvf, buildName):
        """
        Create a new build from build definition info
        @return: the build id
        """
        customTroveDict = { 'mediaTemplateTrove' : 'media-template',
                            'anacondaCustomTrove' : 'anaconda-custom',
                            'anacondaTemplatesTrove' : 'anaconda-templates'}

        n, v, f = str(nvf[0]), nvf[1].freeze(), nvf[2].freeze()

        project = projects.Project(self, projectId)
        buildId = self.newBuild(projectId, buildName)
        newBuild = builds.Build(self, buildId)
        newBuild.setTrove(n, v, f)
        buildType = buildtypes.xmlTagNameImageTypeMap[buildDefinition.getBuildImageType().tag]
        newBuild.setBuildType(buildType)

        buildImageType = buildDefinition.getBuildImageType()
        buildSettings = buildImageType.fields.copy()

        template = newBuild.getDataTemplate()

        # handle custom troves
        for customTroveSetting in ['mediaTemplateTrove', 'anacondaCustomTrove',
                            'anacondaTemplatesTrove']:
            if buildSettings.has_key(customTroveSetting):
                troveName = customTroveDict[customTroveSetting]
                troveVersion = str(buildSettings.pop(customTroveSetting))
                customTroveSpec = project.resolveExtraTrove(troveName, v, f,
                        troveVersion)
                if customTroveSpec:
                    newBuild.setDataValue(troveName, customTroveSpec)

        # handle the rest
        for k, v in buildSettings.iteritems():
            try:
                if template[k][0] == data.RDT_BOOL:
                    v = (str(v) == 'true')
                elif template[k][0] in (data.RDT_STRING, data.RDT_ENUM):
                    v = str(v)
                elif template[k][0] == data.RDT_INT:
                    v = int(v)
                else:
                    continue
            except KeyError:
                pass # if it's not int the template, no matter
            else:
                newBuild.setDataValue(k, v)

        return buildId

    def _resolveTrove(self, projectId, troveName, troveLabel, filterFlavor):
        '''
        Return a list of trove tuples matching C{troveName},
        C{troveLabel}, satisfying C{filterFlavor} and also matching its
        architecture. The repository backing the project at C{projectId}
        will be used.

        @return: List of trove tuples matching the query
        @rtype: list
        '''

        project = projects.Project(self, projectId)
        projectCfg = project.getConaryConfig()
        client = conaryclient.ConaryClient(projectCfg)
        repos = client.getRepos()

        # Get the major architecture from filterFlavor
        filterArch = helperfuncs.getArchFromFlavor(filterFlavor)

        # Find the troves that satisfy the build.
        ret = []
        matches = repos.findTrove(None, (troveName, troveLabel, None))
        if not matches:
            return []

        maxVersion = max(x[1] for x in matches)
        for name, version, flavor in matches:
            if version != maxVersion:
                # Skip older versions that only show up because
                # they're flavored differently
                continue
            if not flavor.stronglySatisfies(filterFlavor):
                # Skip flavors that don't satisfy our original
                # condition in the first place
                continue

            # If filterFlavor has an instruction set, the major
            # architecture must match that of the group so
            # an is: x86 filter does not match is: x86 x86_64 groups
            # even though the flavor is technically satisfied.
            thisArch = helperfuncs.getArchFromFlavor(flavor)
            if filterArch and filterArch != thisArch:
                continue

            ret.append((name, version, flavor))

        return ret

    @typeCheck(int)
    @requiresAuth
    def deleteBuild(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()
        cu = self.db.cursor()
        for filelist in self.getBuildFilenames(buildId):
            fileId = filelist['fileId']
            fileUrlList = filelist['fileUrls']
            for urlId, urlType, url in fileUrlList:
                # if this location is local, delete the file
                if urlType == urltypes.LOCAL:
                    fileName = url
                    try:
                        os.unlink(fileName)
                    except OSError, e:
                            # ignore permission denied, no such file/dir
                            if e.errno not in (2, 13):
                                raise
                    for dirName in (\
                        os.path.sep.join(fileName.split(os.path.sep)[:-1]),
                        os.path.sep.join(fileName.split(os.path.sep)[:-2])):
                        try:
                            os.rmdir(dirName)
                        except OSError, e:
                            # ignore permission denied, dir not empty, no such file/dir
                            if e.errno not in (2, 13, 39):
                                raise
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

    @typeCheck(int, str, str, str, str, str)
    @private
    @requiresAuth
    def resolveExtraTrove(self, projectId, specialTroveName, specialTroveVersion,
            specialTroveFlavor, imageGroupVersion, imageGroupFlavor):

        # Get the project that the build is going to be on
        project = projects.Project(self, projectId)

        searchPath = []
        if imageGroupVersion:
            # Get the image group label as the first part of the searchpath
            igV = versions.ThawVersion(imageGroupVersion)

            # Determine search path; start with imageGroup's label
            searchPath.append(igV.branch().label())

        # Handle anacond-templates using a fallback
        if specialTroveName == 'anaconda-templates':
            # Need to search our system-wide fallback for anaconda templates
            searchPath.append(versions.Label(self.cfg.anacondaTemplatesFallback))

        # if no flavor specified, use the top level group's flavor
        if imageGroupFlavor and not specialTroveFlavor:
            specialTroveFlavor = helperfuncs.getMajorArchFlavor(imageGroupFlavor)

        # Sanitize bits
        if specialTroveVersion == '' or specialTroveFlavor == '':
            specialTroveVersion = None
        if specialTroveFlavor == '':
            specialTroveFlavor = None

        # Get a Conary client
        cfg = project.getConaryConfig()
        cfg.installLabelPath = searchPath
        cfg.initializeFlavors()
        cfg.dbPath = cfg.root = ":memory:"
        cfg.proxy = self.cfg.proxy
        cclient = conaryclient.ConaryClient(cfg)

        try:
            matches = cclient.getRepos().findTrove(searchPath,
                    (specialTroveName, specialTroveVersion, specialTroveFlavor),
                    cfg.flavor)
            if matches:
                strSpec = '%s=%s[%s]' % matches[0]
            else:
                strSpec = ''

        except TroveNotFound:
            return ''

        return strSpec

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

    @typeCheck(int)
    @private
    def serializeBuild(self, buildId):
        self._filterBuildAccess(buildId)

        buildDict = self.builds.get(buildId)
        project = projects.Project(self, buildDict['projectId'])

        cc = project.getConaryConfig()
        cc.entitlementDirectory = os.path.join(self.cfg.dataPath, 'entitlements')
        cc.readEntitlementDirectory()

        # Ignore conaryProxy set by getConaryConfig; it's bound
        # to be localhost, as getConaryConfig() generates
        # config objects intended to be used by NetClient /
        # ConaryClient objects internal to rBuilder (i.e. not the
        # jobslaves)
        cc.conaryProxy = None

        # Add authentication for each project to which the builder has access.
        # This should allow them to run builds that include troves from
        # hidden projects.
        for otherProjectId, level in \
          self.getProjectIdsByMember(self.auth.userId):
            if level in userlevels.WRITERS:
                otherProject = projects.Project(self, otherProjectId)
                cc.user.addServerGlob(otherProject.getFQDN(),
                    self.cfg.authUser, self.cfg.authPass)

        cfgBuffer = StringIO.StringIO()
        cc.display(cfgBuffer)
        cfgData = cfgBuffer.getvalue().split("\n")

        allowedOptions = ['repositoryMap', 'user', 'conaryProxy', 'entitlement']
        cfgData = "\n".join([x for x in cfgData if x.split(" ")[0] in allowedOptions])

        if self.cfg.createConaryRcFile:
            cfgData += "\nincludeConfigFile http://%s%s/conaryrc\n" % \
                (self.cfg.siteHost, self.cfg.basePath)

        r = {}
        r['protocolVersion'] = builds.PROTOCOL_VERSION
        r['type'] = 'build'

        for key in ('buildId', 'name', 'troveName', 'troveVersion',
                    'troveFlavor', 'description', 'buildType'):
            r[key] = buildDict[key]

        r['data'] = self.buildData.getDataDict(buildId)

        r['project'] = {'name' : project.name,
                        'hostname' : project.hostname,
                        'label' : project.getLabel(),
                        'conaryCfg' : cfgData}

        hostBase = '%s.%s' % (self.cfg.hostName, self.cfg.externalDomainName)

        r['UUID'] = '%s-build-%d-%d' % (hostBase, buildId,
                self.builds.bumpBuildCount(buildId))

        # Serialize AMI configuration data (if AMI build)
        if buildDict.get('buildType', buildtypes.STUB_IMAGE) == buildtypes.AMI:

            amiData = {}

            def _readX509File(filepath):
                if os.path.exists(filepath):
                    f = None
                    try:
                        f = open(filepath, 'r')
                        return f.read()
                    finally:
                        if f:
                            f.close()
                else:
                    raise AMIBuildNotConfigured

            for k in ( 'ec2PublicKey', 'ec2PrivateKey', 'ec2AccountId',
                       'ec2S3Bucket', 'ec2LaunchUsers', 'ec2LaunchGroups'):
                amiData[k] = self.cfg[k]
                if not amiData[k] and k not in ('ec2LaunchUsers', 'ec2LaunchGroups'):
                    raise AMIBuildNotConfigured

            amiData['ec2CertificateKey'] = \
                    _readX509File(self.cfg.ec2CertificateKeyFile)
            amiData['ec2Certificate'] = \
                    _readX509File(self.cfg.ec2CertificateFile)

            r['amiData'] = amiData

        r['outputUrl'] = 'http://%s.%s%s' % \
            (self.cfg.hostName, self.cfg.externalDomainName, self.cfg.basePath)
        r['outputToken'] = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        self.buildData.setDataValue(buildId, 'outputToken',
            r['outputToken'], data.RDT_STRING)

        return simplejson.dumps(r)

    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setReleaseDataValue(self, releaseId, name, value, dataType):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        return self.setBuildDataValue(buildId, name, value, dataType)

    @typeCheck(int, str)
    @private
    def getReleaseDataValue(self, releaseId, name):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        return self.getBuildDataValue(buildId, name)

    @typeCheck(int)
    @private
    def getReleaseDataDict(self, releaseId):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        return self.getBuildDataDict(buildId)

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
        if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
            raise PublishedReleasePublished
        if len(valDict):
            valDict.update({'timeUpdated': time.time(),
                            'updatedBy': self.auth.userId})
            return self.publishedReleases.update(pubReleaseId, **valDict)

    @typeCheck(int, bool)
    @requiresAuth
    @private
    def publishPublishedRelease(self, pubReleaseId, shouldMirror):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        project = projects.Project(self, projectId)

        self._checkPublishedRelease(pubReleaseId, projectId)
        
        valDict = {'timePublished': time.time(),
                   'publishedBy': self.auth.userId,
                   'shouldMirror': int(shouldMirror),
                   }
        return self.publishedReleases.update(pubReleaseId, **valDict)

    @typeCheck(int)
    @requiresAuth
    @private
    def getMirrorableReleasesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.publishedReleases.getMirrorableReleasesByProject(projectId)

    @typeCheck(int)
    @requiresAuth
    @private
    def isProjectMirroredByRelease(self, projectId):
        self._filterProjectAccess(projectId)
        return self.outboundMirrors.isProjectMirroredByRelease(projectId)

    def _checkPublishedRelease(self, pubReleaseId, projectId, checkPublished=True):
        """
        Performs some sanity checks on the published release
        """
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        if not len(self.publishedReleases.getBuilds(pubReleaseId)):
            raise PublishedReleaseEmpty
        if checkPublished:
            if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
                raise PublishedReleasePublished

        return True

    def _checkUnpublishedRelease(self, pubReleaseId, projectId, failIfNotPub=True):
        """
        Performs some sanity checks on the unpublished release
        """
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        if failIfNotPub:
            if not self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
                raise PublishedReleaseNotPublished

        return True

    @typeCheck(int)
    @requiresAuth
    @private
    def unpublishPublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)

        self._checkUnpublishedRelease(pubReleaseId, projectId)

        valDict = {'timePublished': None,
                   'publishedBy': None}
        return self.publishedReleases.update(pubReleaseId, **valDict)

    @typeCheck(int)
    @requiresAuth
    def deletePublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
            raise PublishedReleasePublished
        self.publishedReleases.delete(pubReleaseId)
        return True

    @typeCheck(int)
    @private
    def isPublishedReleasePublished(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        return self.publishedReleases.isPublishedReleasePublished(pubReleaseId)

    @typeCheck(int)
    @requiresAuth
    @private
    def getUnpublishedBuildsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.builds.getUnpublishedBuilds(projectId)

    @typeCheck(int, int)
    @private
    def getBuildsForPublishedRelease(self, pubReleaseId, buildType = None):
        """
        Get builds in a release and optionally filters by buildtype
        """
        self._filterPublishedReleaseAccess(pubReleaseId)
        allBuilds = self.publishedReleases.getBuilds(pubReleaseId)

        if buildType:
            builds = []
            for b in allBuilds:
                if self.getBuildType(b) == buildType:
                    builds.append(b)
        else:
            builds = allBuilds
        
        return builds

    @typeCheck(int)
    @private
    def getUniqueBuildTypesForPublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        return self.publishedReleases.getUniqueBuildTypes(pubReleaseId)

    @typeCheck(int, bool)
    @private
    def getPublishedReleasesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        publishedOnly = False
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            publishedOnly = True
        return self.publishedReleases.getPublishedReleasesByProject(projectId,
                publishedOnly)

    @typeCheck(int, int)
    @private
    def getCommunityId(self, projectId, communityType):
        return self.communityIds.getCommunityId(projectId, communityType)

    @typeCheck(int, int, str)
    @private
    @requiresAuth
    def setCommunityId(self, projectId, communityType, communityId):
        return self.communityIds.setCommunityId(projectId, communityType,
                                                communityId)
    @typeCheck(int, int)
    @private
    @requiresAuth
    def deleteCommunityId(self, projectId, communityType):
        return self.communityIds.deleteCommunityId(projectId, communityType)

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
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        self._filterBuildAccess(buildId)
        return self.builds.getTrove(buildId)

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
        r = self.builds.setTrove(buildId, troveName, troveVersion, troveFlavor)

        # clear out all "important flavors"
        for x in buildtypes.flavorFlags.keys():
            self.buildData.removeDataValue(buildId, x)

        # and set the new ones
        for x in builds.getImportantFlavors(troveFlavor):
            self.buildData.setDataValue(buildId, x, 1, data.RDT_INT)
        return r

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
        buildData = self.builds.get(buildId, fields=['projectId', 'buildType'])
        if not self._checkProjectAccess(buildData['projectId'],
                [userlevels.OWNER]):
            raise PermissionDenied()
        if not self.publishedReleases.publishedReleaseExists(pubReleaseId):
            raise PublishedReleaseMissing()
        if self.isPublishedReleasePublished(pubReleaseId):
            raise PublishedReleasePublished()
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if published and (buildData['buildType'] != buildtypes.AMI and buildData['buildType'] != buildtypes.IMAGELESS and not self.getBuildFilenames(buildId)):
            raise BuildEmpty()
        # this exception condition is completely masked. re-enable it if the
        # structure of this code changes
        #if published and self.builds.getPublished(buildId):
        #    raise BuildPublished()
        pubReleaseId = published and pubReleaseId or None
        return self.updateBuild(buildId, {'pubReleaseId': pubReleaseId })

    @typeCheck(int)
    @private
    def getBuildPublished(self, buildId):
        return self.builds.getPublished(buildId)

    @typeCheck(int)
    @private
    def getImageTypes(self, releaseId):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        # old jobservers expect a list here
        imageTypes = [ self.getBuildType(buildId) ]
        return imageTypes

    @typeCheck(int)
    @private
    def getBuildType(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        cu = self.db.cursor()
        cu.execute("SELECT buildType FROM BuildsView WHERE buildId = ?",
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
        buildTypes = set(buildtypes.TYPES)

        if self.cfg.excludeBuildTypes:
            buildTypes -= set(self.cfg.excludeBuildTypes)

        if self.cfg.includeBuildTypes:
            buildTypes |= set(self.cfg.includeBuildTypes)

        # BOOTABLE_IMAGE should never be a valid image type, so make sure it's
        # removed
        buildTypes.remove(buildtypes.BOOTABLE_IMAGE)

        sortedList = sorted(buildTypes) 

        # make image-less the first one for UI display
        if (sortedList.index(buildtypes.IMAGELESS)):
            sortedList.remove(buildtypes.IMAGELESS)
            sortedList.reverse()
            sortedList.append(buildtypes.IMAGELESS)
            sortedList.reverse()

        return sortedList

    @typeCheck(int)
    @requiresAuth
    def startImageJob(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()

        # image-less builds (i.e. group trove builds) don't actually get built,
        # they just get stuffed into the DB
        buildDict = self.builds.get(buildId)
        buildType = buildDict['buildType']

        if buildType != buildtypes.IMAGELESS:
            mc = self._getMcpClient()
            data = self.serializeBuild(buildId)
            try:
                return mc.submitJob(data)
            except mcp_error.NotEntitledError:
                raise NotEntitledError()

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
        mc = self._getMcpClient()
        data = self.serializeGroupTrove(groupTroveId, arch)
        try:
            return mc.submitJob(data)
        except mcp_error.NotEntitledError:
            raise NotEntitledError()

    @typeCheck()
    @requiresAuth
    @private
    def getJobIds(self):
        raise NotImplementedError
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
        raise NotImplementedError
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

        raise NotImplementedError

        from mint import cooktypes

        # what to return if we no job has been started
        jobId = 0

        # scrub archTypes and jobTypes.
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")
        for arch in archTypes:
            if arch not in ("1#x86", "1#x86_64"):
                raise ParameterError("Not a legal architecture")

        buildTypes = []
        try:
            buildTypes = jobTypes['buildTypes']
        except KeyError:
            # This is to handle deprecated jobservers who insist on sending
            # imageTypes
            buildTypes = jobTypes.get('imageTypes', [])

        cookTypes = jobTypes.get('cookTypes', [])

        if sum([(x not in buildtypes.TYPES) \
                for x in buildTypes]):
            raise ParameterError("Not a legal Build Type")

        if sum([(x != cooktypes.GROUP_BUILDER) for x in cookTypes]):
            raise ParameterError("Not a legal Cook Type")

        if jobserverVersion not in jsversion.getVersions(self.cfg):
            raise ParameterError("Not a legal job server version: %s (wants: %s)" % \
                (jobserverVersion, str(jsversion.getVersions(self.cfg))))
        # client asked for nothing, client gets nothing.
        if not (buildTypes or cookTypes) or (not archTypes):
            return 0

        # the pid would suffice, except that fails to be good enough
        # if multiple web servers use one database backend.
        ownerId = (os.getpid() << 47) + random.randint(0, (2 << 47) - 1)

        # lock the jobs using ownerId
        try:
            cu = self.db.transaction()
            cu.execute("""UPDATE Jobs SET owner=?
                              WHERE owner IS NULL AND status=?""",
                       ownerId, jobstatus.WAITING)
            self.db.commit()
        except:
            # do nothing if we fail to lock any rows; we'll be back...
            self.db.rollback()
            return 0

        # we are now in a locked situation; wrap in try/finally
        # to ensure that no matter what happens, we unlock any rows 
        # we may have locked
        try:
            try:
                cu = self.db.transaction()
                archTypeQuery = archTypes and "(%s)" % \
                                ', '.join(['?' for x in archTypes]) or ''

                buildTypeQuery = buildTypes and "(%s)" % \
                                ', '.join(['?' for x in buildTypes]) or ''

                # at least one of buildTypes or cookTypes will be defined,
                # or this code would have already bailed out.
                if not buildTypes:
                    #client wants only cooks
                    query = """SELECT Jobs.jobId FROM Jobs
                               WHERE status=?
                                   AND Jobs.buildId IS NULL
                                   AND owner=?
                               ORDER BY timeSubmitted"""
                    cu.execute(query, jobstatus.WAITING, ownerId)
                elif not cookTypes:
                    # client wants only image jobs
                    query = """SELECT Jobs.jobId FROM Jobs
                               LEFT JOIN JobData
                                   ON Jobs.jobId=JobData.jobId
                                       AND JobData.name='arch'
                               LEFT JOIN BuildsView AS Builds
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
                               LEFT JOIN BuildsView AS Builds
                                   ON Builds.buildId=Jobs.buildId
                               LEFT JOIN BuildData
                                   ON BuildData.buildId=Jobs.buildId
                                       AND BuildData.name='jsversion'
                               WHERE status=? AND owner=?
                                   AND ((BuildData.value=? AND
                                       Builds.buildType IN %s) OR
                                        (groupTroveId IS NOT NULL))
                               ORDER BY timeSubmitted
                               """ % (buildTypeQuery)
                    cu.execute(query, jobstatus.WAITING, ownerId, jobserverVersion,
                               *(buildTypes))

                res = cu.fetchall()
                for r in res:
                    arch = deps.ThawFlavor(self.jobData.getDataValue(r[0], "arch")[1])
                    for x in archTypes:
                        if arch.satisfies(deps.ThawFlavor(x)):
                            jobId = r[0]
                            break # match first usable job we find
                    if jobId:
                        break

                if jobId:
                    cu.execute("""UPDATE Jobs
                                  SET status=?, statusMessage=?, timeStarted=?
                                  WHERE jobId=?""",
                               jobstatus.RUNNING, 'Starting', time.time(),
                               jobId)
                    if self.req:
                        self.jobData.setDataValue(jobId, "hostname", self.remoteIp, data.RDT_STRING)
                    cu.execute("SELECT jobId FROM Jobs WHERE status=?",
                               jobstatus.WAITING)
                    # this is done inside the job lock. there is a small chance of race
                    # condition, but the consequence would be that jobs might not
                    # reflect the correct number on admin page. if this proves to be
                    # too costly, move it outside the lock
                    for ordJobId in [x[0] for x in cu.fetchall()]:
                        cu.execute("UPDATE Jobs SET statusMessage=? WHERE jobId=?",
                                   self.getJobWaitMessage(ordJobId), ordJobId)

                self.db.commit()
            except:
                self.db.rollback()

        finally:
            # This absolutely must happen, so retry at most 10 times,
            # waiting one second between tries. Exceptions other than
            # DatabaseLocked are passed up to the caller.
            tries = 0
            while tries < 10:
                try:
                    cu = self.db.transaction()
                    cu.execute("""UPDATE Jobs SET owner=NULL
                                      WHERE owner=?""", ownerId)
                    self.db.commit()
                    break
                except:
                    # rollback and try again
                    self.db.rollback()
                    tries += 1
                    time.sleep(1)

        return jobId


    @typeCheck(int)
    @requiresAuth
    @private
    def getJobIdForBuild(self, buildId):
        raise NotImplementedError
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
        raise NotImplementedError
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
        raise NotImplementedError
        self._filterJobAccess(jobId)
        self.jobs.update(jobId, status = newStatus, statusMessage = statusMessage, timeFinished = time.time())
        return True

    @typeCheck(int, str, list, (list, str, int))
    def setBuildFilenamesSafe(self, buildId, outputToken, filenames):
        """
        This call validates the outputToken against one stored in the
        build data for buildId, and allows those filenames to be
        rewritten without any other access. This is so the job slave
        doesn't have to have any knowledge of the authuser or authpass,
        just the output hash given to it in the serialized job.
        """
        if outputToken != \
                self.buildData.getDataValue(buildId, 'outputToken')[1]:
            raise PermissionDenied

        ret = self._setBuildFilenames(buildId, filenames, normalize = True)
        self.buildData.removeDataValue(buildId, 'outputToken')

        return ret

    @typeCheck(int, str, str, str)
    def setBuildAMIDataSafe(self, buildId, outputToken, amiId, amiManifestName):
        """
        This call validates the outputToken as above.
        """
        if outputToken != \
                self.buildData.getDataValue(buildId, 'outputToken')[1]:
            raise PermissionDenied

        self.buildData.setDataValue(buildId, 'amiId', amiId, data.RDT_STRING)
        self.buildData.setDataValue(buildId, 'amiManifestName,',
                amiManifestName, data.RDT_STRING)
        self.buildData.removeDataValue(buildId, 'outputToken')
        return True

    @typeCheck(int, list, (list, str, int))
    @requiresAuth
    @private
    def setBuildFilenames(self, buildId, filenames):
        """
        This call expects a buildId and a 2- or 4-tuple of filename
        objects. The 2-tuple form is deprecated and is only here for 
        backwards compatibility.

        4-tuple form: (filename, title, size, sha1)
        2-tuple form: (filename, title)

        Returns True if it worked, False otherwise.
        """
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        if self.builds.getPublished(buildId):
            raise BuildPublished()

        return self._setBuildFilenames(buildId, filenames)

    def _setBuildFilenames(self, buildId, filenames, normalize = False):
        from mint.shimclient import ShimMintClient
        authclient = ShimMintClient(self.cfg, (self.cfg.authUser,
                                               self.cfg.authPass))

        build = authclient.getBuild(buildId)
        project = authclient.getProject(build.projectId)

        cu = self.db.transaction()
        try:
            # sqlite doesn't do delete cascade
            if self.db.driver == 'sqlite':
                cu.execute("""DELETE FROM BuildFilesUrlsMap WHERE fileId IN
                    (SELECT fileId FROM BuildFiles WHERE buildId=?)""",
                        buildId)
            cu.execute("DELETE FROM BuildFiles WHERE buildId=?", buildId)
            for idx, item in enumerate(filenames):
                if len(item) == 2:
                    fileName, title = item
                    sha1 = ''
                    size = 0
                elif len(item) == 4:
                    fileName, title, size, sha1 = item
                    
                    # Newer jobslaves will send this as a string; convert
                    # to a long for the database's sake (RBL-2789)
                    size = long(size)

                    if normalize:
                        # sanitize filename based on configuration
                        fileName = os.path.join(self.cfg.imagesPath, project.hostname,
                            str(buildId), os.path.basename(fileName))
                else:
                    self.db.rollback()
                    raise ValueError
                cu.execute("INSERT INTO BuildFiles VALUES(NULL, ?, ?, NULL, ?, ?, ?)", buildId, idx, title, size, sha1)
                fileId = cu.lastrowid
                cu.execute("INSERT INTO FilesUrls VALUES(NULL, ?, ?)",
                    urltypes.LOCAL, fileName)
                urlId = cu.lastrowid
                cu.execute("INSERT INTO BuildFilesUrlsMap VALUES(?, ?)",
                        fileId, urlId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    @typeCheck(int, int, int, str)
    @requiresAuth
    @private
    def addFileUrl(self, buildId, fileId, urlType, url):
        self._filterBuildFileAccess(fileId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        # Note bene: this can be done after a build has been published,
        # thus we don't have to check to see if the build is published.

        cu = self.db.transaction()
        try:
            # sanity check to make sure the fileId referenced exists
            cu.execute("SELECT fileId FROM BuildFiles where fileId = ?",
                    fileId)
            if not len(cu.fetchall()):
                raise BuildFileMissing()

            cu.execute("INSERT INTO FilesUrls VALUES(NULL, ?, ?)",
                    urlType, url)
            urlId = cu.lastrowid
            cu.execute("INSERT INTO BuildFilesUrlsMap VALUES(?, ?)",
                    fileId, urlId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    @typeCheck(int, int, int)
    @requiresAuth
    @private
    def removeFileUrl(self, buildId, fileId, urlId):
        self._filterBuildFileAccess(fileId)
        if not self.builds.buildExists(buildId):
            raise BuildMissing()
        cu = self.db.transaction()
        try:
            cu.execute("SELECT urlId FROM FilesUrls WHERE urlId = ?",
                    urlId)
            r = cu.fetchall()
            if not len(r):
                raise BuildFileUrlMissing()

            # sqlite doesn't support cascading delete
            if self.db.driver == 'sqlite':
                cu.execute("DELETE FROM BuildFilesUrlsMap WHERE urlId = ?",
                        urlId)
            cu.execute("DELETE FROM FilesUrls WHERE urlId = ?", urlId)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return True

    @typeCheck(int, (list, (list, str)))
    @requiresAuth
    @private
    def setImageFilenames(self, releaseId, filenames):
        """ Backwards-compatible call for older jobservers <= 1.6.3 """
        # releaseId -> buildId
        buildId = releaseId
        return self.setBuildFilenames(buildId, filenames)

    @typeCheck(int)
    @private
    def getBuildFilenames(self, buildId):
        self._filterBuildAccess(buildId)
        cu = self.db.cursor()
        cu.execute("""SELECT bf.fileId, bf.title, bf.idx, bf.size, bf.sha1,
                             u.urlId, u.urlType, u.url
                      FROM buildfiles bf
                           JOIN buildfilesurlsmap bffu
                             USING (fileId)
                           JOIN filesurls u
                             USING (urlId)
                      WHERE bf.buildId = ? ORDER BY bf.fileId""", buildId)

        results = cu.fetchall_dict()

        buildFilesList = []
        lastFileId = -1
        lastDict   = {}
        for x in results:
            if x['fileId'] != lastFileId:
                if lastDict:
                    buildFilesList.append(lastDict)

                lastFileId = x['fileId']
                lastDict = { 'fileId': x['fileId'],
                             'title': x['title'],
                             'idx': x['idx'],
                             'size': x['size'] or 0,
                             'sha1': x['sha1'] or '',
                             'fileUrls': [] }

            lastDict['fileUrls'].append((x['urlId'], x['urlType'], x['url']))
            if x['urlType'] == urltypes.LOCAL and not lastDict['size']:
                try:
                    lastDict['size'] = os.stat(x['url'])[stat.ST_SIZE]
                except (OSError, IOError):
                    lastDict['size'] = 0
            
            # convert size to a string for XML-RPC's sake (RBL-2789)
            lastDict['size'] = str(lastDict['size'])

        if lastDict:
            buildFilesList.append(lastDict)

        return buildFilesList

    @typeCheck(int, str)
    @private
    def addDownloadHit(self, urlId, ip):
        self.urlDownloads.add(urlId, ip)
        return True

    @typeCheck(int)
    @private
    def getFileInfo(self, fileId):
        self._filterBuildFileAccess(fileId)
        cu = self.db.cursor()
        cu.execute("""SELECT bf.buildId, bf.idx, bf.title, fu.urlId, fu.urlType, fu.url
                      FROM BuildFiles bf
                         JOIN BuildFilesUrlsMap USING (fileId)
                         JOIN FilesUrls fu USING (urlId)
                      WHERE fileId=?""", fileId)

        r = cu.fetchall()
        if r:
            info = r[0]
            filenames = [ (x[3], x[4], x[5]) for x in r ]
            return info[0], info[1], info[2], filenames
        else:
            raise FileMissing

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

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getAllTroveLabels(self, projectId, serverName, troveName):
        self._filterProjectAccess(projectId)

        project = projects.Project(self, projectId)
        nc = self._getProjectRepo(project)

        troves = nc.getAllTroveLeaves(str(serverName), {str(troveName): None})
        if troveName in troves:
            ret = sorted(list(set(str(x.branch().label()) for x in troves[troveName])))
        else:
            ret = []
        return ret

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getTroveVersions(self, projectId, labelStr, troveName):
        self._filterProjectAccess(projectId)

        project = projects.Project(self, projectId)
        nc = self._getProjectRepo(project)

        troves = nc.getTroveVersionsByLabel({str(troveName): {versions.Label(str(labelStr)): None}})[troveName]
        versionDict = dict((x.freeze(), [y for y in troves[x]]) for x in troves)
        versionList = sorted(versionDict.keys(), reverse = True)

        # insert a tuple of (flavor differences, full flavor) into versionDict
        strFlavor = lambda x: str(x) and str(x).replace(',', ', ') or '(no flavor)'
        for v, fList in versionDict.items():
            diffDict = deps.flavorDifferences(fList)
            versionDict[v] = sorted([(not diffDict[x].isEmpty() and str(diffDict[x]) or strFlavor(x), str(x)) for x in fList])

        return [versionDict, versionList]

    @typeCheck(int)
    @requiresAuth
    def getAllProjectLabels(self, projectId):
        defaultLabel = projects.Project(self, projectId).getLabel()
        serverName = versions.Label(defaultLabel).getHost()
        cu = self.db.cursor()
        cu.execute("""SELECT DISTINCT(%s) FROM PackageIndex WHERE projectId=?
                      AND serverName=?""" % database.concat(self.db,
                            'serverName', '"@"',  'branchName'),
                      projectId, serverName)
        labels = cu.fetchall()
        return [x[0] for x in labels] or [defaultLabel]

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

        buildDict = self.builds.get(buildId)
        buildType = buildDict['buildType'] 
        count = buildDict['buildCount']

        uuid = '%s.%s-build-%d-%d' %(self.cfg.hostName,
                                  self.cfg.externalDomainName, buildId, count)

        if buildType != buildtypes.IMAGELESS:
            mc = self._getMcpClient()
            try:
                status, message = mc.jobStatus(uuid)
            except mcp_error.UnknownJob:
                status, message = \
                    jobstatus.NO_JOB, jobstatus.statusNames[jobstatus.NO_JOB]
        else:
            # status is always finished since no build is actually done
            status, message = jobstatus.FINISHED, \
                jobstatus.statusNames[jobstatus.FINISHED]

        return { 'status' : status, 'message' : message }

    @typeCheck(unicode)
    @requiresAuth
    def getJobStatus(self, uuid):

        # FIXME: re-enable filtering based on UUID
        #self._filterJobAccess(jobId)

        buildId = helperfuncs.getBuildIdFromUuid(uuid)
        buildDict = self.builds.get(buildId)
        buildType = buildDict['buildType']

        if buildtype != buildtypes.IMAGELESS:
            mc = self._getMcpClient()

            try:
                status, message = mc.jobStatus(uuid)
            except mcp_error.UnknownJob:
                status, message = \
                    jobstatus.NO_JOB, jobstatus.statusNames[jobstatus.NO_JOB]
        else:
            # status is always finished since no build is actually done
            status, message = jobstatus.FINISHED, \
                jobstatus.statusNames[jobstatus.FINISHED]

        return { 'status' : status, 'message' : message }

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
        return True

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
        projectLabels = self.labels.getLabelsForProject( \
            groupTrove['projectId'])[0].keys()
        for label in projectLabels:
            if label in recipeLabels:
                recipeLabels.remove(label)
        recipeLabels.sort()
        for label in projectLabels:
            recipeLabels.insert(0, label)
        return recipeLabels

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

    def _stripKeys(self, dictList, *keys):
        res = []
        for origDict in dictList:
            newDict = {}
            for key in origDict:
                if key not in keys:
                    newDict[key] = origDict[key]
            res.append(newDict)
        return res

    @private
    @typeCheck(int, str)
    @requiresAuth
    def serializeGroupTrove(self, groupTroveId, arch):
        # performed at the mint server level to have access to
        # groupTrove, project and groupTroveItems objects
        projectId = self.groupTroves.getProjectId(groupTroveId)
        self._filterProjectAccess(projectId)

        groupTrove = grouptrove.GroupTrove(self, groupTroveId)
        project = projects.Project(self, groupTrove.projectId)

        cc = project.getConaryConfig()
        cc.entitlementDirectory = os.path.join(self.cfg.dataPath, 'entitlements')
        cc.readEntitlementDirectory()

        # Ignore conaryProxy set by getConaryConfig; it's bound
        # to be localhost, as getConaryConfig() generates
        # config objects intended to be used by NetClient /
        # ConaryClient objects internal to rBuilder (i.e. not the
        # jobslaves)
        cc.conaryProxy = None

        cfgBuffer = StringIO.StringIO()
        cc.display(cfgBuffer)
        cfgData = cfgBuffer.getvalue().split("\n")

        allowedOptions = ['repositoryMap', 'user', 'conaryProxy', 'entitlement']
        cfgData = "\n".join([x for x in cfgData if x.split(" ")[0] in allowedOptions])

        if self.cfg.createConaryRcFile:
            cfgData += "\nincludeConfigFile http://%s%s/conaryrc\n" % \
                (self.cfg.siteHost, self.cfg.basePath)

        mc = self._getMcpClient()

        r = {}
        r['protocolVersion'] = grouptrove.PROTOCOL_VERSION
        r['type'] = 'cook'

        r['recipeName'] = groupTrove.recipeName
        r['upstreamVersion'] = groupTrove.upstreamVersion

        r['autoResolve'] = groupTrove.autoResolve

        try:
            jsversion = mc.getJSVersion()
        except mcp_error.NotEntitledError:
            raise NotEntitledError()
        r['data'] = {'arch' : arch,
                     'jsversion': str(jsversion)}

        r['description'] = groupTrove.description

        r['troveItems'] = self._stripKeys(self.groupTroveItems.listByGroupTroveId(groupTroveId), 'baseUrl', 'groupTroveItemId', 'groupTroveId', 'creatorId')
        r['removedComponents'] = self.groupTroveRemovedComponents.list(groupTroveId)

        r['label'] = project.getLabel()
        r['labelPath'] = self.getGroupTroveLabelPath(groupTroveId)
        r['repositoryMap'] = cc.repositoryMap

        r['project'] = {'name' : project.name,
                        'hostname' : project.hostname,
                        'label' : project.getLabel(),
                        'conaryCfg' : cfgData}

        r['UUID'] = '%s.%s-cook-%d-%d' % \
                         (self.cfg.hostName,
                          self.cfg.externalDomainName,
                          groupTrove.id,
                          self.groupTroves.bumpCookCount(groupTroveId))

        return simplejson.dumps(r)

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
        if name not in reports.__dict__:
            raise InvalidReport
        repModule = reports.__dict__[name]
        for objName in repModule.__dict__.keys():
            try:
                if objName != 'MintReport' and \
                       MintReport in repModule.__dict__[objName].__bases__:
                    return repModule.__dict__[objName](self.db)
            except AttributeError:
                pass

    @private
    @typeCheck(str)
    @requiresAdmin
    def getReport(self, name):
        if name not in reports.getAvailableReports():
            raise InvalidReport
        return self._getReportObject(name).getReport()

    @private
    @typeCheck(str)
    @requiresAdmin
    def getReportPdf(self, name):
        if name not in reports.getAvailableReports():
            raise PermissionDenied
        return base64.b64encode(self._getReportObject(name).getPdf())

    @private
    @typeCheck(int, int, str)
    def getDownloadChart(self, projectId, days, format):
        chart = charts.DownloadChart(self.db, projectId, span = days)
        return chart.getImageData(format)

    # mirrored labels
    @private
    @typeCheck(int, (list, str), str, str, str, str, str, bool)
    @requiresAdmin
    def addInboundMirror(self, targetProjectId, sourceLabels,
            sourceUrl, authType, sourceUsername, sourcePassword,
            sourceEntitlement, allLabels):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM InboundMirrors")
        mirrorOrder = cu.fetchone()[0]

        x = self.inboundMirrors.new(targetProjectId=targetProjectId,
                sourceLabels = ' '.join(sourceLabels),
                sourceUrl = sourceUrl, sourceAuthType=authType,
                sourceUsername = sourceUsername,
                sourcePassword = sourcePassword,
                sourceEntitlement = sourceEntitlement,
                mirrorOrder = mirrorOrder, allLabels = allLabels)

        fqdn = versions.Label(sourceLabels[0]).getHost()
        if not os.path.exists(os.path.join(self.cfg.reposPath, fqdn)):
            self.projects.createRepos(self.cfg.reposPath, self.cfg.reposContentsDir,
                fqdn.split(".")[0], ".".join(fqdn.split(".")[1:]))

        self._generateConaryRcFile()
        return x

    @private
    @typeCheck(int, (list, str), str, str, str, str, str, bool)
    @requiresAdmin
    def editInboundMirror(self, targetProjectId, sourceLabels,
            sourceUrl, authType, sourceUsername, sourcePassword,
            sourceEntitlement, allLabels):
        x = self.inboundMirrors.update(targetProjectId,
                sourceLabels = ' '.join(sourceLabels),
                sourceUrl = sourceUrl, sourceAuthType = authType, 
                sourceUsername = sourceUsername,
                sourcePassword = sourcePassword,
                sourceEntitlement=sourceEntitlement,
                allLabels = allLabels)
        self._generateConaryRcFile()
        return x

    @private
    @typeCheck()
    @requiresAdmin
    def getInboundMirrors(self):
        cu = self.db.cursor()
        cu.execute("""SELECT inboundMirrorId, targetProjectId, sourceLabels, sourceUrl,
            sourceAuthType, sourceUsername, sourcePassword, sourceEntitlement, allLabels
            FROM InboundMirrors ORDER BY mirrorOrder""")
        return [[y is not None and y or '' for y in x[:-1]] + \
                [x[-1]] for x in cu.fetchall()]

    @private
    @typeCheck(int)
    @requiresAdmin
    def getInboundMirror(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM InboundMirrors WHERE targetProjectId=?", projectId)
        x = cu.fetchone_dict()
        if x:
            return x
        else:
            return {}

    @private
    @typeCheck(int)
    @requiresAdmin
    def delInboundMirror(self, inboundMirrorId):
        self.inboundMirrors.delete(inboundMirrorId)
        self._normalizeOrder("InboundMirrors", "inboundMirrorId")
        return True

    @private
    @typeCheck(int, (list, str), bool, bool, bool, int)
    @requiresAdmin
    def addOutboundMirror(self, sourceProjectId, targetLabels,
            allLabels, recurse, useReleases, id):
        if id != -1:
            self.outboundMirrors.update(id, sourceProjectId = sourceProjectId,
                                       targetLabels = ' '.join(targetLabels),
                                       allLabels = allLabels,
                                       recurse = recurse,
                                       useReleases=useReleases,
                                       fullSync = True)
        else:
            cu = self.db.cursor()
            cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM OutboundMirrors")
            mirrorOrder = cu.fetchone()[0]
            id = self.outboundMirrors.new(sourceProjectId = sourceProjectId,
                                           targetLabels = ' '.join(targetLabels),
                                           allLabels = allLabels,
                                           recurse = recurse,
                                           useReleases=useReleases,
                                           mirrorOrder = mirrorOrder,
                                           fullSync = True)
        return id

    @private
    @typeCheck(int, list)
    @requiresAdmin
    def setOutboundMirrorTargets(self, outboundMirrorId, updateServiceIds):
        return self.outboundMirrorsUpdateServices.setTargets(outboundMirrorId,
               updateServiceIds)

    @private
    @typeCheck(int)
    @requiresAdmin
    def delOutboundMirror(self, outboundMirrorId):
        self.outboundMirrors.delete(outboundMirrorId)
        self._normalizeOrder("OutboundMirrors", "outboundMirrorId")
        return True

    @private
    @typeCheck(int, (list, str))
    @requiresAdmin
    def setOutboundMirrorMatchTroves(self, outboundMirrorId, matchStringList):
        if isinstance(matchStringList, str):
            matchStringList = [ str ]
        if [x for x in matchStringList if x[0] not in ('-', '+')]:
            raise ParameterError("First character of each matchString must be + or -")
        self.outboundMirrors.update(outboundMirrorId, matchStrings = ' '.join(matchStringList))
        return True

    @private
    @typeCheck(int)
    @requiresAdmin
    def getOutboundMirrorMatchTroves(self, outboundMirrorId):
        r = self.outboundMirrors.get(outboundMirrorId, fields=['matchStrings'])
        matchStrings = r.get('matchStrings', '')
        return matchStrings.split()

    @private
    @typeCheck(int)
    @requiresAdmin
    def getOutboundMirrorGroups(self, outboundMirrorId):
        r = self.outboundMirrors.get(outboundMirrorId, fields=['matchStrings'])
        matchStrings = r.get('matchStrings', '')
        return [g.replace('+','') for g in matchStrings.split() if g.startswith('+group-')]

    @private
    @typeCheck()
    @requiresAdmin
    def getOutboundMirrors(self):
        return self.outboundMirrors.getOutboundMirrors()

    @private
    @typeCheck(int, bool)
    @requiresAdmin
    def setOutboundMirrorSync(self, outboundMirrorId, fullSync):
        self.outboundMirrors.update(outboundMirrorId, fullSync=fullSync)
        return True

    @private
    @typeCheck(int)
    @requiresAdmin
    def getOutboundMirror(self, outboundMirrorId):
        return self.outboundMirrors.get(outboundMirrorId)

    @private
    @typeCheck(int)
    @requiresAdmin
    def getOutboundMirrorTargets(self, outboundMirrorId):
        return self.outboundMirrorsUpdateServices.getOutboundMirrorTargets(outboundMirrorId)

    @private
    @requiresAdmin
    @typeCheck(str, str, str, ((str, unicode),))
    def addUpdateService(self, hostname, adminUser, adminPassword,
            description=''):
        mirrorUser, mirrorPassword = \
                self._configureUpdateService(hostname, adminUser,
                        adminPassword)
        return self.updateServices.new(hostname = hostname,
                description = description,
                mirrorUser = mirrorUser,
                mirrorPassword = mirrorPassword)

    @private
    @requiresAdmin
    @typeCheck(int)
    def getUpdateService(self, upsrvId):
        try:
            ret = self.updateServices.get(upsrvId)
        except database.ItemNotFound:
            raise UpdateServiceNotFound()
        else:
            return ret

    @private
    @requiresAdmin
    @typeCheck(int, ((str, unicode),)) 
    def editUpdateService(self, upsrvId, newDesc):
        return self.updateServices.update(upsrvId, description = newDesc)

    @private
    @requiresAdmin
    @typeCheck(int)
    def delUpdateService(self, upsrvId):
        return self.updateServices.delete(upsrvId)

    @private
    @typeCheck()
    @requiresAdmin
    def getUpdateServiceList(self):
        return self.updateServices.getUpdateServiceList()

    @private
    @typeCheck(int)
    def isLocalMirror(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT EXISTS(SELECT *
            FROM InboundMirrors
            WHERE targetProjectId=?)""", projectId)
        return bool(cu.fetchone()[0])

    @private
    @typeCheck(int, int)
    def setInboundMirrorOrder(self, mirrorId, order):
        return self._setMirrorOrder("InboundMirrors", "inboundMirrorId", mirrorId, order)

    @private
    @typeCheck(int, int)
    def setOutboundMirrorOrder(self, mirrorId, order):
        return self._setMirrorOrder("OutboundMirrors", "outboundMirrorId", mirrorId, order)

    def _setMirrorOrder(self, table, idField, mirrorId, order):
        cu = self.db.cursor()

        # other id
        cu.execute("SELECT %s FROM %s WHERE mirrorOrder=?" % (idField, table), order)
        oldId = cu.fetchone()
        if oldId:
            oldId = oldId[0]

        # current order
        cu.execute("SELECT mirrorOrder FROM %s WHERE %s=?" % (table, idField), mirrorId)
        oldOrder = cu.fetchone()
        if oldOrder:
            oldOrder = oldOrder[0]

        updates = [(order, mirrorId)]
        if oldId is not None and oldOrder is not None:
            updates.append((oldOrder, oldId))

        # swap
        cu.executemany("UPDATE %s SET mirrorOrder=? WHERE %s=?" % (table, idField), updates)
        self.db.commit()

        return self._normalizeOrder(table, idField)

    def _normalizeOrder(self, table, idField):
        # normalize mirror order, in case of deletions
        updates = []
        cu = self.db.cursor()
        cu.execute("SELECT %s FROM %s ORDER BY mirrorOrder"  % (idField, table))
        for i, x in enumerate(cu.fetchall()):
            updates.append((i, x[0]))

        cu.executemany("UPDATE %s SET mirrorOrder=? WHERE %s=?" % (table, idField), updates)
        self.db.commit()
        return True

    @private
    @typeCheck(str, str)
    @requiresAdmin
    def addRemappedRepository(self, fromName, toName):
        return self._addRemappedRepository(fromName, toName)

    def _addRemappedRepository(self, fromName, toName):
        return self.repNameMap.new(fromName = fromName, toName = toName)

    @private
    @typeCheck(str)
    @requiresAdmin
    def delRemappedRepository(self, fromName):
        cu = self.db.cursor()
        cu.execute("DELETE FROM RepNameMap WHERE fromName=?", fromName)
        self.db.commit()
        return True

    def _getAllRepositories(self):
        """
            Return a list of netclient objects for each repository
            rBuilder knows about and the current user has access to.
        """
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM Projects")

        repos = []
        for projectId in [x[0] for x in cu.fetchall()]:
            if self._checkProjectAccess(projectId, userlevels.LEVELS):
                p = projects.Project(self, projectId)
                repo = self._getProjectRepo(p)
                repos.append((p, repo))

        return repos

    def _getProjectByLabel(self, label):
        hostname = label.getHost()
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Labels WHERE label LIKE '%s@%%'" % hostname)
        r = cu.fetchone()
        if r:
            return projects.Project(self, r[0])
        else:
            return None

    @private
    @typeCheck(str, str, (list, str))
    def getTroveReferences(self, troveName, troveVersion, troveFlavors):
        references = []

        if not troveFlavors:
            v = versions.VersionFromString(troveVersion)
            project = self._getProjectByLabel(v.branch().label())

            repos = self._getProjectRepo(project)
            flavors = repos.getAllTroveFlavors({troveName: [v]})
            troveFlavors = [x.freeze() for x in flavors[troveName][v]]

        q = []
        for flavor in troveFlavors:
            q.append((troveName, versions.VersionFromString(troveVersion), deps.ThawFlavor(flavor)))

        for p, repo in self._getAllRepositories():
            host = versions.Label(p.getLabel()).getHost()
            refs = repo.getTroveReferences(host, q)

            results = set()
            for ref in refs:
                if ref:
                    results.update([(x[0], str(x[1]), x[2].freeze()) for x in ref])

            if results:
                references.append((int(p.id), list(results)))

        return references

    @private
    @typeCheck(str, str, str)
    def getTroveDescendants(self, troveName, troveBranch, troveFlavor):
        descendants = []
        for p, repo in self._getAllRepositories():
            q = (troveName, versions.VersionFromString(troveBranch), deps.ThawFlavor(troveFlavor))
            host = versions.Label(p.getLabel()).getHost()
            refs = repo.getTroveDescendants(host, [q])

            results = set()
            for ref in refs:
                if ref:
                    results.update([(str(x[0]), x[1].freeze()) for x in ref])

            if results:
                descendants.append((int(p.id), list(results)))

        return descendants

    # *** MCP RELATED FUNCTIONS ***
    # always use this method to get an MCP client so that it can be cached
    def _getMcpClient(self):
        if not self.mcpClient:
            mcpClientCfg = mcpClient.MCPClientConfig()

            try:
                mcpClientCfg.read(os.path.join(self.cfg.dataPath,
                                               'mcp', 'client-config'))
            except CfgEnvironmentError:
                # If there is no client-config, default to localhost
                pass

            self.mcpClient = mcpClient.MCPClient(mcpClientCfg)
        return self.mcpClient

    def __del__(self):
        if self.mcpClient:
            self.mcpClient.disconnect()

    #
    # EC2 Support for rBO
    #

    @typeCheck(str, str)
    @requiresAdmin
    @private
    def createBlessedAMI(self, ec2AMIId, shortDescription):
        return self.blessedAMIs.new(ec2AMIId = ec2AMIId,
                shortDescription = shortDescription,
                instanceTTL = self.cfg.ec2DefaultInstanceTTL,
                mayExtendTTLBy = self.cfg.ec2DefaultMayExtendTTLBy)

    @typeCheck(int)
    @private
    def getBlessedAMI(self, blessedAMIsId):
        return self.blessedAMIs.get(blessedAMIsId)

    @typeCheck(int, dict)
    @private
    @requiresAdmin
    def updateBlessedAMI(self, blessedAMIId, valDict):
        if len(valDict):
            return self.blessedAMIs.update(blessedAMIId, **valDict)

    @private
    def getAvailableBlessedAMIs(self):
        return self.blessedAMIs.getAvailable()

    @typeCheck(int)
    @private
    def getLaunchedAMI(self, launchedAMIId):
        return self.launchedAMIs.get(launchedAMIId)

    @typeCheck(int, dict)
    @private
    @requiresAdmin
    def updateLaunchedAMI(self, launchedAMIId, valDict):
        if len(valDict):
            return self.launchedAMIs.update(launchedAMIId, **valDict)

    @private
    def getActiveLaunchedAMIs(self):
        return self.launchedAMIs.getActive()

    @typeCheck(int)
    @private
    def getLaunchedAMIInstanceStatus(self, launchedAMIId):
        ec2Wrapper = ec2.EC2Wrapper(self.cfg)
        rs = self.launchedAMIs.get(launchedAMIId, fields=['ec2InstanceId'])
        return ec2Wrapper.getInstanceStatus(rs['ec2InstanceId'])

    @typeCheck(int)
    @private
    def launchAMIInstance(self, blessedAMIId):
        # get blessed instance
        try:
            bami = self.blessedAMIs.get(blessedAMIId)
        except ItemNotFound:
            raise ec2.FailedToLaunchAMIInstance()

        launchedFromIP = self.remoteIp
        if ((self.launchedAMIs.getCountForIP(launchedFromIP) + 1) > \
                self.cfg.ec2MaxInstancesPerIP):
           raise ec2.TooManyAMIInstancesPerIP()

        userDataTemplate = bami['userDataTemplate']

        # generate the rAA Password
        if self.cfg.ec2GenerateTourPassword:
            from mint.users import newPassword
            raaPassword = newPassword(length=8)
        else:
            raaPassword = 'password'

        if userDataTemplate:
            userData = userDataTemplate.replace('@RAPAPASSWORD@',
                    raaPassword)
        else:
            userData = None

        # attempt to boot it up
        ec2Wrapper = ec2.EC2Wrapper(self.cfg)
        ec2InstanceId = ec2Wrapper.launchInstance(bami['ec2AMIId'],
                userData=userData,
                useNATAddressing=self.cfg.ec2UseNATAddressing)

        if not ec2InstanceId:
            raise ec2.FailedToLaunchAMIInstance()

        # store the instance information in our database
        return self.launchedAMIs.new(blessedAMIId = bami['blessedAMIId'],
                ec2InstanceId = ec2InstanceId,
                launchedFromIP = launchedFromIP,
                raaPassword = raaPassword,
                expiresAfter = toDatabaseTimestamp(offset=bami['instanceTTL']),
                launchedAt = toDatabaseTimestamp(),
                userData = userData)

    @requiresAdmin
    @private
    def terminateExpiredAMIInstances(self):
        ec2Wrapper = ec2.EC2Wrapper(self.cfg)
        instancesToKill = self.launchedAMIs.getCandidatesForTermination()
        instancesKilled = []
        for launchedAMIId, ec2InstanceId in instancesToKill:
            if ec2Wrapper.terminateInstance(ec2InstanceId):
                self.launchedAMIs.update(launchedAMIId, isActive = False)
                instancesKilled.append(launchedAMIId)
        return instancesKilled

    @typeCheck(int)
    @private
    def extendLaunchedAMITimeout(self, launchedAMIId):
        lami = self.launchedAMIs.get(launchedAMIId)
        bami = self.blessedAMIs.get(lami['blessedAMIId'])
        newExpiresAfter = toDatabaseTimestamp(fromDatabaseTimestamp(lami['launchedAt']), offset=bami['instanceTTL'] + bami['mayExtendTTLBy'])
        self.launchedAMIs.update(launchedAMIId,
                expiresAfter = newExpiresAfter)
        return True

    @typeCheck(((unicode, str),), (list, int))
    @private
    def checkHTTPReturnCode(self, uri, expectedCodes):
        if not expectedCodes:
            expectedCodes = [200, 301, 302]
        code = -1
        opener = urllib.URLopener()
        try:
            f = opener.retrieve(uri)
            return True
        except IOError, ioe:
            if ioe[0] == 'http error':
                code = ioe[1]

        return (code in expectedCodes)

    @private
    def getProxies(self):
        return self._getProxies()

    @private
    @requiresAuth
    @typeCheck(int, str, ((str, unicode),))
    def addProductVersion(self, projectId, name, description):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise PermissionDenied
        
        # make sure it is a valid product version
        self._validateProductVersion(name)
        
        try:
            return self.productVersions.new(projectId = projectId,
                                                 name = name,
                                                 description = description) 
        except DuplicateItem:
            raise DuplicateProductVersion

    @private
    @requiresAuth
    @typeCheck(int)
    def getProductVersion(self, versionId):
        try:
            ret = self.productVersions.get(versionId)
        except database.ItemNotFound:
            raise ProductVersionNotFound()
        else:
            return ret

    @private
    @requiresAuth
    @typeCheck(int)
    def getStagesForProductVersion(self, versionId):
        pd = self._getProductDefinitionForVersionObj(versionId)
        return [s.name for s in pd.getStages()]

    @private
    @requiresAuth
    @typeCheck(int)
    def getProductDefinitionForVersion(self, versionId):
        pd = self._getProductDefinitionForVersionObj(versionId)
        sio = StringIO.StringIO()
        pd.serialize(sio)
        return sio.getvalue()

    @private
    @requiresAuth
    @typeCheck(int, ((str, unicode),))
    def setProductDefinitionForVersion(self, versionId,
            productDefinitionXMLString):
        # XXX: Need exception handling here
        pd = proddef.ProductDefinition(fromStream=productDefinitionXMLString)
        version = projects.ProductVersions(self, versionId)
        project = projects.Project(self, version.projectId)

        # TODO put back overrides

        projectCfg = project.getConaryConfig()
        projectCfg['name'] = self.auth.username
        projectCfg['contact'] = self.auth.fullName or ''
        cclient = conaryclient.ConaryClient(projectCfg)
        pd.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')
        return True

    @private
    @requiresAuth
    @typeCheck(int, ((str, unicode),))
    def editProductVersion(self, versionId, newDesc):
        return self.productVersions.update(versionId, description = newDesc)

    @private
    @typeCheck(int)
    @requiresAuth
    def getProductVersionListForProduct(self, projectId):
        return self.productVersions.getProductVersionListForProduct(projectId)

    @private
    @requiresAuth
    @typeCheck(int, ((str, unicode),))
    def getBuildTaskListForDisplay(self, versionId, stageName):
        """
        Get a list of build tasks to be completed for display purposes only
        @param versionId: the product version id
        @param stageName: the name of the stage to use
        @return: a list of task dicts as 
                 {buildName, buildTypeName, buildFlavorName, imageGroup}
        """

        taskList = []
        pd = self._getProductDefinitionForVersionObj(versionId)
        builds = pd.getBuildsForStage(stageName)
        stageLabel = pd.getLabelForStage(stageName)
        for build in builds:
            task = dict()

            # set the build name
            task['buildName'] = build.getBuildName()

            # set the build type
            buildTypeDt = buildtemplates.getDataTemplateByXmlName(
                              build.getBuildImageType().getTag())
            task['buildTypeName'] = buildtypes.typeNamesMarketing[buildTypeDt.id]

            # get the name of the flavor.  If we don't have a name mapped to
            # it, specify that it is custom
            flavor = build.getBuildBaseFlavor()
            if buildtypes.buildDefinitionFlavorToFlavorMapRev.has_key(flavor):
                index = buildtypes.buildDefinitionFlavorToFlavorMapRev[flavor]
                buildFlavor = buildtypes.buildDefinitionFlavorNameMap[index]
            else:
                buildFlavor = "Custom Flavor: %s" % flavor
            task['buildFlavorName'] = buildFlavor

            # set the image group
            task['imageGroup'] = "%s=%s" % (build.getBuildImageGroup(),
                    stageLabel)

            taskList.append(task)

        return taskList


    def __init__(self, cfg, allowPrivate = False, alwaysReload = False, db = None, req = None):
        self.cfg = cfg
        self.req = req
        self.mcpClient = None

        global callLog
        if self.cfg.xmlrpcLogFile:
            if not callLog:
                callLog = CallLogger(self.cfg.xmlrpcLogFile, [self.cfg.siteHost])
        self.callLog = callLog

        if self.req:
            self.remoteIp = self.req.headers_in.get("X-Forwarded-For",
                    self.req.connection.remote_ip)
        else:
            self.remoteIp = "0.0.0.0"

        # sanitize IP just in case it's a list of proxied hosts
        self.remoteIp = self.remoteIp.split(',')[0]

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

        genConaryRc = False
        global tables
        if not tables or alwaysReload:
            tables = getTables(self.db, self.cfg)
            genConaryRc = True

        for table in tables:
            tables[table].db = self.db
            tables[table].cfg = self.cfg
            self.__dict__[table] = tables[table]

        self.users.confirm_table.db = self.db
        self.newsCache.ageTable.db = self.db
        self.projects.reposDB.cfg = self.cfg

        if genConaryRc:
            self._generateConaryRcFile()

            # do these only on table reloads too
            self._normalizeOrder("OutboundMirrors", "outboundMirrorId")
            self._normalizeOrder("InboundMirrors", "inboundMirrorId")


        self.newsCache.refresh()
