#
# Copyright (c) 2005-2006 rPath, Inc.
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
import sys
import time
import traceback
import simplejson

from conary.lib import util as conaryutil
from conary.lib import epdb, log
from conary import dbstore
from conary.dbstore import sqlerrors
from conary.repository.netrepos import netserver
from conary.repository.filecontainer import FileContainer
from conary.repository import changeset
from conary.repository import errors
from conary.repository import shimclient
from conary.repository.transport import Transport

from mint import config
from mint import mint_server
from mint import mirror
from mint import users
from mint import profile
from mint import mint_error
from mint.helperfuncs import extractBasePath
from mint.projects import mysqlTransTable
from webhandler import normPath, HttpError, getHttpAuth
from rpchooks import rpcHandler
import app

BUFFER=1024 * 256

def checkAuth(req, repos):
    if not req.headers_in.has_key('Authorization'):
        return None
    else:
        authToken = getHttpAuth(req)
        if type(authToken) != tuple:
            return authToken

        if not repos.auth.checkUserPass(authToken):
            return None

    return authToken

def post(port, isSecure, repos, cfg, req):
    repos, shimRepo = repos

    if isSecure:
        protocol = "https"
    else:
        protocol = "http"

    if req.headers_in['Content-Type'] == "text/xml":
        if not repos:
            return apache.HTTP_NOT_FOUND

        encoding = req.headers_in.get('Content-Encoding', None)
        data = req.read()
        if encoding == 'deflate':
            data = zlib.decompress(data)

        authToken = getHttpAuth(req)
        if type(authToken) is int:
            return authToken

        if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
            return apache.HTTP_FORBIDDEN

        (params, method) = xmlrpclib.loads(data)

        wrapper = repos.callWrapper
        authToken = (authToken[0], authToken[1], None, None)
        params = [protocol, port, method, authToken, params]
        try:
            result = wrapper(*params)
        except (errors.InsufficientPermission):
            sys.stderr.flush()
            return apache.HTTP_FORBIDDEN

        # take off the usedAnonymous flag
        usedAnonymous = result[0]
        result = result[1:]
        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
        encoding = req.headers_in.get('Accept-encoding', '')
        if len(resp) > 200 and 'deflate' in encoding:
            req.headers_out['Content-encoding'] = 'deflate'
            resp = zlib.compress(resp, 5)
        if usedAnonymous:
            req.headers_out["X-Conary-UsedAnonymous"] = "1"
        req.write(resp)
        return apache.OK
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo)
        return webfe._handle(req.path_info)

def get(port, isSecure, repos, cfg, req):
    repos, shimRepo = repos

    def _writeNestedFile(req, name, tag, size, f, sizeCb):
        if changeset.ChangedFileTypes.refr[4:] == tag[2:]:
            path = f.read()
            size = os.stat(path).st_size
            tag = tag[0:2] + changeset.ChangedFileTypes.file[4:]
            sizeCb(size, tag)
            req.sendfile(path)
        else:
            sizeCb(size, tag)
            req.write(f.read())

    if isSecure:
        protocol = "https"
    else:
        protocol = "http"

    uri = req.uri
    if uri.endswith('/'):
        uri = uri[:-1]
    cmd = os.path.basename(uri)
    fields = util.FieldStorage(req)

    if cmd == "changeset":
        authToken = getHttpAuth(req)
        if type(authToken) is int:
            return authToken
        if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
            return apache.HTTP_FORBIDDEN

        authToken = (authToken[0], authToken[1], None, None)
        localName = repos.tmpPath + "/" + req.args + "-out"
        size = os.stat(localName).st_size

        if localName.endswith(".cf-out"):
            try:
                f = open(localName, "r")
            except IOError:
                self.send_error(404, "File not found")
                return None

            os.unlink(localName)

            items = []
            totalSize = 0
            for l in f.readlines():
                (path, size) = l.split()
                size = int(size)
                totalSize += size
                items.append((path, size))
            del f
        else:
            size = os.stat(localName).st_size;
            items = [ (localName, size) ]
            totalSize = size

        req.content_type = "application/x-conary-change-set"
        for (path, size) in items:
            if path.endswith('.ccs-out'):
                cs = FileContainer(open(path))
                cs.dump(req.write,
                        lambda name, tag, size, f, sizeCb:
                            _writeNestedFile(req, name, tag, size, f,
                                             sizeCb))

                del cs
            else:
                req.sendfile(path)

            if path.startswith(repos.tmpPath) and \
                    not(os.path.basename(path)[0:6].startswith('cache-')):
                os.unlink(path)

        return apache.OK
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo)
        return webfe._handle(req.path_info)

