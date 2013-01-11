#
# Copyright (c) rPath, Inc.
#

from mod_python import apache

import logging
import os
import base64

import rpath_capsule_indexer

from mint import maintenance
from mint.db import database as mdb
from mint.db.sessiondb import SessionsTable
from mint.rest.db import database as rdb
from mint.rest.errors import ProductNotFound
from mint.web import cresthandler
from mint.web.webhandler import normPath, getHttpAuth

from conary import errors as cerrors
from conary.repository import transport
from conary.repository.netrepos import proxy
from conary.repository.netrepos import netauth
from conary.repository.netrepos import netserver
from conary.web import webauth

from conary.server import apachemethods

log = logging.getLogger(__name__)


def post(port, isSecure, repos, cfg, db, req, authToken):
    repos, shimRepo = repos

    if repos:
        items = req.uri.split('/')
        if len(items) >= 4 and items[1] == 'repos' and items[3] == 'api':
            # uri at this point should be repos/<hostname>/
            skippedPart = '/'.join(items[:4])
            return cresthandler.handleCrest(skippedPart,
                    cfg, db, repos, req, authToken=authToken)
    if req.headers_in['Content-Type'] == "text/xml":
        if not repos:
            return apache.HTTP_NOT_FOUND
        return apachemethods.post(port, isSecure, repos, req,
                authToken=authToken)
    return apache.HTTP_NOT_FOUND


CONARY_GET_COMMANDS = ["changeset", "getOpenPGPKey"]

def get(port, isSecure, repos, cfg, db, req, authToken, manager):
    repos, shimRepo = repos

    uri = req.uri
    if uri.endswith('/'):
        uri = uri[:-1]

    cmd = os.path.basename(uri)
    if cmd in CONARY_GET_COMMANDS:
        return apachemethods.get(port, isSecure, repos, req,
                authToken=authToken)
    elif repos:
        items = req.uri.split('/')
        if len(items) >= 4 and items[1] == 'repos' and items[3] == 'api':
            # uri at this point should be repos/<hostname>/
            skippedPart = '/'.join(items[:4])
            return cresthandler.handleCrest(skippedPart,
                    cfg, db, repos, req, authToken=authToken)
    return apache.HTTP_NOT_FOUND


def _getRestDb(context):
    mintDb = mdb.Database(context.cfg, context.db)
    restDb = rdb.Database(context.cfg, mintDb, dbOnly=True)
    return restDb


def _addCapsuleConfig(context, conaryReposCfg, repName):
    restDb = _getRestDb(context)
    indexer = restDb.capsuleMgr.getIndexer(repName)
    if not indexer or not indexer.hasSources():
        return
    conaryReposCfg.excludeCapsuleContents = True
    # These settings are only used by the filter
    conaryReposCfg.injectCapsuleContentServers = [repName]
    conaryReposCfg.capsuleServerUrl = "direct"
    restDb.capsuleIndexer = indexer
    return restDb


