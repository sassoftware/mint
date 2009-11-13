#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All rights reserved.
#

from mod_python import apache

import logging
import os
import time
import traceback
import urllib
import base64

from mint import mint_error
from mint import maintenance
from mint.db.projects import transTables
from mint.rest.errors import ProductNotFound
from mint.web import app
from mint.web import cresthandler
from mint.web.webhandler import normPath

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
proxy_repository = None


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

def getRepository(projectName, repName, cfg,
        req, dbTuple, localMirror, requireSigs, commitEmail):

    nscfg = netserver.ServerConfig()
    nscfg.externalPasswordURL = cfg.externalPasswordURL
    nscfg.authCacheTimeout = cfg.authCacheTimeout
    nscfg.requireSigs = requireSigs
    nscfg.serializeCommits = cfg.serializeCommits
    nscfg.readOnlyRepository = cfg.readOnlyRepositories

    repositoryDir = os.path.join(cfg.reposPath, repName)

    nscfg.repositoryDB = dbTuple
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

    if 'changesetCacheDir' in nscfg.keys():
        # XXX FIXME: deal with capsules
        repos = proxy.SimpleRepositoryFilter(nscfg, urlBase, netRepos)
    else:
        repos = netRepos
    shim = shimclient.NetworkRepositoryServer(nscfg, urlBase, reposDb)

    return netRepos, repos, shim


class RestRequestError(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        Exception.__init__(self, code, msg)


class RestProxyOpener(transport.URLOpener):
    def http_error_default(self, url, fp, errcode, errmsg, headers, data=None):
        raise RestRequestError(errcode, errmsg)

    # override all error handling
    http_error_301 = http_error_default
    http_error_302 = http_error_default
    http_error_303 = http_error_default
    http_error_307 = http_error_default
    http_error_401 = http_error_default


def proxyExternalRestRequest(context, projectHostName, proxyServer):
    cfg, req = context.cfg, context.req
    # FIXME: this only works with entitlements, not user:password

    # /repos/rap/api/foo -> api/foo
    path = '/'.join(req.unparsed_uri.split('/')[3:])
    # get the upstream repo url and label
    urlBase, label = _getUpstreamInfoForExternal(context.db, projectHostName)
    # no external project?  maybe it's a non-entitled platform
    if not urlBase:
        found = False
        for label in cfg.availablePlatforms:
            if label.split('.')[0] == projectHostName:
                serverName = label.split('@')[0]
                urlBase = 'http://%s/conary/' % serverName
                found = True
                break
        if not found:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    url = ''.join((urlBase, path))
    # grab the server name from the label
    serverName = label.split('@')[0]
    # build the entitlement to send in the header
    l = []
    for entitlement in proxyServer.cfg.entitlement.find(serverName):
        if entitlement[0] is None:
            l.append("* %s" % (base64.b64encode(entitlement[1])))
        else:
            l.append("%s %s" % (entitlement[0],
                                base64.b64encode(entitlement[1])))
    entitlement = ' '.join(l)

    opener = RestProxyOpener(proxies=proxyServer.cfg.proxy)
    opener.addheader('X-Conary-Entitlement', entitlement)
    opener.addheader('X-Conary-Servername', serverName)
    opener.addheader('User-agent', transport.Transport.user_agent)

    # make the request
    try:
        f = opener.open(url)
    except RestRequestError, e:
        if e.code != apache.HTTP_FORBIDDEN:
            # translate all errors to a 502
            return apache.HTTP_BAD_GATEWAY
        return e.code

    # form up the base URL to this repository on rBuilder
    if req.is_https():
        protocol = 'https'
    else:
        protocol = 'http'
    port = req.connection.local_addr[1]
    myUrlBase = proxyServer.basicUrl % {'protocol':protocol,
                                        'port':port}
    myUrlBase += 'repos/%s/' % (projectHostName,)

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

class ProxyRepositoryServer(proxy.ProxyRepositoryServer):
    def __init__(self, mintCfg, *args, **kwargs):
        proxy.ProxyRepositoryServer.__init__(self, *args, **kwargs)
        self._mintCfg = mintCfg
        self._setCapsuleServerUrl()
        self.CapsuleDownloader = lambda x: self._CapsuleDownloader(
            self._getRestDb())

    def _setCapsuleServerUrl(self):
        # XXX FIXME reenable after we have the right content
        return
        restdb = self._getRestDb()
        indexer = restdb.capsuleMgr.getIndexer()
        if not list(indexer.iterSources()):
            return
        # It really doesn't matter what the capsule server URL is, as long as
        # it is not None
        self.cfg.capsuleServerUrl = 'direct'

    def _getRestDb(self):
        cfg = self._mintCfg
        from mint.db import database
        from mint.rest.db import database as rdb
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        restdb = rdb.Database(cfg, database.Database(cfg, db))
        return restdb

    class _CapsuleDownloader(object):
        def __init__(self, restdb):
            self._restdb = restdb

        def downloadCapsule(self, capsuleKey, sha1sum):
            indexer = self._restdb.capsuleMgr.getIndexer()
            # XXX FIXME: error handling
            pkg = indexer.getPackage(capsuleKey, sha1sum)
            fobj = file(indexer.getFullFilePath(pkg))
            return self.fromFile(fobj)

        def downloadCapsuleFile(self, capsuleKey, capsuleSha1sum, fileName,
                fileSha1sum):
            indexer = self._restdb.capsuleMgr.getIndexer()
            fobj = indexer.getFileFromPackage(capsuleKey, capsuleSha1sum,
                fileName, fileSha1sum)
            return self.fromFile(fobj)

        fromFile = proxy.ProxyRepositoryServer.CapsuleDownloader.fromFile

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

    paths = normPath(req.uri).split("/")
    if "repos" in paths:
        hostName = paths[paths.index('repos') + 1]
        domainName = None
    else:
        parts = req.hostname.split(".")
        hostName = parts[0]
        domainName = ".".join(parts[1:])

    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (req.subprocess_env.get('HTTPS', 'off') == 'on')

    # resolve the conary repository names
    (projectHostName, _, actualRepName, external, database,
            localMirror, commitEmail
            ) = _resolveProjectRepos(context.db, hostName, domainName)

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
                    actualRepName, cfg, req, dbTuple, localMirror, requireSigs,
                    commitEmail)

            if not repServer:
                return apache.HTTP_NOT_FOUND

            # Cache non-pooled connections by way of their repository
            # instance.
            repositories[repHash] = (repServer, proxyServer, shimRepo)

        # Reset the repository server when we're done with it.
        doReset = True

    else:
        # it's completely external
        # use the Internal Conary Proxy if it's configured and we're
        # passing a fully qualified url
        global proxy_repository
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

        if proxy_repository:
            proxyServer = proxy_repository
        else:
            proxycfg = netserver.ServerConfig()
            proxycfg.proxyContentsDir = cfg.proxyContentsDir
            proxycfg.changesetCacheDir = cfg.proxyChangesetCacheDir
            proxycfg.tmpDir = cfg.proxyTmpDir

            # set a proxy (if it was configured)
            proxycfg.proxy = cfg.proxy

            if ':' in cfg.siteDomainName:
                domain = cfg.siteDomainName
            else:
                domain = cfg.siteDomainName + ':%(port)d'
            urlBase = "%%(protocol)s://%s.%s/" % \
                    (cfg.hostName, domain)
            proxyServer = proxy_repository = ProxyRepositoryServer(
                    cfg, proxycfg, urlBase)

        # inject known authentication (userpass and entitlement)
        proxyServer.cfg.entitlement = conarycfg.EntitlementList()
        proxyServer.cfg.user = conarycfg.UserInformation()
        if cfg.injectUserAuth:
            _updateUserSet(context.db, proxyServer.cfg)
        shimRepo = None

    try:
        if proxyRestRequest:
            # use proxyServer config for http proxy and auth data
            if not projectHostName:
                projectHostName = hostName
            return proxyExternalRestRequest(context, projectHostName,
                    proxyServer)
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