def putFile(port, isSecure, repos, req):
    if not isSecure and repos.forceSecure:
        return apache.HTTP_FORBIDDEN

    path = repos.tmpPath + "/" + req.args + "-in"
    size = os.stat(path).st_size
    if size != 0:
	return apache.HTTP_UNAUTHORIZED

    f = open(path, "w+")
    s = req.read(BUFFER)
    while s:
	f.write(s)
	s = req.read(BUFFER)

    f.close()

    return apache.OK

def conaryHandler(req, cfg, pathInfo):
    if cfg.maintenanceMode:
        raise mint_error.MaintenanceMode

    paths = normPath(req.uri).split("/")
    if "repos" in paths:
        # test suite hook: lop off any port specified in cfg file
        domainName = cfg.projectDomainName.split(":")[0]
        hostName = paths[paths.index('repos')+1]
        repName = hostName + "." + domainName
    else:
        repName = req.hostname

    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (req.subprocess_env.get('HTTPS', 'off') == 'on')

    global db
    repNameMap = getRepNameMap(db)
    projectName = repName.split(".")[0]
    if repName in repNameMap:
        repName = repNameMap[repName]
        req.log_error("remapping repository name: %s" % repName)

    repHash = repName + req.hostname

    if cfg.reposDBDriver == "sqlite":
        db = None
        dbName = repName
    else:
        # XXX mysql-specific hack--this needs to be abstracted out
        dbName = repName.translate(mysqlTransTable)
        try:
            db.rollback() # roll back any hanging transactions
            db.use(dbName)
        except sqlerrors.DatabaseError:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    if not repositories.has_key(repHash):
        nscfg = netserver.ServerConfig()

        repositoryDir = os.path.join(cfg.reposPath, repName)

        nscfg.repositoryDB = (cfg.reposDBDriver, cfg.reposDBPath % dbName)
        nscfg.cacheDB = ('sqlite', repositoryDir + '/cache.sql')

        nscfg.contentsDir = " ".join(x % repName for x in cfg.reposContentsDir)

        nscfg.serverName = repName
        nscfg.tmpDir = os.path.join(cfg.reposPath, repName, "tmp")

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

        if cfg.commitAction:
            nscfg.commitAction = cfg.commitAction % {'repMap': repName + " " + repMapStr,
                                               'buildLabel': buildLabel,
                                               'projectName': projectName,
                                               'commitEmail': cfg.commitEmail,
                                               'basePath' : cfg.basePath}
        else:
            nscfg.commitAction = None

        # XXX hack to override commitAction for foresight until foresight
        # switches to our mailing lists.
        if req.hostname == "foresight.rpath.org":
            nscfg.commitAction = '''/usr/lib64/python2.4/site-packages/conary/commitaction --module "/usr/lib/python2.4/site-packages/mint/rbuilderaction.py --user %%(user)s --url http://www.rpath.org/xmlrpc-private/" --module "/usr/lib64/python2.4/site-packages/conary/changemail.py --user %(user)s --email desktop-commits@bizrace.com"'''
        elif req.hostname == "conary.digium.com":
            # another hack that needs to be generalized
            nscfg.commitAction = '/usr/lib64/python2.4/site-packages/conary/commitaction --module "/usr/lib/python2.4/site-packages/mint/rbuilderaction.py --user %%(user)s --url http://www.rpath.org/xmlrpc-private/" --module "/usr/lib64/python2.4/site-packages/conary/changemail.py --user %(user)s --email digium-commits@lists.rpath.org"'

        if os.access(repositoryDir, os.F_OK):
            repositories[repHash] = netserver.NetworkRepositoryServer(nscfg, urlBase, db)
            shim_repositories[repHash] = shimclient.NetworkRepositoryServer(nscfg, urlBase, db)

            repositories[repHash].forceSecure = cfg.SSL
        else:
            repositories[repHash] = None
            shim_repositories[repHash] = None

    repo = repositories[repHash]
    shimRepo = shim_repositories[repHash]

    if method == "POST":
        return post(port, secure, (repo, shimRepo), cfg, req)
    elif method == "GET":
        return get(port, secure, (repo, shimRepo), cfg, req)
    elif method == "PUT":
        return putFile(port, secure, repo, req)
    else:
        return apache.HTTP_METHOD_NOT_ALLOWED


