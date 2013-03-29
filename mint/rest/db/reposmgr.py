#
# Copyright (c) rPath, Inc.
#

import copy
import os
import sys

from mint import mint_error
from mint import userlevels
from mint.db import projects
from mint.db import repository as reposdb
from mint.lib import mintutils
from mint.lib import unixutils
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager

from conary import conarycfg
from conary import conaryclient
from conary import trove as cny_trove
from conary.repository import changeset
from conary.repository import errors as reposerrors
from conary.repository import shimclient

_cachedCfg = None


class RepositoryManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
        self.cfg = cfg
        self.auth = auth
        self.profiler = None
        self.cache = mintutils.CacheWrapper(cfg.memCache)

    def createRepositorySafe(self, productId, createMaps=True):
        try:
            self.createRepository(productId, createMaps)
        except mint_error.RepositoryAlreadyExists, e:
            pass

    def createRepository(self, productId, createMaps=True):
        repos = self.db.reposShim.getRepositoryFromProjectId(productId)

        authInfo = models.AuthInfo('userpass',
                self.cfg.authUser, self.cfg.authPass)

        if createMaps:
            self._setLabel(productId, repos.fqdn, repos.getURL(), authInfo)

        if repos.hasDatabase:
            # Create the repository infrastructure (db, dirs, etc.).
            repos.create()

            # Create users and roles
            self.populateUsers(repos)

    def populateUsers(self, repos):
        # here we automatically create the USER and DEVELOPER levels
        # This avoids the chance of paying a high price for adding
        # them later - instead we amortize the cost over every commit
        netServer = repos.getNetServer()
        self._getRoleForLevel(netServer, userlevels.USER)
        if not repos.isExternal:
            self._getRoleForLevel(netServer, userlevels.DEVELOPER)
            self._getRoleForLevel(netServer, userlevels.OWNER)

        # add the auth user so we can add additional permissions
        # to this repository
        self.addUser(repos.fqdn, self.cfg.authUser,
                password=self.cfg.authPass, level=userlevels.ADMIN)

    def deleteRepository(self, fqdn):
        # TODO: move this to the internal RepositoryManager
        repos = self._getRepositoryHandle(fqdn)
        driver = repos.dbTuple[0]
        reposFactory = projects.getFactoryForRepos(driver)(self.cfg)
        reposFactory.delete(repos.fqdn)

    def setProfiler(self, profiler):
        self.profiler = profiler

    def _getRoleForLevel(self, repos, level):
        """
        Gets the role name for the given level, creating the role on
        the fly if necessary
        """
        roleName, canWrite, canAdmin = reposdb.ROLE_PERMS[level]

        try:
            repos.auth.addRole(roleName)
        except reposerrors.RoleAlreadyExists:
            # assume that everything is good.
            return roleName
        else:
            repos.auth.addAcl(roleName, trovePattern=None, label=None,
                    write=canWrite, remove=canAdmin)
            repos.auth.setMirror(roleName, canAdmin)
            repos.auth.setAdmin(roleName, canAdmin)
        return roleName

    def addUserByMd5(self, fqdn, username, salt, password, level):
        repos = self._getRepositoryServer(fqdn)
        role = self._getRoleForLevel(repos, level)
        try:
            repos.auth.addUserByMD5(username, salt.decode('hex'), password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username, deleteRole=False)
            repos.auth.addUserByMD5(username, salt.decode('hex'), password)
        repos.auth.setUserRoles(username, [role])

    def addUser(self, fqdn, username, password, level):
        repos = self._getRepositoryServer(fqdn)
        role = self._getRoleForLevel(repos, level)
        try:
            repos.auth.addUser(username, password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username, deleteRole=False)
            repos.auth.addUser(username, password)
        repos.auth.setUserRoles(username, [role])

    def editUser(self, fqdn, username, level):
        repos = self._getRepositoryServer(fqdn)
        role = self._getRoleForLevel(repos, level)
        repos.auth.setUserRoles(username, [role])

    def deleteUser(self, fqdn, username):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.deleteUserByName(username, deleteRole=False)

    def changePassword(self, fqdn, username, password):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.changePassword(username, password)

    def _isProductExternal(self, hostname):
        cu = self.db.cursor()
        cu.execute("SELECT external FROM Projects WHERE hostname=?",
                    hostname.split('.')[0])
        results =  cu.fetchall()
        if not results:
            raise errors.ProductNotFound(hostname)
        return bool(results[0][0])

    def getAdminClient(self, write=False):
        return self.db.reposShim.getAdminClient(write=write)

    def getUserClient(self):
        return self.db.reposShim.getUserClient(auth=self.auth.auth)

    def getConaryClient(self, admin=False):
        # DEPRECATED: Try getAdminClient or getUserClient first; this is going away.
        conaryCfg = self.getConaryConfig(admin=admin)
        return conaryclient.ConaryClient(conaryCfg)

    def getConaryClientForProduct(self, fqdn, conaryCfg=None, admin=False):
        # DEPRECATED: Try getAdminClient or getUserClient first; this is going away.
        if conaryCfg is None:
            conaryCfg = self.getConaryConfig(admin=admin)

        repos = self.getRepositoryClientForProduct(fqdn, conaryCfg=conaryCfg,
                                                   admin=admin)
        return conaryclient.ConaryClient(conaryCfg, repos=repos)

    def getRepositoryClientForProduct(self, fqdn, admin=False, conaryCfg=None):
        """
        Gets a repository client, possibly with a shim connection to 
        one repository (the one associated with the fqdn).
        """ 
        # DEPRECATED: Try getAdminClient or getUserClient first; this is going away.
        if self.auth.isAdmin:
            admin = True
        if self._isProductExternal(fqdn):
            return self.getConaryClient(admin=admin).getRepos()
        if conaryCfg is None: 
            conaryCfg = self.getConaryConfig(admin=admin)
        server = self._getRepositoryServer(fqdn)
        if self.cfg.SSL:
            protocol = "https"
            port = 443
        else:
            protocol = "http"
            port = 80
        if ":" in self.cfg.projectDomainName:
            port = int(self.cfg.projectDomainName.split(":")[1])
        if admin:
            authToken = (self.cfg.authUser, self.cfg.authPass, None, None)
        else:
            authToken = tuple(self.auth.authToken) + (None, None)

        repo = shimclient.ShimNetClient(server, protocol, port,
            authToken,
            conaryCfg.repositoryMap, conaryCfg.user,
            conaryProxies=conarycfg.getProxyFromConfig(conaryCfg))
        if self.profiler:
            repo = self.profiler.wrapRepository(repo)
        return repo

    def _getRepositoryServer(self, fqdn):
        return self._getRepositoryHandle(fqdn).getShimServer()

    def _getRepositoryHandle(self, fqdn):
        if '.' in fqdn:
            return self.db.reposShim.getRepositoryFromFQDN(fqdn)
        elif fqdn.isdigit():
            return self.db.reposShim.getRepositoryFromProjectId(fqdn)
        else:
            return self.db.reposShim.getRepositoryFromShortName(fqdn)

    def _getBaseConfig(self):
        global _cachedCfg
        if _cachedCfg:
            _cachedCfg.user = copy.deepcopy(_cachedCfg._origUser)
            return _cachedCfg
        cfg = self._getGeneratedConaryConfig()
        if self.cfg.useInternalConaryProxy:
            cfg.conaryProxy = self.cfg.getInternalProxies()
        else:
            cfg.proxyMap = self.cfg.getProxyMap()
            # we're not using the internal proxy, therefore we
            # need to add entitlements directly.
            userMap, entMap = self._getAuthMaps()
            for host, entitlement in entMap:
                cfg.entitlement.addEntitlement(host, entitlement)
            for host, username, password in userMap:
                cfg.user.addServerGlob(host, username, password)
        cfg._origUser = copy.deepcopy(cfg.user)
        _cachedCfg = cfg
        return cfg

    def getConaryConfig(self, admin=False):
        # DEPRECATED: Try getAdminClient or getUserClient first; this is going away.
	cfg = self._getBaseConfig()
        if self.auth.isAdmin:
            admin = True
        if admin:
            cfg.user.addServerGlob('*', self.cfg.authUser, 
                                   self.cfg.authPass)
            if self.auth.username:
                cfg.name = self.auth.username
                cfg.contact = self.auth.fullName or ''
            else:
                cfg.name = 'rBuilder Administration'
                cfg.contact = 'rbuilder'
        elif self.auth.authToken:
            # use current user for everything that's unspecified
            cfg.user.addServerGlob('*', 
                                   self.auth.authToken[0],
                                   self.auth.authToken[1])
            cfg.name = self.auth.username
            cfg.contact = self.auth.fullName or ''
        return cfg

    def _getAuthMaps(self):
        cu = self.db.cursor()
        cu.execute('''SELECT label, authType, username, password,
                             entitlement
                      FROM Projects JOIN Labels USING(projectId)
                      WHERE external
                        AND authType IN (?, ?)''', "userpass", "entitlement")
        repoMap = {}
        entMap = []
        userMap = []
        for (label, authType, username, password, entitlement) in cu:
            host = label.split('@')[0]
            if authType == 'userpass':
                userMap.append((host, username, password))
            elif authType == 'entitlement':
                entMap.append((host, entitlement))
        return userMap, entMap

    def _getFqdn(self, hostname, domainname):
        if domainname:
            fqdn = '%s.%s' % (hostname, domainname)
        else:
            fqdn = hostname

        return fqdn            

    def addIncomingMirror(self, productId, hostname, domainname, url,
                          authInfo, createRepo=True):
        fqdn = self._getFqdn(hostname, domainname)
        label = fqdn + '@rpl:1'

        try:
            mirrorId = self.db.db.inboundMirrors.getIdByColumn(
                    'sourceLabels', label)
        except mint_error.ItemNotFound, e:
            mirrorOrder = self._getNextMirrorOrder()
            mirrorId = self.db.db.inboundMirrors.new(
                    targetProjectId=productId,
                    sourceLabels = label,
                    sourceUrl = url, 
                    sourceAuthType=authInfo.authType,
                    sourceUsername = authInfo.username,
                    sourcePassword = authInfo.password,
                    sourceEntitlement = authInfo.entitlement,
                    mirrorOrder = mirrorOrder, allLabels = 1)

        if createRepo:
            self.createRepository(productId)

        self._generateConaryrcFile()

    def getIncomingMirrorUrlByLabel(self, label):
        mirrorId = self.db.db.inboundMirrors.getIdByHostname(
                label.split('@')[0])
        if not mirrorId:
            return None
        mirror = self.db.db.inboundMirrors.get(mirrorId)
        return mirror['sourceUrl']

    def addExternalRepository(self, productId, hostname, domainname, url, 
                              authInfo, mirror=True):
        fqdn = self._getFqdn(hostname, domainname)
        self._setLabel(productId, fqdn, url, authInfo)

    def _setLabel(self, productId, fqdn, url, authInfo):
        authUser = authPass = entitlement = ''
        authType = authInfo.authType
        if authType == 'entitlement':
            entitlement = authInfo.entitlement
        elif authType == 'userpass':
            authUser, authPass = authInfo.username, authInfo.password

        # This table needs to go away, with the authentication bits moved
        # into projects and the rest dropped. Until then, we need a dummy
        # label as too many things depend on it being a label even though
        # they really just need a FQDN.
        label = fqdn + "@rpl:2"

        cu = self.db.cursor()
        cu.execute("""INSERT INTO Labels (projectId, label, url,
                                          authType, username, password, 
                                          entitlement)
                      VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      productId, label, url, authType,
                      authUser, authPass, entitlement)

        hostname = fqdn.split('.', 1)[0]
        localFqdn = hostname + "." + self.cfg.projectDomainName.split(':')[0]
        self._generateConaryrcFile()

    def checkExternalRepositoryAccess(self, hostname, domainname, url, authInfo):
        fqdn = self._getFqdn(hostname, domainname)
        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        cfg.proxyMap = self.cfg.getProxyMap()
        cfg.configLine('repositoryMap %s %s' % (fqdn, url))
        if authInfo.authType == 'entitlement':
            cfg.entitlement.addEntitlement(fqdn, authInfo.entitlement)
        elif authInfo.authType == 'userpass':
            cfg.configLine('user %s %s %s' % (fqdn, authInfo.username,
                                              authInfo.password))

        if not self.db.siteAuth.isOffline():
            nc = conaryclient.ConaryClient(cfg).getRepos()
            try:
                # use 2**64 to ensure we won't make the server do much
                nc.getNewTroveList(fqdn, '4611686018427387904')
            except reposerrors.InsufficientPermission, e:
                e_tb = sys.exc_info()[2]
                raise errors.ExternalRepositoryMirrorError(url, e), None, e_tb
            except reposerrors.OpenError, e:
                e_tb = sys.exc_info()[2]
                raise errors.ExternalRepositoryAccessError(url, e), None, e_tb

    def _getRepositoryUrl(self, fqdn):
        hostname = fqdn.split('.', 1)[0]
        if self.cfg.SSL:
            protocol = 'https'
        else:
            protocol = 'http'
        path = '%srepos/%s/' % (self.cfg.basePath, hostname)
        return "%s://%s%s" % (protocol, self.cfg.siteHost, path)

    def _getNextMirrorOrder(self):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM InboundMirrors")
        return cu.fetchone()[0]

    def _getGeneratedConaryConfig(self):
        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        if os.path.exists(self.cfg.conaryRcFile):
            cfg.read(self.cfg.conaryRcFile)
        return cfg

    def _generateConaryrcFile(self):
        global _cachedCfg
        _cachedCfg = None
        if not self.cfg.createConaryRcFile:
            return
        repoMaps = self._getFullRepositoryMap()

        fObj_v0 = unixutils.atomicOpen(self.cfg.conaryRcFile, 
                                       chmod=0644)
        fObj_v1 = unixutils.atomicOpen(self.cfg.conaryRcFile + "-v1", 
                                       chmod=0644)
        for host, url in repoMaps.iteritems():
            fObj_v0.write('repositoryMap %s %s\n' % (host, url))
            fObj_v1.write('repositoryMap %s %s\n' % (host, url))
        # add proxy stuff for version 1 config clients
        if self.cfg.useInternalConaryProxy:
            fObj_v1.write('conaryProxy http http://%s.%s\n' % (
                self.cfg.hostName, self.cfg.siteDomainName))
            fObj_v1.write('conaryProxy https https://%s\n' % (
                self.cfg.secureHost,))
        self.cfg.displayKey('proxy', out=fObj_v1)

        fObj_v0.commit()
        fObj_v1.commit()

    def _getFullRepositoryMap(self):
        repoMap = {}
        for handle in self.db.reposShim.iterRepositories(
                'NOT hidden AND NOT disabled'):
            repoMap[handle.fqdn] = handle.getURL()
        return repoMap

    def _getKeyValueMetadata(self, troveTups):
        out = []
        client = self.getAdminClient()
        for trv in client.repos.getTroves(troveTups):
            if trv:
                metaDict = trv.troveInfo.metadata.get()['keyValue']
                if metaDict:
                    out.append(dict(metaDict.items()))
                else:
                    out.append({})
            else:
                out.append(None)
        return out

    def getKeyValueMetadata(self, troveTups):
        return self.cache.coalesce(
                keyPrefix='kvmeta:',
                innerFunc=self._getKeyValueMetadata,
                items=troveTups,
                )

    def createSourceTrove(self, *args, **kwargs):
        kwargs.update(auth=self.auth.auth)
        return self.db.reposShim.createSourceTrove(*args, **kwargs)

    def updateKeyValueMetadata(self, jobs, admin=False):
        return self.db.reposShim.updateKeyValueMetadata(jobs, admin=admin,
            auth=self.auth.auth)

    def deleteTroves(self, troveTups, admin=False):
        # NB: this doesn't recurse since it's initially used for deleting
        # source troves
        if not troveTups:
            return []
        if admin:
            client = self.getAdminClient(write=True)
        else:
            client = self.getUserClient()
        repos = client.repos
        changeSet = changeset.ChangeSet()
        added = False
        for tup in troveTups:
            # Resolve trovetup to trovetup with timestamp
            try:
                tup = sorted(repos.findTrove(None, tup))[0]
            except reposerrors.TroveNotFound:
                continue
            antiTrove = cny_trove.Trove(*tup,
                    type=cny_trove.TROVE_TYPE_REMOVED)
            antiTrove.computeDigests()
            changeSet.newTrove(antiTrove.diff(None, absolute=True)[0])
            added = True
        if added:
            repos.commitChangeSet(changeSet)
