#
# Copyright (c) SAS Institute Inc.
#

import sys

from mint import mint_error
from mint import userlevels
from mint.db import projects
from mint.db import repository as reposdb
from mint.lib import mintutils
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager

from conary import conarycfg
from conary import conaryclient
from conary import trove as cny_trove
from conary.repository import changeset
from conary.repository import errors as reposerrors

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
        self.addUser(repos, self.cfg.authUser,
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

    def _getRepositoryServer(self, fqdn):
        return self._getRepositoryHandle(fqdn).getShimServer()

    def _getRepositoryHandle(self, fqdn):
        if isinstance(fqdn, reposdb.RepositoryHandle):
            return fqdn
        elif '.' in fqdn:
            return self.db.reposShim.getRepositoryFromFQDN(fqdn)
        elif fqdn.isdigit():
            return self.db.reposShim.getRepositoryFromProjectId(fqdn)
        else:
            return self.db.reposShim.getRepositoryFromShortName(fqdn)

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

    def _getNextMirrorOrder(self):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE(MAX(mirrorOrder)+1, 0) FROM InboundMirrors")
        return cu.fetchone()[0]

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