def mintHandler(req, cfg, pathInfo):
    webfe = app.MintApp(req, cfg)
    return webfe._handle(pathInfo)

urls = (
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
    # log error
    log.error('[%s] Unhandled exception from mint web interface: %s: %s', timeStamp, exception.__name__, e)
    log.error('sending mail to %s and %s' % (cfg.bugsEmail, cfg.smallBugsEmail))
    # send email
    body = 'Unhandled exception from mint web interface:\n\n%s: %s\n\n' %(exception.__name__, e)
    body += 'Time of occurrence: %s\n\n' %timeStamp
    body += ''.join( traceback.format_tb(bt))
    body += '\nConnection Information:\n'
    for key, val in sorted(info_dict.items()):
        body += '\n' + key + ': ' + str(val)

    body_small = 'Mint Exception: %s: %s' % (exception.__name__, e)
    for key, val in sorted(info_dict_small.items()):
        body_small += '\n' + key + ': ' + str(val)

    if cfg.bugsEmail:
        users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                 cfg.bugsEmail, cfg.bugsEmailSubject, body)
    if cfg.smallBugsEmail:
        users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                 cfg.smallBugsEmail, cfg.bugsEmailSubject, body_small)


cfg = None
cfgMTime = 0
db = None

def getRepNameMap(db):
    d = {}

    # wrap this in a try/except to avoid first-hit problems
    # before RepNameMap even exists.
    try:
        if cfg.dbDriver != "sqlite":
            db.use(cfg.dbPath.split("/")[-1])
        cu = db.cursor()
        cu.execute("SELECT fromName, toName FROM RepNameMap")
        for r in cu.fetchall():
            d.update({r[0]: r[1]})
    except Exception, e:
        apache.log_error("ignoring exception fetching RepNameMap: %s" % str(e))

    return d

def handler(req):
    if not req.hostname:
        return apache.HTTP_BAD_REQUEST

    # only reload the configuration file if it's changed
    # since our last read
    global cfg, cfgMTime
    mtime = os.stat(req.filename)[stat.ST_MTIME]
    if mtime > cfgMTime:
        cfg = config.MintConfig()
        cfg.read(req.filename)
        cfgMTime = mtime

    if os.path.exists(cfg.maintenanceLockPath):
        cfg.maintenanceMode = True
    else:
        # must be explicit or the server won't come back without a poke.
        cfg.maintenanceMode = False

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

    prof = profile.Profile(cfg)

    # reopen a dead database
    if db.reopen():
        req.log_error("reopened a dead database connection in hooks.py")

    if not req.uri.startswith('/setup/') and not cfg.configured:
        req.headers_out['Location'] = "/setup/"
        raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

    prof.startHttp(req.uri)

    ret = apache.HTTP_NOT_FOUND
    try:
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                newPath = normPath(pathInfo[len(match)-1:])
                try:
                    ret = urlHandler(req, cfg, newPath)
                except HttpError, e:
                    raise apache.SERVER_RETURN, e.code
                except apache.SERVER_RETURN, e:
                    raise apache.SERVER_RETURN, e
                except mint_error.MaintenanceMode, e:
                    # this is a conary client, or an unknown python browser
                    if 'User-agent' in req.headers_in and \
                           req.headers_in['User-agent'] == Transport.user_agent:
                        return apache.HTTP_FORBIDDEN
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
                    # only handle actual mint errors
                    if match !='^/':
                        raise
                    exception, e, bt = sys.exc_info()
                    logErrorAndEmail(req, cfg, exception, e, bt)
                    ret = urlHandler(req, cfg, '/unknownError')
                break
    finally:
        prof.stopHttp(req.uri)
    return ret

repositories = {}
shim_repositories = {}
