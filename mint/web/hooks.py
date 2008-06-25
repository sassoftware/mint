#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

from mod_python import apache
from mod_python import util

import os
import xmlrpclib
import zlib
import re
import stat
import shutil
import socket
import sys
import tempfile
import time
import traceback
import simplejson
import urllib

from mint import config
from mint import mirror
from mint import users
from mint import profile
from mint import mint_error
from mint import maintenance
from mint import server
from mint.helperfuncs import extractBasePath
from mint.projects import transTables
from mint.users import MailError
from mint.web import app
from mint.web.rpchooks import rpcHandler
from mint.web.webhandler import normPath, HttpError, getHttpAuth

from conary.web import webauth
from conary import dbstore, conarycfg
from conary import versions
from conary.dbstore import sqlerrors
from conary.lib import log
from conary.lib import coveragehook
from conary.lib import util as conary_util
from conary.repository import shimclient
from conary.repository.netrepos import proxy
from conary.repository.netrepos import netserver
from conary.repository.transport import Transport

from conary.server import apachemethods

BUFFER=1024 * 256

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

    if req.hostname != "conary.digium.com":
        urlBase = "%%(protocol)s://%s:%%(port)d/repos/%s/" % \
            (req.hostname, projectName)
    else:
        urlBase = "%%(protocol)s://%s:%%(port)d/conary/"% \
            req.hostname

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

        shim.forceSecure = repos.forceSecure = cfg.SSL
    else:
        req.log_error("failed to open repository directory: %s" % repositoryDir)
        repos = shim = None
    return repos, shim


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

    global db, cachedMySQLDb
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

    if actualRepName and (localMirror or not external):
        # it's local
        repHash = actualRepName + req.hostname + str(requireSigs)
        dbName = actualRepName.translate(transTables[cfg.reposDBDriver])
        reposDBDriver, reposDBPath, isDefault = getReposDB(db, dbName, projectId, cfg)

        # reposDb is the database connection we'll ultimately use
        # when creating a NetworkRepositoryServer object.
        reposDb = None

        # We cache the last accessed MySQLDb db connection if it
        # is a default (i.e. not alternate) database. This way, we
        # can use use() to switch databases rather than reconnect.
        if isDefault and reposDBDriver == 'mysql':

            # If we have the connection already, reset it.
            # If the database name changed, then use use() to switch.
            if cachedMySQLDb:
                try:
                    cachedMySQLDb.reopen()
                    cachedMySQLDb.rollback()
                    if cachedMySQLDb.dbName != dbName:
                        cachedMySQLDb.use(dbName)
                    reposDb = cachedMySQLDb
                except:
                    # Whiteout the cache if the client throws an error;
                    # we'll re-open below.
                    cachedMySQLDb = reposDb = None

        # If we still don't have a database; just create a new
        # connection.
        if not reposDb:
            try:
                reposDb = dbstore.connect(reposDBPath, reposDBDriver)
            except sqlerrors.DatabaseError, e:
                req.log_error("Error opening database %s: %s" % \
                        (dbName, str(e)))
                raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

            # Cache this connection IFF it's MySQL and was the default.
            if isDefault and reposDBDriver == 'mysql' \
                    and not cachedMySQLDb:
                cachedMySQLDb = reposDb

        # clear the repository cache if the db connection has changed
        if repHash in repositories and repositories[repHash]:
            if repositories[repHash].dbTuple != (reposDBDriver, reposDBPath):
                del repositories[repHash]
                del shim_repositories[repHash]

        if not repositories.has_key(repHash):
            repo, shimRepo = getRepository(projectHostName, actualRepName,
                    dbName, cfg, req, reposDb, (reposDBDriver, reposDBPath),
                    localMirror, requireSigs, commitEmail)
            if repo:
                repo.dbTuple = (reposDBDriver, reposDBPath)

            repositories[repHash] = repo
            shim_repositories[repHash] = shimRepo
        else:
            repo = repositories[repHash]
            shimRepo = shim_repositories[repHash]
    else:
        # it's completely external
        # use the Internal Conary Proxy if it's configured

        global proxy_repository
        if cfg.useInternalConaryProxy:

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
                repo = proxy_repository
            else:
                proxycfg = netserver.ServerConfig()
                proxycfg.proxyContentsDir = cfg.proxyContentsDir
                proxycfg.changesetCacheDir = cfg.proxyChangesetCacheDir
                proxycfg.tmpDir = cfg.proxyTmpDir

                # set a proxy (if it was configured)
                proxycfg.proxy = cfg.proxy

                urlBase = "%%(protocol)s://%s.%s:%%(port)d/" % \
                        (cfg.hostName, cfg.siteDomainName)
                repo = proxy.ProxyRepositoryServer(proxycfg, urlBase)
                repo.forceSecure = False
                proxy_repository = repo

            # inject known authentication (userpass and entitlement)
            repo.cfg.entitlement = conarycfg.EntitlementList()
            repo.cfg.user = conarycfg.UserInformation()
            if cfg.injectUserAuth:
                _updateUserSet(db, proxy_repository.cfg)
        else:
            repo = None

        shimRepo = None

    if method == "POST":
        return post(port, secure, (repo, shimRepo), cfg, req)
    elif method == "GET":
        return get(port, secure, (repo, shimRepo), cfg, req)
    elif method == "PUT":
        return apachemethods.putFile(port, secure, repo, req)
    else:
        return apache.HTTP_METHOD_NOT_ALLOWED


