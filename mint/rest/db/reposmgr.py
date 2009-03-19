#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from cStringIO import StringIO
import os

from mint import helperfuncs
from mint import userlevels

from conary import changelog
from conary import conarycfg
from conary import conaryclient
from conary import dbstore
from conary.conaryclient import filetypes
from conary.deps import deps
from conary.lib import util
from conary.repository import errors
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
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname from Projects where hostname=?', hostname)
        return '.'.join(tuple(cu.next()))

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
        except errors.UserAlreadyExists:
            repos.auth.deleteUserByName(username)
            repos.auth.addUserByMD5(username, salt, password)
        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def addUser(self, fqdn, username, password, write=False, mirror=False,
                admin=False):
        repos = self._getRepositoryServer(fqdn)
        try:
            repos.auth.addUser(username, password)
        except errors.UserAlreadyExists:
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
        except errors.RoleNotFound:
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
        except errors.RoleAlreadyExists:
            repos.auth.editAcl(role, None, None, None, None,
                               write=write, canRemove=False)
        else:
            repos.auth.addAcl(role, trovePattern=None, label=None, 
                              write=write, remove=False)
            repos.auth.addRoleMember(role, username)
        repos.auth.setMirror(role, mirror)
        repos.auth.setAdmin(role, admin)

    def getProjectConaryConfig(self, fqdn):
        """
        Creates a conary configuration object, suitable for internal or external
        rBuilder use.
        @param project: Project to create a Conary configuration for.
        @type project: C{mint.project.Project} object
        @param internal: True if configuration object is to be used by a
           NetClient/ShimNetClient internal to rBuilder; False otherwise.
        @type internal: C{bool}
        """
        ccfg = self.getConaryConfig(fqdn)
        conarycfgFile = self.cfg.conaryRcFile
        # This step reads all of the repository maps for cross talk, and, if
        # external, sets up the cfg object to use the rBuilder conary proxy
        if os.path.exists(conarycfgFile):
            ccfg.read(conarycfgFile)

        #Set up the user config lines
        for otherProjectData, level, memberReqs in \
          self.db.db.projects.getProjectDataByMember(self.auth.userId):
            if level in userlevels.WRITERS:
                otherFqdn = self._getProductFQDN(otherProjectData['hostname'])
                ccfg.user.addServerGlob(otherFqdn,
                                        self.auth.authToken[0], self.auth.authToken[1])

        ccfg['name'] = self.auth.username
        ccfg['contact'] = self.auth.fullName or ''
        return ccfg

    def _getProxies(self):
        useInternalConaryProxy = self.cfg.useInternalConaryProxy
        if useInternalConaryProxy:
            httpProxies = {}
            useInternalConaryProxy = self.cfg.getInternalProxies()
        else:
            httpProxies = self.cfg.proxy or {}
        return [ useInternalConaryProxy, httpProxies ]

    def getConaryConfig(self, fqdn, overrideAuth = False, newUser = '', newPass = ''):
        '''Creates a ConaryConfiguration object suitable for repository access
        from the same server as MintServer'''
        projectId = self.db.db.projects.getProjectIdByHostname(fqdn.split('.', 1)[0])
        labelPath, repoMap, userMap, entMap = self.db.db.labels.getLabelsForProject(projectId, 
                                                             overrideAuth, newUser, newPass)

        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        cfg.buildFlavor = deps.parseFlavor('')
        installLabelPath = " ".join(x for x in labelPath.keys())
        cfg.configLine("installLabelPath %s" % installLabelPath)

        cfg.repositoryMap.update(dict((x[0], x[1]) for x in repoMap.items()))
        for host, authInfo in userMap:
            cfg.user.addServerGlob(host, authInfo[0], authInfo[1])
        for host, entitlement in entMap:
            cfg.entitlement.addEntitlement(host, entitlement[1])

        internalConaryProxies, httpProxies = self._getProxies()
        cfg = helperfuncs.configureClientProxies(cfg, internalConaryProxies,
                httpProxies, internalConaryProxies)
        return cfg

    def getInternalConaryClient(self, fqdn, conaryCfg=None):
        if conaryCfg is None:
            conaryCfg = self.getProjectConaryConfig(fqdn)
        repos = self.getInternalRepositoryClient(fqdn, conaryCfg=conaryCfg)
        return conaryclient.ConaryClient(conaryCfg, repos=repos)

    def getInternalRepositoryClient(self, fqdn, conaryCfg=None):
        if conaryCfg is None:
            conaryCfg = self.getProjectConaryConfig(fqdn)
        server = self._getRepositoryServer(fqdn)
        conaryCfg = helperfuncs.configureClientProxies(conaryCfg, 
                                           self.cfg.useInternalConaryProxy, 
                                           self.cfg.proxy)
        if self.cfg.SSL:
            protocol = "https"
            port = 443
        else:
            protocol = "http"
            port = 80
        if ":" in self.cfg.projectDomainName:
            port = int(self.cfg.projectDomainName.split(":")[1])
        repo = shimclient.ShimNetClient(server, protocol, port,
            (self.cfg.authUser, self.cfg.authPass, None, None),
            conaryCfg.repositoryMap, conaryCfg.user,
            conaryProxies=conarycfg.getProxyFromConfig(conaryCfg))
        if self.profiler:
            repo = self.profiler.wrapRepository(repo)
        return repo

    def getRepositoryClient(self, fqdn, useShim=True, conaryCfg=None):
        if conaryCfg is None:
            conaryCfg = self.getProjectConaryConfig(fqdn)
        repos = conaryclient.ConaryClient(conaryCfg).getRepos()
        if self.profiler:
            repos = self.profiler.wrapRepository(repos)
        return repos

    def createSourceTrove(self, fqdn, trovename, buildLabel, 
                          upstreamVersion, streamMap, changeLogMessage):
        # Get repository + client
        client = self.getInternalConaryClient(fqdn)

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
