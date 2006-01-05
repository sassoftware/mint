#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

try:
    import coverage
    coverage.use_cache(True)
    coverage.start()
except ImportError:
    coverage = None

from mod_python import apache
from mod_python import util

import base64
import os
import xmlrpclib
import zlib
import re
import sys
import time
import traceback

from conary.lib import util as conaryutil
from conary.lib import epdb, log
from conary.repository.netrepos import netserver
from conary.repository.filecontainer import FileContainer
from conary.repository import changeset
from conary.repository import errors
from conary.repository import shimclient

from mint import config
from mint import mint_server
from mint import users
from webhandler import normPath, HttpError
import app
import cookie_http

profiling = False 
BUFFER=1024 * 256

def getHttpAuth(req):
    # special header to pass a session id through
    # instead of a real http authorization token
    if 'X-Session-Id' in req.headers_in:
        return req.headers_in['X-Session-Id']
 
    if not 'Authorization' in req.headers_in:
        return ('anonymous', 'anonymous')
    
    info = req.headers_in['Authorization'].split()
    if len(info) != 2 or info[0] != "Basic":
        return apache.HTTP_BAD_REQUEST

    try:
        authString = base64.decodestring(info[1])
    except:
        return apache.HTTP_BAD_REQUEST

    if authString.count(":") != 1:
        return apache.HTTP_BAD_REQUEST

    authToken = authString.split(":")

    return authToken

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
        result = result[1:]
        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
        encoding = req.headers_in.get('Accept-encoding', '')
        if len(resp) > 200 and 'deflate' in encoding:
            req.headers_out['Content-encoding'] = 'deflate'
            resp = zlib.compress(resp, 5)
        req.write(resp)
        return apache.OK
    else:
        webfe = app.MintApp(req, cfg, repServer = shimRepo)
        return webfe._handle(req.uri)

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
        return webfe._handle(req.uri)

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
    paths = normPath(req.uri).split("/")
    if paths[1] == "repos":
        # test suite hook: lop off any port specified in cfg file
        domainName = cfg.projectDomainName.split(":")[0]
        repName = paths[2] + "." + domainName
    else:
        repName = req.hostname
                        
    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (req.subprocess_env.get('HTTPS', 'off') == 'on')

    repHash = repName + req.hostname
    if not repositories.has_key(repHash) or 1:
        nscfg = netserver.ServerConfig()
        
        repositoryDir = os.path.join(cfg.reposPath, repName)
        nscfg.repositoryDB = ('sqlite', repositoryDir + '/sqldb')
        nscfg.cacheDB = ('sqlite', repositoryDir + '/cache.sql')
        nscfg.contentsDir = repositoryDir + '/contents/'
        
        nscfg.serverName = repName
        nscfg.tmpDir = os.path.join(cfg.reposPath, repName, "tmp")
        nscfg.logFile = os.path.join(repositoryDir, "contents.log")

        if os.path.basename(req.uri) == "changeset":
           rest = os.path.dirname(req.uri) + "/"
        else:
           rest = req.uri 

        # pull out any queryargs
        if '?' in rest:
            rest = req.uri.split("?")[0]

        urlBase = "%%(protocol)s://%s:%%(port)d" % \
                        (req.hostname) + rest
        
        # set up the commitAction
        buildLabel = repName + "@" + cfg.defaultBranch
        projectName = repName.split(".")[0]
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
            nscfg.commitAction = '''/usr/lib64/python2.4/site-packages/conary/commitaction 
                --module "/usr/lib/python2.4/site-packages/mint/rbuilderaction.py 
                  --user %%(user)s --url http://www.rpath.org/xmlrpc-private/" 
                --module "/usr/lib64/python2.4/site-packages/conary/changemail.py 
                  --user %(user)s --email desktop-commits@bizrace.com"'''
                                
        if os.access(repositoryDir, os.F_OK):
            repositories[repHash] = netserver.NetworkRepositoryServer(nscfg, urlBase)
            shim_repositories[repHash] = shimclient.NetworkRepositoryServer(nscfg, urlBase)

            repositories[repHash].forceSecure = cfg.SSL
            repositories[repHash].cfg = cfg
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

