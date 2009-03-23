#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from cStringIO import StringIO
import os

from mint import helperfuncs
from mint import userlevels
from mint.rest import errors

from conary import changelog
from conary import conarycfg
from conary import conaryclient
from conary import dbstore
from conary.conaryclient import filetypes
from conary.deps import deps
from conary.lib import util
from conary.repository import errors as reposerrors
from conary.repository import shimclient
from conary.repository.netrepos import netserver
from conary.server import schema

class RepositoryManager(object):
    def __init__(self, cfg, db, reposDB, auth):
        self.cfg = cfg
        self.reposDB = reposDB
        self.db = db
        self.auth = auth
        self.profiler = None

    def _getProductFQDN(self, hostname):
        #FIXME: this breaks when the project is external.
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname FROM Projects WHERE'
                   ' hostname=?', hostname)
        return '.'.join(tuple(cu.next()))
        
    def createRepository(self, hostname, domainname, isPrivate=False):
        fqdn = "%s.%s" % (hostname, domainname)
        dbPath = os.path.join(self.cfg.reposPath, fqdn)
        tmpPath = os.path.join(dbPath, 'tmp')
        util.mkdirChain(tmpPath)
        self.reposDB.create(fqdn)

        repositoryDB =  self.reposDB.getRepositoryDB(fqdn)
        db = dbstore.connect(repositoryDB[1], repositoryDB[0])
        schema.loadSchema(db)
        db.commit()
        db.close()

        if not isPrivate:
            self.addUser(fqdn, 'anonymous', password='anonymous')

        # add the auth user so we can add additional permissions
        # to this repository
        self.addUser(fqdn, self.cfg.authUser, 
                     password=self.cfg.authPass,
                     write=True, mirror=True, admin=True)

    def deleteRepository(self, fqdn):
        self.reposDB.delete(fqdn)

    def setProfiler(self, profiler):
        self.profiler = profiler

    def addUserByMd5(self, fqdn, username, salt, password, 
                     write=False, mirror=False,
                     admin=False):
        repos = self._getRepositoryServer(fqdn)
        try:
            repos.auth.addUserByMD5(username, salt, password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username)
            repos.auth.addUserByMD5(username, salt, password)
        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def addUser(self, fqdn, username, password, write=False, mirror=False,
                admin=False):
        repos = self._getRepositoryServer(fqdn)
        try:
            repos.auth.addUser(username, password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username)
            repos.auth.addUser(username, password)

        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def editUser(self, fqdn, username, write=False, mirror=False,
                 admin=False):
        repos = self._getRepositoryServer(fqdn)
        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def deleteUser(self, fqdn, username):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.deleteUserByName(username)
        try:
            # TODO: This will go away when using role-based permissions
            # instead of one-role-per-user. Without this, admin users'
            # roles would not be deleted due to CNY-2775
            repos.auth.deleteRole(username)
        except reposerrors.RoleNotFound:
            # Conary deleted the (unprivileged) role for us
            pass

    def changePassword(self, fqdn, username, password):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.changePassword(username, password)

    def _setUserPermissions(self, fqdn, username, write=False, mirror=False,
                            admin=False):

        repos = self._getRepositoryServer(fqdn)

        # create a role with the same name as this user
        # with the permissions we want.
        role = username
        try:
            repos.auth.addRole(role)
        except reposerrors.RoleAlreadyExists:
            repos.auth.editAcl(role, None, None, None, None,
                               write=write, canRemove=False)
        else:
            repos.auth.addAcl(role, trovePattern=None, label=None, 
                              write=write, remove=False)
            repos.auth.addRoleMember(role, username)
        repos.auth.setMirror(role, mirror)
        repos.auth.setAdmin(role, admin)

    def _isProductExternal(self, hostname):
        cu = self.db.cursor()
        cu.execute("SELECT external FROM Projects WHERE hostname=?",
                    hostname.split('.')[0])
        results =  cu.fetchall()
        if not results:
            raise errors.ProductNotFound(hostname)
        return bool(results[0][0])

    def getConaryClient(self, admin=False):
        conaryCfg = self.getConaryConfig(admin=admin)
        return conaryclient.ConaryClient(conaryCfg)

    def getConaryClientForProduct(self, fqdn, conaryCfg=None, admin=False):
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
            authToken = self.auth.authToken + (None, None)

        repo = shimclient.ShimNetClient(server, protocol, port,
            authToken,
            conaryCfg.repositoryMap, conaryCfg.user,
            conaryProxies=conarycfg.getProxyFromConfig(conaryCfg))
        if self.profiler:
            repo = self.profiler.wrapRepository(repo)
        return repo

    def _getRepositoryServer(self, fqdn):
        if '.' not in fqdn:
            fqdn = self._getProductFQDN(fqdn)
        dbPath = os.path.join(self.cfg.reposPath, fqdn)
        tmpPath = os.path.join(dbPath, 'tmp')
        cfg = netserver.ServerConfig()
        cfg.repositoryDB = self.reposDB.getRepositoryDB(fqdn)
        cfg.tmpDir = tmpPath
        cfg.serverName = fqdn
        cfg.repositoryMap = {}
        cfg.authCacheTimeout = self.cfg.authCacheTimeout
        cfg.externalPasswordURL = self.cfg.externalPasswordURL

        contentsDirs = self.cfg.reposContentsDir
        cfg.contentsDir = " ".join(x % fqdn for x in contentsDirs.split(" "))
        repos = shimclient.NetworkRepositoryServer(cfg, '')
        return repos

    def getConaryConfig(self, admin=False):
        if self.auth.isAdmin:
            admin = True

        cfg = self._getGeneratedConaryrc()
        if self.cfg.useInternalConaryProxy:
            cfg.conaryProxy = self.cfg.getInternalProxies()
        elif self.cfg.proxy:
            cfg.proxy = self.cfg.proxy
            # we're not using the internal proxy, therefore we
            # need to add entitlements directly.
            userMap, entMap = self._getAuthMaps(self, cfg)
            for host, entitlement in entMap:
                cfg.entitlement.addEntitlement(host, entitlement)
            for host, username, password in userMap:
                cfg.user.addServerGlob(host, username, password)
        if admin:
            cfg.user.addServerGlob('*', self.cfg.authUser, 
                                   self.cfg.authPass)
            if self.auth.username:
                cfg.name = self.auth.username
                cfg.contact = self.auth.fullName or ''
            else:
                cfg.name = 'rBuilder Administration'
                cfg.contact = 'rbuilder'
        else:
            # use current user for everything that's unspecified
            cfg.user.addServerGlob('*', 
                                   self.auth.authToken[0],
                                   self.auth.authToken[1])
            cfg.name = self.auth.username
            cfg.contact = self.auth.fullName or ''
        return cfg

    def _getGeneratedConaryrc(self):
        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        if os.path.exists(self.cfg.conaryRcFile):
            cfg.read(self.cfg.conaryRcFile)
        return cfg

    def _getAuthMaps(self):
        cu = self.db.cursor()
        cu.execute('''SELECT label, authType, username, password,
                             entitlement
                      FROM Projects JOIN Labels USING(projectId)
                      WHERE external=1 
                        AND authType IN ("userpass", "entitlement")''')
        repoMap = {}
        entMap = []
        userMap = []
        for (label, authType, username, password, entitlement) in cu:
            host = label[:label.find('@')]
            if authType == 'userpass':
                userMap.append((host, username, password))
            elif authType == 'entitlement':
                entMap.append((host, entitlement))
        return entMap, userMap

    def _getRepositoryUrl(self, hostname):
        if self.cfg.SSL:
            protocol = "https"
            domain = self.cfg.secureHost
            defaultPort = 443
            newHost, newPort = hostPortParse(443)
        else:
            protocol = "http"
            domain = self.cfg.projectDomainName
            defaultPort = 80
        newHost, newPort = hostPortParse(domain, defaultPort)
        return rewriteUrlProtocolPort(url, protocol, newPort)

    def createSourceTrove(self, fqdn, trovename, buildLabel, 
                          upstreamVersion, streamMap, changeLogMessage):
        # Get repository + client
        client = self.getConaryClientForProduct(fqdn)

        # ensure that the changelog message ends with a newline
        if not changeLogMessage.endswith('\n'):
            changeLogMessage += '\n'

        # create a pathdict out of the streamMap
        pathDict = {}
        for filename, filestream in streamMap.iteritems():
            if isinstance(filestream, str):
                filestream = StringIO(filestream)
            pathDict[filename] = filetypes.RegularFile(contents=filestream,
                                                       config=True)

        # create the changelog message using the currently
        # logged-on user's username and fullname, if available
        newchangelog = changelog.ChangeLog(self.auth.username,
                             self.auth.fullName or '',
                             changeLogMessage)

        # create a change set object from our source data
        changeSet = client.createSourceTrove('%s:source' % trovename,
                                             buildLabel,
                                             upstreamVersion, pathDict, 
                                             newchangelog)

        # commit the change set to the repository
        client.getRepos().commitChangeSet(changeSet)