def mintHandler(req, cfg, pathInfo):
    webfe = app.MintApp(req, cfg)
    return webfe._handle(pathInfo)

urls = (
    (r'^/changeset/',        conaryHandler),
    (r'^/conary/',           conaryHandler),
    (r'^/repos/',            conaryHandler),
    (r'^/xmlrpc/',           rpcHandler),
    (r'^/jsonrpc/',          rpcHandler),
    (r'^/xmlrpc-private/',   rpcHandler),
    (r'^/',                  mintHandler),
)

def logErrorAndEmail(req, cfg, exception, e, bt):
    c = req.connection
    req.add_common_vars()
    info_dict = {
        'local_addr'     : c.local_ip + ':' + str(c.local_addr[1]),
        'local_host'     : c.local_host,
        'protocol'       : req.protocol,
        'hostname'       : req.hostname,
        'request_time'   : time.ctime(req.request_time),
        'status'         : req.status,
        'method'         : req.method,
        'headers_in'     : req.headers_in,
        'headers_out'    : req.headers_out,
        'uri'            : req.uri,
        'subprocess_env' : req.subprocess_env,
        'referer'        : req.headers_in.get('referer', 'N/A')
    }
    info_dict_small = {
        'local_addr'     : c.local_ip + ':' + str(c.local_addr[1]),
        'uri'            : req.uri,
        'request_time'   : time.ctime(req.request_time),
    }

    timeStamp = time.ctime(time.time())
    realHostName = socket.getfqdn()

    # Format large traceback to file
    (fd, tb_path) = tempfile.mkstemp('.txt', 'mint-error-')
    large = os.fdopen(fd, 'w')
    print >>large, 'Unhandled exception from mint web interface on %s:' \
        % realHostName
    print >>large, 'Time of occurrence: %s' % timeStamp
    print >>large, 'See also: %s' % tb_path
    print >>large
    conary_util.formatTrace(exception, e, bt, stream=large, withLocals=False)
    print >>large
    print >>large, 'Full stack:'
    print >>large
    conary_util.formatTrace(exception, e, bt, stream=large, withLocals=True)
    print >>large
    print >>large, 'Environment:'
    for key, val in sorted(info_dict.items()):
        print >>large, '%s: %s' % (key, val)
    large.seek(0)

    # Format small traceback to memory
    small = conary_util.BoundedStringIO()
    print >>small, 'Unhandled exception from mint web interface on %s:' \
        % realHostName
    conary_util.formatTrace(exception, e, bt, stream=small, withLocals=False)
    print >>small, 'Extended traceback at %s' % tb_path
    small.seek(0)

    # Log to apache
    apache.log_error('sending mail to %s and %s' % (cfg.bugsEmail, cfg.smallBugsEmail))
    shutil.copyfileobj(small, sys.stderr)
    sys.stderr.flush()
    small.seek(0)

    # send email
    base_exception = traceback.format_exception_only(exception, e)[-1].strip()
    if cfg.rBuilderOnline:
        subject = '%s: %s' % (realHostName, base_exception)
    else:
        extra = {'hostname': realHostName}
        subject = cfg.bugsEmailSubject % extra
    try:
        if cfg.bugsEmail:
            users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.bugsEmail, subject, large.read())
        if cfg.smallBugsEmail:
            users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.smallBugsEmail, subject, small.read())
    except MailError, e:
        apache.log_error("Failed to send e-mail to %s, reason: %s" % \
            (cfg.bugsEmail, str(e)))

    small.close()
    large.close()

cfg = None
db = None

def getReposDB(db, dbName, projectId, cfg):
    cu = db.cursor()
    cu.execute("""SELECT driver, path
        FROM ReposDatabases JOIN ProjectDatabase USING (databaseId)
        WHERE projectId=?""", projectId)
    r = cu.fetchone()
    if r:
        apache.log_error("using alternate database connection: %s %s" % (r[0], r[1]), apache.APLOG_INFO)
        return r[0], r[1], False
    else:
        return cfg.reposDBDriver, cfg.reposDBPath % dbName, True


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
    try:
        cu = db.cursor()
        cu.execute("""SELECT projectId, domainname, external,
                         EXISTS(SELECT * FROM InboundMirrors
                         WHERE projectId=targetProjectId) AS localMirror, commitEmail
                      FROM Projects WHERE hostname=? %s""" % extraWhere, hostname)
    except sqlerrors.CursorError:
        # until schema migration hits, we won't have a commitEmail field
        cu = db.cursor()
        cu.execute("""SELECT projectId, domainname, external,
                         EXISTS(SELECT * FROM InboundMirrors
                         WHERE projectId=targetProjectId) AS localMirror, '' as commitEmail
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
                        req.err_headers_out['Cache-Control'] = "no-store"
                        req.headers_out['Location'] = cfg.basePath + 'maintenance'
                        return apache.HTTP_MOVED_TEMPORARILY
                except:
                    # we only want to handle errors in production mode
                    if cfg.debugMode or req.bytes_sent > 0:
                        raise

                    # Generate a nice traceback and email it to
                    # interested parties
                    exception, e, bt = sys.exc_info()
                    logErrorAndEmail(req, cfg, exception, e, bt)

                    # Send an error page to the user and set the status
                    # code to 500 (internal server error).
                    req.status = 500
                    ret = urlHandler(req, cfg, '/unknownError')
                break
    finally:
        prof.stopHttp(req.uri)
        coveragehook.save()
    return ret

cfg = None
cachedMySQLDb = None
repositories = {}
shim_repositories = {}
proxy_repository = None
