#
# Copyright (c) SAS Institute Inc.
#

import base64
import errno
import logging
import os
import re
import json
import socket
import stat
import sys
import time
import tempfile
import StringIO

from mint import buildtypes
from mint.db import database as mint_database
from mint.rest.db import database as rest_database
from mint import users
from mint.lib import data
from mint.lib import database
from mint.lib import maillib
from mint.lib import profile
from mint.lib import siteauth
from mint.lib.mintutils import ArgFiller
from mint import builds
from mint import ec2
from mint import helperfuncs
from mint import jobstatus
from mint import maintenance
from mint import mint_error
from mint import buildtemplates
from mint import projects
from mint import reports
from mint import templates
from mint import userlevels
from mint import usertemplates
from mint import urltypes
from mint.db import repository
from mint.reports import MintReport
from mint.image_gen.wig import client as wig_client
from mint import packagecreator
from mint.rest import errors as rest_errors
from mint.scripts import repository_sync

from conary import conarycfg
from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec
from conary.deps import deps
from conary.lib import networking as cny_net
from conary.lib import sha1helper
from conary.lib import util
from conary.lib.http import http_error
from conary.lib.http import request as cny_req
from conary.repository.errors import TroveNotFound, UserNotFound
from conary.repository import netclient
from conary.repository.netrepos.reposlog import RepositoryCallLogger as CallLogger
from conary import errors as conary_errors

from mcp import client as mcp_client
from mcp import mcp_error
from rmake.lib import procutil
from rmake3 import client as rmk_client
from rpath_proddef import api1 as proddef
from pcreator import errors as pcreator_errors


import gettext
gettext.install('rBuilder')

SERVER_VERSIONS = [8]
# XMLRPC Schema History
# Version 8
# * Added preexisting data retrieval to getPackageFactories*
# Version 7
#  * Added package creator methods
#  * Added namespace parameter to newPackage, addProductVersion
# Version 6
#  * Reworked exception marshalling API. All exceptions derived from MintError
#    are now marshalled automatically.

# first argument needs to be fairly unique so that we can detect
# detect old (unversioned) clients.
VERSION_STRINGS = ["RBUILDER_CLIENT:%d" % x for x in SERVER_VERSIONS]

log = logging.getLogger(__name__)

reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'lists']
reservedExtHosts = ['admin', 'mail', 'mint', 'www', 'web', 'wiki', 'lists']
# XXX do we need to reserve localhost?
# XXX reserve proxy hostname (see cfg.proxyHostname) if it's not
#     localhost
# valid product version
validProductVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')

callLog = None

def deriveBaseFunc(func):
    r = func
    while hasattr(r, '__wrapped_func__'):
        r = r.__wrapped_func__
    return r

def requiresAdmin(func):
    def wrapper(self, *args, **kwargs):
        if self.auth.admin or list(self.authToken) == [self.cfg.authUser, self.cfg.authPass]:
            return func(self, *args, **kwargs)
        else:
            raise mint_error.PermissionDenied
    wrapper.__wrapped_func__ = func
    return wrapper

def requiresAuth(func):
    def wrapper(self, *args, **kwargs):
        if self.auth.authorized or list(self.authToken) == [self.cfg.authUser, self.cfg.authPass]:
            return func(self, *args, **kwargs)
        else:
            raise mint_error.PermissionDenied
    wrapper.__wrapped_func__ = func
    return wrapper

def requiresCfgAdmin(cond):
    def deco(func):
        def wrapper(self, *args, **kwargs):
            if (list(self.authToken) == \
                [self.cfg.authUser, self.cfg.authPass]) or self.auth.admin or \
                 (not self.cfg.__getitem__(cond) and self.auth.authorized):
                    return func(self, *args, **kwargs)
            else:
                raise mint_error.PermissionDenied
        wrapper.__wrapped_func__ = func
        return wrapper
    return deco

