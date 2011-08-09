#
# Copyright (c) 2011 rPath, Inc.
#

from mod_python import apache

import logging
import os
import time
import urllib
import base64

import rpath_capsule_indexer

from mint import mint_error
from mint import maintenance
from mint.db import database as mdb
from mint.db.projects import transTables
from mint.rest.db import database as rdb
from mint.web import app
from mint.web import cresthandler
from mint.web.webhandler import normPath

from conary import errors as cerrors
from conary.web import webauth
from conary import dbstore, conarycfg
from conary.dbstore import sqlerrors
from conary.repository import shimclient, transport
from conary.repository.netrepos import proxy
from conary.repository.netrepos import netserver

from conary.server import apachemethods

log = logging.getLogger(__name__)


# Global cached objects
repositories = {}


def post(port, isSecure, repos, cfg, db, req):
    repos, shimRepo = repos

    if repos:
        items = req.uri.split('/')
        if len(items) >= 4 and items[1] == 'repos' and items[3] == 'api':
            # uri at this point should be repos/<hostname>/
            skippedPart = '/'.join(items[:4])
            return cresthandler.handleCrest(skippedPart,
                    cfg, db, repos, req)
    if req.headers_in['Content-Type'] == "text/xml":
        if not repos:
            return apache.HTTP_NOT_FOUND

        return apachemethods.post(port, isSecure, repos, req)
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo, db=db)
        return webfe._handle(normPath(req.uri[len(cfg.basePath):]))


CONARY_GET_COMMANDS = ["changeset", "getOpenPGPKey"]

def get(port, isSecure, repos, cfg, db, req):
    repos, shimRepo = repos

    uri = req.uri
    if uri.endswith('/'):
        uri = uri[:-1]

    cmd = os.path.basename(uri)
    if cmd in CONARY_GET_COMMANDS:
        return apachemethods.get(port, isSecure, repos, req)
    elif repos:
        items = req.uri.split('/')
        if len(items) >= 4 and items[1] == 'repos' and items[3] == 'api':
            # uri at this point should be repos/<hostname>/
            skippedPart = '/'.join(items[:4])
            return cresthandler.handleCrest(skippedPart,
                    cfg, db, repos, req)
    webfe = app.MintApp(req, cfg, repServer = shimRepo, db=db)
    return webfe._handle(normPath(req.uri[len(cfg.basePath):]))


def getRepositoryMap(cfg):
    conaryrc = os.path.join(cfg.dataPath, 'config', 'conaryrc')
    if os.path.exists(conaryrc):
        cc = conarycfg.ConaryConfiguration()
        cc.read(conaryrc)
        #pylint: disable-msg=E1101
        return cc.repositoryMap
    else:
        return {}

