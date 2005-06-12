#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

from mod_python import apache
from mod_python import util
from mod_python import Cookie

import base64
import os
import traceback
import sqlite3
import xmlrpclib
import zlib
import sys

from repository.netrepos import netserver
import conarycfg

from mint import config
from mint import users
from mint import projects
from mint import database
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
    if req.headers_in['Content-Type'] == "text/xml":
        authToken = getHttpAuth(req)
        if type(authToken) is int:
            return authToken

        if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
            return apache.HTTP_FORBIDDEN

        (params, method) = xmlrpclib.loads(req.read())

        if isSecure:
            protocol = "https"
        else:
            protocol = "http"

        if req.path_info.startswith("/conary"):
            wrapper = repos.callWrapper
            params = [protocol, port, method, authToken, params]
        else:
            server = mint_server.MintServer(cfg)
            wrapper = server.callWrapper
            params = [method, authToken, params]
            
        try:
            result = wrapper(*params)
        except (netserver.InsufficientPermission, users.PermissionDenied):
            return apache.HTTP_FORBIDDEN

        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
        encoding = req.headers_in.get('Accept-encoding', '')
        if len(resp) > 200 and 'zlib' in encoding:
            req.headers_out['Content-encoding'] = 'zlib'
            resp = zlib.compress(resp, 5)
        req.write(resp)
        return apache.OK
    else:
        if req.path_info.startswith("/conary"):
            webfe = cookie_http.CookieHttpHandler(req, cfg, repos)
            return webfe._methodHandler()
        else:
            webfe = app.MintApp(req, cfg)
            return webfe._handle()

def get(isSecure, repos, cfg, req):
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
            req.sendfile(path)

            if path.startswith(repos.tmpPath) and \
                    not(os.path.basename(path)[0:6].startswith('cache-')):
                os.unlink(path)

        return apache.OK
    else:
        if req.path_info.startswith("/conary"):
            webfe = cookie_http.CookieHttpHandler(req, cfg, repos)
            return webfe._methodHandler()
        else:
            webfe = app.MintApp(req, cfg)
            return webfe._handle()

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


def subhandler(req):
    repName = req.filename
    cfg = config.MintConfig()
    cfg.read(req.filename)
    # XXX hack, combine these names
    cfg.staticPath = cfg.staticUrl

    method = req.method.upper()
    port = req.server.port
    if not port:
        port = req.parsed_uri[apache.URI_PORT]
        if not port:
            port = 80
    secure = (port == 443)

    if not repositories.has_key(repName):
        db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        projectsTable = projects.ProjectsTable(db, cfg)
        try:
            projectId = projectsTable.getProjectIdByHostname(req.hostname)
        except database.ItemNotFound:
            return apache.HTTP_NOT_FOUND

        repositoryDir = os.path.join(cfg.reposPath, req.hostname)

        if os.path.basename(req.uri) == "changeset":
           rest = os.path.dirname(req.uri) + "/"
        else:
           rest = req.uri

        rest = req.uri
        # pull out any queryargs
        if '?' in rest:
            rest = req.uri.split("?")[0]

        # and throw away any subdir portion
        rest = req.uri[:-len(req.path_info)] + '/'
        
        urlBase = "%%(protocol)s://%s:%%(port)d" % \
                        (req.hostname) + rest
        
        buildLabel = req.hostname + "@rpl:devel"
        repMap = buildLabel + " http://" + req.hostname + "/conary/"
        repositories[repName] = netserver.NetworkRepositoryServer(
                                repositoryDir,
                                cfg.tmpPath,
                                urlBase, 
                                req.hostname,
                                {},
                                commitAction = cfg.commitAction % {'repMap': repMap, 'buildLabel': buildLabel},
                                cacheChangeSets = True,
                                logFile = None)

        repositories[repName].forceSecure = False
        repositories[repName].cfg = cfg
   
    repo = repositories[repName]
        
    if method == "POST":
	return post(port, secure, repo, cfg, req)
    elif method == "GET":
	return get(secure, repo, cfg, req)
    elif method == "PUT":
	return putFile(port, secure, repo, req)
    else:
	return apache.HTTP_METHOD_NOT_ALLOWED

def handler(req):
    if profiling:
        import hotshot
        prof = hotshot.Profile("/tmp/mint.prof")
        ret = prof.runcall(subhandler, req)
        prof.close()
    else:
        ret = subhandler(req)
    return ret

repositories = {}
