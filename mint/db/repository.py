#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

"""
A unified interface to rBuilder project repositories.
"""


import logging
import os
import weakref
from conary import conarycfg
from conary import dbstore
from conary.lib import util
from conary.repository import errors as reposerrors
from conary.repository import netclient
from conary.repository import shimclient
from conary.repository.netrepos import netserver
from conary.repository.netrepos import proxy
from conary.repository.netrepos.netauth import ValidPasswordToken, ValidUser
from conary.server import schema as conary_schema

from mint.mint_error import RepositoryDatabaseError, RepositoryAlreadyExists
from mint.rest.errors import ProductNotFound

log = logging.getLogger(__name__)


def cached(method):
    #pylint: disable-msg=W0212,W0612
    name = method.func_name
    def wrapper(self, *args, **kwargs):
        key = (name, args, tuple(sorted(kwargs.items())))
        if key not in self._cache:
            self._cache[key] = method(self, *args, **kwargs)
        return self._cache[key]
    wrapper.func_name = method.func_name
    return wrapper


def withNetServer(method):
    def wrapper(self, *args, **kwargs):
        repos = self.getNetServer()
        return method(self, repos, *args, **kwargs)
    wrapper.func_name = method.func_name
    return wrapper


class RepositoryManager(object):
    __slots__ = (
            'cfg', 'db',
            'authToken', 'reposDBCache',
            'repos', '_cache', '__weakref__',
            )
    def __init__(self, cfg, db, authToken=None):
        self.cfg = cfg
        self.db = db
        if authToken:
            self.authToken = authToken
        else:
            self.authToken = [ValidUser(), None, [], None]
        self.reposDBCache = {}
        self.repos = MultiShimNetClient(self)
        self._cache = {}

    def _getRepository(self, whereClause, *args):
        """
        Return a new L{RepositoryHandle} object by querying the database.
        """
        joins = ''

        cu = self.db.cursor()
        cu.execute("""
                SELECT projectId, shortname, fqdn, external, hidden,
                    EXISTS ( SELECT * FROM InboundMirrors
                        WHERE projectId = targetProjectId
                        ) AS localMirror,
                    commitEmail, %s, url, authType, username, password,
                    entitlement
                FROM Projects LEFT JOIN Labels USING ( projectId )%s
                WHERE %s ORDER BY projectId ASC""" % (
                    (self.db.driver == 'mysql' and '`database`' or 'database'),
                    joins, whereClause),
                *args)

        try:
            project = cu.next()
        except StopIteration:
            log.warning("No project found matching %r %% %r",
                    whereClause, args)
            raise ProductNotFound(args[0])
        else:
            return RepositoryHandle(self, project)

    @cached
    def getRepositoryFromFQDN(self, fqdn):
        return self._getRepository('fqdn = ?', fqdn)

    @cached
    def getRepositoryFromProjectId(self, projectId):
        return self._getRepository('projectId = ?', projectId)

    @cached
    def getRepositoryFromShortName(self, shortName):
        return self._getRepository('shortname = ?', shortName)

    def reset(self):
        """
        Reset all open database connections. Call this before finishing a
        request.
        """
        for key, reposDB in self.reposDBCache.items():
            if reposDB.poolmode:
                reposDB.close()
                del self.reposDBCache[key]
            elif reposDB.inTransaction(default=True):
                reposDB.rollback()
        self._cache = {}

    def close(self):
        while self.reposDBCache:
            reposDB = self.reposDBCache.popitem()[1]
            reposDB.close()
        self._cache = {}

    def getServerProxy(self, fqdn, url=None, user=None, entitlement=None):
        """
        Get a generic XMLRPC server proxy for C{fqdn}, optionally using
        C{url}, C{user}, and C{entitlement}.
        """
        repMap = conarycfg.RepoMap()
        if url:
            repMap.append(('*', url))

        userMap = conarycfg.UserInformation()
        if user:
            userMap.addServerGlob('*', user)

        entitlements = conarycfg.EntitlementList()
        if entitlement:
            entitlements.addEntitlement('*', entitlement)

        proxies = conarycfg.getProxyFromConfig(self.cfg) or None
        cache = netclient.ServerCache(repMap, userMap,
                entitlements=entitlements, proxies=proxies)
        return cache[fqdn]

    def getRepos(self):
        return self.repos