def getRepository(projectName, repName, context,
        dbTuple, localMirror, requireSigs, commitEmail):

    cfg, req = context.cfg, context.req

    # FIXME: Until there is a per-project signature requirement flag, this will
    # have to do.
    if repName.startswith('rmake-repository.'):
        requireSigs = False

    nscfg = netserver.ServerConfig()
    nscfg.externalPasswordURL = cfg.externalPasswordURL
    nscfg.authCacheTimeout = cfg.authCacheTimeout
    nscfg.requireSigs = requireSigs
    nscfg.serializeCommits = cfg.serializeCommits
    nscfg.readOnlyRepository = cfg.readOnlyRepositories

    repositoryDir = os.path.join(cfg.reposPath, repName)

    nscfg.repositoryDB = dbTuple
    nscfg.proxyContentsDir = os.path.join(cfg.dataPath, 'proxy-contents')
    nscfg.changesetCacheDir = os.path.join(cfg.dataPath, 'cscache')
    nscfg.contentsDir = " ".join(x % repName
            for x in cfg.reposContentsDir.split(" "))

    nscfg.serverName = [repName]
    nscfg.tmpDir = os.path.join(cfg.dataPath, 'tmp')
    nscfg.logFile = cfg.reposLog and \
                    os.path.join(cfg.logPath, 'repository.log') \
                    or None
    nscfg.repositoryMap = getRepositoryMap(cfg)

    urlBase = "%%(protocol)s://%s:%%(port)d/repos/%s/" % (req.hostname,
            projectName)

    # set up the commitAction
    buildLabel = repName + "@" + cfg.defaultBranch
    if cfg.SSL:
        protocol = "https"
        host = cfg.secureHost
    else:
        protocol = "http"
        host = req.hostname

    repMapStr = "%s://%s/repos/%s/" % (protocol, host, projectName)

    if cfg.commitAction and not localMirror:
        actionDict = {'repMap': repName + " " + repMapStr,
                      'buildLabel': buildLabel,
                      'projectName': projectName,
                      'fqdn': repName,
                      'commitFromEmail': cfg.commitEmail,
                      'commitEmail': commitEmail,
                      'basePath' : cfg.basePath,
                      'authUser' : cfg.authUser,
                      'authPass' : cfg.authPass
        }

        nscfg.commitAction = cfg.commitAction % actionDict
        if cfg.commitActionEmail and commitEmail:
            nscfg.commitAction += " " + cfg.commitActionEmail % actionDict
    else:
        nscfg.commitAction = None

    if not os.access(repositoryDir, os.F_OK):
        log.error("Failed to open repository directory %s", repositoryDir)
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    netRepos = reposDb = None
    for x in range(5):
        try:
            reposDb = dbstore.connect(dbTuple[1], dbTuple[0])
        except sqlerrors.DatabaseError, err:
            req.log_error("Error opening database %r: %s" %
                    (dbTuple, str(err)))
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

        restDb = _addCapsuleConfig(context, nscfg, repName)

        try:
            netRepos = netserver.NetworkRepositoryServer(nscfg, urlBase,
                    reposDb)
        except sqlerrors.DatabaseLocked:
            reposDb.close()
            time.sleep(0.1)
        else:
            break
    else:
        raise

    repos = CachingRepositoryServer(restDb, nscfg, urlBase, netRepos)
    shim = shimclient.NetworkRepositoryServer(nscfg, urlBase, reposDb)

    return netRepos, repos, shim


def _getRestDb(context):
    mintDb = mdb.Database(context.cfg, context.db)
    restDb = rdb.Database(context.cfg, mintDb, dbOnly=True)
    return restDb


def _addCapsuleConfig(context, conaryReposCfg, repName):
    restDb = _getRestDb(context)
    # XXX we should speed these up by combining into a single call
    contentInjectionServers = restDb.capsuleMgr.getContentInjectionServers()
    if not contentInjectionServers or repName not in contentInjectionServers:
        return
    indexer = restDb.capsuleMgr.getIndexer()
    if not indexer.hasSources():
        return
    conaryReposCfg.excludeCapsuleContents = True
    # These settings are only used by the filter
    conaryReposCfg.injectCapsuleContentServers = contentInjectionServers
    conaryReposCfg.capsuleServerUrl = "direct"
    return restDb


