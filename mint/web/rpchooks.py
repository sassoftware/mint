#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import base64
import sys
import xmlrpclib
import simplejson

from conary.repository import errors
from mod_python import apache
from mint import config
from mint import mint_server
from webhandler import getHttpAuth

def rpcHandler(req, cfg, pathInfo = None):
    isJSONrpc = isXMLrpc = allowPrivate = False

    # only handle POSTs
    if req.method.upper() != 'POST':
        return apache.HTTP_METHOD_NOT_ALLOWED

    if "allowPrivate" in req.get_options():
        allowPrivate = req.get_options()['allowPrivate']

    if req.headers_in['Content-Type'] == 'text/xml':
        isXMLrpc = True
    elif req.headers_in['Content-Type'] == 'application/x-json':
        isJSONrpc = True
    else:
        return apache.HTTP_BAD_REQUEST

    authToken = getHttpAuth(req)

    # instantiate a MintServer
    server = mint_server.MintServer(cfg, allowPrivate = allowPrivate, req = req)

    # switch on XML/JSON here
    if isXMLrpc:
        (paramList, method) = xmlrpclib.loads(req.read())
    if isJSONrpc:
        (method, paramList) = simplejson.loads(req.read())

    # coax parameters into something MintServer likes
    params = [method, authToken, paramList]

    # go for it; return 403 if permission is denied
    try:
        # result is (isError, returnValues)
        result = server.callWrapper(*params)
    except (errors.InsufficientPermission, mint_server.PermissionDenied):
        return apache.HTTP_FORBIDDEN

    # create a response
    if isXMLrpc:
        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
    elif isJSONrpc:
        resp = simplejson.dumps(result[1])
        req.content_type = "application/x-json"

    # write repsonse
    req.write(resp)
    return apache.OK

def handler(req):
    cfg = config.MintConfig()
    cfg.read(req.filename)

    return rpcHandler(req, cfg)