class RepositoryHandle(object):
    __slots__ = (
            '_manager', '_cfg', '_projectInfo', '_cache',
            )

    def __init__(self, manager, projectInfo):
        self._manager = weakref.ref(manager)
        self._cfg = manager.cfg
        self._projectInfo = projectInfo
        self._cache = {}

    def __repr__(self):
        try:
            return '%s(%r)' % (type(self).__name__,
                    self._projectInfo['fqdn'])
        except:
            return object.__repr__(self)

    # Properties
    @property
    def commitEmail(self):
        return self._projectInfo['commitEmail']
    @property
    def dbTuple(self):
        return self._getReposDBParams()
    @property
    def fqdn(self):
        return self._projectInfo['fqdn']
    @property
    def hasDatabase(self):
        return bool((not self.isExternal) or self.isLocalMirror)
    @property
    def isExternal(self):
        return bool(self._projectInfo['external'])
    @property
    def isHidden(self):
        return bool(self._projectInfo['hidden'])
    @property
    def isLocalMirror(self):
        return bool(self._projectInfo['localMirror'])
    @property
    def projectId(self):
        return self._projectInfo['projectId']
    @property
    def shortName(self):
        return self._projectInfo['shortname']


    # Getters for repository objects
    def _getURLPieces(self):
        if self._cfg.SSL:
            protocol, port = 'https', 443
            host = self._cfg.secureHost
        else:
            protocol, port = 'http', 80
            host = self._cfg.projectSiteHost

        if ':' in host:
            host, port = host.split(':')
            port = int(port)

        return protocol, host, port

    def getURL(self):
        protocol, host, port = self._getURLPieces()
        return '%s://%s:%d/repos/%s/' % (protocol, host, port, self.shortName)

    @cached
    def _getReposDBParams(self):
        """
        Return the "database tuple" for this project. Don't call this
        directly if you intend to open the database; use getReposDB().
        """
        if not self.hasDatabase:
            raise RuntimeError("Cannot open database for external project %r"
                    % (self.shortName,))

        database = self._projectInfo['database']
        if ' ' in database:
            # It's a connect string w/ driver and path
            driver, path = database.split(' ', 1)
        else:
            # It's a reference to the config file
            if database not in self._cfg.database:
                raise RepositoryDatabaseError(
                        "Database alias %r is not defined" % (database,))
            driver, path = self._cfg.database[database]

        dbName = self.fqdn.lower()
        if driver != 'sqlite':
            for badchar in '-.':
                dbName = dbName.replace(badchar, '_')

        if '%s' in path:
            path %= dbName

        return driver, path

    def getReposDB(self, skipCache=False):
        """
        Open and return a connection to the repository database. May use
        a cached connection.
        """
        params = self._getReposDBParams()
        if params in self._manager().reposDBCache and not skipCache:
            db = self._manager().reposDBCache[params]
            db.reopen()
            if db.inTransaction(True):
                db.rollback()
        else:
            driver, path = params
            db = dbstore.connect(path, driver)
            if not skipCache:
                self._manager().reposDBCache[params] = db
        return db

    @cached
    def getNetServerConfig(self):
        """
        Return a C{ServerConfig} suitable for creating a
        C{NetworkRepositoryServer}. The object is cached, so don't
        modify it.
        """
        fqdn, shortName = self.fqdn, self.shortName

        if not self.hasDatabase:
            raise RuntimeError("Cannot create a netserver for "
                    "external project %r" % (shortName,))

        cfg = netserver.ServerConfig()
        cfg.authCacheTimeout = self._cfg.authCacheTimeout
        cfg.changesetCacheDir = os.path.join(self._cfg.dataPath, 'cscache')
        cfg.externalPasswordURL = self._cfg.externalPasswordURL
        cfg.logFile = (self._cfg.reposLog
                and os.path.join(self._cfg.logPath, 'repository.log') or None)
        cfg.repositoryDB = None # We open databases ourselves
        if self.isLocalMirror:
            cfg.requireSigs = False
        else:
            cfg.requireSigs = self._cfg.requireSigs
        cfg.serializeCommits = True

        cfg.serverName = [fqdn]
        cfg.contentsDir = ' '.join(x % (fqdn,)
                for x in self._cfg.reposContentsDir.split())
        cfg.tmpDir = os.path.join(self._cfg.reposPath, fqdn, 'tmp')

        if self._cfg.commitAction and not self.isLocalMirror:
            actionDict = {
                    'repMap': '%s %s' % (fqdn, self.getURL()),
                    'buildLabel': '%s@rpl:1' % (fqdn,),
                    'projectName': shortName,
                    'commitFromEmail': self._cfg.commitEmail,
                    'commitEmail': self.commitEmail,
                    'basePath': self._cfg.basePath,
                    'authUser': self._cfg.authUser,
                    'authPass': self._cfg.authPass,
                    }
            cfg.commitAction = self._cfg.commitAction % actionDict
            if self._cfg.commitActionEmail and self.commitEmail:
                cfg.commitAction += (
                        ' ' + self._cfg.commitActionEmail % actionDict)
            else:
                cfg.commitAction = None

        return cfg

    def _getServer(self, serverClass):
        nscfg = self.getNetServerConfig()
        if not os.access(nscfg.tmpDir, os.R_OK | os.X_OK):
            raise RepositoryDatabaseError(
                    "Unable to access repository dir %r for project %r"
                    % (nscfg.tmpDir, self.shortName))

        db = self.getReposDB()
        baseUrl = self.getURL()
        return serverClass(nscfg, baseUrl, db)

    @cached
    def getNetServer(self):
        """
        Return a (cached) C{NetworkRepositoryServer} for this project.
        """
        return self._getServer(netserver.NetworkRepositoryServer)

    @cached
    def getProxyServer(self):
        """
        Return a (cached) C{SimpleRepositoryFilter} for this project's
        repository.
        """
        return proxy.SimpleRepositoryFilter(self.getNetServerConfig(),
                self.getURL(), self.getNetServer())

    @cached
    def getShimServer(self):
        """
        Return a (cached) shim C{NetworkRepositoryServer} for this project.
        """
        return self._getServer(shimclient.NetworkRepositoryServer)

    @cached
    def _getShimServerProxy(self):
        """
        Get a (cached) shim XMLRPC server proxy for this project's repository.
        """
        protocol, _, port = self._getURLPieces()
        return shimclient.ShimServerProxy(self.getShimServer(),
                protocol, port, self._manager().authToken)

    def getServerProxy(self):
        """
        Get a XMLRPC server proxy for this project's repository. If the
        project has a local database, a shim proxy will be used.
        """
        if self.hasDatabase:
            return self._getShimServerProxy()
        else:
            user = entitlement = None
            authType = self._projectInfo['authType']
            if authType == 'entitlement':
                entitlement = self._projectInfo['entitlement']
            elif authType == 'userpass':
                user = (self._projectInfo['username'],
                        self._projectInfo['password'])

            return self._manager().getServerProxy(self.fqdn,
                    self._projectInfo['url'], user, entitlement)


    # Database management
    def create(self):
        """
        Create a repository database for this project.
        """
        driver, path = self._getReposDBParams()

        if driver == 'sqlite':
            util.mkdirChain(os.path.dirname(path))

        elif driver in ('postgresql', 'pgpool'):
            if '/' in path:
                base, dbName = path.rsplit('/', 1)[0] + '/'
                + '/postgres'
            else:
                base, dbName = '', path

            # Connect to the postgres database so we can create the reposDB.
            controlDb = dbstore.connect(base + 'postgres', 'postgresql')
            ccu = controlDb.cursor()

            ccu.execute("""SELECT COUNT(*) FROM pg_catalog.pg_database
                    WHERE datname = ?""", dbName)
            if ccu.fetchone()[0]:
                # Database exists
                log.error("PostgreSQL database %r already exists while "
                        "creating project %r", path, self.shortName)
                raise RepositoryAlreadyExists(self.shortName)

            ccu.execute("CREATE DATABASE %s ENCODING 'UTF8'" % (dbName,))

            controlDb.close()
        else:
            raise RuntimeError("Cannot create repository with driver %r"
                    % (driver,))

        # Set up some other infrastructure that is independent of the db.
        nscfg = self.getNetServerConfig()
        util.mkdirChain(nscfg.tmpDir)
        for contDir in nscfg.contentsDir.split():
            util.mkdirChain(contDir)

        # Initialize the repos schema.
        db = self.getReposDB()
        conary_schema.loadSchema(db)

    # Repository management
    @withNetServer
    def addRoleWithACE(self, repos, role,
            write=False, remove=False, mirror=False, admin=False):
        try:
            repos.auth.addRole(role)
        except reposerrors.RoleAlreadyExists:
            pass
        else:
            repos.auth.setMirror(role, mirror)
            repos.auth.setAdmin(role, admin)
            repos.auth.addAcl(role, trovePattern=None, label=None,
                    write=write, remove=remove)

    @withNetServer
    def addUserByMD5(self, repos, username, salt, password, roles=None):
        try:
            repos.auth.addUserByMD5(username, salt, password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username, deleteRole=False)
            repos.auth.addUserByMD5(username, salt, password)
        repos.auth.setUserRoles(username, roles or [])

    @withNetServer
    def addUser(self, repos, username, password, roles=None):
        try:
            repos.auth.addUser(username, password)
        except reposerrors.UserAlreadyExists:
            repos.auth.deleteUserByName(username, deleteRole=False)
            repos.auth.addUser(username, password)
        repos.auth.setUserRoles(username, roles or [])

    @withNetServer
    def setUserRoles(self, repos, username, roles=None):
        repos.auth.setUserRoles(username, roles or [])

    @withNetServer
    def deleteUser(self, repos, username):
        repos.auth.deleteUserByName(username, deleteRole=False)

    @withNetServer
    def changePassword(self, repos, username, password):
        repos.auth.changePassword(username, password)