def proxyExternalRestRequest(context, fqdn, proxyServer):
    cfg, req = context.cfg, context.req
    # FIXME: this only works with entitlements, not user:password

    # /repos/rap/api/foo -> api/foo
    path = '/'.join(req.unparsed_uri.split('/')[3:])
    # get the upstream repo url and label
    urlBase, label = _getUpstreamInfoForExternal(context.db, fqdn)
    # no external project?  maybe it's a non-entitled platform
    if not urlBase:
        found = False
        for label in cfg.availablePlatforms:
            if label.split('@')[0].lower() == fqdn.lower():
                urlBase = 'http://%s/conary/' % fqdn
                found = True
                break
        if not found:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    url = ''.join((urlBase, path))
    # build the entitlement to send in the header
    l = []
    for entitlement in proxyServer.cfg.entitlement.find(fqdn):
        if entitlement[0] is None:
            l.append("* %s" % (base64.b64encode(entitlement[1])))
        else:
            l.append("%s %s" % (entitlement[0],
                                base64.b64encode(entitlement[1])))
    entitlement = ' '.join(l)

    opener = transport.URLOpener(proxyMap=context.cfg.getProxyMap())
    headers = [
            ('X-Conary-Entitlement', entitlement),
            ('X-Conary-Servername', fqdn),
            ('User-agent', transport.Transport.user_agent),
            ]

    # make the request
    try:
        f = opener.open(url, headers=headers)
    except Exception, err:
        if getattr(err, 'errcode', None) == 403:
            return 403  # Forbidden
        else:
            # translate all errors to a 502
            log.error("Cannot proxy REST request to %s: %s", urlBase, err)
            return 502  # Bad Gateway

    # form up the base URL to this repository on rBuilder
    if req.subprocess_env.get('HTTPS', '') == 'on':
        protocol = 'https'
    else:
        protocol = 'http'
    myUrlBase = '%s://%s/repos/%s/' % (protocol, req.hostname, fqdn)

    # translate the response
    l = []
    for line in f:
        # rewrite hrefs to point at ourself
        l.append(line.replace(urlBase, myUrlBase))
    buf = ''.join(l)
    req.headers_out['Content-length'] = str(len(buf))

    # copy response headers from upstream
    skippedHeaders = ('content-length', 'server', 'connection', 'date')
    for header in f.headers.keys():
        if header not in skippedHeaders:
            req.headers_out[header] = f.headers.get(header)
    req.write(buf)
    f.close()
    return apache.OK

class CapsuleFilterMixIn(object):
    class _CapsuleDownloader(object):
        def __init__(self, restDb):
            self._restDb = restDb

        def downloadCapsule(self, capsuleKey, sha1sum):
            indexer = self._restDb.capsuleMgr.getIndexer()
            msgTmpl = ("Error downloading capsule. "
                "Upstream error message: (fault code: %s) %s")
            try:
                pkg = indexer.getPackage(capsuleKey, sha1sum)
            except rpath_capsule_indexer.errors.RPCError, e:
                raise cerrors.RepositoryError(msgTmpl %
                    (e.faultCode, e.faultString))
            if pkg is None:
                raise cerrors.RepositoryError("Error downloading capsule.  Please check the repository logs and verify credentials")
            fobj = file(indexer.getFullFilePath(pkg))
            return self.fromFile(fobj)

        def downloadCapsuleFile(self, capsuleKey, capsuleSha1sum, fileName,
                fileSha1sum):
            if capsuleSha1sum == fileSha1sum or fileName == '':
                # Troves do contain the capsule too, it's legitimate to
                # request it; however, we can fall back to downloadCapsule for
                # it.
                # The SHA-1 check doesn't normally work because the
                # FileStreams.sha1 column is often null for capsule files, but
                # the repository will also return fileName='' if the capsule
                # fileId is the same as the contents fileId. Either of these
                # mean that the capsule itself is being requested.
                return self.downloadCapsule(capsuleKey, capsuleSha1sum)
            indexer = self._restDb.capsuleMgr.getIndexer()
            msgTmpl = ("Error downloading file from capsule. "
                "Upstream error message: (fault code: %s) %s")
            try:
                fobj = indexer.getFileFromPackage(capsuleKey, capsuleSha1sum,
                    fileName, fileSha1sum)
            except rpath_capsule_indexer.errors.RPCError, e:
                raise cerrors.RepositoryError(msgTmpl %
                    (e.faultCode, e.faultString))
            return self.fromFile(fobj)

        def downloadCapsuleFiles(self, capsuleKey, capsuleSha1sum, fileList):
            return [ self.downloadCapsuleFile(capsuleKey, capsuleSha1sum,
                fileName, fileSha1sum)
                    for (fileName, fileSha1sum) in fileList ]

        fromFile = proxy.ChangesetFilter.CapsuleDownloader.fromFile

    def __init__(self):
        self.CapsuleDownloader = lambda x: self._CapsuleDownloader(
            self._restDb)

class CachingRepositoryServer(proxy.CachingRepositoryServer, CapsuleFilterMixIn):
    withCapsuleInjection = True
    def __init__(self, restDb, nscfg, urlBase, netRepos):
        proxy.CachingRepositoryServer.__init__(self, nscfg, urlBase, netRepos)
        self.setRestDb(restDb)

    def setRestDb(self, restDb):
        self._restDb = restDb
        CapsuleFilterMixIn.__init__(self)