def proxyExternalRestRequest(context, fqdn, handle, authToken):
    cfg, req = context.cfg, context.req
    # FIXME: this only works with entitlements, not user:password

    # /repos/rap/api/foo -> api/foo
    path = '/'.join(req.unparsed_uri.split('/')[3:])
    # get the upstream repo url and label
    if handle:
        urlBase = handle.getURL()
    else:
        # no external project?  maybe it's a non-entitled platform
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
    for entitlement in authToken.entitlements:
        if entitlement[0] is None:
            l.append("* %s" % (base64.b64encode(entitlement[1])))
        else:
            l.append("%s %s" % (entitlement[0],
                                base64.b64encode(entitlement[1])))
    entitlement = ' '.join(l)

    opener = transport.URLOpener(proxyMap=context.cfg.getProxyMap())
    headers = [
            ('X-Conary-Servername', fqdn),
            ('User-agent', transport.Transport.user_agent),
            ]
    if entitlement:
        headers.append(('X-Conary-Entitlement', entitlement))

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
            indexer = self._restDb.capsuleIndexer
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

        def downloadCapsuleFile(self, capsuleKey, capsuleSha1sum, fileKey,
                fileSha1sum):
            return self.downloadCapsuleFiles(capsuleKey, capsuleSha1sum,
                    [(fileKey, fileSha1sum)])[0]

        def downloadCapsuleFiles(self, capsuleKey, capsuleSha1sum, fileList):
            out = [None] * len(fileList)
            fileKeys = []
            fileSha1sums = []
            fileIndexes = []
            for n, (fileName, fileSha1sum) in enumerate(fileList):
                if capsuleSha1sum == fileSha1sum or fileName == '':
                    # Troves do contain the capsule too, it's legitimate to
                    # request it; however, we can fall back to downloadCapsule
                    # for it.
                    # The SHA-1 check doesn't normally work because the
                    # FileStreams.sha1 column is often null for capsule files,
                    # but the repository will also return fileName='' if the
                    # capsule fileId is the same as the contents fileId. Either
                    # of these mean that the capsule itself is being requested.
                    out[n] = self.downloadCapsule(capsuleKey, capsuleSha1sum)
                else:
                    fileKeys.append(fileName)
                    fileSha1sums.append(fileSha1sum)
                    fileIndexes.append(n)
            if fileKeys:
                indexer = self._restDb.capsuleIndexer
                msgTmpl = ("Error downloading file from capsule. "
                    "Upstream error message: (fault code: %s) %s")
                try:
                    fileObjs = indexer.getFilesFromPackage(capsuleKey,
                            capsuleSha1sum, fileKeys, fileSha1sums)
                except rpath_capsule_indexer.errors.RPCError, e:
                    raise cerrors.RepositoryError(msgTmpl %
                        (e.faultCode, e.faultString))
                for n, fileObj in zip(fileIndexes, fileObjs):
                    out[n] = self.fromFile(fileObj)
            assert None not in out
            return out

        fromFile = proxy.ChangesetFilter.CapsuleDownloader.fromFile

    def setRestDb(self, restDb):
        self.CapsuleDownloader = lambda x: self._CapsuleDownloader(restDb)


class CachingRepositoryServer(proxy.CachingRepositoryServer, CapsuleFilterMixIn):
    withCapsuleInjection = True


class ProxyRepositoryServer(proxy.ProxyRepositoryServer, CapsuleFilterMixIn):
    pass


