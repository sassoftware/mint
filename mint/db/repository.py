#
# Copyright (c) 2009-2010 rPath, Inc.
#
# All rights reserved.
#

"""
A unified interface to rBuilder project repositories.
"""


import errno
import logging
import os
import time
import weakref
from conary import conarycfg
from conary import conaryclient
from conary import dbstore
from conary.dbstore.sqlerrors import CursorError
from conary.lib import util
from conary.repository import errors as reposerrors
from conary.repository import netclient
from conary.repository import shimclient
from conary.repository.netrepos import netserver
from conary.repository.netrepos import proxy
from conary.repository.netrepos.netauth import ValidUser
from conary.server import schema as conary_schema

from mint import userlevels
from mint.mint_error import RepositoryDatabaseError, RepositoryAlreadyExists
from mint.rest.errors import ProductNotFound

log = logging.getLogger(__name__)


ROLE_PERMS = {
        # level                 role name           write   admin
        userlevels.ADMIN:     ('rb_internal_admin', True,   True),
        userlevels.OWNER:     ('rb_owner',          True,   True),
        userlevels.DEVELOPER: ('rb_developer',      True,   False),
        userlevels.USER:      ('rb_user',           False,  False),
}

# Tokens for internal, userless repository access. Use with getServerProxy,
# etc.
ANONYMOUS = -1
ANY_READER = -2
ANY_WRITER = -3


def _makeClient(repos):
    """
    Make a C{ConaryClient} around the given C{repos} with a default
    configuration.
    """
    cfg = conarycfg.ConaryConfiguration(False)
    cfg.name = 'rBuilder'
    cfg.contact = 'rbuilder'
    return conaryclient.ConaryClient(cfg=cfg, repos=repos)


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
    def __init__(self, cfg, db, bypass=False):
        self.cfg = cfg
        self.db = db
        self.bypass = bypass
        self.reposDBCache = {}

    def iterRepositories(self, whereClause='', *args):
        """
        Generate a sequence of L{RepositoryHandle}s matching a given
        query.
        """
        if whereClause:
            whereClause = 'WHERE ' + whereClause

        cu = self.db.cursor()
        cu.execute("""
                SELECT projectId, shortname, fqdn, external, hidden,
                    EXISTS ( SELECT * FROM InboundMirrors
                        WHERE projectId = targetProjectId
                        ) AS localMirror,
                    commitEmail, %s, url, authType, username, password,
                    entitlement, EXISTS (
                        SELECT * FROM PlatformsContentSourceTypes
                            JOIN Platforms AS plat USING (platformId)
                        WHERE plat.projectId = projectId) AS hasContentSources
                FROM Projects LEFT JOIN Labels USING ( projectId )
                %s ORDER BY projectId ASC""" % (
                    (self.db.driver == 'mysql' and '`database`' or 'database'),
                    whereClause),
                *args)

        for row in cu:
            yield RepositoryHandle(self, row)

    def _getRepository(self, whereClause, *args):
        """
        Return a new L{RepositoryHandle} object by querying the database.
        """
        repoIter = self.iterRepositories(whereClause, *args)
        try:
            return repoIter.next()
        except StopIteration:
            raise ProductNotFound(args[0])

    def getRepositoryFromFQDN(self, fqdn):
        return self._getRepository('fqdn = ?', fqdn)

    def getRepositoryFromProjectId(self, projectId):
        return self._getRepository('projectId = ?', projectId)

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

    def close(self):
        while self.reposDBCache:
            reposDB = self.reposDBCache.popitem()[1]
            reposDB.close()

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

        cache = netclient.ServerCache(repMap, userMap,
                entitlements=entitlements, proxies=self.cfg.proxy)
        return cache[fqdn]

    def getRepos(self, userId=None):
        """
        Get a global C{NetworkRepositoryClient} for this site, optionally
        constrained to the permissions of a particular user.
        """
        return MultiShimNetClient(self, userId)

    def getClient(self, userId=None):
        """
        Get a global C{ConaryClient} for this site, optionally constrained to
        the permissions of a particular user.
        """
        return _makeClient(self.getRepos(userId))