class ProxyRepositoryServer(proxy.ProxyRepositoryServer, CapsuleFilterMixIn):
    def __init__(self, restDb, *args, **kwargs):
        self._restDb = restDb
        proxy.ProxyRepositoryServer.__init__(self, *args, **kwargs)
        CapsuleFilterMixIn.__init__(self)

def conaryHandler(context):
    req, cfg = context.req, context.cfg
    maintenance.enforceMaintenanceMode(cfg)

    auth = webauth.getAuth(req)
    if type(auth) is int:
        return auth
    requireSigs = cfg.requireSigs
    if auth[0] == cfg.authUser:
        # don't require signatures for the internal user (this would break
        # group builder)
        requireSigs = False
    # From this point on we don't use the authentication information
    # Get rid of it so it doesn't show up in tracebacks
    del auth

    paths = normPath(req.uri).split("/")
    fqdn = hostName = None
    if "repos" in paths:
        hostPart = paths[paths.index('repos') + 1]
        if '.' in hostPart:
            fqdn = hostPart
            if fqdn.endswith('.'):
                fqdn = fqdn[:-1]
        else:
            hostName = hostPart
    else:
        fqdn = req.hostname

    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (req.subprocess_env.get('HTTPS', 'off') == 'on')

    # resolve the conary repository names
    (projectHostName, _, actualRepName, external, database,
            localMirror, commitEmail
            ) = _resolveProjectRepos(context.db, hostName, fqdn)

    # By now we must know the FQDN, either from the request itself or from
    # the project looked up in the database.
    if not fqdn:
        if not actualRepName:
            log.warning("Unknown project %s in request for %s", hostName,
                    req.uri)
            return apache.HTTP_NOT_FOUND
        fqdn = actualRepName

    # do not require signatures when committing to a local mirror
    if localMirror:
        requireSigs = False

    doReset = False

    items = req.uri.split('/')
    proxyRestRequest = (len(items) >= 4
                        and items[1] == 'repos'
                        and items[3] == 'api')
    disallowInternalProxy = False

    if actualRepName and (localMirror or not external):
        # it's local

        # no need to proxy a rest request..
        proxyRestRequest = False

        if ' ' in database:
            driver, path = database.split(' ', 1)
        else:
            if database not in cfg.database:
                raise mint_error.RepositoryDatabaseError(
                        "Database alias %r is not defined" % (database,))
            driver, path = cfg.database[database]

        if '%s' in path:
            path %= actualRepName.translate(transTables[driver])
        dbTuple = driver, path

        repHash = (actualRepName, req.hostname, dbTuple)

        # Check for a cached connection.
        if repHash in repositories:
            repServer, proxyServer, shimRepo = repositories[repHash]
            repServer.reopen()
        else:
            # Create a new connection.
            repServer, proxyServer, shimRepo = getRepository(projectHostName,
                    actualRepName, context, dbTuple, localMirror, requireSigs,
                    commitEmail)

            if not repServer:
                return apache.HTTP_NOT_FOUND

            # Cache non-pooled connections by way of their repository
            # instance.
            repositories[repHash] = (repServer, proxyServer, shimRepo)

        proxyServer.setRestDb(_getRestDb(context))

        # Reset the repository server when we're done with it.
        doReset = True

    else:
        # it's completely external
        # use the Internal Conary Proxy if it's configured and we're
        # passing a fully qualified url
        if (not cfg.useInternalConaryProxy
            or not urllib.splittype(req.unparsed_uri)[0]):
            # don't use the proxy we set up if the configuration says
            # not to, or if it is not fully qualified
            disallowInternalProxy = True
        # Conary >= 1.1.26 proxies will add a Via header for all
        # requests forwarded for the Conary Proxy. If it contains our
        # IP address and port, then we've already handled this request.
        via = req.headers_in.get("Via", "")
        myHostPort = "%s:%d" % (req.connection.local_ip,
                req.connection.local_addr[1])
        if myHostPort in via:
            apache.log_error('Internal Conary Proxy was attempting an infinite '
                    'loop (request %s, via %s)' % (req.hostname, via))
            raise apache.SERVER_RETURN, apache.HTTP_BAD_GATEWAY

        proxycfg = netserver.ServerConfig()
        proxycfg.proxyContentsDir = cfg.proxyContentsDir
        proxycfg.changesetCacheDir = cfg.proxyChangesetCacheDir
        proxycfg.tmpDir = cfg.proxyTmpDir
        if actualRepName:
            restDb = _addCapsuleConfig(context, proxycfg, actualRepName)
        else:
            restDb = None

        # set a proxy (if it was configured)
        proxycfg.proxy = cfg.proxy

        if ':' in cfg.siteDomainName:
            domain = cfg.siteDomainName
        else:
            domain = cfg.siteDomainName + ':%(port)d'
        urlBase = "%%(protocol)s://%s.%s/" % \
                (cfg.hostName, domain)
        proxyServer = ProxyRepositoryServer(restDb, proxycfg, urlBase)

        # inject known authentication (userpass and entitlement)
        proxyServer.cfg.entitlement = conarycfg.EntitlementList()
        proxyServer.cfg.user = conarycfg.UserInformation()
        if cfg.injectUserAuth:
            _updateUserSet(context.db, proxyServer.cfg)
        shimRepo = None

    try:
        if proxyRestRequest:
            # use proxyServer config for http proxy and auth data
            return proxyExternalRestRequest(context, fqdn, proxyServer)
        if disallowInternalProxy:
            proxyServer = None
        if method == "POST":
            return post(port, secure, (proxyServer, shimRepo), cfg, context.db,
                    req)
        elif method == "GET":
            return get(port, secure, (proxyServer, shimRepo), cfg, context.db,
                    req)
        elif method == "PUT":
            if proxyServer:
                return apachemethods.putFile(port, secure, proxyServer, req)
            else:
                return apache.HTTP_NOT_FOUND
        else:
            return apache.HTTP_METHOD_NOT_ALLOWED
    finally:
        if doReset and hasattr(repServer, 'reset'):
            repServer.reset()



