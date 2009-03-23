#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

from mod_python import apache

import os
import re
import socket
import shutil
import sys
import tempfile
import time
import traceback
import urllib

from mint import config
from mint import users
from mint.lib import profile
from mint import mint_error
from mint import maintenance
from mint.db.projects import transTables
from mint.helperfuncs import extractBasePath
from mint.logerror import logWebErrorAndEmail
from mint.rest.server import restHandler
from mint.web import app
from mint.web.rpchooks import rpcHandler
from mint.web.catalog import catalogHandler
from mint.web.webhandler import normPath, setCacheControl, HttpError

from conary.web import webauth
from conary import dbstore, conarycfg
from conary import versions
from conary.dbstore import sqlerrors
from conary.lib import coveragehook
from conary.lib import util as conary_util
from conary.repository import shimclient
from conary.repository.netrepos import proxy
from conary.repository.netrepos import netserver
from conary.repository.transport import Transport

from conary.server import apachemethods

BUFFER=1024 * 256


# Global cached objects
db = None
cfg = None
repositories = {}
proxy_repository = None


def getProtocol(isSecure):
    return isSecure and "https" or "http"

def post(port, isSecure, repos, cfg, req):
    repos, shimRepo = repos

    protocol = getProtocol(isSecure)

    if req.headers_in['Content-Type'] == "text/xml":
        if not repos:
            return apache.HTTP_NOT_FOUND

        return apachemethods.post(port, isSecure, repos, req)
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo)
        return webfe._handle(normPath(req.uri[len(cfg.basePath):]))

CONARY_GET_COMMANDS = ["changeset", "getOpenPGPKey"]
def get(port, isSecure, repos, cfg, req):
    repos, shimRepo = repos

    protocol = getProtocol(isSecure)

    uri = req.uri
    if uri.endswith('/'):
        uri = uri[:-1]
    cmd = os.path.basename(uri)

    if cmd in CONARY_GET_COMMANDS:
        return apachemethods.get(port, isSecure, repos, req)
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo)
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

def getRepository(projectName, repName, dbName, cfg,
        req, conaryDb, dbTuple, localMirror, requireSigs, commitEmail):

    nscfg = netserver.ServerConfig()
    nscfg.externalPasswordURL = cfg.externalPasswordURL
    nscfg.authCacheTimeout = cfg.authCacheTimeout
    nscfg.requireSigs = requireSigs
    nscfg.serializeCommits = cfg.serializeCommits

    repositoryDir = os.path.join(cfg.reposPath, repName)

    nscfg.repositoryDB = dbTuple
    nscfg.changesetCacheDir = os.path.join(cfg.dataPath, 'cscache')
    nscfg.contentsDir = " ".join(x % repName for x in cfg.reposContentsDir.split(" "))

    nscfg.serverName = [repName]
    nscfg.tmpDir = os.path.join(cfg.reposPath, repName, "tmp")
    nscfg.logFile = cfg.reposLog and \
                    os.path.join(cfg.logPath, 'repository.log') \
                    or None
    nscfg.repositoryMap = getRepositoryMap(cfg)

    if os.path.basename(req.uri) == "changeset":
       rest = os.path.dirname(req.uri) + "/"
    else:
       rest = req.uri

    urlBase = "%%(protocol)s://%s:%%(port)d/repos/%s/" % \
        (req.hostname, projectName)

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

    if os.access(repositoryDir, os.F_OK):
        netRepos = netserver.NetworkRepositoryServer(nscfg, urlBase, conaryDb)

        if 'changesetCacheDir' in nscfg.keys():
            repos = proxy.SimpleRepositoryFilter(nscfg, urlBase, netRepos)
        else:
            repos = netRepos

        shim = shimclient.NetworkRepositoryServer(nscfg, urlBase, conaryDb)
    else:
        req.log_error("failed to open repository directory: %s" % repositoryDir)
        repos = shim = None
    return netRepos, repos, shim