class MultiShimServerCache(object):
    """
    C{ServerCache} replacement for use with rBuilder. It will automatically
    use a shim client for any repositories which are hosted or cached on the
    rBuilder, and will use the credentials in the database for any external
    projects.
    """
    def __init__(self, manager):
        self.manager = weakref.ref(manager)
        self.cache = {}

    @staticmethod
    def _getServerName(item):
        #pylint: disable-msg=W0212
        return netclient.ServerCache._getServerName(item)

    def __getitem__(self, item):
        serverName = self._getServerName(item)

        server = self.cache.get(serverName, None)
        if server is not None:
            return server

        ret = self.cache[serverName] = self._getProxy(serverName)
        return ret

    def _getProxy(self, serverName):
        manager = self.manager()
        if not manager:
            raise RuntimeError("Repository manager went away")

        try:
            repo = manager.getRepositoryFromFQDN(serverName)
        except ProductNotFound:
            # No project -- use a generic server proxy
            return manager.getServerProxy(serverName)
        else:
            # Found the project -- use that project's (maybe shim) server proxy
            return repo.getServerProxy()


class MultiShimNetClient(shimclient.ShimNetClient):
    def __init__(self, manager):
        repMap = conarycfg.RepoMap()
        userMap = conarycfg.UserInformation()
        netclient.NetworkRepositoryClient.__init__(self, repMap, userMap)

        self.c = MultiShimServerCache(manager)
