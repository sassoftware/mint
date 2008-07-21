#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import simplejson
import xmlrpclib

from mod_python import apache

from mint import config
from mint import server
from mint import maintenance
from mint.web.webhandler import getHttpAuth

from conary.lib import coveragehook
from conary.repository import errors

def rpcHandler(req, cfg, pathInfo = None):
    maintenance.enforceMaintenanceMode(cfg)
    isJSONrpc = isXMLrpc = allowPrivate = False

    # only handle POSTs
    if req.method.upper() != 'POST':
        return apache.HTTP_METHOD_NOT_ALLOWED

    if "allowPrivate" in req.get_options():
        allowPrivate = req.get_options()['allowPrivate']
    elif "xmlrpc-private" in req.uri.split("/")[1]:
        allowPrivate = True

    if req.headers_in['Content-Type'] == 'text/xml':
        isXMLrpc = True
    elif req.headers_in['Content-Type'].startswith('application/x-json'):
        isJSONrpc = True
    else:
        return apache.HTTP_BAD_REQUEST

    authToken = getHttpAuth(req)

    if type(authToken) is list:
        authToken = authToken[0:2] # throw away entitlement
    # instantiate a MintServer
    srvr = server.MintServer(cfg, allowPrivate = allowPrivate, req = req)

    # switch on XML/JSON here
    if isXMLrpc:
        (args, method) = xmlrpclib.loads(req.read())
    if isJSONrpc:
        (method, args) = simplejson.loads(req.read())

    # coax parameters into something MintServer likes
    params = [method, authToken, args]

    # go for it; return 403 if permission is denied
    try:
        # result is (isError, returnValues)
        result = srvr.callWrapper(*params)
    except (errors.InsufficientPermission, server.PermissionDenied):
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
    coveragehook.install()
    cfg = config.getConfig(req.filename)

    return rpcHandler(req, cfg)
