#
# Copyright (c) SAS Institute Inc.
#

import errno
import logging
import os
import re
import json
import stat
import sys
import time
import StringIO

from mint import buildtypes
from mint.db import database as mint_database
from mint.rest.db import database as rest_database
from mint import users
from mint.lib import data
from mint.lib import database
from mint.lib.mintutils import ArgFiller
from mint import builds
from mint import helperfuncs
from mint import jobstatus
from mint import mint_error
from mint import buildtemplates
from mint import projects
from mint import userlevels
from mint import urltypes
from mint.db import repository
from mint.rest import errors as rest_errors
from mint.scripts import repository_sync

from conary import conarycfg
from conary import trovetup
from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec
from conary.deps import deps
from conary.lib import sha1helper
from conary.lib import util
from conary.repository.errors import TroveNotFound
from conary.repository.netrepos.reposlog import RepositoryCallLogger as CallLogger
from conary import errors as conary_errors

from mcp import client as mcp_client
from mcp import mcp_error
from rpath_proddef import api1 as proddef


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
    if paramType is None:
        return True
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
            try:
                args = filler.fill(args, kwargs)
            except TypeError, e:
                # RCE-2231: don't surface TypeError, which results in a 500
                raise mint_error.ParameterError(e[0])
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

        try:
            if methodName.startswith('_'):
                raise AttributeError
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", (methodName,)))

        try:
            try:
                if not authToken:
                    # Until the session is proven valid, assume anonymous
                    # access -- we don't want a broken session preventing
                    # anonymous access or logins.
                    authToken = ('anonymous', 'anonymous')
                self.restDb = rest_database.Database(self.cfg, self.db,
                                                             dbOnly=True)
                self._setAuth(authToken)

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

            except mint_error.MintError as e:
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

    def checkVersion(self):
        if self.clientVer < SERVER_VERSIONS[0]:
            raise mint_error.InvalidClientVersion(
                'Invalid client version %s. Server '
                'accepts client versions %s' % (self.clientVer,
                    ', '.join(str(x) for x in SERVER_VERSIONS)))
        return SERVER_VERSIONS

    @typeCheck(str, str, str, str, str, bool)
    @requiresAdmin
    @private
    def newExternalProject(self, name, hostname, domainname, label, url, mirrored):
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
            log.exception("Error synchronizing repository branches")
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

    def getProjectDataByMember(self, userId):
        filter = (self.auth.userId != userId) and (not self.auth.admin)
        return self.projects.getProjectDataByMember(userId, filter)

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

    # user methods
    @typeCheck(int)
    @private
    def getUser(self, id):
        return self.users.get(id)

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

    @typeCheck(str)
    @private
    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

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

    @typeCheck()
    @requiresAdmin
    @private
    def getProjectsList(self):
        """
        Collect a list of all projects suitable for creating a select box
        """
        return self.projects.getProjectsList()

    #
    # LABEL STUFF
    #

    @typeCheck(int, bool, ((str, type(None)),), ((str, type(None)),))
    @private
    def getLabelsForProject(self, projectId, overrideAuth, newUser, newPass):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        self._filterProjectAccess(projectId)
        return self.labels.getLabelsForProject(projectId, overrideAuth, newUser, newPass)

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
    def getBuild(self, buildId):
        if not self.builds.buildExists(buildId):
            raise mint_error.ItemNotFound
        self._filterBuildAccess(buildId)
        build = self.builds.get(buildId)

        return build

    @staticmethod
    def _formatTupForModel(tup):
        return '"%s=%s/%s[%s]"' % (
                tup[0],
                tup[1].trailingLabel(),
                tup[1].trailingRevision(),
                tup[2])

    @typeCheck(int, ((str, unicode),), bool, list, str, list)
    @requiresAuth
    @private
    def newBuildsFromProductDefinition(self, versionId, stageName, force,
                                       buildNames = None, versionSpec = None,
                                       groupSpecs = None):
        """
        Launch the image builds defined in the product definition for the
        given version id and stage.  If provided, use versionSpec as the top
        level group for the image, otherwise use the top level group defined
        in the product defintion.
        If groupSpecs is provided, build the image from the specified list of
        groups. This is an extended form of versionSpec, and does not use the
        groups defined in the product definition.

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

        stageLabel, buildList = self._getStageLabelAndBuilds(pd, stageName)

        # Create build data for each defined build so we can create the builds
        # later
        filteredBuilds = []
        buildErrors = []

        client = self.reposMgr.getUserClient(self.auth)
        repos = client.getRepos()

        if groupSpecs:
            parsedGroupSpecs = [ parseTroveSpec(x) for x in groupSpecs ]
            groupTroves = repos.findTroves(None, parsedGroupSpecs,
                    allowMissing=True)
        else:
            if not versionSpec:
                versionSpec = stageLabel
            grps = set([(str(x.getBuildImageGroup()), versionSpec, None)
                for x in buildList])
            # Add system model items from the build into the list of groups
            # we're looking up
            for build in buildList:
                if buildNames and build.name not in buildNames:
                    continue
                for item in (build.systemModelItem or []):
                    for trv in item.trove:
                        trv = trovetup.TroveSpec(str(trv))
                        v = trv.version or versionSpec
                        grps.add((trv.name, v, None))

            groupTroves = repos.findTroves(None, grps, allowMissing=True)

        pdefs = dict()
        # Add version of the current proddef, so we don't look for it again
        pdefs[trovetup.TroveSpec(pd.getLoadedTrove()).version] = pd

        imgGroupTups = set()

        filteredBuilds1 = []

        for build in buildList:
            if buildNames and build.name not in buildNames:
                continue
            buildFlavor = deps.parseFlavor(str(build.getBuildBaseFlavor()))
            if groupSpecs:
                candidateGroupLists = [ (x, buildFlavor, groupTroves.get(x, []))
                        for x in parsedGroupSpecs ]
            else:
                buildGroup = str(build.getBuildImageGroup())
                candidateGroupLists = [
                    (buildGroup, buildFlavor,
                        groupTroves.get((buildGroup, versionSpec, None), []))
                    ]

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

            groupTups = []
            for buildGroup, buildFlavor, groupList in candidateGroupLists:
                # Returns a list of troves that satisfy buildFlavor.
                groupTup = self._resolveTrove(groupList, flavorSet, architecture)
                if not groupTup:
                    # No troves were found, save the error.
                    buildErrors.append(str(conary_errors.TroveNotFound(
                        "Trove '%s' has no matching flavors for '%s'" % \
                        (buildGroup, buildFlavor))))
                    break
                groupTups.append(groupTup)
                if not groupSpecs:
                    imgGroupTups.add(groupTup)
            if len(groupTups) != len(candidateGroupLists):
                # One of the groups was not found; give up
                continue
            filteredBuilds1.append((build, groupTups, flavorSet, architecture))

        # Initialize the group-to-proddef with the current proddef, in case
        # one is not found in the group's troveinfo
        grp2pd = dict((x, pd) for x in imgGroupTups)
        # Find potential extra product definition references
        if imgGroupTups:
            groupTrvs = repos.getTroves(imgGroupTups, withFiles=False)
            for groupTrv in groupTrvs:
                pdv = groupTrv.getProductDefinitionVersion()
                if not pdv or pdv in pdefs:
                    continue
                sourceTrove = "product-definition:source=%s" % pdv
                newpd = proddef.ProductDefinition()
                newpd.setBaseLabel(str(pdv.trailingLabel()))
                newpd.loadFromRepository(client, sourceTrove=sourceTrove)
                pdefs[pdv] = newpd
                grp2pd[groupTrv.getNameVersionFlavor()] = newpd

        searchTroves = set()
        for pdobj in pdefs.values():
            searchTroves.update(x.getTroveTup()
                    for x in pdobj.getSearchPaths())
        searchTroves = repos.findTroves(None, searchTroves, allowMissing=True)

        for build, groupTups, flavorSet, architecture in filteredBuilds1:
            systemModelItems = build.systemModelItem
            imageModel = []
            for groupTup in groupTups:
                pdobj = grp2pd.get(groupTup)
                if not pdobj:
                    continue
                for item in pdobj.getSearchPaths():
                    matches = searchTroves.get(item.getTroveTup(), ())
                    searchTup = self._resolveTrove(matches, flavorSet, architecture)
                    if not searchTup or searchTup[0].endswith(':source'):
                        # Skip any searchPath elements that are source troves
                        # (APPENG-2967)
                        continue
                    imageModelLine = 'search {trv}\n'.format(
                            trv=self._formatTupForModel(searchTup))
                    if not build.systemModelItem:
                        # For now, comment out the line, unless a multi-trove
                        # system model
                        imageModelLine = '#' + imageModelLine
                    imageModel.append(imageModelLine)
            if systemModelItems:
                for item in systemModelItems:
                    trvs = []
                    for trvSpec in item.trove:
                        ptrvSpec = trovetup.TroveSpec(str(trvSpec))
                        v = ptrvSpec.version or versionSpec
                        matches = groupTroves.get((ptrvSpec.name, v, None), [])
                        trvTup = self._resolveTrove(matches, flavorSet, architecture)
                        if trvTup:
                            trvs.append(self._formatTupForModel(trvTup))
                        else:
                            trvs.append(ptrvSpec.asString())
                    imageModel.append('{op} {data}\n'.format(
                        op=item.operation, data=' '.join(trvs)))
            else:
                for groupTup in groupTups:
                    imageModel.append('install %s\n' %
                            self._formatTupForModel(groupTup))
            # Store a build with options for the best match for each build
            # results are sorted best to worst
            filteredBuilds.append((build, groupTups, imageModel))

        if buildErrors and not force:
            raise mint_error.TroveNotFoundForBuildDefinition(buildErrors)

        dockerBuildChains, filteredBuilds = self._filterDockerImages(
                filteredBuilds, repos, pd, projectId, versionId, stageName,
                stageLabel, buildList)

        dockerBuilds = self._categorizeDockerBuilds(dockerBuildChains)

        # Create/start each build.
        buildIds = []
        for buildObj in filteredBuilds:
            buildIds.append(self._newBuild(buildObj, start=True))
        for buildObj in dockerBuilds:
            if buildObj.withJobslave:
                continue
            buildIds.append(self._newBuild(buildObj, start=False))
            # Serialize build so we generate the proper output tokens
            buildObj.buildData = self.serializeBuild(buildObj.id)
        for buildObj in dockerBuilds:
            if not buildObj.withJobslave:
                continue
            buildIds.append(self._newBuild(buildObj, start=True,
                buildTree=buildObj.tree))
        return buildIds

    def _newBuild(self, buildObj, start=False, buildTree=None):
        nvf = buildObj.nvf
        n, v, f = str(nvf[0]), nvf[1].freeze(), nvf[2].freeze()
        if buildTree is not None:
            buildObj.buildSettings['dockerBuildTree'] = json.dumps(
                    buildTree.serialize())
        buildId = self.newBuildWithOptions(buildObj.projectId, buildObj.buildName,
                n, v, f,
                buildObj.buildType, buildObj.buildSettings,
                imageModel=buildObj.imageModel,
                start=False,
                productVersionId=buildObj.productVersionId,
                stageName=buildObj.stageName,
                _proddef=buildObj.proddef,
                )
        buildObj.id = buildId
        if start:
            self.startImageJob(buildId)
        return buildId

    def _categorizeDockerBuilds(self, dockerBuildChains):
        # Grab the unique roots of the build chains
        trees = dict((id(x[0]), x[0]) for x in dockerBuildChains).values()
        for dockerBuild in trees:
            node = dockerBuild
            # Find the first node in this tree that needs to be built.
            while 1:
                if node.url is None:
                    break
                assert node.childrenMap
                node = node.childrenMap.values()[0]
            assert node.url is None
            node.withJobslave = True
            node.tree = dockerBuild
            # XXX we use swapSize even though there's no swap in docker
            # images. This is so we can artificially enlarge the LVM volume
            # created by the jobmaster for the jobslave to accommodate all the
            # layers, compressed and uncompressed, that we need at the same
            # time.
            node.buildSettings['swapSize'] = 3 * int(
                    node.computedSize() / 1024 / 1024)
        # Now find everything we need to build
        buildsMap = dict()
        stack = trees
        while stack:
            top = stack.pop()
            stack.extend(top.childrenMap.values())
            if top.url is None:
                buildsMap[id(top)] = top
        return buildsMap.values()

    def _filterDockerImages(self, buildsL, repos, pd,
            projectId, versionId, stageName, stageLabel, buildDefList):
        # Find docker images, we may have to build extra images
        dockerImages = []
        rest = []
        # XXX it is possible to have the same image point to the same group,
        # with different dockerfiles. This map should take that into account.
        nvfToBuildMap = {}
        for buildDefinition, nvfList, imageModel in buildsL:
            buildImage = buildDefinition.getBuildImage()
            buildType = buildImage.containerFormat and \
                    str(buildImage.containerFormat) or ''
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
            img = ImageBuild(buildType=buildType,
                    buildName=buildDefinition.name,
                    buildDefinition=buildDefinition,
                    nvf=nvfList[0],
                    proddef=pd,
                    imageModel=imageModel,
                    projectId = projectId,
                    productVersionId=versionId,
                    buildSettings=buildSettings,
                    stageName=stageName)
            if buildType != DockerImageBuild.TypeName:
                rest.append(img)
                continue
            assert len(nvfList) == 1
            dockerImg = nvfToBuildMap.get(img.nvf)
            if dockerImg is None:
                dockerImg = DockerImageBuild.fromObject(img)
                nvfToBuildMap[img.nvf] = dockerImg
            buildChain = self._findBuildChain(repos, dockerImg, nvfToBuildMap)
            dockerImages.append(buildChain)

        buildsMap = { versionId : (pd, {
            stageName : (stageLabel, buildDefList) }) }

        processed = set()

        # For Docker builds without a build definition, try to find one
        for buildChain in dockerImages:
            for buildObj in buildChain:
                if buildObj.nvf in processed:
                    continue
                processed.add(buildObj.nvf)
                if buildObj.buildDefinition is not None:
                    continue
                # Choose a somewhat sensible default for this build: the group
                # name minus the group- part (APPENG-3467)
                # This will get overwritten with a real name if a build
                # definition is found
                buildObj.buildName = buildObj.nvf.name[6:]
                # Try to find a stage
                label = buildObj.nvf.version.trailingLabel()
                prjInfo = self._getProjectInfoForLabelOnly(str(label))
                if prjInfo is None:
                    continue
                buildObj.projectId = prjInfo[0]
                buildObj.productVersionId = vId = prjInfo[1]
                buildObj.stageName = stgName = prjInfo[2]

                pd1, stagesToBuildList = buildsMap.get(vId, (None, {}))
                if pd1 is None:
                    pd1 = self._getProductDefinitionForVersionObj(vId)
                    buildsMap[vId] = (pd1, stagesToBuildList)
                stgLabel, blist = stagesToBuildList.get(stageName, (None, None))
                if blist is None:
                    stgLabel, blist = self._getStageLabelAndBuilds(pd1, stgName)
                    stagesToBuildList[stageName] = (stgLabel, blist)

                buildDef = self._findImageDefinition(blist, buildObj.nvf,
                        DockerImageBuild.TypeName)
                buildObj.proddef = pd1
                buildObj.buildDefinition = buildDef
                if buildDef:
                    buildObj.buildName = buildDef.name

        return dockerImages, rest

    def _getStageLabelAndBuilds(self, pd, stageName):
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
        return stageLabel, buildList

    @classmethod
    def _matchTroveSpec(cls, nvf, troveSpec):
        # Returns True if troveSpec matches nvf
        if nvf.name != troveSpec.name:
            return False
        if troveSpec.version is None:
            if troveSpec.flavor is None:
                return True
            return troveSpec.flavor.satisfies(nvf.flavor)
        # Is the version a fully specified version?
        troveSpecLabel = troveSpecRevision = None
        if troveSpec.version.startswith('/'):
            trvSpecVersion = versions.VersionFromString(troveSpec.version)
            troveSpecLabel = trvSpecVersion.trailingLabel()
            if hasattr(trvSpecVersion, 'trailingRevision'):
                troveSpecRevision = trvSpecVersion.trailingRevision()
        else:
            _l, _r = troveSpec.version.partition('/')
            troveSpecLabel = versions.Label(_l)
            if _r:
                troveSpecRevision = versions.Revision(_r)
        if troveSpecLabel != nvf.version.trailingLabel():
            return False
        if troveSpecRevision is not None and troveSpecRevision != nvf.version.trailingRevision():
            return False
        if troveSpec.flavor is None:
            return True
        return troveSpec.flavor.satisfies(nvf.flavor)

    def _findImageDefinition(self, buildList, nvf, containerFormat):
        for build in buildList:
            buildImage = build.getBuildImage()
            buildType = buildImage.containerFormat and \
                    str(buildImage.containerFormat) or ''
            if buildType != containerFormat:
                continue
            grpSpec = parseTroveSpec(build.getBuildImageGroup())
            if self._matchTroveSpec(nvf, grpSpec):
                return build
        return None

    def _findImageByNvf(self, nvf, buildType):
        cu = self.db.cursor()
        cu.execute("""\
                SELECT b.buildId, b.status, b.name, b.productVersionId, b.stageName
                  FROM Builds b
                 WHERE b.buildType = ?
                   AND b.troveName = ?
                   AND b.troveVersion = ?
                   AND b.troveFlavor = ?
                 ORDER BY timecreated DESC
                   """, buildType,
                   nvf.name, nvf.version.freeze(),
                   nvf.flavor.freeze())
        return cu.fetchone()

    @classmethod
    def _getTroveHierarchy(cls, repos, trvtup):
        ret = []
        while 1:
            trv = repos.getTrove(*trvtup)
            ret.append(trvtup)
            parent = cls._getParentGroup(trv)
            if parent is None:
                break
            trvtup = parent
        ret.reverse()
        return ret

    def _findBuildChain(self, repos, img, nvfToBuildMap):
        ret = [img]
        while 1:
            trv = repos.getTrove(*img.nvf)
            img.groupSize = trv.troveInfo.size()
            parent = self._getParentGroup(trv)
            if parent is None:
                break
            pimg = nvfToBuildMap.get(parent)
            if pimg is None:
                pimg = DockerImageBuild(nvf=parent)
                nvfToBuildMap[parent] = pimg
            pimg.childrenMap[img.nvf] = img
            ret.append(pimg)
            if pimg.url:
                break
            buildInfo = self._findImageByNvf(parent, buildtypes.DOCKER_IMAGE)
            if buildInfo and buildInfo[1] == 300:
                pimg.id = buildInfo[0]
                buildName, pimg.productVersionId, pimg.stageName = buildInfo[2:]
                bfn = self.getBuildFilenames(pimg.id)
                pimg.url = bfn[0]['downloadUrl']
                bdDict = self.buildData.getDataDict(pimg.id)
                # Remove the stuff that we don't care about
                for k in ['dockerBuildTree', 'outputToken']:
                    bdDict.pop(k, None)
                pimg.dockerImageId = bdDict.get('attributes.docker_image_id')
                pimg.groupSize = bdDict.get('attributes.installed_size')
                pimg.buildData = dict(buildId=pimg.id, name=buildName,
                        data=bdDict)
                break
            img = pimg
        ret.reverse()
        return ret

    @classmethod
    def _getParentGroup(cls, trv):
        for trvtup, byDefault, isStrong in trv.iterTroveListInfo():
            if isStrong and not byDefault and trvtup.name.startswith("group-"):
                return trvtup
        return None

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

    @typeCheck(int, ((str, unicode), ), str, str, str, str, dict, bool, list,
            int, str, None)
    @requiresAuth
    @private
    def newBuildWithOptions(self, projectId, buildName, groupName,
            groupVersion, groupFlavor, buildType, buildSettings, start=False,
            imageModel=None, productVersionId=None, stageName=None,
            _proddef=None,
            ):
        self._filterProjectAccess(projectId)

        version = helperfuncs.parseVersion(groupVersion)
        groupVersion = version.freeze()
        flavor = helperfuncs.parseFlavor(groupFlavor)
        groupFlavor = flavor.freeze()

        pd = None
        if not productVersionId:
            # Detect branch and stage based on the group's label
            label = version.trailingLabel().asString()
            productVersionId, stageName = self._getProductVersionForLabel(
                    projectId, label)
        if productVersionId:
            if _proddef:
                pd = _proddef
            else:
                pd = self._getProductDefinitionForVersionObj(productVersionId)

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
        self.setBuildTrove(buildId, groupName, groupVersion, groupFlavor)
        if not imageModel:
            imageModel = ['install "%s=%s/%s[%s]"\n' % (
                    groupName,
                    version.trailingLabel(),
                    version.trailingRevision(),
                    flavor)]
        self.builds.setModel(buildId, imageModel)
        buildType = buildtypes.xmlTagNameImageTypeMap[buildType]
        newBuild.setBuildType(buildType)

        if pd:
            platName = pd.getPlatformName()
            if 'platformName' in newBuild.getDataTemplate():
                newBuild.setDataValue('platformName', str(platName))
            # RCE-814
            self.builds.setProductVersion(buildId, productVersionId, stageName,
                    proddefVersion=pd.getLoadedTrove())

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

    def _resolveTrove(self, groupList, flavorSet, archFlavor):
        '''
        Return the best matching trove tuple from C{groupList} given flavor
        constraints for the build.

        @return: Matching trove tuple, or None if no match exists
        @rtype: TroveTuple
        '''
        if not groupList:
            return None
        # Get the major architecture from filterFlavor
        filterArch = helperfuncs.getArchFromFlavor(archFlavor)
        completeFlavor = deps.overrideFlavor(flavorSet, archFlavor)
        # Hard filtering is done strictly by major architecture. This ensures
        # two things:
        #  * "is: x86" filter does NOT match "is: x86 x86_64" group
        #  * "is: x86 x86_64" filter DOES match "is: x86_64" group
        # After that, any remaining contests are broken using flavor scoring,
        # but the vast majority of proddefs use one flavor per arch only and
        # thus that case needs to be the most robust.
        archMatches = [ x for x in groupList
                if helperfuncs.getArchFromFlavor(x[2]) in ('', filterArch) ]
        if not archMatches:
            # Nothing even had the correct architecture, bail out.
            return None
        # Filter out old group versions, which show up here if they have a
        # flavor that is no longer present in the latest version
        maxVersion = max(x[1] for x in archMatches)
        latest = [x for x in archMatches if x[1] == maxVersion]
        # Score each group flavor against the filter
        scored = sorted((completeFlavor.score(x[2]), x) for x in latest)
        # Discard flavors that are not satisfied at all
        scored = [(score, x) for (score, x) in scored if score is not False]
        if not scored:
            return None
        # Pick the highest scoring result
        return sorted(scored)[-1][1]

    def _deleteBuild(self, buildId, force=False):
        if not self.builds.buildExists(buildId)  and not force:
            raise mint_error.BuildMissing()

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

    def updateBuild(self, buildId, valDict):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        if len(valDict):
            columns = { 'timeUpdated': time.time(),
                        'updatedBy':   self.auth.userId,
                        }
            for column in ('name', 'description'):
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
        return self.buildData.setDataValue(buildId, name, value, dataType)

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

    @staticmethod
    def _partitionLines(text):
        ret = []
        while '\n' in text:
            n = text.find('\n')
            line, text = text[:n+1], text[n+1:]
            ret.append(line)
        if text:
            ret.append(text)
        return ret

    def serializeBuild(self, buildId):
        self._filterBuildAccess(buildId)

        buildDict = self.builds.get(buildId)
        project = projects.Project(self, buildDict['projectId'])

        cc = conarycfg.ConaryConfiguration(False)
        self._addInternalConaryConfig(cc)

        cfgBuffer = StringIO.StringIO()
        cc.displayKey('repositoryMap', cfgBuffer)
        repoToken = os.urandom(16).encode('hex')
        print >> cfgBuffer, 'user * %s %s' % (self.auth.username, repoToken)
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
                        'conaryCfg' : cfgData,
                        'repoToken': repoToken,
                        }
        if buildDict['proddef_version']:
            proddefTup = trovetup.TroveSpec(buildDict['proddef_version'])
            proddefVersion = versions.VersionFromString(proddefTup[1])
            r['proddefLabel'] = str(proddefVersion.trailingLabel())
            r['proddefVersion'] = buildDict['proddef_version']
        else:
            r['proddefLabel'] = r['proddefVersion'] = ''
        if buildDict['image_model']:
            r['imageModel'] = self._partitionLines(buildDict['image_model'])

        hostBase = '%s.%s' % (self.cfg.hostName, self.cfg.siteDomainName)

        r['UUID'] = '%s-build-%d-%d' % (hostBase, buildId,
                self.builds.bumpBuildCount(buildId))

        #Set up the http/https proxy
        r['proxy'] = dict(self.cfg.proxy)
        r['outputToken'] = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        self.buildData.setDataValue(buildId, 'outputToken',
            r['outputToken'], data.RDT_STRING)

        return r

    @typeCheck(int)
    @private
    def getBuildTrove(self, buildId):
        self._filterBuildAccess(buildId)
        return self.builds.getTrove(buildId)

    def setBuildTrove(self, buildId, troveName, troveVersion, troveFlavor):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        r = self.builds.setTrove(buildId, troveName, troveVersion, troveFlavor)
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

    def _getProjectInfoForLabelOnly(self, label):
        cu = self.db.cursor()
        cu.execute('''
            SELECT pb.projectid, pbs.project_branch_id, pbs.name
              FROM project_branch_stage pbs
              JOIN ProductVersions pb ON (pbs.project_branch_id = pb.productVersionId)
             WHERE pbs.label = ?
        ''', str(label))
        return cu.fetchone()

    @typeCheck(int, int)
    @requiresAuth
    @private
    def setBuildType(self, buildId, buildType):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()
        cu = self.db.cursor()
        cu.execute("UPDATE Builds SET buildType = ? WHERE buildId = ?",
                buildType, buildId)
        self.db.commit()
        return True

    def startImageJob(self, buildId):
        self._filterBuildAccess(buildId)
        if not self.builds.buildExists(buildId):
            raise mint_error.BuildMissing()

        # Clear any previously-existing files.
        self._setBuildFilenames(buildId, [])
        try:
            jobData = self.serializeBuild(buildId)
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

    def _setBuildFilenames(self, buildId, filenames, normalize=False):
        from mint.shimclient import ShimMintClient
        authclient = ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db._db)

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

    @typeCheck(int)
    @requiresAuth
    def getAllProjectLabels(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT DISTINCT(serverName || '@' || branchName)
                FROM PackageIndex WHERE projectId=?""", projectId)
        return [x[0] for x in cu]

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
                                       useReleases = 0,
                                       fullSync = 1)
        else:
            cu = self.db.cursor()
            cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM OutboundMirrors")
            mirrorOrder = cu.fetchone()[0]
            id = self.outboundMirrors.new(sourceProjectId = sourceProjectId,
                                           targetLabels = ' '.join(targetLabels),
                                           allLabels = int(allLabels),
                                           recurse = int(recurse),
                                           useReleases = 0,
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
    def addUpdateService(self, hostname, mirrorUser, mirrorPassword,
            description=''):
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
    @typeCheck(int, str, str, str, ((str, unicode),))
    def editUpdateService(self, upsrvId, hostname, mirrorUser, mirrorPassword, newDesc):
        return self.updateServices.update(upsrvId,
                hostname=hostname,
                description=newDesc,
                mirrorUser=mirrorUser,
                mirrorPassword=mirrorPassword)

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

    def _getMcpClient(self):
        try:
            return mcp_client.Client(self.cfg.queueHost, self.cfg.queuePort)
        except mcp_error.BuildSystemUnreachableError:
            util.rethrow(mint_error.BuildSystemDown)

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
    def getProductDefinitionForVersion(self, versionId):
        pd = self._getProductDefinitionForVersionObj(versionId)
        sio = StringIO.StringIO()
        # Since we write back what we read in, we should not validate here
        pd.serialize(sio, validate = False)
        return sio.getvalue()

    @private
    @typeCheck(int)
    def getProductVersionListForProduct(self, projectId):
        return self.productVersions.getProductVersionListForProduct(projectId)

    @typeCheck(str)
    @requiresAuth
    def getAllBuildsByType(self, buildType):
        res = self.builds.getAllBuildsByType(buildType, self.auth.userId,
                                             not self.auth.admin)

        for buildData in res:
            # we want to drop the hostname. it was collected by the builds
            # module call for speed reasons
            buildId = buildData['buildId']
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

    def _setAuth(self, authToken):
        auth = self.users.checkAuth(authToken)
        authToken = (authToken[0], '')
        self.authToken = authToken
        self.auth = users.Authorization(**auth)
        if self.restDb:
            self.restDb.setAuth(self.auth, authToken)

    def __init__(self, cfg, allowPrivate=False, db=None, req=None):
        self.cfg = cfg
        self.req = req
        self.db = mint_database.Database(cfg, db=db)
        self.restDb = None
        self.reposMgr = repository.RepositoryManager(cfg, self.db._db)

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

    def getDownloadUrlTemplate(self, useRequest=True):
        if self.req and useRequest:
            hostname = self.req.host
        else:
            hostname = self.cfg.siteHost
        return "http://%s%sdownloadImage?fileId=%%d" % (hostname, self.cfg.basePath)

class _BaseImageBuild(object):
    __slots__ = [ 'id', 'nvf', 'projectId', 'productVersionId', 'stageName',
            'buildName', 'buildType', 'buildDefinition', 'buildSettings',
            'proddef', 'imageModel', ]
    def __init__(self, **kwargs):
        kwargs.setdefault('buildSettings', {})
        for s in self._getSlots():
            setattr(self, s, kwargs.pop(s, None))
        if kwargs:
            raise TypeError("Unexpected keywords: %s" % ' '.join(kwargs))

    @classmethod
    def _getSlots(cls):
        slots = set()
        for kls in cls.__mro__:
            slots.update(getattr(kls, '__slots__', []))
        return slots

    @classmethod
    def fromObject(cls, otherObject):
        attrs = {}
        for slot in cls._getSlots():
            val = getattr(otherObject, slot, None)
            if val is not None:
                attrs[slot] = val
        obj = cls(**attrs)
        return obj

    def serialize(self):
        ret = dict(id=self.id)
        ret['nvf'] = self.nvf.asString(withTimestamp=True)
        if self.url:
            ret['url'] = self.url
            assert self.dockerImageId is not None
            ret['dockerImageId'] = self.dockerImageId
        ret['children'] = [ x.serialize() for x in self.childrenMap.values() ]
        return ret

class ImageBuild(_BaseImageBuild):
    __slots__ = []

class DockerImageBuild(_BaseImageBuild):
    __slots__ = [ 'url', 'childrenMap', 'withJobslave', 'tree', 'buildData',
            'dockerImageId', 'groupSize', ]
    TypeName = buildtypes.imageTypeXmlTagNameMap[buildtypes.DOCKER_IMAGE]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('childrenMap', {})
        kwargs['buildType'] = self.__class__.TypeName
        super(DockerImageBuild, self).__init__(*args, **kwargs)

    def serialize(self):
        ret = super(DockerImageBuild, self).serialize()
        ret['buildData'] = self.buildData
        return ret

    def computedSize(self, parentSize=0):
        thisSize = parentSize + self.groupSize
        return thisSize + sum(x.computedSize(thisSize)
                for x in self.childrenMap.values())