class RepositoryHandle(object):
    preloadSuffix = 'sql'

    def __init__(self, manager, projectInfo):
        self._manager = weakref.ref(manager)
        self._cfg = manager.cfg
        self._db = manager.db
        self._projectInfo = projectInfo
        self._cache = {}

        # Switch to a subclass for whichever database driver is needed.
        if self.hasDatabase:
            if self.driver == 'sqlite':
                self.__class__ = SQLiteRepositoryHandle
            elif self.driver in ('postgresql', 'pgpool'):
                self.__class__ = PostgreSQLRepositoryHandle

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
    def contentsDirs(self):
        return [x % (self.fqdn,) for x in self._cfg.reposContentsDir.split()]
    @property
    def dbTuple(self):
        return self._getReposDBParams()
    @property
    def driver(self):
        return self._getReposDBParams()[0]
    @property
    def fqdn(self):
        return self._projectInfo['fqdn']
    @property
    def hasDatabase(self):
        return self._projectInfo['database'] is not None
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
    def repositoryMap(self):
        return self._projectInfo['url']
    @property
    def shortName(self):
        return self._projectInfo['shortname']
    @property
    def hasContentSources(self):
        return bool(self._projectInfo['hasContentSources'])


    # Getters for repository objects
    def _getURLPieces(self):
        if self._cfg.SSL:
            protocol, port = 'https', 443
            host = self._cfg.secureHost
        else:
            protocol, port = 'http', 80
            host = self._cfg.siteHost

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
        database = self._projectInfo['database']
        if database is None:
            raise RuntimeError("Cannot open database for external project %r"
                    % (self.shortName,))
        elif ' ' in database:
            # It's a connect string w/ driver and path
            driver, path = database.split(' ', 1)
        else:
            # It's a reference to the config file
            if database not in self._cfg.database:
                raise RepositoryDatabaseError(
                        "Database alias %r is not defined" % (database,))
            driver, path = self._cfg.database[database]

        if driver == 'pgpool' and self._manager().bypass:
            driver = 'postgresql'
            path = path.replace(':6432', ':5439')

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
        cfg.readOnlyRepository = self._cfg.readOnlyRepositories
        # FIXME: Until there is a per-project signature requirement flag, this
        # will have to do.
        if self.isLocalMirror or shortName == 'rmake-repository':
            cfg.requireSigs = False
        else:
            # FIXME: Shim clients will eventually need to sign packages, and
            # all repository traffic will eventually go through this interface
            # as well. But for now we don't and won't sign shim commits, and
            # the primary consumer of this interface is shim clients, so
            # disable signature requirements.
            cfg.requireSigs = False
            #cfg.requireSigs = self._cfg.requireSigs
        cfg.serializeCommits = True

        cfg.serverName = [fqdn]
        cfg.contentsDir = ' '.join(self.contentsDirs)
        cfg.tmpDir = os.path.join(self._cfg.dataPath, 'tmp')

        if self._cfg.commitAction and not self.isLocalMirror:
            actionDict = {
                    'repMap': '%s %s' % (fqdn, self.getURL()),
                    'buildLabel': '%s@rpl:1' % (fqdn,),
                    'projectName': shortName,
                    'fqdn': fqdn,
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
        for path in nscfg.contentsDir.split():
            if not os.access(path, os.R_OK | os.X_OK):
                raise RepositoryDatabaseError("Unable to read repository "
                        "contents dir %r for project %r"
                        % (path, self.shortName))
            if not nscfg.readOnlyRepository and  not os.access(path, os.W_OK):
                raise RepositoryDatabaseError("Unable to write to repository "
                        "contents dir %r for project %r"
                        % (path, self.shortName))

        if not os.access(nscfg.tmpDir, os.W_OK):
            raise RepositoryDatabaseError("Unable to write to repository "
                    "temporary directory %r for project %r"
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
        Return a (cached) C{CachingRepositoryServer} for this project's
        repository.
        """
        return proxy.CachingRepositoryServer(self.getNetServerConfig(),
                self.getURL(), self.getNetServer())

    @cached
    def getShimServer(self):
        """
        Return a (cached) shim C{NetworkRepositoryServer} for this project.
        """
        return self._getServer(shimclient.NetworkRepositoryServer)

    @cached
    def _getAuthToken(self, userId):
        """
        Return a role-based auth token for given user, or raise a
        C{ProductNotFoundError} if they do not have read permissions.

        C{userId} may also be a special value less than zero, either
        C{ANY_READER} or C{ANY_WRITER}.
        """
        if userId == ANY_WRITER:
            level = userlevels.ADMIN
        elif userId == ANY_READER:
            level = userlevels.USER
        elif userId == ANONYMOUS:
            if self.isHidden:
                raise ProductNotFound(self.shortName)
            else:
                level = userlevels.USER
        elif userId < 0:
            raise RuntimeError("Invalid userId %d" % userId)
        else:
            cu = self._db.cursor()
            cu.execute("""SELECT level FROM ProjectUsers
                    WHERE projectId = ? AND userId = ?""",
                    self.projectId, userId)
            try:
                level, = cu.next()
            except StopIteration:
                if self.isHidden:
                    # Not a member on a private project -> project not found
                    raise ProductNotFound(self.shortName)
                else:
                    # Not a member on a public project -> "user" level
                    level = userlevels.USER
            else:
                if level not in userlevels.LEVELS:
                    raise RuntimeError("Invalid userlevel %d" % (level,))

        roleName = ROLE_PERMS[level][0]
        return [ValidUser(roleName), None, [], None]

    def _getShimServerProxy(self, userId=None):
        """
        Get a shim XMLRPC server proxy for this project's repository.
        If C{userId} is not C{None} then the proxy will emulate that user's
        permissions in the repository, otherwise the proxy will have access to
        all roles.
        """
        protocol, _, port = self._getURLPieces()
        authToken = self._getAuthToken(userId)
        return shimclient.ShimServerProxy(self.getShimServer(),
                protocol, port, authToken)

    @cached
    def getServerProxy(self, userId=None):
        """
        Get a XMLRPC server proxy for this project's repository. If the
        project has a local database, a shim proxy will be used.
        """
        if self.hasDatabase:
            return self._getShimServerProxy(userId=userId)
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
        Create a repository database for this project including associated
        infrastructure such as the content store and temporary storage.
        """
        # Set up some infrastructure that is independent of the db.
        nscfg = self.getNetServerConfig()
        util.mkdirChain(nscfg.tmpDir)
        for contDir in nscfg.contentsDir.split():
            util.mkdirChain(contDir)

        # Check for a preload tarball.
        if self.preload():
            return

        # Now do the driver-specfic bits and initialize the schema.
        self._create()
        db = self.getReposDB()
        conary_schema.loadSchema(db)

    def _create(self):
        """
        Internal, driver-specific method to create an empty repository
        database.
        """
        raise NotImplementedError

    def dump(self, path):
        """
        Dump the repository database to C{path}.
        """
        raise NotImplementedError

    def restore(self, path):
        """
        Load the repository database from the backup at C{path}.
        """
        raise NotImplementedError

    def destroy(self):
        """
        Delete the entire repository including database and content store.
        """
        nscfg = self.getNetServerConfig()

        self.drop()

        for contDir in nscfg.contentsDir.split():
            contDir = os.path.normpath(contDir)
            if os.path.isdir(contDir):
                util.rmtree(contDir)

            # If the parent of the content store is named the same as the
            # project FQDN, try to delete it, too. There may be an old 'tmp'
            # directory that needs to be deleted first.
            parentDir = os.path.dirname(contDir)
            if os.path.basename(parentDir) == self.fqdn:
                try:
                    tmpDir = os.path.join(parentDir, 'tmp')
                    if os.path.isdir(tmpDir):
                        util.rmtree(tmpDir)
                    os.rmdir(parentDir)
                except OSError, err:
                    if err.errno not in (errno.ENOTEMPTY, errno.EACCES):
                        raise

    def drop(self):
        """
        Drop the repository database, if it exists.

        Note that this does not delete any other repository infrastructure,
        e.g. contents.
        """
        raise NotImplementedError

    def preload(self):
        """ Load contents and database from a compressed tarball on disk. """

        workDir = os.path.dirname(os.path.normpath(self.contentsDirs[0]))
        preloadPath = os.path.join(workDir, 'preload.tar.xz')
        if not os.path.isfile(preloadPath):
            return False

        # Preloads with multiple content store dirs are not supported yet.
        assert len(self.contentsDirs) == 1

        log.info("Preloading repository %s from archive at %s", self.fqdn,
                preloadPath)

        # Extract contents and dump file.
        util.execute("xzdec '%s' | tar -C '%s' -x" % (preloadPath, workDir))

        # Restore and delete the dump file.
        dumpPath = os.path.join(workDir, 'database.' + self.preloadSuffix)
        self.restore(dumpPath)
        os.unlink(dumpPath)

        log.info("Preload of %s is complete", self.fqdn)

        return True

    # Repository management
    @withNetServer
    def getRoleList(self, repos):
        return set(repos.auth.getRoleList())

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


class SQLiteRepositoryHandle(RepositoryHandle):
    @property
    def _dbPath(self):
        return self.dbTuple[1]

    def _create(self):
        "SQLite-specific repository creation."
        util.mkdirChain(os.path.dirname(self._dbPath))

    def dump(self, path):
        if os.path.exists(self._dbPath):
            util.execute("sqlite3 '%s' .dump > '%s'" % (self._dbPath, path))

    def restore(self, path):
        self.drop()
        if os.path.exists(path):
            util.execute("sqlite3 '%s' < '%s'" % (self._dbPath, path))

    def drop(self):
        if os.path.exists(self._dbPath):
            os.unlink(self._dbPath)


class PostgreSQLRepositoryHandle(RepositoryHandle):
    preloadSuffix = 'pgtar'

    @cached
    def _getName(self):
        return self.dbTuple[1].rsplit('/')[-1]

    @cached
    def _splitParams(self):
        driver, path = self.dbTuple
        host, user = 'localhost', 'postgres'
        if driver == 'pgpool':
            port = 6432
        else:
            port = 5432
        if '/' in path:
            host, database = path.rsplit('/', 1)
            if '@' in host:
                user, host = host.split('@', 1)
            if ':' in host:
                host, port = host.rsplit(':', 1)
                port = int(port)
        else:
            database = path
        return host, port, user, database

    def _getControlConnection(self):
        "Return a connection to the control database."
        driver, path = self.dbTuple
        if '/' in path:
            base = path.rsplit('/', 1)[0] + '/'
        else:
            base = ''

        controlPath = base + 'postgres'
        return dbstore.connect(controlPath, driver)

    def _getBouncerConnection(self):
        """Return a connection to pgbouncer."""
        driver, path = self.dbTuple

        # Discard everything except the host/port
        if '/' in path:
            start = path.find('@')
            end = path.find('/')
            host = path[start + 1 : end]
        else:
            host = 'localhost:6432'

        # Fill in the rest
        # NB: don't use the pgpool driver or it will try to interrogate
        # the admindb for schema information, which doesn't work.
        bouncerPath = 'pgbouncer@%s/pgbouncer' % (host,)
        return dbstore.connect(bouncerPath, 'postgresql')

    def _dbExists(self, controlDb):
        ccu = controlDb.cursor()
        ccu.execute("""SELECT COUNT(*) FROM pg_catalog.pg_database
                WHERE datname = ?""", self._getName())
        return bool(ccu.fetchone()[0])

    def _create(self, empty=False):
        """
        PostgreSQL-specific repository creation.

        This is currently used by C{restore} as well so make sure it doesn't
        create anything that would interfere with the restore process.
        """
        user, dbName = self._splitParams()[2:]
        controlDb = self._getControlConnection()
        ccu = controlDb.cursor()

        if self._dbExists(controlDb):
            # Database exists
            log.error("PostgreSQL database %r already exists while "
                    "creating project %r", dbName, self.shortName)
            raise RepositoryAlreadyExists(self.shortName)

        extra = ''
        if empty:
            # Clone template0 when restoring from a dump since the dump already
            # has all the prefab stuff like plpgsql.
            extra += ' TEMPLATE template0'
        ccu.execute("CREATE DATABASE %s ENCODING 'UTF8'%s" % (dbName, extra))

    def drop(self):
        controlDb = self._getControlConnection()

        if not self._dbExists(controlDb):
            return

        name = self._getName()
        bcu = None
        if ':6432/' in self.dbTuple[1]:
            # pgbouncer normally holds idle connections for 45 seconds. Our
            # version supports a custom KILL command that terminates all open
            # client and server connections to that database and prevents new
            # ones until the following RESUME. A little bit of trickery is
            # needed to get around the fact that python-pgsql's primary API
            # always uses prepared statements, which aren't supported by
            # pgbouncer's admin interface.
            bouncerDb = self._getBouncerConnection()
            bcu = bouncerDb.cursor()
            bcu._cursor._source.query("KILL " + name)

        try:
            ccu = controlDb.cursor()
            for n in range(5):
                try:
                    ccu.execute("DROP DATABASE %s" % (name,))
                except CursorError, err:
                    if 'is being accessed by other users' not in err.msg:
                        raise
                    time.sleep(1.0)
                else:
                    break
            else:
                log.error("Could not drop repository database %r because a "
                        "connection is still open -- continuing.", name)

        finally:
            if bcu:
                bcu._cursor._source.query("RESUME " + name)

    def dump(self, path):
        controlDb = self._getControlConnection()

        if self._dbExists(controlDb):
            # TODO: genericize
            util.execute("pg_dump -U postgres -p 5439 -f '%s' '%s'"
                    % (path, self._getName()))

    def restore(self, path):
        dbName = self._getName()
        controlDb = self._getControlConnection()
        ccu = controlDb.cursor()

        self.drop()
        if os.path.exists(path):
            log.info("Restoring database dump for project %s", self.fqdn)
            self._create(empty=True)

            host, port, user, database = self._splitParams()
            cxnArgs = "-h '%s' -p '%s' -U postgres" % (host, port)

            if path.endswith('.pgtar'):
                util.execute("pg_restore %s --single-transaction "
                        "-d '%s' '%s'" % (cxnArgs, database, path))
            else:
                util.execute("psql %s -f '%s' '%s' >/dev/null"
                        % (cxnArgs, path, dbName))

            db = self.getReposDB(skipCache=True)
            db.analyze()
            db.close()


class MultiShimServerCache(object):
    """
    C{ServerCache} replacement for use with rBuilder. It will automatically
    use a shim client for any repositories which are hosted or cached on the
    rBuilder, and will use the credentials in the database for any external
    projects.
    """
    def __init__(self, manager, userId=None):
        self.manager = weakref.ref(manager)
        self.userId = userId
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
            return repo.getServerProxy(userId=self.userId)


class MultiShimNetClient(shimclient.ShimNetClient):
    def __init__(self, manager, userId=None):
        repMap = conarycfg.RepoMap()
        userMap = conarycfg.UserInformation()
        netclient.NetworkRepositoryClient.__init__(self, repMap, userMap,
                proxy=manager.cfg.proxy)

        self.c = MultiShimServerCache(manager, userId)
