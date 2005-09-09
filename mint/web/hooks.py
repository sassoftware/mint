#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
from mod_python import apache
from mod_python import util

import base64
import os
import xmlrpclib
import zlib
import re
import sys

from lib import epdb
from repository.netrepos import netserver
from repository.filecontainer import FileContainer
from repository import changeset

from mint import config
from mint import mint_server
from webhandler import normPath
import app
import cookie_http

profiling = False 
BUFFER=1024 * 256

def getHttpAuth(req):
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
    if isSecure:
        protocol = "https"
    else:
        protocol = "http"

    if req.headers_in['Content-Type'] == "text/xml":
        authToken = getHttpAuth(req)
        if type(authToken) is int:
            return authToken
        
        if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
            return apache.HTTP_FORBIDDEN

        (params, method) = xmlrpclib.loads(req.read())

        wrapper = repos.callWrapper
        params = [protocol, port, method, authToken, params]
        try:
            result = wrapper(*params)
        except (netserver.InsufficientPermission):
            sys.stderr.flush()
            return apache.HTTP_FORBIDDEN

        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
        encoding = req.headers_in.get('Accept-encoding', '')
        if len(resp) > 200 and 'deflate' in encoding:
            req.headers_out['Content-encoding'] = 'deflate'
            resp = zlib.compress(resp, 5)
        # FIXME: 'zlib' is not RFC 2616 (HTTP 1.1) compliant
        # and should be removed after a deprecation period
        elif len(resp) > 200 and 'zlib' in encoding:
            req.headers_out['Content-encoding'] = 'zlib'
            resp = zlib.compress(resp, 5)
        req.write(resp)
        return apache.OK
    else:
        webfe = cookie_http.CookieHttpHandler(req, cfg, repos, protocol, port)
        return webfe._methodHandler()

def get(port, isSecure, repos, cfg, req):
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
        webfe = cookie_http.CookieHttpHandler(req, cfg, repos, protocol, port)
        return webfe._methodHandler()

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
    if req.hostname == cfg.reposHost + "." + cfg.domainName:
        repName = pathInfo.split("/")[1] + "." + cfg.domainName
    else:
        repName = req.hostname

    method = req.method.upper()
    port = req.connection.local_addr[1]
    secure = (port == 443)

    if not repositories.has_key(repName):
        repositoryDir = os.path.join(cfg.reposPath, repName)
        tmpPath = os.path.join(cfg.reposPath, repName, "tmp")

        if os.path.basename(req.uri) == "changeset":
           rest = os.path.dirname(req.uri) + "/"
        else:
           rest = pathInfo

        # pull out any queryargs
        if '?' in rest:
            rest = req.uri.split("?")[0]

        urlBase = "%%(protocol)s://%s:%%(port)d" % \
                        (req.hostname) + rest
        
        # set up the commitAction
        # FIXME: don't hardcode @rpl:devel
        buildLabel = repName + "@rpl:devel"
        projectName = repName.split(".")[0]
        if req.hostname == cfg.reposHost + "." + cfg.domainName:
            repMapStr = "http://%s/%s/" % (req.hostname, projectName)
        else:   
            repMapStr = "http://%s/conary/" % (req.hostname)
           
        repMap = {buildLabel: repMapStr,
                  'conary.rpath.com': 'https://conary-commits.rpath.com/conary/',
                  'contrib.rpath.com': 'https://conary-commits.rpath.com/contrib/'}
        if cfg.commitAction:
            commitAction = cfg.commitAction % {'repMap': buildLabel + " " + repMapStr,
                                               'buildLabel': buildLabel,
                                               'projectName': projectName}
        else:
            commitAction = None

        if os.access(repositoryDir, os.F_OK):
            repositories[repName] = netserver.NetworkRepositoryServer(
                                        repositoryDir,
                                        tmpPath,
                                        urlBase, 
                                        repName,
                                        repMap,
                                        commitAction = commitAction,
                                        cacheChangeSets = True,
                                        logFile = None
                                    )
       
        repositories[repName].forceSecure = False
        repositories[repName].cfg = cfg
   
    repo = repositories[repName]
        
    if method == "POST":
	return post(port, secure, repo, cfg, req)
    elif method == "GET":
	return get(port, secure, repo, cfg, req)
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
    except (netserver.InsufficientPermission, mint_server.PermissionDenied):
        return apache.HTTP_FORBIDDEN

    resp = xmlrpclib.dumps((result,), methodresponse=1)
    req.content_type = "text/xml"
    encoding = req.headers_in.get('Accept-encoding', '')
    if len(resp) > 200 and 'deflate' in encoding:
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
    (r'^/',                  mintHandler),
)

def handler(req):
    cfg = config.MintConfig()
    cfg.read(req.filename)

    # normalize req path and base path
    pathInfo = normPath(req.uri)
    basePath = normPath(cfg.basePath)

    # strip off base path and normalize again
    pathInfo = pathInfo[len(basePath):]
    pathInfo = normPath(pathInfo)

    # special case for http://$reposHost.$domainName/conary/
    if req.hostname == "%s.%s" % (cfg.reposHost, cfg.domainName):
        return conaryHandler(req, cfg, pathInfo)

    for match, urlHandler in urls:
        if re.match(match, pathInfo):
            newPath = normPath(pathInfo[len(match)-1:])
            return urlHandler(req, cfg, newPath)
    return apache.HTTP_NOT_FOUND

repositories = {}