def conaryHandler(context):
    req, cfg, manager = context.req, context.cfg, context.manager
    maintenance.enforceMaintenanceMode(cfg)

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
    elif 'x-conary-servername' in req.headers_in:
        fqdn = req.headers_in['x-conary-servername']
    else:
        fqdn = req.hostname

    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (req.subprocess_env.get('HTTPS', 'off') == 'on')

    # resolve the conary repository names
    try:
        if fqdn:
            handle = manager.getRepositoryFromFQDN(fqdn)
        else:
            handle = manager.getRepositoryFromShortName(hostName)
    except ProductNotFound:
        handle = None

    # By now we must know the FQDN, either from the request itself or from
    # the project looked up in the database.
    if handle:
        fqdn = handle.fqdn
    elif not fqdn:
        log.warning("Unknown project %s in request for %s", hostName,
                req.uri)
        return apache.HTTP_NOT_FOUND

    # Determine the user's authorization with respect to the rBuilder
    # project, if there is one.
    authToken = _getAuth(context)
    if handle:
        # Convert mint user/pass into abstract repository roles, if the
        # user is successfully authenticated to mint.
        try:
            authToken = handle.convertAuthToken(authToken, useRepoDb=True)
        except ProductNotFound:
            # User doesn't have read permission, so they can't see the
            # repository at all. However there are some unauthenticated calls,
            # like GETing and PUTting changesets, so just downgrade the auth
            # token and leave it at that.
            authToken.user = authToken.password = 'anonymous'

    # TODO: Push restdb setup and capsule filtering down to repository.py,
    # otherwise shims won't have access to it.
    if handle and handle.hasDatabase:
        # Local database
        serverCfg = handle.getNetServerConfig()
        restDb = _addCapsuleConfig(context, serverCfg, fqdn)
        netServer = handle.getServer(netserver.NetworkRepositoryServer,
                serverCfg)
        if restDb:
            proxyClass = CachingRepositoryServer
            serverCfg.proxyContentsDir = cfg.proxyContentsDir
        else:
            proxyClass = proxy.SimpleRepositoryFilter
        proxyServer = proxyClass(serverCfg, handle.getURL(), netServer)
        if restDb:
            proxyServer.setRestDb(restDb)
        # TODO: This shim server doesn't do capsule filtering, which may
        # affect the conary REST API.
        shimRepo = handle.getShimServer()
        proxyRestRequest = False
        del netServer, restDb
    else:
        # Remote repository
        overrideUrl = None
        if handle:
            overrideUrl = handle.getURL()
        serverCfg, proxyServer, shimRepo = _getProxyServer(context, fqdn,
                withCapsuleFilter=(handle is not None), overrideUrl=overrideUrl)
        items = req.uri.split('/')
        proxyRestRequest = (len(items) >= 4
                            and items[1] == 'repos'
                            and items[3] == 'api')

    if proxyRestRequest:
        # use proxyServer config for http proxy and auth data
        return proxyExternalRestRequest(context, fqdn, handle, authToken)
    if method == "POST":
        return post(port, secure, (proxyServer, shimRepo), cfg, context.db,
                req, authToken)
    elif method == "GET":
        return get(port, secure, (proxyServer, shimRepo), cfg, context.db,
                req, authToken, manager)
    elif method == "PUT":
        if proxyServer:
            return apachemethods.putFile(port, secure, proxyServer, req)
        else:
            return apache.HTTP_NOT_FOUND
    else:
        return apache.HTTP_METHOD_NOT_ALLOWED


def _getAuth(context):
    authToken = netserver.AuthToken(*webauth.getAuth(context.req))
    pysid = getHttpAuth(context.req)
    if isinstance(pysid, list):
        # No pysid found.
        return authToken

    sessions = SessionsTable(context.db)
    d = sessions.load(pysid)
    if not d:
        # Session is invalid.
        return authToken
    mintToken = d.get('_data', {}).get('authToken', None)
    if not mintToken:
        return authToken
    authToken.user = mintToken[0]
    authToken.password = netauth.ValidPasswordToken
    return authToken


def _getProxyServer(context, fqdn, withCapsuleFilter, overrideUrl):
    """Create a ProxyRepositoryServer for remote proxied calls."""
    cfg, req = context.cfg, context.req

    serverCfg = netserver.ServerConfig()
    serverCfg.proxyContentsDir = cfg.proxyContentsDir
    serverCfg.changesetCacheDir = cfg.proxyChangesetCacheDir
    serverCfg.tmpDir = cfg.proxyTmpDir
    serverCfg.proxyMap = cfg.getProxyMap()
    if overrideUrl:
        serverCfg.repositoryMap.append((fqdn, overrideUrl))

    restDb = None
    if withCapsuleFilter:
        restDb = _addCapsuleConfig(context, serverCfg, fqdn)
    if restDb:
        serverClass = ProxyRepositoryServer
    else:
        serverClass = proxy.ProxyRepositoryServer

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

    if ':' in cfg.siteDomainName:
        domain = cfg.siteDomainName
    else:
        domain = cfg.siteDomainName + ':%(port)d'
    urlBase = "%%(protocol)s://%s.%s/" % \
            (cfg.hostName, domain)
    # Entitlement and password injection used to live here, now
    # convertAuthToken handles it.

    proxyServer = serverClass(serverCfg, urlBase)
    if restDb:
        proxyServer.setRestDb(restDb)
    shimRepo = None
    return serverCfg, proxyServer, shimRepo