def _getUpstreamInfoForExternal(db, hostname):
    cu = db.cursor()
    cu.execute("""SELECT url, label FROM Labels JOIN projects USING(projectId)
                  WHERE hostName=?""", (hostname,))
    ret = cu.fetchall()
    if len(ret) < 1:
        return None, None
    return ret[0]

def _resolveProjectRepos(db, hostname, domainname):
    # Start with some reasonable assumptions
    external = True
    localMirror = False
    projectHostName = None
    projectDomainName = None
    projectId = None
    database = None
    actualRepName = possibleRepName = None
    commitEmail = None

    if domainname:
        extraWhere = "AND domainname = '%s'" % domainname
    else:
        extraWhere = ""

    # Determine if the project is local by checking the projects table
    cu = db.cursor()
    cu.execute("""SELECT projectId, domainname, external, %s,
                     EXISTS(SELECT * FROM InboundMirrors
                     WHERE projectId=targetProjectId) AS localMirror,
                     commitEmail
                  FROM Projects WHERE hostname=? %s""" % (
                      (db.driver == 'mysql' and '`database`' or 'database'),
                      extraWhere),
                  hostname)
    try:
        project = cu.fetchone()
        if project:
            (projectId, projectDomainName, external, database, localMirror,
                    commitEmail) = project
            projectHostName = hostname
            possibleRepName = "%s.%s" % (projectHostName, projectDomainName)

            # Optionally remap the repository name (forward lookup)
            cu.execute("SELECT toName FROM RepNameMap WHERE fromName = ?",
                    possibleRepName)
            mapping = cu.fetchone()
            if mapping:
                actualRepName = mapping[0]
            else:
                actualRepName = possibleRepName

        if not actualRepName:
            # Reverse lookup in repNameMap (ugh)
            possibleRepName = "%s.%s" % (hostname, domainname)
            # XXX: This is not guaranteed to be unique, so we'll make it so.
            #      (not sure that this matters on rBA, actually)
            cu.execute("""SELECT fromName FROM repNameMap where toName = ?
                    LIMIT 1""", possibleRepName)
            mapping = cu.fetchone()
            if mapping:
                fromName = mapping[0]
                projectHostName = fromName[0:fromName.find('.')]
                projectDomainName = fromName[fromName.find('.')+1:]

                cu.execute("""SELECT projectId, external, %s,
                                EXISTS(SELECT * FROM InboundMirrors
                                WHERE projectId=targetProjectId) AS localMirror
                              FROM Projects WHERE hostname=? AND domainname=?"""
                                % ((db.driver == 'mysql' and '`database`'
                                    or 'database'),),
                              projectHostName, projectDomainName)
                project = cu.fetchone()
                if project:
                    projectId, external, database, localMirror = project
                    actualRepName = possibleRepName

    except (IndexError, TypeError):
        log.exception("Error in _resolveProjectRepos:")
        actualRepName = None

    return (projectHostName, projectId, actualRepName, external, database,
            localMirror, commitEmail)