def private(func):
    """Mark a method as callable only if self._allowPrivate is set
    to mask out functions not callable via XMLRPC over the web."""
    def wrapper(self, *args, **kwargs):
        if self._allowPrivate:
            return func(self, *args, **kwargs)
        else:
            raise mint_error.PermissionDenied
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
                    elif type(param) is util.ProtectedString:
                        # allow protected passwords through
                        return True
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
        baseFunc = deriveBaseFunc(func)
        filler = ArgFiller.fromFunc(baseFunc)

        underlying = len(filler.names) - 1 # remove self
        if underlying != len(paramTypes):
            raise TypeError("paramTypes got %d arguments but the underlying "
                    "method %s has %d" % (len(paramTypes), baseFunc.func_name,
                        underlying))

        def wrapper(*args, **kwargs):
            # Collapse keyword arguments to positional ones
            args = filler.fill(args, kwargs)
            del kwargs

            # [1:] here to skip 'self'
            for name, default, arg, ptype in zip(filler.names[1:], filler.defaults[1:],
                    args[1:], paramTypes):
                if arg is not default and not checkParam(arg, ptype):
                    if isinstance(ptype, tuple):
                        types = ', '.join(x.__name__ for x in ptype)
                    elif isinstance(ptype, type):
                        types = ptype.__name__
                    else:
                        types = '<unknown>'
                    raise mint_error.ParameterError("%s was passed %r of "
                            "type %s when expecting %s for parameter %s"
                            % (baseFunc.func_name, arg, type(arg).__name__,
                                types, name))
            return func(*args)
        baseFunc.__args_enforced__ = True
        wrapper.__wrapped_func__ = func
        return wrapper
    return deco


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
            return (True, ("MethodNotSupported", (methodName,)))

        # start profile
        prof.startXml(methodName)

        try:
            try:
                if not authToken:
                    # Until the session is proven valid, assume anonymous
                    # access -- we don't want a broken session preventing
                    # anonymous access or logins.
                    authToken = ('anonymous', 'anonymous')
                auth = self.users.checkAuth(authToken)
                authToken = (authToken[0], '')
                self.authToken = authToken
                self.auth = users.Authorization(**auth)

                self.restDb = rest_database.Database(self.cfg, self.db,
                                                             dbOnly=True)
                self.restDb.setAuth(self.auth, authToken)
                self.siteAuth.refresh()
                try:
                    maintenance.enforceMaintenanceMode(self.cfg, self.auth)
                except mint_error.MaintenanceMode:
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

            except (mint_error.MintError, pcreator_errors.PackageCreatorError), e:
                e_type, e_value, e_tb = sys.exc_info()
                self._handleError(e, authToken, methodName, args)
                frozen = (e.__class__.__name__, e.freeze())
                return (True, frozen)
            except:
                e_type, e_value, e_tb = sys.exc_info()
                self._handleError(e_value, authToken, methodName, args)
                raise
            else:
                if self.db.inTransaction(True):
                    self.db.commit()
                return (False, r)
        finally:
            prof.stopXml(methodName)
            if self.restDb:
                self.restDb.reset()

    def __getattr__(self, key):
        if key[0] != '_':
            # backwards-compatible reference to all the database table objects.
            return getattr(self.db, key)

    def _handleError(self, e, authToken, methodName, args):
        if self.db.inTransaction(True):
            self.db.rollback()
        if self.callLog:
            # See above for rant about pickling args
            str_args = [isinstance(x, (int, long)) and x or str(x)
                for x in args]
            self.callLog.log(self.remoteIp, list(authToken) + [None, None],
                methodName, str_args, exception = e)

    def _addInternalConaryConfig(self, ccfg, repoMaps=True, repoToken=None):
        """
        Adds user lines and repository maps for the current user.
        """
        for (otherProjectData, level, memberReqs,
                ) in self.getProjectDataByMember(self.auth.userId):
            if level not in userlevels.WRITERS:
                continue
            otherProject = projects.Project(self,
                    otherProjectData['projectId'],
                    initialData=otherProjectData)
            passwd = repoToken or self.authToken[1]
            ccfg.user.addServerGlob(otherProject.getFQDN(),
                self.authToken[0], passwd)

        # Also add repositoryMap entries for external cached projects.
        if repoMaps:
            for repos in self.reposMgr.iterRepositories('external'):
                if repos.isLocalMirror:
                    # No repomap required for anything with a database.
                    continue
                ccfg.repositoryMap.append((repos.fqdn, repos.getURL()))

    def _getProjectConaryConfig(self, project, repoToken=None):
        """
        Creates a conary configuration object, suitable for internal or external
        rBuilder use.
        @param project: Project to create a Conary configuration for.
        @type project: C{mint.project.Project} object
        @param internal: True if configuration object is to be used by a
           NetClient/ShimNetClient internal to rBuilder; False otherwise.
        @type internal: C{bool}
        """
        ccfg = conarycfg.ConaryConfiguration(False)
        ccfg.conaryProxy = self.cfg.getInternalProxies()
        self._addInternalConaryConfig(ccfg, repoMaps=True, repoToken=repoToken)
        return ccfg

    def _getProductDefinition(self, project, version):
        cclient = self.reposMgr.getAdminClient(write=False)
        pd = proddef.ProductDefinition()
        pd.setBaseLabel(version.label)
        try:
            pd.loadFromRepository(cclient)
            return pd
        except:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise mint_error.ProductDefinitionVersionNotFound

    def _getProductDefinitionForVersionObj(self, versionId):
        version = projects.ProductVersions(self, versionId)
        project = projects.Project(self, version.projectId)
        return self._getProductDefinition(project, version)

    def _getProductVersionLabel(self, project, versionId):
        version = projects.ProductVersions(self, versionId)
        return version.label

    # unfortunately this function can't be a proper decorator because we
    # can't always know which param is the projectId.
    # We'll just call it at the begining of every function that needs it.
    def _filterProjectAccess(self, projectId):
        # Allow admins to see all projects
        if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return
        handle = self.reposMgr.getRepositoryFromProjectId(projectId)
        try:
            handle.getLevelForUser(self.auth.userId)
        except rest_errors.ProductNotFound:
            raise mint_error.ItemNotFound('project')

    def _filterBuildAccess(self, buildId):
        try:
            buildRow = self.builds.get(buildId, fields=['projectId'])
        except mint_error.ItemNotFound:
            return

        self._filterProjectAccess(buildRow['projectId'])


    def _filterPublishedReleaseAccess(self, pubReleaseId):
        try:
            pubReleaseRow = self.publishedReleases.get(pubReleaseId,
                    fields=['projectId'])
        except mint_error.ItemNotFound:
            return

        isFinal = self.publishedReleases.isPublishedReleasePublished(pubReleaseId)
        # if the release is not published, then only project members
        # with write access can see the published release
        if not isFinal and not self._checkProjectAccess(pubReleaseRow['projectId'], userlevels.WRITERS):
            raise mint_error.ItemNotFound()
        # if the published release is published, then anyone can see it
        # unless the project is hidden and the user is not an admin
        else:
            self._filterProjectAccess(pubReleaseRow['projectId'])

    def _filterLabelAccess(self, labelId):
        try:
            labelRow = self.labels.get(labelId, fields=['projectId'])
        except mint_error.ItemNotFound:
            return

        self._filterProjectAccess(labelRow['projectId'])


    def _filterBuildFileAccess(self, fileId):
        cu = self.db.cursor()
        cu.execute("""SELECT projectId FROM BuildFiles
                          LEFT JOIN Builds AS Builds
                              ON Builds.buildId = BuildFiles.buildId
                          WHERE fileId=?""", fileId)
        r = cu.fetchall()
        if len(r):
            self._filterProjectAccess(r[0][0])

    def _checkProjectAccess(self, projectId, allowedUserlevels):
        if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            # Assert that the project exists
            self.projects.get(projectId)

            return True
        try:
            if (self.projectUsers.getUserlevelForProjectMember(projectId,
                    self.auth.userId) in allowedUserlevels):
                return True
        except mint_error.ItemNotFound:
            pass
        return False

    def _isUserAdmin(self, userId):
        try:
            user = self.users.get(userId)
            return user['is_admin']
        except mint_error.ItemNotFound:
            return False

    def _getProxies(self):
        useInternalConaryProxy = self.cfg.useInternalConaryProxy
        if useInternalConaryProxy:
            httpProxies = {}
            useInternalConaryProxy = self.cfg.getInternalProxies()
        else:
            httpProxies = self.cfg.proxy or {}
        return [ useInternalConaryProxy, httpProxies ]

    def _getRmakeClient(self):
        """Return an instance of a rMake 3 client."""
        return rmk_client.RmakeClient('http://localhost:9998')

    def _configureSputnik(self, sp, urlhostname):
        """Try to configure remote sputnik.

        It might fail if the upsrv is too old to have a sputnik (pre-5.7) in
        which case we should succeed anyway with just the repository setup.
        """
        result = sp.configure.Network.index()
        if 'errors' in result:
            log.error("Error configuring update service %s", urlhostname)
            for error in result['errors']:
                log.error("  %s", error.rstrip())
            return
        fqdn = result.get('host_hostName')
        if not fqdn:
            log.warning("Update service %s has no FQDN configured "
                    "-- not creating certificate pair.", urlhostname)
            return

        log.info("Creating certificate pair for update service %s", fqdn)
        x509_pem, pkey_pem = self.restDb.createCertificate(
                purpose='upsrv %s' % (fqdn,),
                desc='rPath Update Service',
                issuer='hg_ca',
                common=fqdn,
                conditional=True,
                )
        confDict = {
            'x509_pem': x509_pem,
            'pkey_pem': pkey_pem,
            }

        rbuilder_ip = procutil.getNetName()
        if rbuilder_ip != 'localhost':
            confDict['xmpp_host'] = rbuilder_ip

        ret = sp.rusconf.RusConf.pushConfiguration(confDict)
        if 'errors' in ret:
            # Too old to have a sputnik installation.
            if ('method "pushConfiguration" is not supported'
                    not in ret['errors'][-1]):
                log.error("Error configuring update service %s: %s",
                        urlhostname, ret['errors'][-1])
                raise mint_error.UpdateServiceUnknownError(urlhostname)
            log.warning("Update service %s does not support system inventory "
                    "-- only repository services will be configured.",
                    urlhostname)
            return

        # At this point, the rmake node should be connecting back to our XMPP
        # server. Push the new JID to rmake's whitelist so it can authenticate.
        jid = ret.get('jid')
        try:
            client = self._getRmakeClient()
            client.registerWorker(jid)
        except:
            log.exception("Failed to register remote update service %s "
                    "(JID %s) with local rMake dispatcher:", fqdn, jid)
        else:
            log.info("Registered update service %s w/ JID %s", fqdn, jid)

    def _configureUpdateService(self, hostname, adminUser, adminPassword):
        import xmlrpclib
        from mint.lib import proxiedtransport
        mirrorUser = ''
        try:
            # Connect to the rUS via XML-RPC
            urlhostname = hostname
            if ':' not in urlhostname:
                hostport = cny_net.HostPort(urlhostname, 8003)
                protocol = 'https'
            else:
                # Hack to allow testsuite, which passes 'hostname:port'
                # and isn't using HTTPS
                hostport = cny_net.HostPort(urlhostname)
                protocol = 'http'

            url = cny_req.URL(scheme=protocol,
                    userpass=(adminUser, util.ProtectedString(adminPassword)),
                    hostport=hostport,
                    path='/rAA/xmlrpc/')
            transport = proxiedtransport.ProxiedTransport(
                    proxyMap=self.cfg.getProxyMap())
            sp = util.ServerProxy(url, transport=transport)

            mirrorUser = helperfuncs.generateMirrorUserName("%s.%s" % \
                    (self.cfg.hostName, self.cfg.siteDomainName), hostname)

            # Add a user to the update service with mirror permissions
            try:
                mirrorPassword = \
                    sp.mirrorusers.MirrorUsers.addRandomUser(mirrorUser)
            except socket.error:
                from M2Crypto import m2xmlrpclib, SSL
                SSL.Connection.clientPostConnectionCheck = None
                sp = xmlrpclib.ServerProxy(url, transport=m2xmlrpclib.SSL_Transport())
                mirrorPassword = \
                    sp.mirrorusers.MirrorUsers.addRandomUser(mirrorUser)

            self._configureSputnik(sp, urlhostname)
        except http_error.ResponseError, e:
            if e.errcode == 403:
                raise mint_error.UpdateServiceAuthError(urlhostname)
            else:
                raise mint_error.UpdateServiceConnectionFailed(urlhostname,
                        "%d %s" % (e.errcode, e.reason))
        except socket.error, e:
            raise mint_error.UpdateServiceConnectionFailed(urlhostname, 
                                                           str(e[1]))

        if mirrorPassword == '':
            # rUS is in proxy mode
            return 'proxy_mode', ''
        elif isinstance(mirrorPassword, dict):
            raise mint_error.UpdateServiceUnknownError(urlhostname)
        else:
            return (mirrorUser, mirrorPassword)

    def checkVersion(self):
        if self.clientVer < SERVER_VERSIONS[0]:
            raise mint_error.InvalidClientVersion(
                'Invalid client version %s. Server '
                'accepts client versions %s' % (self.clientVer,
                    ', '.join(str(x) for x in SERVER_VERSIONS)))
        return SERVER_VERSIONS

    @typeCheck(str, str, str, str, str, str, str, str, str, str, str, bool,
               str)
    @requiresCfgAdmin('adminNewProjects')
    @private
    def newProject(self, projectName, hostname, domainname, projecturl, desc, 
                   appliance, shortname, namespace, prodtype, version, 
                   commitEmail, isPrivate, platformLabel):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")

        # make sure the shortname, version, and prodtype are valid, and
        # validate the hostname also in case it ever splits from being
        # the same as the short name
        projects._validateShortname(shortname, domainname, reservedHosts)
        projects._validateHostname(hostname, domainname, reservedHosts)
        projects._validateProductVersion(version)
        if namespace:
            projects._validateNamespace(namespace)
        else:
            #If none was set use the default namespace set in config
            namespace = self.cfg.namespace
        if not prodtype or (prodtype != 'Appliance' and prodtype != 'Component' and prodtype != 'Platform' and prodtype != 'Repository' and prodtype != 'PlatformFoundation'):
            raise mint_error.InvalidProdType

        if projecturl and not (projecturl.startswith('https://') or projecturl.startswith('http://')):
            projecturl = "http://" + projecturl

        isPrivate = isPrivate or self.cfg.hideNewProjects
        projectId = self.restDb.productMgr.createProduct(name=projectName,
                                  description=desc,
                                  hostname=hostname,
                                  domainname=domainname,
                                  namespace=namespace,
                                  projecturl=projecturl,
                                  shortname=shortname, 
                                  prodtype=prodtype,
                                  version=version, 
                                  commitEmail=commitEmail,
                                  isPrivate=isPrivate)
        return projectId

    @typeCheck(int, str, str)
    @requiresAdmin
    @private
    def addProjectRepositoryUser(self, projectId, username, password):
        project = projects.Project(self, projectId)
        self.restDb.productMgr.reposMgr.addUser(project.getFQDN(),
                                                username, password,
                                                userlevels.OWNER)
        return username

    @typeCheck(str, str, str, str, str, bool)
    @requiresAdmin
    @private
    def newExternalProject(self, name, hostname, domainname, label, url, mirrored):
        maintenance.enforceMaintenanceMode( \
            self.cfg, auth = None, msg = "Repositories are currently offline.")

        now = time.time()

        # make sure the hostname is valid
        if not domainname:
            domainname = self.cfg.projectDomainName
        projects._validateHostname(hostname, domainname, reservedExtHosts)

        # ensure that the label we were passed is valid
        try:
            versions.Label(label)
        except conary_errors.ParseError:
            raise mint_error.ParameterError("Not a valid Label")

        fqdn = label.split('@')[0]
        if not url:
            url = 'http://%s/conary/' % (fqdn,)

        creatorId = self.auth.userId > 0 and self.auth.userId or None

        self.db.transaction()
        try:
            # create the project entry
            projectId = self.projects.new(name=name, creatorId=creatorId,
                    description='', shortname=hostname, fqdn=fqdn,
                    hostname=hostname, domainname=domainname, projecturl='',
                    external=True, timeModified=now, timeCreated=now,
                    database=None,
                    prodtype="Repository",
                    commit=False,
                    )

            if creatorId:
                # create the projectUsers entry
                self.projectUsers.new(userId=creatorId,
                        projectId=projectId, level=userlevels.OWNER,
                        commit=False)

            # create the labels entry
            self.labels.addLabel(projectId, label, url, 'none', commit=False)
        except:
            self.db.rollback()
            raise
        self.db.commit()

        sync = repository_sync.SyncTool(self.cfg, self.db)
        try:
            sync.syncReposByFQDN(fqdn)
        except:
            log.traceback("Error synchronizing repository branches")
        return projectId

    @typeCheck(int)
    @private
    def getProject(self, id):
        self._filterProjectAccess(id)
        project = self.projects.get(id)

        if not hasattr(self, 'clientVer'):
            return project

        if self.clientVer < 3:
            del project['isAppliance']

        if self.clientVer < 4:
            del project['commitEmail']

        return project


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
    def getProjectDataByMember(self, userId):
        filter = (self.auth.userId != userId) and (not self.auth.admin)
        return self.projects.getProjectDataByMember(userId, filter)

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
        reqList = self._listAllJoinRequests(projectId)
        return [ (x, self.users.getUsername(x)) for x in reqList]
    
    def _listAllJoinRequests(self, projectId):
        return self.membershipRequests.listRequests(projectId)

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
                maillib.sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, email, subject, message)
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
        if username and not userId:
            cu = self.db.cursor()
            cu.execute("""SELECT userId FROM Users
                              WHERE username=? AND active=1""", username)
            r = cu.fetchone()
            if not r:
                raise mint_error.ItemNotFound(username)
            else:
                userId = r[0]
        else:
            cu = self.db.cursor()
            cu.execute("""SELECT userId FROM Users
                          WHERE userId=? AND active=1""", userId)
            r = cu.fetchone()
            if not r:
                raise mint_error.ItemNotFound(userId)
        self.restDb.productMgr.setMemberLevel(projectId, userId, level)
        return True

    @private
    def projectAdmin(self, projectId, userName):
        """Check for admin ACL in a given project repo."""
        # XXX: rewrite me, i suck
        if not userName:
            return False
        if self.auth.admin:
            return True
        self._filterProjectAccess(projectId)

        handle = self.reposMgr.getRepositoryFromProjectId(projectId)
        if handle.isExternal:
            return False

        db = handle.getReposDB()
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
            self.getUserLevel(userId, projectId)
        except mint_error.ItemNotFound:
            raise netclient.UserNotFound()

        try:
            project = projects.Project(self, projectId)
            self.db.transaction()

            user = self.getUser(userId)

            if notify:
                self._notifyUser('Removed', user, project)

            self.projectUsers.delete(projectId, userId, commit=False)

        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

        if not project.external:
            self.restDb.productMgr.reposMgr.deleteUser(project.getFQDN(),
                                                       user['username'])
        return True

    def _notifyUser(self, action, user, project, userlevel=None):
        userlevelname = ((userlevel >=0) and userlevels.names[userlevel] or\
                                             'Unknown')
        projectUrl = 'http://%s%sproject/%s/' %\
                      (self.cfg.siteHost,
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
                maillib.sendMail(self.cfg.adminMail, self.cfg.productName,
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
                        maillib.sendMail(self.cfg.adminMail, self.cfg.productName,
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
            raise mint_error.PermissionDenied

        return self.projects.update(projectId, commitEmail = commitEmail)
    
    @typeCheck(int, str)
    @requiresAuth
    @private
    def setProjectNamespace(self, projectId, namespace):
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied

        projects._validateNamespace(namespace)

        return self.projects.update(projectId, namespace = namespace)

    @typeCheck(int)
    @requiresAdmin
    @private
    def hideProject(self, projectId):
        project = projects.Project(self, projectId)

        try:
            self.restDb.productMgr.reposMgr.deleteUser(project.getFQDN(),
                                                   'anonymous')
        except UserNotFound:
            pass
        # Hide the project
        self.projects.hide(projectId)
        return True

    @typeCheck(int)
    @private
    def unhideProject(self, projectId):
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied

        self.projects.unhide(projectId)
        return True

    @typeCheck(int, bool)
    @requiresAdmin
    @private
    def setBackupExternal(self, projectId, backupExternal):
        return self.projects.update(projectId,
                backupExternal=bool(backupExternal))

    @typeCheck(int, bool)
    @requiresAuth
    @private
    def setProductVisibility(self, projectId, makePrivate):
        """
        Set the visibility of a product
        @param projectId: the project id
        @type  projectId: C{int}
        @param makePrivate: True to make private, False to make public
        @type  makePrivate: C{bool}
        @raise mint_error.PermissionDenied: if not the product owner
        @raise PublicToPrivateConversionError: if trying to convert a public
               product to private
        """
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied

        project = projects.Project(self, projectId)
        
        # if the product is currently hidden and they want to go public, do it
        if project.hidden and not makePrivate:
            self.unhideProject(projectId)
            return True
            
        # if the product is currently public, do not allow them to go private
        # unless admin
        if not project.hidden and makePrivate:
            if list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] \
                    or self.auth.admin:
                self.hideProject(projectId)
            else:
                raise mint_error.PublicToPrivateConversionError()
        
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
            raise mint_error.ItemNotFound("membership")
        else:
            return r[0]

    @typeCheck(int, int, int)
    @requiresAuth
    def setUserLevel(self, userId, projectId, level):
        self._filterProjectAccess(projectId)
        if self.projectUsers.onlyOwner(projectId, userId) and \
               (level != userlevels.OWNER):
            raise mint_error.LastOwner
        self.restDb.productMgr.setMemberLevel(projectId, userId, level)
        return True

    @typeCheck(int)
    @private
    def getProjectsByUser(self, userId):
        cu = self.db.cursor()

        # audited for SQL injection.
        cu.execute("""SELECT fqdn, name, level
                      FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=?
                      ORDER BY level, name""", userId)

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
            raise mint_error.PermissionDenied
        # per https://issues.rpath.com/browse/RBL-8350, don't enforce this anymore unless rBO or flagged external
        if self.cfg.rBuilderOnline or self.cfg.rBuilderExternal:
            if active and not (list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin):
                raise mint_error.PermissionDenied
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
        return self.users.checkAuth((user, password), useToken=True
                )['authorized']

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
        client = self.reposMgr.getAdminClient(write=True)
        project = projects.Project(self, projectId)
        client.repos.addNewAsciiPGPKey(versions.Label(project.getLabel()),
                username, keydata)
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
        """ 
        Make sure accounts and privileges belonging to the user are removed
        prior to removing the user.
        """
        if (self.auth.userId != userId) and (not self.auth.admin):
            raise mint_error.PermissionDenied()

        self._ensureNoOrphans(userId)

        self.membershipRequests.userAccountCanceled(userId)

        self.removeUserAccount(userId)
        
        return True
    
    def _ensureNoOrphans(self, userId):
        """
        Make sure there won't be any orphans
        """
        cu = self.db.cursor()

        # Find all projects of which userId is an owner, has no other owners, and/or
        # has developers.
        cu.execute("""SELECT MAX(D.flagged)
                        FROM (SELECT A.projectId,
                               COUNT(B.userId) * (CASE COUNT(C.userId) WHEN 0 THEN 1 ELSE 0 END) AS flagged
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
            raise mint_error.LastOwner
        
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
        cu.execute("SELECT userId FROM UserGroups WHERE is_admin = true")
        if [x[0] for x in cu.fetchall()] == [userId]:
            # userId is admin, and there is only one admin => last admin
            raise mint_error.LastAdmin(
                            "There are no more admin accounts. Your request "
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
            raise mint_error.PermissionDenied
        self.filterLastAdmin(userId)

        self.setEC2CredentialsForUser(userId, '', '', '', True)

        #Handle projects
        projectList = self.getProjectIdsByMember(userId)
        for (projectId, level) in projectList:
            self.delMember(projectId, userId, False)

        cu = self.db.transaction()
        try:
            cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?",
                       userId)
            cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
            cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
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
            raise mint_error.PermissionDenied
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM Users WHERE username=?", username)
        r = cu.fetchall()
        if not r:
            raise mint_error.ItemNotFound
        cu.execute("SELECT confirmation FROM Confirmations WHERE userId=?",
                   r[0][0])
        r = cu.fetchall()
        if not r:
            raise mint_error.ItemNotFound
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

    @typeCheck(str, str, ((str, int, bool),))
    @requiresAuth
    @private
    def setUserDataValue(self, username, name, value):
        if name in ['awsAccountNumber', 'awsPublicAccessKeyId',
                'awsSecretAccessKey']:
            raise RuntimeError("Should not set EC2 credentials using this call")
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise mint_error.PermissionDenied
        if name not in usertemplates.userPrefsTemplate:
            raise mint_error.ParameterError("Undefined data entry")
        dataType = usertemplates.userPrefsTemplate[name][0]
        self.userData.setDataValue(userId, name, value, dataType)
        return True

    @typeCheck(str, str)
    @requiresAuth
    @private
    def getUserDataValue(self, username, name):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise mint_error.PermissionDenied
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
            raise mint_error.PermissionDenied

        cu = self.db.cursor()
        cu.execute("SELECT name FROM UserData WHERE userId=?", userId)
        res = usertemplates.userPrefsAttTemplate.keys()
        for ent in [x[0] for x in cu.fetchall() if x[0] in res]:
            res.remove(ent)
        return res
    
    @typeCheck(str)
    @requiresAuth
    @private
    def getUserDataDefaultedAWS(self, username):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise mint_error.PermissionDenied

        cu = self.db.cursor()
        cu.execute("SELECT name FROM UserData WHERE userId=?", userId)
        res = usertemplates.userPrefsAWSTemplate.keys()
        for ent in [x[0] for x in cu.fetchall() if x[0] in res]:
            res.remove(ent)
        return res

    @typeCheck(str)
    @requiresAuth
    @private
    def getUserDataDict(self, username):
        userId = self.getUserIdByName(username)
        if userId != self.auth.userId and not self.auth.admin:
            raise mint_error.PermissionDenied
        return self.userData.getDataDict(userId)

    @typeCheck(int, str)
    @private
    def setPassword(self, userId, newPassword):
        if (self.auth.admin or
            list(self.authToken) == [self.cfg.authUser, self.cfg.authPass] or
            self.auth.userId == userId):

            username = self.users.get(userId)['username']

            # New users are no longer added to repository databases but old
            # ones might still contain some. At the moment there's no support
            # for having users in the repository database inherit their
            # password from mint, so if the user exists then the password must
            # be set and must match.
            for projectId, level in self.getProjectIdsByMember(userId):
                repoHandle = self.reposMgr.getRepositoryFromProjectId(projectId)
                if repoHandle.hasDatabase:
                    server = repoHandle.getNetServer()
                    server.auth.changePassword(username, newPassword)

            self.users.changePassword(username, newPassword)

            return True
        else:
            raise mint_error.PermissionDenied


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

        @param userId: the userId to promote
        """
        if self._isUserAdmin(userId):
            raise mint_error.UserAlreadyAdmin
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET is_admin = true WHERE userId = ?", userId)
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
            raise mint_error.AdminSelfDemotion
        cu = self.db.cursor()
        cu.execute("UPDATE Users SET is_admin = false WHERE userId = ?", userId)
        self.db.commit()
        return True

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
        return True

    @typeCheck(int, int)
    @requiresAuth
    @private
    def removeLabel(self, projectId, labelId):
        self._filterProjectAccess(projectId)
        return self.labels.removeLabel(projectId, labelId)

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

        userId = None
        if username != self.cfg.authUser:
            try:
                userId = self.getUserIdByName(username)
            except mint_error.ItemNotFound:
                pass

        self.commits.new(projectId, time.time(), name, version, userId)
        return True

    @typeCheck(int)
    @private
    def getCommitsForProject(self, projectId):
        self._filterProjectAccess(projectId)
        return self.commits.getCommitsByProject(projectId)

    @typeCheck(int)
    def getBuild(self, buildId):
        if not self.builds.buildExists(buildId):
            raise mint_error.ItemNotFound
        self._filterBuildAccess(buildId)
        build = self.builds.get(buildId)

        return build

    @typeCheck(int, str)
    @requiresAuth
    @private
    def newBuild(self, projectId, productName):
        self._filterProjectAccess(projectId)
        buildId = self.builds.new(projectId = projectId,
                      name = productName,
                      timeCreated = time.time(),
                      buildCount = 0,
                      createdBy = self.auth.userId,
                      status = jobstatus.WAITING,
                      statusMessage = jobstatus.statusNames[jobstatus.WAITING])

        return buildId

    @typeCheck(int, ((str, unicode),), bool, list, str)
    @requiresAuth
    @private
    def newBuildsFromProductDefinition(self, versionId, stageName, force,
                                       buildNames = None, versionSpec = None):
        """
        Launch the image builds defined in the product definition for the
        given version id and stage.  If provided, use versionSpec as the top
        level group for the image, otherwise use the top level group defined
        in the
        product defintion.

        @return: buildIds
        @rtype: list of ints
        """
        version = projects.ProductVersions(self, versionId)
        projectId = version.projectId
        self._filterProjectAccess(projectId)

        # must check mint RBAC mechanism to see if images are buildable
        # unless using mint-auth or an admin user.
        if self.auth and self.auth.userId > 0 and not self.auth.admin:
            from mint.django_rest.rbuilder.manager import rbuildermanager
            djMgr = rbuildermanager.RbuilderManager()
            user = djMgr.getUser(self.auth.userId)
            project = djMgr.getProjectById(projectId)
            if not djMgr.userHasRbacCreatePermission(user, 'image'):
                raise mint_error.PermissionDenied
            if not djMgr.userHasRbacPermission(user, project, 'ReadMembers'):
                raise mint_error.PermissionDenied


        # Read build definition from product definition.
        pd = self._getProductDefinitionForVersionObj(versionId)

        # Look up the label for the stage name that was passed in.
        try:
            stageLabel = str(pd.getLabelForStage(stageName))
        except proddef.StageNotFoundError:
            raise mint_error.ProductDefinitionInvalidStage(
                    "Stage %s was not found in the product definition" %
                    stageName)
        except proddef.MissingInformationError:
            raise mint_error.ProductDefinitionError(
                    "Cannot determine the product label as the product "
                    "definition is incomplete")

        # Filter builds by stage
        buildList = pd.getBuildsForStage(stageName)
        if not buildList:
            raise mint_error.NoBuildsDefinedInBuildDefinition

        # Create build data for each defined build so we can create the builds
        # later
        filteredBuilds = []
        buildErrors = []

        groupNames = [ str(x.getBuildImageGroup()) for x in buildList ]
        if not versionSpec:
            versionSpec = stageLabel

        client = self.reposMgr.getUserClient(self.auth)
        repos = client.getRepos()
        groupTroves = repos.findTroves(None, 
                                       [(x, versionSpec, None) for x in 
                                         groupNames ], allowMissing = True)

        for build in buildList:
            if buildNames and build.name not in buildNames:
                continue
            buildFlavor = deps.parseFlavor(str(build.getBuildBaseFlavor()))
            buildGroup = str(build.getBuildImageGroup())
            groupList = groupTroves.get((buildGroup, versionSpec, None), [])

            flavorSet = build.flavorSetRef and \
                    (pd.getFlavorSet(build.flavorSetRef, None) \
                    or pd.getPlatformFlavorSet( \
                            build.flavorSetRef, None))
            flavorSet = deps.parseFlavor(flavorSet and flavorSet.flavor or '')

            architecture = build.architectureRef and \
                    (pd.getArchitecture(build.architectureRef, None) \
                    or pd.getPlatformArchitecture( \
                            build.architectureRef, None))
            architecture = deps.parseFlavor(architecture \
                    and architecture.flavor or '')

            # As of schema 2.0, builds no longer have custom flavors, so use
            # an empty flavor for the custom flavor
            customFlavor = deps.parseFlavor('')

            # Returns a list of troves that satisfy buildFlavor.
            nvfs = self._resolveTrove(groupList, flavorSet, architecture,
                    customFlavor)

            if nvfs:
                # Store a build with options for the best match for each build
                # results are sorted best to worst
                filteredBuilds.append((build, nvfs[0]))
            else:
                # No troves were found, save the error.
                buildErrors.append(str(conary_errors.TroveNotFound(
                    "Trove '%s' has no matching flavors for '%s'" % \
                    (buildGroup, buildFlavor))))

        if buildErrors and not force:
            raise mint_error.TroveNotFoundForBuildDefinition(buildErrors)

        # Create/start each build.
        buildIds = []
        for buildDefinition, nvf in filteredBuilds:
            buildImage = buildDefinition.getBuildImage()

            containerTemplate = pd.getContainerTemplate( \
                    buildDefinition.containerTemplateRef, None)
            if not containerTemplate:
                containerTemplate = pd.getPlatformContainerTemplate( \
                        buildDefinition.containerTemplateRef, None)
            buildSettings = {}
            if containerTemplate:
                buildSettings = containerTemplate.fields.copy()

            for key, val in buildImage.fields.iteritems():
                if val is not None and val != '':
                    buildSettings[key] = val
            buildType = buildImage.containerFormat and \
                    str(buildImage.containerFormat) or ''

            n, v, f = str(nvf[0]), nvf[1].freeze(), nvf[2].freeze()
            buildName = buildDefinition.name
            buildId = self.newBuildWithOptions(projectId, buildName,
                                               n, v, f, buildType,
                                               buildSettings, start=False)
            buildIds.append(buildId)
            self.startImageJob(buildId)
        return buildIds

    @typeCheck(int)
    def getBuildBaseFileName(self, buildId):
        self._filterBuildAccess(buildId)
        build = builds.Build(self, buildId)
        project = self.getProject(build.projectId)
        found, baseFileName = \
                self.buildData.getDataValue(buildId, 'baseFileName')
        if not found:
            baseFileName = ''
        baseFileName = ''.join([(x.isalnum() or x in ('-', '.')) and x or '_' \
                for x in baseFileName])
        arch = build.getArch()
        ver = helperfuncs.parseVersion(build.troveVersion)
        baseFileName = baseFileName or \
                "%(name)s-%(version)s-%(arch)s" % {
                'name': project['hostname'],
                'version': ver.trailingRevision().version,
                'arch': arch}
        return baseFileName

    def _getBuildPageUrl(self, buildId, hostname = None):
        # hostname arg is an optimization for getAllBuildsByType
        if not hostname:
            projectId = self.getBuild(buildId)['projectId']
            project = self.getProject(projectId)
            hostname = project.get('hostname')
        if self.req:
            target = self.req.host
        else:
            target = self.cfg.siteHost
        return "http://%s%sproject/%s/build?id=%d" % (target,
                self.cfg.basePath, hostname, buildId)

    @typeCheck(int)
    def getBuildPageUrl(self, buildId):
        # break this function to avoid excessive filter checks for local calls
        self._filterBuildAccess(buildId)
        return self._getBuildPageUrl(buildId)

    @typeCheck(int, ((str, unicode), ), str, str, str, str, dict, bool)
    @requiresAuth
    @private
    def newBuildWithOptions(self, projectId, buildName,
                            groupName, groupVersion, groupFlavor,
                            buildType, buildSettings, start=False):
        self._filterProjectAccess(projectId)

        version = helperfuncs.parseVersion(groupVersion)
        
        groupVersion = version.freeze()
        groupFlavor = helperfuncs.parseFlavor(groupFlavor).freeze()

        # Make sure we convert from Unicode to UTF-8
        buildName = buildName.encode('UTF-8')
        buildId = self.builds.new(projectId = projectId,
                      name = buildName,
                      timeCreated = time.time(),
                      buildCount = 0,
                      createdBy = self.auth.userId,
                      status = jobstatus.WAITING,
                      statusMessage=jobstatus.statusNames[jobstatus.WAITING])

        newBuild = builds.Build(self, buildId)
        newBuild.setTrove(groupName, groupVersion, groupFlavor)
        buildType = buildtypes.xmlTagNameImageTypeMap[buildType]
        newBuild.setBuildType(buildType)

        label = version.trailingLabel().asString()
        versionId, stage = self._getProductVersionForLabel(projectId, label)
        if versionId and stage:
            pd = self._getProductDefinitionForVersionObj(versionId)
            platName = pd.getPlatformName()
            if 'platformName' in newBuild.getDataTemplate():
                newBuild.setDataValue('platformName', str(platName))
            # RCE-814
            self.builds.setProductVersion(buildId, versionId, stage)

        template = newBuild.getDataTemplate()

        # Aliases for custom trove settings from product-definition
        for before, after in buildtemplates.optionNameMap.items():
            if before in buildSettings:
                buildSettings[after] = buildSettings.pop(before)

        # handle the rest
        for name, value in buildSettings.iteritems():
            try:
                settingType = template[name][0]
            except KeyError:
                # If there is no template, ignore it.
                continue

            if settingType == data.RDT_BOOL:
                value = (str(value).lower() == 'true')
            elif settingType in (data.RDT_STRING, data.RDT_ENUM):
                value = str(value)
            elif settingType == data.RDT_INT:
                value = int(value)
            elif settingType == data.RDT_TROVE:
                if isinstance(value, unicode):
                    value = value.encode('utf8')
                if '@' in value and '=' not in value:
                    # Just a version (probably a label)
                    # The setting name is the trove name.
                    specName, specVersion, specFlavor = name, value, ''
                else:
                    # A trovespec
                    specName, specVersion, specFlavor = parseTroveSpec(value)
                    if not specName:
                        specName = name
                    if not specVersion:
                        specVersion = ''
                    if specFlavor is not None:
                        specFlavor = str(specFlavor)
                    else:
                        specFlavor = ''

                # Resolve to an exact NVF so recreating will use the
                # old thing.
                value = self.resolveExtraTrove(projectId,
                        specName, specVersion, specFlavor,
                        groupVersion, groupFlavor)
                if not value:
                    continue
            else:
                # Unknown type
                continue

            newBuild.setDataValue(name, value)

        if start:
            self.startImageJob(buildId)
        return buildId

    def _resolveTrove(self, groupList, flavorSet, archFlavor, customFlavor):
        '''
        Return a list of trove tuples matching C{troveName},
        C{troveLabel}, satisfying flavor constraints. customFlavor overrides
        flavorSet and archFlavor. result is sorted according to flavor score.
        The repository backing the project at C{projectId} will be used.

        @return: List of trove tuples matching the query
        @rtype: list
        '''
        if not groupList:
            return []
        # Get the major architecture from filterFlavor
        arch = deps.overrideFlavor(archFlavor, customFlavor)
        filterArch = helperfuncs.getArchFromFlavor(arch)
        completeFlavor = deps.overrideFlavor(flavorSet, arch)
        # Hard filtering is done strictly by major architecture. This ensures
        # two things:
        #  * "is: x86" filter does NOT match "is: x86 x86_64" group
        #  * "is: x86 x86_64" filter DOES match "is: x86_64" group
        # After that, any remaining contests are broken using flavor scoring,
        # but the vast majority of proddefs use one flavor per arch only and
        # thus that case needs to be the most robust.
        archMatches = [ x for x in groupList
                if helperfuncs.getArchFromFlavor(x[2]) == filterArch ]
        if not archMatches:
            # Nothing even had the correct architecture, bail out.
            return []
        maxVersion = max(x[1] for x in archMatches)
        latest = [x for x in archMatches if x[1] == maxVersion]
        if len(latest) < 2:
            # A single group flavor matched the architecture so no need for
            # flavor scoring.
            return latest
        scored = sorted((x[2].score(completeFlavor), x) for x in latest)
        maxScore = scored[-1][0]
        return sorted([ x[1] for x in scored if x[0] == maxScore ],
                      key=lambda x: x[2])[-1:]

    def _deleteBuild(self, buildId, force=False):
        if not self.builds.buildExists(buildId)  and not force:
            raise mint_error.BuildMissing()

        if self.builds.getPublished(buildId) and not force:
            raise mint_error.BuildPublished()

        self.db.transaction()
        try:
            for filelist in self.getBuildFilenames(buildId):
                fileUrlList = filelist['fileUrls']
                for urlId, urlType, url in fileUrlList:
                    self.filesUrls.delete(urlId, commit=False)

                    if urlType != urltypes.LOCAL:
                        continue

                    # if this location is local, delete the file
                    path = url
                    try:
                        os.unlink(path)
                    except OSError, e:
                        # ignore permission denied, no such file/dir
                        if e.errno not in (errno.ENOENT, errno.EACCES):
                            raise

                    # Try to delete parent directories
                    for n in range(2):
                        path = os.path.dirname(path)
                        try:
                            os.rmdir(path)
                        except OSError, err:
                            if err.errno in (errno.ENOENT, errno.EACCES,
                                    errno.ENOTEMPTY):
                                break
                            else:
                                raise

            self.builds.delete(buildId, commit=False)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
            return True

    @typeCheck(int)
    @requiresAuth
    def deleteBuild(self, buildId):
        """
        Delete a build
        @param buildId: The id of the build to delete
        @type buildId: C{int}
        """
        self._filterBuildAccess(buildId)
        return self._deleteBuild(buildId, force=False)      

    @typeCheck(int, dict)
    @requiresAuth
    @private
    def updateBuild(self, buildId, valDict):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
        if len(valDict):
            columns = { 'timeUpdated': time.time(),
                        'updatedBy':   self.auth.userId,
                        }
            for column in ('pubReleaseId', 'name', 'description'):
                if column in valDict:
                    columns[column] = valDict.pop(column)
            if valDict:
                # Unknown argument
                raise mint_error.ParameterError()
            return self.builds.update(buildId, **columns)
        return False

    # build data calls
    @typeCheck(int, str, ((str, int, bool),), int)
    @requiresAuth
    @private
    def setBuildDataValue(self, buildId, name, value, dataType):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
        return self.buildData.setDataValue(buildId, name, value, dataType)

    @typeCheck(int, str, str, str, str, str)
    @private
    @requiresAuth
    def resolveExtraTrove(self, projectId, specialTroveName, specialTroveVersion,
            specialTroveFlavor, imageGroupVersion, imageGroupFlavor):
        searchPath = []
        if imageGroupVersion:
            # Get the image group label as the first part of the searchpath
            igV = helperfuncs.parseVersion(imageGroupVersion)

            # Determine search path; start with imageGroup's label
            searchPath.append(igV.branch().label())

        # if no flavor specified, use the top level group's flavor
        if not specialTroveFlavor:
            specialTroveFlavor = helperfuncs.getMajorArchFlavor(
                imageGroupFlavor)

        # Sanitize bits
        if specialTroveVersion == '':
            # empty version -> no version in particular
            specialTroveVersion = None
        elif '/' in specialTroveVersion:
            try:
                # frozen version -> normal version
                specialTroveVersion = \
                    helperfuncs.parseVersion(specialTroveVersion).asString()
            except:
                # maybe not
                pass
        if specialTroveFlavor == '':
            # empty flavor -> no flavor in particular
            specialTroveFlavor = None
        if isinstance(specialTroveFlavor, basestring):
            # string flavor -> thawed flavor object
            specialTroveFlavor = deps.ThawFlavor(specialTroveFlavor)

        # Get a Conary client
        client = self.reposMgr.getUserClient(self.auth)
        repos = client.getRepos()
        try:
            matches = repos.findTrove(searchPath,
                    (specialTroveName, specialTroveVersion, specialTroveFlavor),
                    client.cfg.flavor)
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

        cc = conarycfg.ConaryConfiguration(False)
        self._addInternalConaryConfig(cc)

        cfgBuffer = StringIO.StringIO()
        cc.displayKey('repositoryMap', cfgBuffer)
        repoToken = os.urandom(16).encode('hex')
        print >> cfgBuffer, 'user %s %s' % (self.auth.username, repoToken)
        cfgData = cfgBuffer.getvalue()

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
                        'conaryCfg' : cfgData,
                        'repoToken': repoToken,
                        }
        if buildDict['productVersionId']:
            r['proddefLabel'] = self._getProductVersionLabel(project,
                    buildDict['productVersionId'])
        else:
            r['proddefLabel'] = ''

        hostBase = '%s.%s' % (self.cfg.hostName, self.cfg.siteDomainName)

        r['UUID'] = '%s-build-%d-%d' % (hostBase, buildId,
                self.builds.bumpBuildCount(buildId))

        #Set up the http/https proxy
        r['proxy'] = dict(self.cfg.proxy)

        # CA certificates for rpath-tools.
        hg_ca, lg_ca = self.restDb.getCACertificates()
        r['pki'] = {
                'hg_ca': hg_ca or '',
                'lg_ca': lg_ca or '',
                }
        if not hg_ca:
            log.warning("High-grade CA certificate is missing. Images will "
                    "not be registerable.")
        if not lg_ca:
            log.warning("Low-grade CA certificate is missing. Images will "
                    "not be remote-registerable.")

        # Send our IP to jobslave for rpath-tools configuration. This is mainly
        # here for demoability, because images booted in a different management
        # zone will fail to contact the rBuilder. Eventually SLP will work out
        # of the box and this won't be necessary.
        rbuilder_ip = procutil.getNetName()
        if rbuilder_ip == 'localhost':
            rbuilder_ip = self.cfg.siteHost
        r['inventory_node'] = rbuilder_ip + ':8443'
        r['outputUrl'] = 'http://%s%s' % (rbuilder_ip, self.cfg.basePath)
        r['outputToken'] = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        self.buildData.setDataValue(buildId, 'outputToken',
            r['outputToken'], data.RDT_STRING)

        return r

    #
    # published releases 
    #
    @typeCheck(int)
    @requiresAuth
    def newPublishedRelease(self, projectId):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise mint_error.PermissionDenied
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
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            raise mint_error.PermissionDenied
        if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
            raise mint_error.PublishedReleasePublished
        if len(valDict):
            columns = { 'timeUpdated': time.time(),
                        'updatedBy': self.auth.userId,
                        }
            for column in ('name', 'version', 'description'):
                if column in valDict:
                    columns[column] = valDict.pop(column)
            if valDict:
                # Unknown argument
                raise mint_error.ParameterError()
            return self.publishedReleases.update(pubReleaseId, **columns)
        return False

    @typeCheck(int, bool)
    @requiresAuth
    @private
    def publishPublishedRelease(self, pubReleaseId, shouldMirror):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied

        self._checkPublishedRelease(pubReleaseId, projectId)
        
        valDict = {'timePublished': time.time(),
                   'publishedBy': self.auth.userId,
                   'shouldMirror': int(shouldMirror),
                   }

        try:
            self.db.transaction()
            result = self.publishedReleases.update(pubReleaseId, commit=False,
                                                   **valDict)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return result

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
            raise mint_error.PermissionDenied
        if not len(self.publishedReleases.getBuilds(pubReleaseId)):
            raise mint_error.PublishedReleaseEmpty
        if checkPublished:
            if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
                raise mint_error.PublishedReleasePublished

        return True

    def _checkUnpublishedRelease(self, pubReleaseId, projectId, failIfNotPub=True):
        """
        Performs some sanity checks on the unpublished release
        """
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied
        if failIfNotPub:
            if not self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
                raise mint_error.PublishedReleaseNotPublished

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


        try:
            self.db.transaction()
            result = self.publishedReleases.update(pubReleaseId, commit=False,
                                                   **valDict)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
        return result

    @typeCheck(int)
    @requiresAuth
    def deletePublishedRelease(self, pubReleaseId):
        self._filterPublishedReleaseAccess(pubReleaseId)
        projectId = self.publishedReleases.getProject(pubReleaseId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied
        if self.publishedReleases.isPublishedReleasePublished(pubReleaseId):
            raise mint_error.PublishedReleasePublished
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

    @typeCheck(int)
    @private
    def getPublishedReleasesByProject(self, projectId):
        self._filterProjectAccess(projectId)
        publishedOnly = False
        if not self._checkProjectAccess(projectId, userlevels.WRITERS):
            publishedOnly = True
        return self.publishedReleases.getPublishedReleasesByProject(projectId,
                publishedOnly)

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
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
        r = self.builds.setTrove(buildId, troveName, troveVersion, troveFlavor)
        troveLabel = helperfuncs.parseVersion(troveVersion).trailingLabel()
        projectId = self.builds.get(buildId)['projectId']
        productVersionId, stage = self._getProductVersionForLabel(projectId, 
                                                                  troveLabel)
        if productVersionId:
            self.builds.setProductVersion(buildId, productVersionId, stage)

        # clear out all "important flavors"
        for x in buildtypes.flavorFlags.keys():
            self.buildData.removeDataValue(buildId, x)

        # and set the new ones
        for x in builds.getImportantFlavors(troveFlavor):
            self.buildData.setDataValue(buildId, x, 1, data.RDT_INT)
        return r

    def _getProductVersionForLabel(self, projectId, label):
        cu = self.db.cursor()
        # First look in the database, we may have all the data already, without
        # loading the proddef
        cu.execute('''
            SELECT project_branch_id, name
              FROM project_branch_stage
             WHERE project_id = ?
               AND label = ?
        ''', projectId, str(label))
        for versionId, stageName in cu:
            return versionId, stageName
        return None, None

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setBuildDesc(self, buildId, desc):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
        self.builds.update(buildId, description = desc)
        return True

    @typeCheck(int, str)
    @requiresAuth
    @private
    def setBuildName(self, buildId, name):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
        self.builds.update(buildId, name = name)
        return True

    @typeCheck(int, int, bool)
    @requiresAuth
    @private
    def setBuildPublished(self, buildId, pubReleaseId, published):
        self._filterBuildAccess(buildId)
        buildData = self.builds.get(buildId, fields=['projectId', 'buildType'])
        if not self._checkProjectAccess(buildData['projectId'],
                userlevels.WRITERS):
            raise mint_error.PermissionDenied()
        if not self.publishedReleases.publishedReleaseExists(pubReleaseId):
            raise mint_error.PublishedReleaseMissing()
        if self.isPublishedReleasePublished(pubReleaseId):
            raise mint_error.PublishedReleasePublished()
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if published and (buildData['buildType'] != buildtypes.AMI and buildData['buildType'] != buildtypes.IMAGELESS and not self.getBuildFilenames(buildId)):
            raise mint_error.BuildEmpty()
        # this exception condition is completely masked. re-enable it if the
        # structure of this code changes
        #if published and self.builds.getPublished(buildId):
        #    raise mint_error.BuildPublished()
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
            raise mint_error.BuildMissing()
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
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()
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
        try:
            sortedList.insert(0,
                    sortedList.pop(sortedList.index(buildtypes.IMAGELESS)))
        except ValueError:
            pass # do nothing if buildtypes.IMAGELESS isn't in the list

        return sortedList

    @typeCheck(int)
    @requiresAuth
    def startImageJob(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()

        buildDict = self.builds.get(buildId)
        buildType = buildDict['buildType']

        # Clear any previously-existing files.
        self._setBuildFilenames(buildId, [])

        if buildType == buildtypes.IMAGELESS:
            # image-less builds (i.e. group trove builds) don't actually get
            # built, they just get stuffed into the DB
            self.db.builds.update(buildId, status=jobstatus.FINISHED,
                    statusMessage="Job Finished")
            return '0' * 32
        else:
            try:
                jobData = self.serializeBuild(buildId)
                if buildType in buildtypes.windowsBuildTypes:
                    return self.startWindowsImageJob(buildId, jobData)
                elif buildType == buildtypes.DEFERRED_IMAGE:
                    return self.startDeferredImageJob(buildId, jobData)

                # Check the product definition to see if this is based on a
                # Windows platform.
                if buildDict['productVersionId']:
                    pd = self._getProductDefinitionForVersionObj(
                            buildDict['productVersionId'])
                    platInfo = pd.getPlatformInformation()
                    tags = []
                    if (platInfo and hasattr(platInfo, 'platformClassifier')
                        and hasattr(platInfo.platformClassifier, 'tags')):
                        tags = platInfo.platformClassifier.tags.split()
                    if 'windows' in tags:
                        return self.startWindowsImageJob(buildId, jobData)

                return self.startMcpImageJob(buildId, jobData)
            except:
                log.exception("Failed to start image job:")
                self.db.builds.update(buildId, status=jobstatus.FAILED,
                        statusMessage="Failed to start image job - check logs")
                raise

    def _addRepoToken(self, buildId, jobData):
        repoToken = jobData['project']['repoToken']
        self.db.auth_tokens.addToken(repoToken, self.auth.userId, buildId)

    def startMcpImageJob(self, buildId, jobData):
        """Start a standard MCP image job."""
        self._addRepoToken(buildId, jobData)
        client = self._getMcpClient()
        uuid = client.new_job(client.LOCAL_RBUILDER, json.dumps(jobData))
        self.buildData.setDataValue(buildId, 'uuid', uuid, data.RDT_STRING)
        return uuid

    def startWindowsImageJob(self, buildId, jobData):
        """Direct Windows image builds to rMake 3."""
        self._addRepoToken(buildId, jobData)
        jsonData = json.dumps(jobData)
        cli = wig_client.WigClient(self._getRmakeClient())
        job_uuid, job = cli.createJob(jsonData, subscribe=False)
        log.info("Created Windows image job, UUID %s", job_uuid)
        self.builds.update(buildId, job_uuid=str(job_uuid))
        return str(job_uuid)

    def startDeferredImageJob(self, buildId, jobData):
        """Create a deferred image record in the database."""
        baseTrove = jobData['data'].get('baseImageTrove', '')
        try:
            baseId = self.db.builds.getIdByColumn('output_trove',
                    baseTrove)
        except database.ItemNotFound:
            self.db.builds.update(buildId, status=jobstatus.FAILED,
                    statusMessage="Base image %r not found" % (baseTrove,))
            return -1
        self.db.builds.update(buildId,
                base_image=baseId,
                status=jobstatus.FINISHED,
                statusMessage="Deferred image has been recorded")
        self.db.commit()

        from mint.django_rest.rbuilder.manager import rbuildermanager
        from mint.django_rest.rbuilder.images import models as image_models
        mgr = rbuildermanager.RbuilderManager()
        try:
            mgr.enterTransactionManagement()
            image = image_models.Image.objects.get(pk=buildId)
            mgr.addToMyQuerySet(image, image.created_by)
            mgr.retagQuerySetsByType('image')
            mgr.commit()
        except:
            mgr.rollback()
            raise
        finally:
            mgr.leaveTransactionManagement()

        return 1

    @typeCheck(int, str, list)
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
            raise mint_error.PermissionDenied

        ret = self._setBuildFilenames(buildId, filenames, normalize=True)
        self.buildData.removeDataValue(buildId, 'outputToken')

        return ret

    @typeCheck(int, list)
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
            raise mint_error.BuildMissing()
        if self.builds.getPublished(buildId):
            raise mint_error.BuildPublished()

        return self._setBuildFilenames(buildId, filenames)

    def _setBuildFilenames(self, buildId, filenames, normalize=False):
        from mint.shimclient import ShimMintClient
        authclient = ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db._db)

        build = authclient.getBuild(buildId)
        project = authclient.getProject(build.projectId)
        username = self.users.get(build.createdBy)['username']
        buildName = build.name
        buildType = buildtypes.typeNamesMarketing.get(build.buildType, None)

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
                cu.execute("""INSERT INTO BuildFiles (buildId, idx, title,
                        size, sha1) VALUES(?, ?, ?, ?, ?)""",
                        buildId, idx, title, size, sha1)
                fileId = cu.lastrowid
                cu.execute("""INSERT INTO FilesUrls (urlType, url)
                        VALUES (?, ?)""", urltypes.LOCAL, fileName)
                urlId = cu.lastrowid
                cu.execute("""INSERT INTO BuildFilesUrlsMap (fileId, urlId)
                        VALUES(?, ?)""", fileId, urlId)
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
            raise mint_error.BuildMissing()
        # Note bene: this can be done after a build has been published,
        # thus we don't have to check to see if the build is published.

        cu = self.db.transaction()
        try:
            # sanity check to make sure the fileId referenced exists
            cu.execute("SELECT fileId FROM BuildFiles where fileId = ?",
                    fileId)
            if not len(cu.fetchall()):
                raise mint_error.BuildFileMissing()

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
            raise mint_error.BuildMissing()
        cu = self.db.transaction()
        try:
            cu.execute("SELECT urlId FROM FilesUrls WHERE urlId = ?",
                    urlId)
            r = cu.fetchall()
            if not len(r):
                raise mint_error.BuildFileUrlMissing()

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

        results = cu.fetchall()

        downloadUrlTemplate = self.getDownloadUrlTemplate()

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
                             'fileUrls': [] ,
                             'downloadUrl': downloadUrlTemplate % lastFileId}

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
            raise mint_error.FileMissing

    @typeCheck(int, ((str, unicode),))
    @requiresAuth
    def getTroveVersionsByArch(self, projectId, troveNameWithLabel):
        self._filterProjectAccess(projectId)

        def dictByArch(versionList, trove):
            archMap = {}
            for v, flavors in reversed(sorted(versionList[trove].items())):
                for f in flavors:
                    arch = helperfuncs.getArchFromFlavor(f)

                    l = archMap.setdefault(arch, [])
                    l.append((v.asString(), v.freeze(), f.freeze()))
            return archMap

        project = projects.Project(self, projectId)
        trove, label = troveNameWithLabel.split('=')
        label = versions.Label(label)

        client = self.reposMgr.getUserClient(self.auth)
        versionList = client.repos.getTroveVersionList(project.getFQDN(),
                {trove: None})

        # group trove by major architecture
        return dictByArch(versionList, trove)

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getAllTroveLabels(self, projectId, serverName, troveName):
        self._filterProjectAccess(projectId)
        client = self.reposMgr.getUserClient(self.auth)

        troves = client.repos.getAllTroveLeaves(str(serverName),
                {str(troveName): None})
        if troveName in troves:
            ret = sorted(list(set(str(x.branch().label()) for x in troves[troveName])))
        else:
            ret = []
        return ret

    @typeCheck(int, ((str, unicode),), ((str, unicode),))
    def getTroveVersions(self, projectId, labelStr, troveName):
        self._filterProjectAccess(projectId)
        client = self.reposMgr.getUserClient(self.auth)

        troves = client.repos.getTroveVersionsByLabel(
                    {str(troveName): {versions.Label(str(labelStr)): None}}
                )[troveName]
        versionDict = dict((x.freeze(), [y for y in troves[x]]) for x in troves)
        versionList = sorted(versionDict.keys(), reverse = True)

        # insert a tuple of (flavor differences, full flavor) into versionDict
        strFlavor = lambda x: str(x) and str(x).replace(',', ', ') or '(no flavor)'
        for v, fList in versionDict.items():
            diffDict = deps.flavorDifferences(fList)
            versionDict[v] = sorted([(not diffDict[x].isEmpty() and str(diffDict[x]) or strFlavor(x), str(x)) for x in fList])

        return [versionDict, versionList]

    @typeCheck(int)
    # @requiresAuth
    def getAllProjectLabels(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT DISTINCT(%s) FROM PackageIndex WHERE projectId=?"
                % database.concat(self.db, 'serverName', "'@'",  'branchName'),
            projectId)
        labels = cu.fetchall()
        return [x[0] for x in labels]

    @typeCheck(int)
    @requiresAuth
    def getGroupTroves(self, projectId):
        self._filterProjectAccess(projectId)
        project = projects.Project(self, projectId)
        client = self.reposMgr.getUserClient(self.auth)
        troves = client.repos.troveNamesOnServer(project.fqdn)

        troves = sorted(trove for trove in troves if
            (trove.startswith('group-') or
             trove.startswith('fileset-')) and
            not trove.endswith(':source'))
        return troves

    @typeCheck(int)
    @requiresAuth
    def getBuildStatus(self, buildId):
        self._filterBuildAccess(buildId)

        buildDict = self.builds.get(buildId)
        return { 'status': buildDict['status'],
                'message': buildDict['statusMessage'] }

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
            raise mint_error.InvalidReport
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
            raise mint_error.InvalidReport
        return self._getReportObject(name).getReport()

    @private
    @typeCheck(str)
    @requiresAdmin
    def getReportPdf(self, name):
        if name not in reports.getAvailableReports():
            raise mint_error.PermissionDenied
        return base64.b64encode(self._getReportObject(name).getPdf())

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

        project = self.projects.get(targetProjectId)
        createDB = False
        if not project['database']:
            # Project was not previously assigned a database.
            self.projects.update(targetProjectId,
                    database=self.cfg.defaultDatabase)
            createDB = True

        x = self.inboundMirrors.new(targetProjectId=targetProjectId,
                sourceLabels = ' '.join(sourceLabels),
                sourceUrl = sourceUrl, sourceAuthType=authType,
                sourceUsername = sourceUsername,
                sourcePassword = sourcePassword,
                sourceEntitlement = sourceEntitlement,
                mirrorOrder = mirrorOrder, allLabels = int(allLabels))

        if createDB:
            self.restDb.productMgr.reposMgr.createRepository(targetProjectId,
                    createMaps=False)

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
                allLabels = int(allLabels))
        return x

    @private
    @typeCheck()
    @requiresAdmin
    def getInboundMirrors(self):
        cu = self.db.cursor()
        cu.execute("""
            SELECT DISTINCT
                inboundMirrorId,
                targetProjectId,
                sourceLabels,
                sourceUrl,
                sourceAuthType,
                sourceUsername,
                sourcePassword,
                sourceEntitlement,
                mirrorOrder,
                allLabels
            FROM InboundMirrors
            LEFT OUTER JOIN Platforms AS Platforms
                ON InboundMirrors.targetProjectId = Platforms.projectId
            WHERE
                COALESCE(Platforms.mode, 'auto')  = 'auto'
            ORDER BY mirrorOrder""")
        return [[y is not None and y or '' for y in x[:-1]] + \
                [x[-1]] for x in cu.fetchall()]

    @private
    @typeCheck(int)
    @requiresAdmin
    def getInboundMirror(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM InboundMirrors WHERE targetProjectId=?", projectId)
        x = cu.fetchone()
        if x:
            # bw compat: psycopg2 driver returns case-folded keys
            keys = self.db.inboundMirrors.fields
            return dict((key, x[key]) for key in keys)
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
                                       allLabels = int(allLabels),
                                       recurse = int(recurse),
                                       useReleases = int(useReleases),
                                       fullSync = 1)
        else:
            cu = self.db.cursor()
            cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM OutboundMirrors")
            mirrorOrder = cu.fetchone()[0]
            id = self.outboundMirrors.new(sourceProjectId = sourceProjectId,
                                           targetLabels = ' '.join(targetLabels),
                                           allLabels = int(allLabels),
                                           recurse = int(recurse),
                                           useReleases = int(useReleases),
                                           mirrorOrder = mirrorOrder,
                                           fullSync = 1)
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
            raise mint_error.ParameterError("First character of each matchString must be + or -")
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
        self.outboundMirrors.update(outboundMirrorId, fullSync=int(fullSync))
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
            raise mint_error.UpdateServiceNotFound()
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
        cu.execute("SELECT mirrorOrder, %s FROM %s ORDER BY mirrorOrder ASC"
                % (idField, table))
        for newIndex, (oldIndex, rowId) in enumerate(cu.fetchall()):
            if newIndex != oldIndex:
                updates.append((newIndex, rowId))

        if updates:
            cu.executemany("UPDATE %s SET mirrorOrder=? WHERE %s=?"
                    % (table, idField), updates)
            self.db.commit()
        return True

    def _iterVisibleRepositories(self):
        """
        Yield a list of repository hostnames that rBuilder knows about and
        that the current user has read access to.
        """
        for repoHandle in self.reposMgr.iterRepositories():
            try:
                # This checks for user read access
                repoHandle.getAuthToken(self.auth.userId)
            except rest_errors.ProductNotFound:
                continue
            yield repoHandle.projectId, repoHandle.fqdn

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
        client = self.reposMgr.getUserClient(self.auth)
        if not troveFlavors:
            v = versions.VersionFromString(troveVersion)
            flavors = client.repos.getAllTroveFlavors({troveName: [v]})
            troveFlavors = [x.freeze() for x in flavors[troveName][v]]

        q = []
        for flavor in troveFlavors:
            q.append((troveName, versions.VersionFromString(troveVersion), deps.ThawFlavor(flavor)))

        for projectId, fqdn in self._iterVisibleRepositories():
            refs = client.repos.getTroveReferences(fqdn, q)

            results = set()
            for ref in refs:
                if ref:
                    results.update([(x[0], str(x[1]), x[2].freeze()) for x in ref])

            if results:
                references.append((projectId, list(results)))

        return references

    @private
    @typeCheck(str, str, str)
    def getTroveDescendants(self, troveName, troveBranch, troveFlavor):
        descendants = []
        client = self.reposMgr.getUserClient(self.auth)
        for projectId, fqdn in self._iterVisibleRepositories():
            q = (troveName, versions.VersionFromString(troveBranch), deps.ThawFlavor(troveFlavor))
            refs = client.repos.getTroveDescendants(fqdn, [q])

            results = set()
            for ref in refs:
                if ref:
                    results.update([(str(x[0]), x[1].freeze()) for x in ref])

            if results:
                descendants.append((projectId, list(results)))

        return descendants

    def _getMcpClient(self):
        try:
            return mcp_client.Client(self.cfg.queueHost, self.cfg.queuePort)
        except mcp_error.BuildSystemUnreachableError:
            util.rethrow(mint_error.BuildSystemDown)


    #
    # EC2 Support for rBO
    #
    
    @typeCheck(tuple)
    @private
    def validateEC2Credentials(self, authToken):
        """
        Validate the EC2 credentials
        @param authToken: the EC2 authentication credentials
        @type  authToken: C{tuple}
        @return: True if the credentials are valid
        @rtype: C{bool}
        @raises: C{EC2Exception}
        """
        return ec2.EC2Wrapper(authToken, self.cfg.proxy.get('https')).validateCredentials()
    
    @typeCheck(tuple, list)
    @private
    def getEC2KeyPairs(self, authToken, keyNames):
        """
        Get the EC2 key pairs given a list of key names, or get all key pairs
        if no key names are specified.
        @param authToken: the EC2 authentication credentials
        @type  authToken: C{tuple}
        @param keyNames: a list of string key names or an empty list
        @type  keyNames: C{list}
        @return: a tuple consisting of the key name, fingerprint, and material
        @rtype: C{tuple}
        @raises: C{EC2Exception}
        """
        ec2Wrapper = ec2.EC2Wrapper(authToken, self.cfg.proxy.get('https'))
        return ec2Wrapper.getAllKeyPairs(keyNames)

    @private
    def getProxies(self):
        return self._getProxies()

    @private
    @requiresAuth
    @typeCheck(int, str, str, ((str, unicode),))
    def addProductVersion(self, projectId, namespace, name, description):
        self._filterProjectAccess(projectId)
        if not self._checkProjectAccess(projectId, [userlevels.OWNER]):
            raise mint_error.PermissionDenied
        # Check the namespace
        projects._validateNamespace(namespace)
        # make sure it is a valid product version
        projects._validateProductVersion(name)
        project = projects.Project(self, projectId)
        versionId = self.restDb.productMgr.createProductVersion(
                                                 project.getFQDN(),
                                                 name, namespace, description,
                                                 None)
        return versionId

    @private
    @requiresAuth
    @typeCheck(int)
    def getProductVersion(self, versionId):
        try:
            ret = self.productVersions.get(versionId)
        except database.ItemNotFound:
            raise mint_error.ProductVersionNotFound()
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
        # Since we write back what we read in, we should not validate here
        pd.serialize(sio, validate = False)
        return sio.getvalue()

    @private
    @requiresAuth
    @typeCheck(int, ((str, unicode),), str)
    def setProductDefinitionForVersion(self, versionId, productDefinitionXMLString,
            rebaseToPlatformLabel):
        # XXX: Need exception handling here
        pd = proddef.ProductDefinition(fromStream=productDefinitionXMLString)

        # TODO put back overrides

        cclient = self.reposMgr.getClient(self.auth.userId)
        if rebaseToPlatformLabel:
            pd.rebase(cclient, rebaseToPlatformLabel)
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
                              build.getBuildImage().containerFormat)
            task['buildTypeName'] = buildtypes.typeNamesMarketing[buildTypeDt.id]

            # get the name of the flavor.  If we don't have a name mapped to
            # it, specify that it is custom
            flavor = str(build.getBuildBaseFlavor())
            flavorMap = buildtypes.makeBuildFlavorMap(pd)
            if flavorMap.has_key(flavor):
                buildFlavor = flavorMap[flavor]
            else:
                buildFlavor = "Custom Flavor: %s" % flavor
            task['buildFlavorName'] = buildFlavor

            # set the image group
            task['imageGroup'] = "%s=%s" % (build.getBuildImageGroup(),
                    stageLabel)

            taskList.append(task)

        return taskList

    @requiresAuth
    def createPackageTmpDir(self):
        '''
        Creates a directory for use by the package creator UI and Service.
        This directory is the receiving target for uploads, and the cache
        location for pc service operations.

        @rtype: String
        @return: A X{uploadDirectoryHandle} to be used with subsequent calls to
        file upload methods
        '''
        path = tempfile.mkdtemp('', packagecreator.PCREATOR_TMPDIR_PREFIX,
            dir = os.path.join(self.cfg.dataPath, 'tmp'))
        return os.path.basename(path).replace(packagecreator.PCREATOR_TMPDIR_PREFIX, '')

    def _getMinCfg(self, project):
        repoToken = os.urandom(16).encode('hex')
        self.db.auth_tokens.addToken(repoToken, self.auth.userId)
        cfg = self._getProjectConaryConfig(project, repoToken=repoToken)
        cfg['name'] = self.auth.username
        cfg['contact'] = ''
        localhost = 'localhost'
        if ':' in self.cfg.siteHost:
            # Copy the port from secureHost (for the testsuite)
            localhost += self.cfg.siteHost[self.cfg.siteHost.index(':'):]
        cfg.configLine('conaryProxy http http://%s/conary/' % localhost)
        cfg.configLine('conaryProxy https http://%s/conary/' % localhost)

        #package creator service should get the searchpath from the product definition
        rmakeUser = (self.authToken[0], repoToken)
        mincfg = packagecreator.MinimalConaryConfiguration(cfg, rmakeUser)
        return mincfg

    @typeCheck(int, ((str,unicode),), int, ((str,unicode),), ((str,unicode),), ((str,unicode),))
    @requiresAuth
    def getPackageFactories(self, projectId, uploadDirectoryHandle, versionId, sessionHandle, upload_url, label):
        '''
            Given a file represented by L{uploadDirectoryHandle}, query the PC Service for
            possible factories to handle it.

            @param projectId: The id for the project being worked on
            @type projectId: int
            @param uploadDirectoryHandle: Unique key generated by the call to
            L{createPackageTmpDir}
            @type uploadDirectoryHandle: string
            @param versionId: A product version ID
            @type versionId: int
            @param sessionHandle: A sessionHandle.  If empty, one will be created
            @type sessionHandle: string
            @param upload_url: Not used (yet)
            @type upload_url: string
            @param label: stage label
            @type label: str

            @return: L{sessionHandle} and A list of the candidate build factories and the data scanned
            from the uploaded file
            @rtype: list of 3-tuples.  The 3-tuple consists of the
            factory name (i.e. X{factoryHandle}, the factory definition XML and a
            dictionary of key-value pairs representing the scanned data.

            @raise PackageCreatorError: If the file provided is not supported by
            the package creator service, or if the L{uploadDirectoryHandle} does not
            contain a valid manifest file as generated by the upload CGI script.
        '''
        from mint.lib.fileupload import fileuploader

        path = packagecreator.getUploadDir(self.cfg, uploadDirectoryHandle)
        fileuploader = fileuploader(path, 'uploadfile')
        try:
            info = fileuploader.parseManifest()
        except IOError, e:
            log.exception("Error parsing pcreator manifest:")
            raise mint_error.PackageCreatorError("unable to download the file and/or parse the uploaded file's manifest: %s" % str(e))

        if info.get('error'):
            raise mint_error.PackageCreatorError('File download failed with '
                'the following error: %s' % info.get('error'))

        #TODO: Check for a URL
        #Now go ahead and start the Package Creator Service

        #Register the file
        pc = self.getPackageCreatorClient()
        project = projects.Project(self, projectId)

        if not sessionHandle:
            mincfg = self._getMinCfg(project)
            #Get the version object
            version = self.getProductVersion(versionId)
            #Start the PC Session
            sesH = pc.startSession(dict(hostname=project.getFQDN(),
                shortname=project.shortname, namespace=version['namespace'],
                version=version['name']), mincfg, label=label)
        else:
            sesH = sessionHandle

        # "upload" the data
        pc.uploadData(sesH, info['filename'], info['tempfile'], None)
        fact, data = packagecreator.getPackageCreatorFactories(pc, sesH)

        return sesH, fact, data

    @requiresAuth
    def getPackageCreatorPackages(self, projectId):
        """
            Return a list of all of the packages that are available for maintenance by the package creator UI.  This is done via a conary API call to retrieve all source troves with the PackageCreator troveInfo.
            @param projectId: Project ID of the project for which to request the list
            @type projectId: int

            @rtype: dict(dict(dict(data)))
            @return: The available packages: outer dict uses the version string
            as the key, inner uses the namespace, third uses the trove name as
            keys.  Data is a dict containing the c{productDefinition} dict and
            the C{stageLabel}.
        """
        # Get the conary repository client
        project = projects.Project(self, projectId)
        client = self.reposMgr.getUserClient(self.auth)

        troves = client.repos.getPackageCreatorTroves(project.getFQDN())
        #Set up a dictionary structure
        ret = dict()

        for (n, v, f), sjdata in troves:
            data = json.loads(sjdata)
            # First version
            # We expect data to look like {'productDefinition':
            # dict(hostname='repo.example.com', shortname='repo',
            # namespace='rbo', version='2.0'), 'stageLabel':
            # 'repo.example.com@rbo:repo-2.0-devel'}

            # Do a backwards compatability check if it is an older trove
            stageLabel = str((('stageLabel' in data and data['stageLabel']) or data['develStageLabel']))

            #Filter out labels that don't match the stageLabel
            label = str(v.trailingLabel())
            if label == stageLabel:
                pDefDict = data['productDefinition']
                manip = ret.setdefault(pDefDict['version'], dict())
                manipns = manip.setdefault(pDefDict['namespace'], dict())
                manipns[n] = data
                
            if v.trailingRevision():
                data['stageLabel'] += '/%s' % v.trailingRevision()
                
        return ret

    @requiresAuth
    def startPackageCreatorSession(self, projectId, prodVer, namespace, troveName, label):
        project = projects.Project(self, projectId)

        sesH, pc = self._startPackageCreatorSession(project, prodVer, namespace, troveName, label)

        return sesH

    def _startPackageCreatorSession(self, project, prodVer, namespace, troveName, label):
        pc = self.getPackageCreatorClient()
        mincfg = self._getMinCfg(project)
        try:
            sesH = pc.startSession(dict(hostname=project.getFQDN(),
                shortname=project.shortname, namespace=namespace,
                version=prodVer), mincfg, "%s=%s" % (troveName, label))
        except packagecreator.errors.PackageCreatorError, err:
            raise mint_error.PackageCreatorError( \
                    "Error starting the package creator service session: %s", str(err))
        return sesH, pc

    @requiresAuth
    @typeCheck(((str, unicode),))
    def getPackageCreatorRecipe(self, sesH):
        """
        Return a tuple of (isDefault, recipeData)

        isDefault is True if the user has not modified the recipe
        """
        pc = self.getPackageCreatorClient()
        return pc.getRecipe(sesH)

    @requiresAuth
    @typeCheck(((str, unicode),), str)
    def savePackageCreatorRecipe(self, sesH, recipeData):
        """
        Store a package creator recipe. using an empty string for recipeData
        will return recipe to default.
        """
        pc = self.getPackageCreatorClient()

        # Strip off CRLFs and replace them with LFs
        sanitizedRecipeData = recipeData.replace('\r\n', '\n')
        pc.saveRecipe(sesH, sanitizedRecipeData)

        return False

    @requiresAuth
    def getPackageFactoriesFromRepoArchive(self, projectId, prodVer, namespace, troveName, label):
        """
            Get the list of factories, but instead of using an uploaded file,
            it uses the archive that is stored in the :source trove referred to
            by C{troveSpec}.

            @param projectId: Project ID
            @type projectId: int
            @param troveSpec:
        """
        project = projects.Project(self, projectId)
        #start the session
        sesH, pc = self._startPackageCreatorSession(project, prodVer, namespace, troveName, label)
        fact, data = packagecreator.getPackageCreatorFactories(pc, sesH)

        return sesH, fact, data

    @typeCheck(((str,unicode),), ((str,unicode),), dict, bool, ((str,unicode),))
    @requiresAuth
    def savePackage(self, sessionHandle, factoryHandle, data, build, recipeContents=''):
        """
        Save the package to the devel repository and optionally start building it

        @param sessionHandle: Unique key generated by the call to
        L{createPackageTmpDir}
        @type sessionHandle: string
        @param factoryHandle: The handle to the chosen factory as returned by
        L{getPackageFactories}
        @type factoryHandle: string
        @param data: The data requested by the factory definition referred to
        by the L{factoryHandle}
        @type data: dictionary
        @param build: Build the package after it's been saved?
        @type build: boolean
        @param recipeContents: The contents of the recipe to use
        @type recipeContents: string

        @return: a troveSpec pointing to the created source trove
        @rtype: str
        """
        if recipeContents:
            self.savePackageCreatorRecipe(sessionHandle, recipeContents)

        pc = self.getPackageCreatorClient()

        try:
            datastream = packagecreator.getFactoryDataFromDataDict(pc, sessionHandle, factoryHandle, data)
            srcHandle = pc.makeSourceTrove(sessionHandle, factoryHandle, datastream.getvalue())
        except packagecreator.errors.ConstraintsValidationError, err:
            raise mint_error.PackageCreatorValidationError(*err.args)
        except packagecreator.errors.PackageCreatorError, err:
            raise mint_error.PackageCreatorError( \
                    "Error attempting to create source trove: %s", str(err))
        if build:
            try:
                pc.build(sessionHandle, commit=True)
            except packagecreator.errors.PackageCreatorError, err:
                raise mint_error.PackageCreatorError( \
                        "Error attempting to build package: %s", str(err))
        return srcHandle

    @typeCheck(((str,unicode),))
    @requiresAuth
    def getPackageBuildStatus(self, sessionHandle):
        """
        Retrieve the build status of the package referred to by L{sessionHandle}, if any.

        @param sessionHandle: Unique key generated by the call to
        L{createPackageTmpDir}
        @type sessionHandle: string

        @return: a list of four items: whether or not the build is complete, a
        build status code (as returned by rmake), a message, and the list of
        built packages if any.
        @rtype: list(bool, int, string, list of three-tuples)
        """
        pc = self.getPackageCreatorClient()
        try:
            return pc.isBuildFinished(sessionHandle, commit=True)
        except packagecreator.errors.PackageCreatorError, e:
            # TODO: Get a real error status code
            return [True, -1, str(e), []]

    @typeCheck(((str,unicode),))
    @requiresAuth
    def getPackageBuildLogs(self, sessionHandle):
        """
        Get the build logs for the package creator build, if a build has been performed.

        @param sessionHandle: Unique key generated by the call to
        L{createPackageTmpDir}
        @type sessionHandle: string

        @return: The entire rmake build log
        @rtype: string
        @raise PackageCreatorError: If no build has been attempted, or an error
        occurs talking to the build process.
        """
        pc = self.getPackageCreatorClient()
        try:
            return pc.getBuildLogs(sessionHandle)
        except packagecreator.errors.PackageCreatorError, e:
            raise mint_error.PackageCreatorError("Error retrieving build logs: %s" % str(e))

    @typeCheck(((str,unicode),), ((str,unicode),))
    @requiresAuth
    def pollUploadStatus(self, uploadDirectoryHandle, fieldname):
        """
        Check the status of the upload to the CGI script by reading the status
        file.  Return some measurements useful for displaying progress.

        @param uploadDirectoryHandle: Unique key generated by the call to
        L{createPackageTmpDir}
        @type uploadDirectoryHandle: string
        @param fieldname: The name of the upload field (default in package
        creator is B{fileupload}).  This is used if more than one fileupload is
        to happen on the same form as a sort of namespace.
        @type fieldname: string

        @return: See L{mint.web.whizzyupload.pollStatus}.  Contains the
        metadata, the current status, and the current time for calculating
        upload speed, and estimated time remaining.
        @rtype: dictionary

        @raise mint_error.PermissionDenied: If the L{uploadDirectoryHandle} doesn't exist, or is
        invalid.
        """
        from mint.lib.fileupload import fileuploader
        fieldname = str(fieldname)
        ## Connect up to the tmpdir
        path = packagecreator.getUploadDir(self.cfg, uploadDirectoryHandle)

        if os.path.isdir(path):
            #Look for the status and metadata files
            return fileuploader(path, fieldname).pollStatus()
        else:
            raise mint_error.PermissionDenied("You are not allowed to check status on this file")

    @typeCheck(((str,unicode),), (list, ((str,unicode),)))
    @requiresAuth
    def cancelUploadProcess(self, uploadDirectoryHandle, fieldnames):
        """
        If an upload is in progress to the cgi script, kill the processId being
        used to handle it

        @param uploadDirectoryHandle: Unique key generated by the call to
        L{createPackageTmpDir}
        @type uploadDirectoryHandle: string
        @param fieldnames: The name(s) of the upload fields (default in package
        creator is B{fileupload}).  This is used if more than one fileupload is
        to happen on the same form as a sort of namespace.
        @type fieldname: list of strings

        @return: True if the uploadDirectoryHandle is a valid session, False otherwise.
        @rtype: boolean
        """
        from mint.lib.fileupload import fileuploader
        str_fieldnames = [str(x) for x in fieldnames]
        path = packagecreator.getUploadDir(self.cfg, uploadDirectoryHandle)
        if os.path.isdir(path):
            for fieldname in str_fieldnames:
                fileuploader(path, fieldname).cancelUpload()
            return True
        else:
            return False

    @requiresAuth
    def startApplianceCreatorSession(self, projectId, versionId, rebuild, stageLabel = None):
        project = projects.Project(self, projectId)
        version = self.getProductVersion(versionId)
        pc = self.getApplianceCreatorClient()
        mincfg = self._getMinCfg(project)
        try:
            sesH, otherInfo = pc.startApplianceSession(dict(hostname=project.getFQDN(),
                shortname=project.shortname, namespace=version['namespace'],
                version=version['name']), mincfg, rebuild, stageLabel)
        except packagecreator.errors.NoFlavorsToCook, err:
            raise mint_error.NoImagesDefined( \
                    "Error starting the appliance creator service session: %s",
                    str(err))
        except packagecreator.errors.ApplianceFactoryNotFound, err:
            raise mint_error.OldProductDefinition( \
                    "Error starting the appliance creator service session: %s",
                    str(err))

        except packagecreator.errors.PackageCreatorError, err:
            log.exception("Error starting appliance creator session:")
            raise mint_error.PackageCreatorError( \
                    "Error starting the appliance creator service session: %s", str(err))
        return sesH, otherInfo

    @requiresAuth
    def makeApplianceTrove(self, sessionHandle, buildStandardGroup = False):
        pc = self.getApplianceCreatorClient()
        # If we ever allow jumping past the editApplianceGroup page, this will
        # have to filter out the :source troves added through package creator
        return pc.makeApplianceTrove(sessionHandle, buildStandardGroup)

    @requiresAuth
    def addApplianceTrove(self, sessionHandle, troveSpec):
        pc = self.getApplianceCreatorClient()
        # hard code the explicit flag to True for this codepath
        return pc.addTrove(sessionHandle, troveSpec, True)

    @requiresAuth
    def addApplianceTroves(self, sessionHandle, troveList):
        pc = self.getApplianceCreatorClient()
        # abstract out the implicit troves
        troveDict = pc.listTroves(sessionHandle)
        explicit = set(troveDict.get('explicitTroves', []))
        explicit.update(set(troveList))
        return pc.setTroves(sessionHandle, list(explicit),
                troveDict.get('implicitTroves', []))

    @requiresAuth
    def setApplianceTroves(self, sessionHandle, troveList):
        pc = self.getApplianceCreatorClient()
        # abstract out the implicit troves
        troveDict = pc.listTroves(sessionHandle)
        return pc.setTroves(sessionHandle, troveList,
                troveDict.get('implicitTroves', []))

    @requiresAuth
    def addApplianceSearchPaths(self, sessionHandle, searchPaths):
        pc = self.getApplianceCreatorClient()
        try:
            return pc.addSearchPaths(sessionHandle, searchPaths)
        except packagecreator.errors.PackageCreatorError, e:
            raise mint_error.SearchPathError(str(e))

    @requiresAuth
    def listApplianceSearchPaths(self, sessionHandle):
        pc = self.getApplianceCreatorClient()
        return pc.listSearchPaths(sessionHandle)

    @requiresAuth
    def removeApplianceSearchPaths(self, sessionHandle, searchPaths):
        pc = self.getApplianceCreatorClient()
        return pc.removeSearchPaths(sessionHandle, searchPaths)

    @requiresAuth
    def listApplianceTroves(self, projectId, sessionHandle):
        pc = self.getApplianceCreatorClient()
        client = self.reposMgr.getUserClient(self.auth)
        pkgs = []
        # we only care about explicit troves here
        for x in pc.listTroves(sessionHandle).get('explicitTroves', []):
            if ':source' in x:
                src = (x.replace(":source", '') + '-1').encode('utf-8') #Have to assume the build count
                ts = parseTroveSpec(src)
                try:
                    # Later on we can use this to get a specific version, now
                    # we just care that it doesn't raise a TroveNotFound
                    # exception
                    client.repos.findTrove(None, ts)
                except TroveNotFound:
                    #Don't add it to our final list, no binary got built
                    pass
                else:
                    pkgs.append(ts[0])
            else:
                pkgs.append(x)
        return pkgs

    @requiresAuth
    def getProductVersionSourcePackages(self, projectId, versionId):
        pd = self._getProductDefinitionForVersionObj(versionId)
        label = versions.Label(pd.getDefaultLabel())
        client = self.reposMgr.getUserClient(self.auth)
        ret = []
        trvlist = client.repos.findTroves(label, [(None, None, None)],
                allowMissing=True)
        for k,v in trvlist.iteritems():
            for n, v, f in v:
                if n.endswith(':source'):
                    ret.append((n, v.freeze()))
        return ret

    @typeCheck(int, int, ((str,unicode),), ((str,unicode),))
    @requiresAuth
    def buildSourcePackage(self, projectId, versionId, troveName, troveVersion):
        project = projects.Project(self, projectId)
        version = self.getProductVersion(versionId)
        pc = self.getPackageCreatorClient()
        mincfg = self._getMinCfg(project)
        try:
            sesH = pc.startPackagingSession(dict(hostname=project.getFQDN(),
                shortname=project.shortname, namespace=version['namespace'],
                version=version['name']), mincfg, "%s=%s" % (troveName, troveVersion))
        except packagecreator.errors.PackageCreatorError, err:
            raise mint_error.PackageCreatorError( \
                    "Error starting the package creator service session: %s", str(err))
        try:
            pc.build(sesH, commit=True)
        except packagecreator.errors.PackageCreatorError, err:
            raise mint_error.PackageCreatorError( \
                    "Error attempting to build package: %s", str(err))
        return sesH

    @requiresAuth
    def getAvailablePackages(self, sessionHandle, refresh = False):
        pc = self.getPackageCreatorClient()
        return pc.getAvailablePackagesFrozen(sessionHandle, refresh)

    @requiresAuth
    def getAvailablePackagesFiltered(self, sessionHandle, refresh = False, ignoreComponents = True):
        pc = self.getPackageCreatorClient()
        return pc.getAvailablePackagesFiltered(sessionHandle, refresh, ignoreComponents)

    @typeCheck(str, str, dict)
    @requiresAdmin
    def addTarget(self, targetType, targetName, dataDict):
        """
        Add a new deployment target to rBuilder.
        @param targetType: a string identifying the type of deployment target
                           eg. 'ec2'
        @type targetType: C{str}
        @param targetName: a string representing the name of the deployement
                           target. eg. 'aws'. together with targetType, these
                           values uniquely identify a specific deployment target
                           instance
        @type targetName: C{str}
        @param dataDict: a dictionary of target specific data. keys are strings
                         and values must be json serializable objects.
        returns: True
        raises: TargetExists if addTarget is called with targetType, targetName
                that duplicate an existing target.
        """
        targetId = self.targets.addTarget(targetType, targetName)
        self.targetData.addTargetData(targetId, dataDict)
        return True

    @typeCheck(str, str)
    @requiresAdmin
    def deleteTarget(self, targetType, targetName):
        """
        delete a deployment target from rBuilder.
        @param targetType: a string identifying the type of deployment target
                           eg. 'ec2'
        @type targetType: C{str}
        @param targetName: a string representing the name of the deployement
                           target. eg. 'aws'. together with targetType, these
                           values uniquely identify a specific deployment target
                           instance
        returns: True
        raises: TargetMissing if targetType, targetName don't map to an existing
                target
        """
        targetId = self.targets.getTargetId(targetType, targetName)
        self.targetData.deleteTargetData(targetId)
        self.targets.deleteTarget(targetId)
        return True

    @typeCheck(str, str)
    @requiresAdmin
    def getTargetData(self, targetType, targetName):
        """
        Get dictionary of target specific data
        @param targetType: a string identifying the type of deployment target
                           eg. 'ec2'
        @type targetType: C{str}
        @param targetName: a string representing the name of the deployement
                           target. eg. 'aws'. together with targetType, these
                           values uniquely identify a specific deployment target
                           instance
        returns: dict representing target specific data
        raises: TargetMissing if targetType, targetName don't map to an existing
                target
        """
        # an admin-only interface to retrieve the data associated with a target
        # XXX it's not clear if this function should be more open, but just
        # not return all data
        return self._getTargetData(targetType, targetName)

    def _getTargetData(self, targetType, targetName, supressException = False):
        default = -1
        if supressException:
            default = None
        targetId = self.targets.getTargetId(targetType, targetName, default)
        if targetId is None:
            return {}
        return self.targetData.getTargetData(targetId)

    @typeCheck(str)
    @requiresAuth
    def getAllBuildsByType(self, buildType):
        res = self.builds.getAllBuildsByType(buildType, self.auth.userId,
                                             not self.auth.admin)

        for buildData in res:
            # we want to drop the hostname. it was collected by the builds
            # module call for speed reasons
            hostname = buildData.pop('hostname')
            buildId = buildData['buildId']
            buildData['buildPageUrl'] = \
                    self._getBuildPageUrl(buildId, hostname = hostname)
            buildData['baseFileName'] = self.getBuildBaseFileName(buildId)

            buildFilenames = self.getBuildFilenames(buildId)
            if buildFilenames:
                first = buildFilenames[0]
                buildData['downloadUrl'] = first['downloadUrl']
                buildData['sha1'] = first['sha1']
            buildData['files'] = [ self._buildFileRepr(x)
                    for x in buildFilenames or [] ]

        return res

    @classmethod
    def _buildFileRepr(cls, buildFile):
        fileFields = [ 'idx', 'sha1', 'downloadUrl', 'size' ]
        ret = dict((x, buildFile[x]) for x in fileFields)

        fileUrls = buildFile['fileUrls']
        fileNames = [ x[2] for x in fileUrls if x[1] == urltypes.LOCAL ]
        if fileNames:
            ret['filename'] = os.path.basename(fileNames[0])
        return ret

    def getAvailablePlatforms(self):
        """
        Returns a list of available platforms and their names (descriptions).
        Any platform definitions that cannot be fetched will be skipped (and
        an error message will be logged).
        @rtype: C{list} of C{tuple}s. Each tuple is a pair; first element is
           the platform label, the second element is the platform name.
        """
        return zip(self.cfg.availablePlatforms, self.cfg.availablePlatformNames)

    def isPlatformAcceptable(self, platformLabel):
        return (platformLabel in set(self.cfg.acceptablePlatforms + self.cfg.availablePlatforms))

    def isPlatformAvailable(self, platformLabel):
        return (platformLabel in self.cfg.availablePlatforms)

    def __init__(self, cfg, allowPrivate=False, db=None, req=None):
        self.cfg = cfg
        self.req = req
        self.db = mint_database.Database(cfg, db=db)
        self.restDb = None
        self.reposMgr = repository.RepositoryManager(cfg, self.db._db)
        self.siteAuth = siteauth.getSiteAuth(cfg.siteAuthCfgPath)

        global callLog
        if self.cfg.xmlrpcLogFile:
            if not callLog:
                callLog = CallLogger(self.cfg.xmlrpcLogFile, [self.cfg.siteHost])
        self.callLog = callLog

        if self.req:
            self.remoteIp = self.req.client_addr
        else:
            self.remoteIp = "0.0.0.0"

        # sanitize IP just in case it's a list of proxied hosts
        self.remoteIp = self.remoteIp.split(',')[0]

        # all methods are private (not callable via XMLRPC)
        # except the ones specifically decorated with @public.
        self._allowPrivate = allowPrivate

        self.maintenanceMethods = ('checkAuth', 'loadSession', 'saveSession',
                                   'deleteSession')

    @typeCheck(int)
    @requiresAdmin
    def deleteProject(self, projectId):
        """
        Delete a project
        @param projectId: The id of the project to delete
        @type projectId: C{int}
        """
        handle = self.reposMgr.getRepositoryFromProjectId(projectId)
        log.info("Deleting project %s (%d)", handle.shortName, projectId)

        # Delete images first since some of them may be AMIs or otherwise
        # reside on S3.
        try:
            for buildId in self.builds.iterBuildsForProject(projectId):
                self._deleteBuild(buildId, force=True)
        except:
            log.warning("Could not delete images for project %s:",
                    handle.shortName, exc_info=True)

        # Perform all the remaining database operations in a single
        # transaction.
        cu = self.db.transaction()
        try:
            cu.execute("DELETE FROM Projects WHERE projectId = ?", projectId)
        except:
            self.db.rollback()
            raise
        self.db.commit()

        # Delete the repository database.
        if handle.hasDatabase:
            try:
                handle.destroy()
            except:
                log.exception("Could not delete repository for project %s:",
                        handle.shortName)

        # Clean up the stragglers
        imagesDir = os.path.join(self.cfg.imagesPath, handle.shortName)
        if os.path.exists(imagesDir):
            try:
                util.rmtree(imagesDir)
            except:
                log.warning("Could not delete project images directory %s:",
                        imagesDir, exc_info=True)
        
        return True

    def getPackageCreatorClient(self):
        return self._getPackageCreatorClient()

    def getApplianceCreatorClient(self):
        return self._getPackageCreatorClient()

    def _getPackageCreatorClient(self):
        def _getManager():
            from mint.django_rest.rbuilder.manager import rbuildermanager
            return rbuildermanager.RbuilderManager()
        return packagecreator.getPackageCreatorClient(self.cfg, self.authToken,
            djangoManagerCallback=_getManager)

    def getDownloadUrlTemplate(self, useRequest=True):
        if self.req and useRequest:
            hostname = self.req.host
        else:
            hostname = self.cfg.siteHost
        return "http://%s%sdownloadImage?fileId=%%d" % (hostname, self.cfg.basePath)

