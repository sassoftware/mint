#
# Copyright (c) SAS Institute Inc.
#

import logging
import base64
import socket
from webob import exc as web_exc

from mint import maintenance
from mint.rest.errors import ProductNotFound

from conary.repository import transport
from conary.repository.netrepos import proxy
from conary.repository.netrepos import netserver
from conary.server import wsgi_hooks

log = logging.getLogger(__name__)


class MintConaryHandler(wsgi_hooks.ConaryHandler):

    def __init__(self, context):
        wsgi_hooks.ConaryHandler.__init__(self, None)
        self.context = context

    def _loadCfg(self):
        req, cfg, manager = self.context.req, self.context.cfg, self.context.rm
        maintenance.enforceMaintenanceMode(cfg)

        fqdn = hostName = None
        if req.path_info_peek() == 'repos':
            req.path_info_pop()
            hostPart = req.path_info_pop()
            if not hostPart:
                raise web_exc.HTTPNotFound()
            if '.' in hostPart:
                fqdn = hostPart
                if fqdn.endswith('.'):
                    fqdn = fqdn[:-1]
            else:
                hostName = hostPart
        else:
            for x in range(req.path_info.count('/') - 1):
                req.path_info_pop()
            if 'x-conary-servername' in req.headers:
                fqdn = req.headers['x-conary-servername']
            else:
                fqdn = req.host.split(':')[0]
        self.isSecure = req.scheme == 'https'

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
            log.warning("Unknown project %s in request for %s",
                    hostName, req.url)
            raise web_exc.HTTPNotFound()
        elif 'x-conary-proxy-host' not in req.headers:
            log.warning("Request for unknown repository %s via URL %s",
                    fqdn, req.url)
            raise web_exc.HTTPNotFound()

        # Determine the user's authorization with respect to the rBuilder
        # project, if there is one.
        authToken = self.context.req.environ['mint.authToken']
        if handle:
            # Convert mint user/pass into abstract repository roles, if the
            # user is successfully authenticated to mint.
            authToken = handle.convertAuthToken(authToken, useRepoDb=True)

        if handle and handle.hasDatabase:
            # Local database
            serverCfg = handle.getNetServerConfig()
            netServer = handle.getServer(netserver.NetworkRepositoryServer,
                    serverCfg)
            proxyClass = proxy.SimpleRepositoryFilter
            proxyServer = proxyClass(serverCfg, handle.getURL(), netServer)
            contentsStore = netServer.repos.contentsStore
            shimRepo = handle.getShimServer()
        else:
            # Remote repository
            netServer = contentsStore = None
            overrideUrl = handle.getURL() if handle else None
            serverCfg, proxyServer, shimRepo = self._getProxyServer(fqdn,
                    overrideUrl=overrideUrl,
                    )

        self.fqdn = fqdn
        self.handle = handle

        self.auth = authToken
        self.cfg = serverCfg
        self.repositoryServer = netServer
        self.shimServer = shimRepo
        self.proxyServer = proxyServer
        self.contentsStore = contentsStore

    def _loadAuth(self):
        pass

    def _getProxyServer(self, fqdn, overrideUrl):
        """Create a ProxyRepositoryServer for remote proxied calls."""
        cfg, req = self.context.cfg, self.request

        serverCfg = netserver.ServerConfig()
        serverCfg.proxyContentsDir = cfg.proxyContentsDir
        serverCfg.changesetCacheDir = cfg.proxyChangesetCacheDir
        serverCfg.tmpDir = cfg.proxyTmpDir
        serverCfg.proxyMap = cfg.getProxyMap()
        if overrideUrl:
            serverCfg.repositoryMap.append((fqdn, overrideUrl))

        restDb = None
        serverClass = proxy.ProxyRepositoryServer

        # Conary >= 1.1.26 proxies will add a Via header for all
        # requests forwarded for the Conary Proxy. If it contains our
        # IP address and port, then we've already handled this request.
        via = req.headers.get("Via", "")
        if socket.gethostname() in via:
            log.error('Internal Conary Proxy was attempting an infinite '
                    'loop (request %s, via %s)' % (req.host, via))
            raise web_exc.HTTPBadGateway()

        basicUrl = self.context.req.application_url
        if not basicUrl.endswith('/'):
            basicUrl += '/'
        proxyServer = serverClass(serverCfg, basicUrl)
        if restDb:
            proxyServer.setRestDb(restDb)
        shimRepo = None
        return serverCfg, proxyServer, shimRepo

    def getApi(self):
        """Handle proxied REST requests"""
        if self.repositoryServer:
            # Regular, local repository
            return super(MintConaryHandler, self).getApi()
        # FIXME: this only works with entitlements, not user:password

        # get the upstream repo url and label
        if self.handle:
            urlBase = self.handle.getURL()
            if not urlBase.endswith('/'):
                urlBase += '/'
            urlBase += 'api'
        else:
            # no external project?  maybe it's a non-entitled platform
            found = False
            for label in self.context.cfg.availablePlatforms:
                if label.split('@')[0].lower() == self.fqdn.lower():
                    urlBase = '%s://%s/conary/api' % (self.request.scheme,
                            self.fqdn)
                    found = True
                    break
            if not found:
                raise web_exc.HTTPNotFound("Could not proxy request to "
                        "unknown repository '%s'" % self.fqdn)
        url = urlBase + self.request.path_info
        if self.request.query_string:
            url += '?' + self.request.query_string
        # build the entitlement to send in the header
        l = []
        for entitlement in self.auth.entitlements:
            if entitlement[0] is None:
                l.append("* %s" % (base64.b64encode(entitlement[1])))
            else:
                l.append("%s %s" % (entitlement[0],
                                    base64.b64encode(entitlement[1])))
        entitlement = ' '.join(l)

        opener = transport.URLOpener(proxyMap=self.context.cfg.getProxyMap())
        headers = [
                ('X-Conary-Servername', self.fqdn),
                ('User-Agent', transport.Transport.user_agent),
                ]
        if entitlement:
            headers.append(('X-Conary-Entitlement', entitlement))

        # make the request
        try:
            f = opener.open(url, headers=headers)
        except Exception, err:
            if getattr(err, 'errcode', None) == 403:
                raise web_exc.HTTPForbidden()
            else:
                # translate all errors to a 502
                log.error("Cannot proxy REST request to %s: %s", urlBase, err)
                return web_exc.HTTPBadGateway("Error proxying REST request")

        # copy response headers from upstream
        skippedHeaders = ('content-length', 'server', 'connection', 'date',
                'transfer-encoding')
        response = self.responseFactory()
        for header in f.headers.keys():
            if header.lower() not in skippedHeaders:
                response.headers[header.title()] = f.headers.get(header)

        # translate the response
        contentType = f.headers.get('content-type', '').split(';')[0]
        if contentType in ('text/xml', 'application/xml'):
            myUrlBase = self.request.application_url
            l = []
            for line in f:
                # rewrite hrefs to point at ourself
                l.append(line.replace(urlBase, myUrlBase))
            response.body = ''.join(l)
            f.close()
        else:
            if f.headers.get('Content-Length'):
                response.headers['Content-Length'] = f.headers['Content-Length']
            response.body_file = f
        return response


def conaryHandler(context):
    return MintConaryHandler(context).handleRequest(context.req)