def xmlrpcHandler(req, cfg, pathInfo):
    if req.method.upper() != "POST":
        return apache.HTTP_METHOD_NOT_ALLOWED
    if req.headers_in['Content-Type'] != "text/xml":
        return apache.HTTP_NOT_FOUND

    authToken = getHttpAuth(req)
    if type(authToken) is int:
        return authToken
        
    (params, method) = xmlrpclib.loads(req.read())
    params = [method, authToken, params]
    
    if req.uri.startswith("/xmlrpc-private"):
        server = mint_server.MintServer(cfg, allowPrivate = True)
    elif req.uri.startswith("/xmlrpc"):
        server = mint_server.MintServer(cfg, allowPrivate = False)
    try:
        result = server.callWrapper(*params)
    except (errors.InsufficientPermission, mint_server.PermissionDenied):
        return apache.HTTP_FORBIDDEN

    resp = xmlrpclib.dumps((result,), methodresponse=1)
    req.content_type = "text/xml"
    encoding = req.headers_in.get('Accept-encoding', '')
    useragent = req.headers_in.get('User-Agent', '')
    if len(resp) > 200 and 'deflate' in encoding and 'MSIE' not in useragent:
        req.headers_out['Content-encoding'] = 'deflate'
        resp = zlib.compress(resp, 5)
    req.write(resp)
    return apache.OK

def mintHandler(req, cfg, pathInfo):
    webfe = app.MintApp(req, cfg)
    return webfe._handle(pathInfo)

urls = (
    (r'^/conary/',           conaryHandler),
    (r'^/xmlrpc/',           xmlrpcHandler),
    (r'^/xmlrpc-private/',   xmlrpcHandler),
    (r'^/repos/',            conaryHandler),
    (r'^/',                  mintHandler),
)

def logErrorAndEmail(req, cfg, exception, e, bt):
    c = req.connection
    req.add_common_vars()
    info_dict = {
        'local_addr'     : c.local_ip + ':' + str(c.local_addr[1]),
        'remote_addr'    : c.remote_ip + ':' + str(c.remote_addr[1]),
        'remote_host'    : c.remote_host,
        'remote_logname' : c.remote_logname,
        'aborted'        : c.aborted,
        'keepalive'      : c.keepalive,
        'double_reverse' : c.double_reverse,
        'keepalives'     : c.keepalives,
        'local_host'     : c.local_host,
        'connection_id'  : c.id,
        'notes'          : c.notes,
        'the_request'    : req.the_request,
        'proxyreq'       : req.proxyreq,
        'header_only'    : req.header_only,
        'protocol'       : req.protocol,
        'proto_num'      : req.proto_num,
        'hostname'       : req.hostname,
        'request_time'   : time.ctime(req.request_time),
        'status_line'    : req.status_line,
        'status'         : req.status,
        'method'         : req.method,
        'allowed'        : req.allowed,
        'headers_in'     : req.headers_in,
        'headers_out'    : req.headers_out,
        'uri'            : req.uri,
        'unparsed_uri'   : req.unparsed_uri,
        'args'           : req.args,
        'parsed_uri'     : req.parsed_uri,
        'filename'       : req.filename,
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
def handler(req):
    startTime = time.time()
    if not req.hostname:
        return apache.HTTP_BAD_REQUEST

    global cfg
    if not cfg:
        cfg = config.MintConfig()
        cfg.read(req.filename)

    if not req.uri.startswith('/setup/') and not cfg.configured:
        req.headers_out['Location'] = "/setup/"
        raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

    # normalize req path and base path
    pathInfo = normPath(req.uri)
    basePath = normPath(cfg.basePath)

    # strip off base path and normalize again
    pathInfo = pathInfo[len(basePath):]
    pathInfo = normPath(pathInfo)

    ret = apache.HTTP_NOT_FOUND
    for match, urlHandler in urls:
        if re.match(match, pathInfo):
            newPath = normPath(pathInfo[len(match)-1:])
            try:
                ret = urlHandler(req, cfg, newPath)
            except HttpError, e:
                raise apache.SERVER_RETURN, e.code
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
    if cfg.profiling:
        print >> sys.stderr, "WEB HIT: %.2fms" % ((time.time() - startTime) * 1000)
        sys.stderr.flush()
    if coverage:
        coverage.the_coverage.save()
    return ret
    
repositories = {}
shim_repositories = {}

if coverage:
    import atexit
    atexit.register(coverage.the_coverage.save)