def conaryHandler(req, cfg, pathInfo):
    maintenance.enforceMaintenanceMode(cfg)

    auth = webauth.getAuth(req)
    if type(auth) is int:
        return auth
    requireSigs = cfg.requireSigs
    if auth[0] == cfg.authUser:
        # don't require signatures for the internal user (this would break
        # group builder)
        requireSigs = False

    global db
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
    projectHostName, projectId, actualRepName, external, localMirror, commitEmail = \
            _resolveProjectRepos(db, hostName, domainName)

    # do not require signatures when committing to a local mirror
    if localMirror:
        requireSigs = False

    doReset = False
    reposDb = None

    if actualRepName and (localMirror or not external):
        # it's local
        dbName = actualRepName.translate(transTables[cfg.reposDBDriver])
        dbTuple = getReposDB(db, dbName, projectId, cfg)
        repHash = (actualRepName, req.hostname, dbTuple)

        # Check for a cached connection.
        if repHash in repositories:
            repServer, proxyServer, shimRepo = repositories[repHash]
            repServer.reopen()
        else:
            # Create a new connection.
            try:
                reposDb = dbstore.connect(dbTuple[1], dbTuple[0])
            except sqlerrors.DatabaseError, err:
                req.log_error("Error opening database %s: %s" %
                        (dbName, str(err)))
                raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

            repServer, proxyServer, shimRepo = getRepository(projectHostName,
                    actualRepName, dbName, cfg, req, reposDb, dbTuple,
                    localMirror, requireSigs, commitEmail)

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
        if cfg.useInternalConaryProxy and urllib.splittype(req.unparsed_uri)[0]:

            # Don't proxy stuff that should have been caught in the above if block
            # Conary >= 1.1.26 proxies will add a Via header for all
            # requests forwarded for the Conary Proxy. If it contains our
            # IP address and port, then we've already handled this request.
            via = req.headers_in.get("Via", "")
            myHostPort = "%s:%d" % (req.connection.local_ip,
                    req.connection.local_addr[1])
            if myHostPort in via:
                apache.log_error('Internal Conary Proxy was attempting an infinite loop (request %s, via %s)' % (req.hostname, via))
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
                    domain = cfg.siteDomainName + '%(port)d'
                urlBase = "%%(protocol)s://%s.%s/" % \
                        (cfg.hostName, domain)
                proxyServer = proxy_repository = proxy.ProxyRepositoryServer(
                        proxycfg, urlBase)

            # inject known authentication (userpass and entitlement)
            proxyServer.cfg.entitlement = conarycfg.EntitlementList()
            proxyServer.cfg.user = conarycfg.UserInformation()
            if cfg.injectUserAuth:
                _updateUserSet(db, proxyServer.cfg)
        else:
            proxyServer = None

        shimRepo = None

    try:
        if method == "POST":
            return post(port, secure, (proxyServer, shimRepo), cfg, req)
        elif method == "GET":
            return get(port, secure, (proxyServer, shimRepo), cfg, req)
        elif method == "PUT":
            return apachemethods.putFile(port, secure, proxyServer, req)
        else:
            return apache.HTTP_METHOD_NOT_ALLOWED
    finally:
        if doReset:
            repServer.reset()


def mintHandler(req, cfg, pathInfo):
    webfe = app.MintApp(req, cfg)
    return webfe._handle(pathInfo)

urls = (
    (r'^/changeset/',        conaryHandler),
    (r'^/conary/',           conaryHandler),
    (r'^/repos/',            conaryHandler),
    (r'^/catalog/',          catalogHandler),
    (r'^/api/',              restHandler),
    (r'^/xmlrpc/',           rpcHandler),
    (r'^/jsonrpc/',          rpcHandler),
    (r'^/xmlrpc-private/',   rpcHandler),
    (r'^/',                  mintHandler),
)


def getReposDB(db, dbName, projectId, cfg):
    cu = db.cursor()
    cu.execute("""SELECT driver, path
        FROM ReposDatabases JOIN ProjectDatabase USING (databaseId)
        WHERE projectId=?""", projectId)
    r = cu.fetchone()
    if r:
        apache.log_error("using alternate database connection: %s %s" % (r[0], r[1]), apache.APLOG_INFO)
        return r[0], r[1]
    else:
        return cfg.reposDBDriver, cfg.reposDBPath % dbName


def _updateUserSet(db, cfgObj):
    cu = db.cursor()
    cu.execute("""SELECT label, authType, username, password, entitlement
        FROM Labels WHERE authType IS NOT NULL AND authType != 'none'""")

    for label, authType, username, password, entitlement in cu.fetchall():
        host = versions.Label(label).getHost()
        if authType == 'userpass':
            cfgObj.user.addServerGlob(host, (username, password))
        elif authType == 'entitlement':
            cfgObj.entitlement.addEntitlement(host, entitlement)


