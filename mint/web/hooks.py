#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any waranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
# 

from mod_python import apache
from mod_python import util
import os
import traceback
import sqlite3
import xmlrpclib
import zlib

import conary
from repository.netrepos import netserver
from server.http import HttpHandler
import conarycfg

from web.webauth import getAuth
from mint import config
from mint import repos

BUFFER=1024 * 256

def checkAuth(req, repos):
    if not req.headers_in.has_key('Authorization'):
        return None
    else:
        authToken = getAuth(req)
        if type(authToken) != tuple:
            return authToken

        if not repos.auth.checkUserPass(authToken):
            return None
            
    return authToken

def post(port, isSecure, repos, httpHandler, req):
    authToken = getAuth(req)
    if type(authToken) is int:
        return authToken

    if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
        return apache.HTTP_FORBIDDEN

    if req.headers_in['Content-Type'] == "text/xml":
        (params, method) = xmlrpclib.loads(req.read())

        if isSecure:
            protocol = "https"
        else:
            protocol = "http"

        try:
            result = repos.callWrapper(protocol, port, method, authToken, 
                                       params)
        except netserver.InsufficientPermission:
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
        return httpHandler._methodHandler()

def get(isSecure, repos, httpHandler, req):
    uri = req.uri
    if uri.endswith('/'):
        uri = uri[:-1]
    cmd = os.path.basename(uri)
    fields = util.FieldStorage(req)

    authToken = getAuth(req)
    if authToken[0] != "anonymous" and not isSecure and repos.forceSecure:
        return apache.HTTP_FORBIDDEN
   
    if cmd == "changeset":
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
        return httpHandler._methodHandler()

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

def handler(req):
    repName = req.filename
    if not repositories.has_key(repName):
        cfg = config.MintConfig()
        cfg.read(req.filename)

        db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        reposTable = repos.ReposTable(db)
        try:
            reposId = reposTable[req.hostname]
        except KeyError:
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
                        (req.server.server_hostname) + rest

	repositories[repName] = netserver.NetworkRepositoryServer(
                                repositoryDir,
                                cfg.tmpPath,
				urlBase, 
                                req.hostname,
                                {},
				commitAction = None,
                                cacheChangeSets = True,
                                logFile = None)

	repositories[repName].forceSecure = False
        repositories[repName].cfg = cfg
    port = req.server.port
    if not port:
        port = req.parsed_uri[apache.URI_PORT]
        if not port:
            port = 80
    secure = (port == 443)
    
    repo = repositories[repName]
    httpHandler = HttpHandler(req, repo.cfg, repo)
    
    method = req.method.upper()

    if method == "POST":
	return post(port, secure, repo, httpHandler, req)
    elif method == "GET":
	return get(secure, repo, httpHandler, req)
    elif method == "PUT":
	return putFile(port, secure, repo, req)
    else:
	return apache.HTTP_METHOD_NOT_ALLOWED

repositories = {}