def _updateUserSet(db, cfgObj):
    cu = db.cursor()
    cu.execute("""SELECT label, authType, username, password, entitlement
        FROM Labels WHERE authType IS NOT NULL AND authType != 'none'""")

    for label, authType, username, password, entitlement in cu.fetchall():
        host = label.split('@')[0]
        if authType == 'userpass':
            cfgObj.user.addServerGlob(host, (username, password))
        elif authType == 'entitlement':
            cfgObj.entitlement.addEntitlement(host, entitlement)


def _getUpstreamInfoForExternal(db, fqdn):
    cu = db.cursor()
    cu.execute("""SELECT url, label
        FROM Labels JOIN projects USING(projectId) WHERE fqdn = ?""", fqdn)
    ret = cu.fetchall()
    if len(ret) < 1:
        return None, None
    return ret[0]


def _resolveProjectRepos(db, hostname, fqdn):
    if fqdn:
        where = 'fqdn = ?'
        whereArg = fqdn
    else:
        where = 'hostname = ?'
        whereArg = hostname

    external = True
    localMirror = False
    projectHostName = None
    projectId = None
    database = None
    commitEmail = None
    fqdn = None

    # Determine if the project is local by checking the projects table
    cu = db.cursor()
    cu.execute("""
        SELECT projectId, hostname, fqdn, external, %s, commitEmail,
            EXISTS(SELECT * FROM InboundMirrors
                WHERE projectId=targetProjectId) AS localMirror
        FROM Projects WHERE %s""" % (
                (db.driver == 'mysql' and '`database`' or 'database'), where),
            whereArg)
    project = cu.fetchone()
    if project:
        (projectId, projectHostName, fqdn, external, database, commitEmail,
                localMirror) = project

    return (projectHostName, projectId, fqdn, external, database,
            localMirror, commitEmail)