def _resolveProjectRepos(db, hostname, domainname):
    # Start with some reasonable assumptions
    external = True
    localMirror = False
    projectHostName = None
    projectDomainName = None
    projectId = None
    actualRepName = possibleRepName = None
    commitEmail = None

    if domainname:
        extraWhere = "AND domainname = '%s'" % domainname
    else:
        extraWhere = ""

    # Determine if the project is local by checking the projects table
    cu = db.cursor()
    cu.execute("""SELECT projectId, domainname, external,
                     EXISTS(SELECT * FROM InboundMirrors
                     WHERE projectId=targetProjectId) AS localMirror, commitEmail
                  FROM Projects WHERE hostname=? %s""" % extraWhere, hostname)
    try:
        rs = cu.fetchone()
        if rs:
            projectId, projectDomainName, external, localMirror, commitEmail = rs
            projectHostName = hostname
            possibleRepName = "%s.%s" % (projectHostName, projectDomainName)

            # Optionally remap the repository name (forward lookup)
            cu.execute("SELECT toName FROM RepNameMap WHERE fromName = ?",
                    possibleRepName)
            rs = cu.fetchone()
            if rs:
                actualRepName = rs[0]
            else:
                actualRepName = possibleRepName

        if not actualRepName:
            # Reverse lookup in repNameMap (ugh)
            possibleRepName = "%s.%s" % (hostname, domainname)
            # XXX: This is not guaranteed to be unique, so we'll make it so.
            #      (not sure that this matters on rBA, actually)
            cu.execute("""SELECT fromName FROM repNameMap where toName = ? LIMIT 1""",\
                    possibleRepName)
            rs = cu.fetchone()
            if rs:
                fromName = rs[0]
                projectHostName = fromName[0:fromName.find('.')]
                projectDomainName = fromName[fromName.find('.')+1:]

                cu.execute("""SELECT projectId, external,
                                EXISTS(SELECT * FROM InboundMirrors
                                            WHERE projectId=targetProjectId) AS localMirror
                              FROM Projects WHERE hostname=? AND domainname=?""",
                              projectHostName, projectDomainName)
                rs = cu.fetchone()
                if rs:
                    projectId, external, localMirror = rs
                    actualRepName = possibleRepName

    except (IndexError, TypeError):
        import traceback
        tb = traceback.format_exc()
        apache.log_error("error in _resolveProjectRepos('%s'):" % hostname)
        for line in tb.split("\n"):
            apache.log_error(line, apache.APLOG_DEBUG)
        actualRepName = None

    return projectHostName, projectId, actualRepName, external, localMirror, commitEmail


def handler(req):
    coveragehook.install()
    if not req.hostname:
        return apache.HTTP_BAD_REQUEST

    # only reload the configuration file if it's changed
    # since our last read
    cfgPath = req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)

    global cfg
    if not cfg:
        cfg = config.getConfig(cfgPath)

    if "basePath" not in req.get_options():
        cfg.basePath = extractBasePath(normPath(req.uri), normPath(req.path_info))
        pathInfo = req.path_info
    else:
        cfg.basePath = req.get_options()['basePath']
        # chop off the provided base path
        pathInfo = normPath(req.uri[len(cfg.basePath):])

    global db
    if not db:
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    else:
        db.rollback()

    prof = profile.Profile(cfg)

    # reopen a dead database
    if db.reopen():
        req.log_error("reopened a dead database connection in hooks.py", apache.APLOG_WARNING)

    if not req.uri.startswith(cfg.basePath + 'setup/') and not cfg.configured:
        if req.uri == cfg.basePath + 'pwCheck':
            # allow pwCheck requests to go through without being
            # redirected - they will simply return "False"
            pass
        else:
            req.headers_out['Location'] = cfg.basePath + "setup/"
            raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

    prof.startHttp(req.uri)

    ret = apache.HTTP_NOT_FOUND
    try:
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                try:
                    ret = urlHandler(req, cfg, pathInfo)
                except HttpError, e:
                    raise apache.SERVER_RETURN, e.code
                except apache.SERVER_RETURN, e:
                    raise apache.SERVER_RETURN, e
                except mint_error.MaintenanceMode, e:
                    # this is a conary client, or an unknown python browser
                    if 'User-agent' in req.headers_in and \
                           req.headers_in['User-agent'] == Transport.user_agent:
                        return apache.HTTP_SERVICE_UNAVAILABLE
                    else:
                        # this page offers a way to log in. vice standard error
                        # we must force a redirect to ensure half finished
                        # work flowpaths don't trigger more errors.
                        setCacheControl(req, strict=True)
                        req.headers_out['Location'] = cfg.basePath + 'maintenance'
                        return apache.HTTP_MOVED_TEMPORARILY
                except:
                    # we only want to handle errors in production mode
                    if cfg.debugMode or req.bytes_sent > 0:
                        raise

                    # Generate a nice traceback and email it to
                    # interested parties
                    exception, e, bt = sys.exc_info()
                    logWebErrorAndEmail(req, cfg, exception, e, bt)
                    del exception, e, bt

                    # Send an error page to the user and set the status
                    # code to 500 (internal server error).
                    req.status = 500
                    try:
                        ret = mintHandler(req, cfg, '/unknownError')
                    except:
                        # Some requests cause MintApp to choke on setup
                        # We've already logged the error, so just display
                        # the apache ISE page.
                        ret = apache.HTTP_INTERNAL_SERVER_ERROR
                break
    finally:
        prof.stopHttp(req.uri)
        if db:
            db.rollback()
        coveragehook.save()
    return ret
